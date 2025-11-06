"""
Reference resolver for Terraform configurations.
Resolves references, evaluates functions, and populates computed values.
"""

import base64
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tfkit.inspector.models import (
    AttributeType,
    AttributeValue,
    ReferenceType,
    TerraformAttribute,
    TerraformBlock,
    TerraformFunction,
    TerraformModule,
    TerraformObjectType,
    TerraformReference,
)


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected."""

    pass


class ReferenceResolver:
    """
    Resolves Terraform references and evaluates functions.
    """

    def __init__(
        self, module: TerraformModule, terraform_vars: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize resolver with a parsed module.

        Args:
            module: Parsed TerraformModule
            terraform_vars: Optional dictionary of variable values to use for resolution
        """
        self.module = module
        self.terraform_vars = terraform_vars or {}

        # Resolution cache to avoid re-resolving
        self._resolution_cache: Dict[str, Any] = {}

        # Track resolution chain to detect circular dependencies
        self._resolution_stack: Set[str] = set()

        # Track partially resolved locals to handle self-references
        self._partial_locals: Dict[str, Dict[str, Any]] = {}

    # ========================================================================
    # MAIN RESOLUTION METHODS
    # ========================================================================

    def resolve_module(self) -> TerraformModule:
        """
        Resolve all references in the module.

        Returns:
            The same module with resolved values populated
        """
        # First pass: Resolve variables and locals (they're the foundation)
        self._resolve_variables()
        self._resolve_locals()

        # Second pass: Resolve resources, data sources, and modules
        for file in self.module.files:
            for block in file.blocks:
                if block.block_type in (
                    TerraformObjectType.RESOURCE,
                    TerraformObjectType.DATA_SOURCE,
                    TerraformObjectType.MODULE,
                    TerraformObjectType.OUTPUT,
                ):
                    self._resolve_block(block)

        return self.module

    def resolve_reference(self, reference: TerraformReference) -> Optional[Any]:
        """
        Resolve a single reference to its value.

        Args:
            reference: The reference to resolve

        Returns:
            Resolved value or None if not resolvable
        """
        # Check cache
        cache_key = reference.full_reference
        if cache_key in self._resolution_cache:
            return self._resolution_cache[cache_key]

        # Check for circular dependency
        if cache_key in self._resolution_stack:
            # Allow self-references within locals (for partial resolution)
            if reference.reference_type == ReferenceType.LOCAL:
                local_name = reference.target
                if local_name in self._partial_locals:
                    # Try to get the attribute from partial locals
                    value = self._partial_locals[local_name]
                    for attr in reference.attribute_path:
                        if isinstance(value, dict):
                            value = value.get(attr)
                        else:
                            return None
                    return value

            raise CircularDependencyError(
                f"Circular dependency detected: {' -> '.join(self._resolution_stack)} -> {cache_key}"
            )

        # Add to resolution stack
        self._resolution_stack.add(cache_key)

        try:
            value = self._resolve_reference_internal(reference)
            self._resolution_cache[cache_key] = value
            reference.resolved_value = value
            reference.is_resolvable = value is not None
            return value
        finally:
            self._resolution_stack.discard(cache_key)

    def _resolve_reference_internal(
        self, reference: TerraformReference
    ) -> Optional[Any]:
        """Internal reference resolution logic."""
        if reference.reference_type == ReferenceType.VARIABLE:
            return self._resolve_variable_reference(reference)

        elif reference.reference_type == ReferenceType.LOCAL:
            return self._resolve_local_reference(reference)

        elif reference.reference_type == ReferenceType.RESOURCE:
            return self._resolve_resource_reference(reference)

        elif reference.reference_type == ReferenceType.DATA_SOURCE:
            return self._resolve_data_source_reference(reference)

        elif reference.reference_type == ReferenceType.MODULE:
            return self._resolve_module_reference(reference)

        elif reference.reference_type == ReferenceType.PATH:
            return self._resolve_path_reference(reference)

        elif reference.reference_type == ReferenceType.TERRAFORM:
            return self._resolve_terraform_reference(reference)

        return None

    # ========================================================================
    # TYPE-SPECIFIC RESOLUTION
    # ========================================================================

    def _resolve_variable_reference(
        self, reference: TerraformReference
    ) -> Optional[Any]:
        """Resolve a variable reference (var.name)."""
        # Extract variable name
        var_name = reference.target.replace("var.", "")

        # Check provided terraform_vars
        if var_name in self.terraform_vars:
            value = self.terraform_vars[var_name]

            # Navigate attribute path if present
            for attr in reference.attribute_path:
                if isinstance(value, dict):
                    value = value.get(attr)
                elif isinstance(value, list) and attr.isdigit():
                    try:
                        value = value[int(attr)]
                    except (IndexError, ValueError):
                        return None
                else:
                    return None

            return value

        # Check variable block for default value
        block = self.module._global_variable_index.get(reference.target)
        if block:
            default_attr = block.attributes.get("default")
            if default_attr:
                return default_attr.value.raw_value

        return None

    def _resolve_local_reference(self, reference: TerraformReference) -> Optional[Any]:
        """Resolve a local value reference (local.name)."""
        block = self.module._global_local_index.get(reference.target)

        if not block:
            return None

        # Get the value attribute (locals have a single 'value' attribute)
        value_attr = block.attributes.get("value")
        if not value_attr:
            return None

        # If already resolved, return it
        if value_attr.value.is_fully_resolved:
            value = value_attr.value.resolved_value
        else:
            # Resolve the value
            value = self._resolve_attribute_value(value_attr.value)

        # Navigate attribute path
        for attr in reference.attribute_path:
            if isinstance(value, dict):
                value = value.get(attr)
            elif isinstance(value, list) and attr.isdigit():
                try:
                    value = value[int(attr)]
                except (IndexError, ValueError):
                    return None
            else:
                return None

        return value

    def _resolve_resource_reference(
        self, reference: TerraformReference
    ) -> Optional[Any]:
        """Resolve a resource reference (aws_vpc.main.id)."""
        block = self.module._global_resource_index.get(reference.target)

        if not block:
            return None

        # If no attribute path, return a dict of all attributes
        if not reference.attribute_path:
            return self._block_to_dict(block)

        # Navigate to the specific attribute
        attr = block.get_attribute(".".join(reference.attribute_path))
        if not attr:
            return None

        # If it's computed, we can't resolve it
        if attr.value.is_computed:
            return None

        # Resolve if not already resolved
        if not attr.value.is_fully_resolved:
            return self._resolve_attribute_value(attr.value)

        return attr.value.resolved_value

    def _resolve_data_source_reference(
        self, reference: TerraformReference
    ) -> Optional[Any]:
        """Resolve a data source reference (data.aws_ami.ubuntu.id)."""
        # Data sources are computed at apply time, so we generally can't resolve them
        # However, we can return the configuration
        block = self.module._global_resource_index.get(reference.target)

        if not block:
            return None

        # If no attribute path, return the configuration
        if not reference.attribute_path:
            return self._block_to_dict(block)

        # Can't resolve computed data source attributes
        return None

    def _resolve_module_reference(self, reference: TerraformReference) -> Optional[Any]:
        """Resolve a module output reference (module.vpc.vpc_id)."""
        # Module outputs are only available after apply
        # We can't resolve them without the module's state
        return None

    def _resolve_path_reference(self, reference: TerraformReference) -> Optional[str]:
        """Resolve path references (path.module, path.root, path.cwd)."""
        path_parts = reference.target.split(".")

        if len(path_parts) != 2:
            return None

        path_type = path_parts[1]

        if path_type == "module":
            return str(Path(self.module.root_path).resolve())
        elif path_type == "root":
            return str(Path(self.module.root_path).resolve())
        elif path_type == "cwd":
            return str(Path.cwd())

        return None

    def _resolve_terraform_reference(
        self, reference: TerraformReference
    ) -> Optional[str]:
        """Resolve terraform references (terraform.workspace)."""
        # These are runtime values, return defaults
        parts = reference.target.split(".")

        if len(parts) != 2:
            return None

        if parts[1] == "workspace":
            return "default"

        return None

    # ========================================================================
    # ATTRIBUTE VALUE RESOLUTION
    # ========================================================================

    def _resolve_attribute_value(self, attr_value: AttributeValue) -> Any:
        """Resolve an attribute value by processing references and functions."""
        # If already resolved, return cached value
        if attr_value.is_fully_resolved:
            return attr_value.resolved_value

        raw_value = attr_value.raw_value

        # Handle different value types
        if attr_value.value_type == AttributeType.STRING:
            # Simple string, no resolution needed
            resolved = raw_value

        elif attr_value.value_type == AttributeType.REFERENCE:
            # Direct reference
            if attr_value.references:
                resolved = self.resolve_reference(attr_value.references[0])
            else:
                resolved = raw_value

        elif attr_value.value_type == AttributeType.INTERPOLATION:
            # String with interpolations
            resolved = self._resolve_interpolation(raw_value, attr_value.references)

        elif attr_value.value_type == AttributeType.FUNCTION:
            if attr_value.functions:
                resolved = self._evaluate_function(attr_value.functions[0])
            else:
                resolved = raw_value

        elif attr_value.value_type == AttributeType.LIST:
            # Resolve list items
            resolved = [self._resolve_nested_value(item) for item in raw_value]

        elif attr_value.value_type == AttributeType.MAP:
            # Resolve map values
            resolved = {k: self._resolve_nested_value(v) for k, v in raw_value.items()}

        else:
            # Number, bool, null - no resolution needed
            resolved = raw_value

        # Update attribute value
        attr_value.resolved_value = resolved
        attr_value.is_fully_resolved = True

        return resolved

    def _resolve_nested_value(self, value: Any) -> Any:
        """Resolve a nested value (in lists/maps)."""
        if isinstance(value, str):
            # Check for interpolation
            if "${" in value:
                return self._resolve_string_with_interpolations(value)
            return value

        elif isinstance(value, list):
            return [self._resolve_nested_value(item) for item in value]

        elif isinstance(value, dict):
            return {k: self._resolve_nested_value(v) for k, v in value.items()}

        return value

    def _resolve_string_with_interpolations(self, text: str) -> str:
        """Resolve a string that may contain interpolations."""
        result = text

        # Find all interpolations
        pattern = r"\$\{([^}]+)\}"

        def replace_interpolation(match):
            expression = match.group(1)
            resolved_value = self._resolve_expression(expression)

            if resolved_value is not None:
                # Convert to string appropriately
                if isinstance(resolved_value, bool):
                    return str(resolved_value)
                elif isinstance(resolved_value, (int, float)):
                    return str(resolved_value)
                elif isinstance(resolved_value, str):
                    return resolved_value
                else:
                    # For complex types, try JSON encoding
                    try:
                        return json.dumps(resolved_value)
                    except Exception:
                        return str(resolved_value)

            # If can't resolve, keep original
            return match.group(0)

        result = re.sub(pattern, replace_interpolation, result)
        return result

    def _resolve_interpolation(
        self, template: str, references: List[TerraformReference]
    ) -> str:
        """Resolve a string with interpolations."""
        return self._resolve_string_with_interpolations(template)

    def _resolve_expression(self, expression: str) -> Optional[Any]:
        """Resolve an expression (reference, function, or combination)."""
        expression = expression.strip()

        # Try as function first (functions can contain references)
        from tfkit.inspector.parser import TerraformParser

        parser = TerraformParser()

        func = parser._parse_function_call(expression)
        if func:
            return self._evaluate_function(func)

        # Try as reference
        refs = parser._find_all_reference_patterns(expression)
        if refs and expression in refs:
            # Direct reference
            ref = parser._parse_reference(expression)
            if ref:
                return self.resolve_reference(ref)

        # Try to evaluate as literal
        # Boolean
        if expression.lower() in ("true", "false"):
            return expression.lower() == "true"

        # Null
        if expression.lower() == "null":
            return None

        # Number
        try:
            if "." in expression:
                return float(expression)
            return int(expression)
        except ValueError:
            pass

        # String literal
        if (expression.startswith('"') and expression.endswith('"')) or (
            expression.startswith("'") and expression.endswith("'")
        ):
            return expression[1:-1]

        # Complex expression - can't resolve
        return None

    # ========================================================================
    # FUNCTION EVALUATION
    # ========================================================================

    def _evaluate_function(self, func: TerraformFunction) -> Optional[Any]:
        """Evaluate a Terraform function."""
        # Resolve arguments first
        resolved_args = []
        for arg in func.arguments:
            if isinstance(arg, TerraformReference):
                resolved_arg = self.resolve_reference(arg)
                resolved_args.append(resolved_arg)
            elif isinstance(arg, TerraformFunction):
                resolved_arg = self._evaluate_function(arg)
                resolved_args.append(resolved_arg)
            elif isinstance(arg, dict):
                if "_ref" in arg:
                    ref_data = arg["_ref"]
                    ref = TerraformReference(
                        reference_type=ReferenceType(ref_data.get("type", "unknown")),
                        target=ref_data.get("target", ""),
                        attribute_path=ref_data.get("attribute_path", []),
                        full_reference=ref_data.get("full_reference", ""),
                        is_resolvable=ref_data.get("is_resolvable", False),
                        resolved_value=ref_data.get("resolved_value"),
                    )
                    resolved_arg = self.resolve_reference(ref)
                    resolved_args.append(resolved_arg)
                else:
                    resolved_dict = {}
                    for k, v in arg.items():
                        # Resolve the key
                        resolved_key = self._resolve_nested_value(k)
                        # Resolve the value (which might have interpolations)
                        resolved_value = self._resolve_nested_value(v)
                        resolved_dict[resolved_key] = resolved_value
                    resolved_args.append(resolved_dict)
            elif isinstance(arg, list):
                # Recursively resolve list items
                resolved_list = [self._resolve_nested_value(item) for item in arg]
                resolved_args.append(resolved_list)
            else:
                resolved_args.append(arg)

        # Evaluate based on function name
        result = None

        try:
            if func.name == "timestamp":
                result = self._func_timestamp(resolved_args)
            elif func.name == "file":
                result = self._func_file(resolved_args)
            elif func.name == "filebase64":
                result = self._func_filebase64(resolved_args)
            elif func.name == "jsonencode":
                result = self._func_jsonencode(resolved_args)
            elif func.name == "jsondecode":
                result = self._func_jsondecode(resolved_args)
            elif func.name == "join":
                result = self._func_join(resolved_args)
            elif func.name == "split":
                result = self._func_split(resolved_args)
            elif func.name == "concat":
                result = self._func_concat(resolved_args)
            elif func.name == "merge":
                result = self._func_merge(resolved_args)
            elif func.name == "lookup":
                result = self._func_lookup(resolved_args)
            elif func.name == "format":
                result = self._func_format(resolved_args)
            elif func.name == "lower":
                result = self._func_lower(resolved_args)
            elif func.name == "upper":
                result = self._func_upper(resolved_args)
            elif func.name == "replace":
                result = self._func_replace(resolved_args)
            elif func.name == "length":
                result = self._func_length(resolved_args)
            elif func.name == "keys":
                result = self._func_keys(resolved_args)
            elif func.name == "values":
                result = self._func_values(resolved_args)
            elif func.name == "element":
                result = self._func_element(resolved_args)
            elif func.name == "flatten":
                result = self._func_flatten(resolved_args)
            elif func.name == "distinct":
                result = self._func_distinct(resolved_args)
            elif func.name == "compact":
                result = self._func_compact(resolved_args)
            elif func.name == "contains":
                result = self._func_contains(resolved_args)
            elif func.name == "min":
                result = self._func_min(resolved_args)
            elif func.name == "max":
                result = self._func_max(resolved_args)
            elif func.name == "range":
                result = self._func_range(resolved_args)
            elif func.name == "cidrsubnet":
                result = self._func_cidrsubnet(resolved_args)
            # Add more functions as needed
        except Exception as e:
            print(f"Error evaluating function {func.name}: {e}")
            result = None

        func.evaluated_value = result
        return result

    def _func_timestamp(self, args: List[Any]) -> str:
        """Return current timestamp in RFC 3339 format."""
        from datetime import datetime

        return datetime.now().isoformat() + "Z"

    # Function implementations
    def _func_file(self, args: List[Any]) -> Optional[str]:
        """Read file content."""
        if not args or args[0] is None:
            return None

        file_path = Path(self.module.root_path) / args[0]
        try:
            return file_path.read_text()
        except Exception:
            return None

    def _func_filebase64(self, args: List[Any]) -> Optional[str]:
        """Read file content as base64."""
        if not args or args[0] is None:
            return None

        file_path = Path(self.module.root_path) / args[0]
        try:
            content = file_path.read_bytes()
            return base64.b64encode(content).decode("utf-8")
        except Exception:
            return None

    def _func_jsonencode(self, args: List[Any]) -> Optional[str]:
        """Encode value as JSON."""
        if not args:
            return None

        try:
            return json.dumps(args[0])
        except Exception:
            return None

    def _func_jsondecode(self, args: List[Any]) -> Optional[Any]:
        """Decode JSON string."""
        if not args or args[0] is None:
            return None

        try:
            return json.loads(args[0])
        except Exception:
            return None

    def _func_join(self, args: List[Any]) -> Optional[str]:
        """Join list with separator."""
        if len(args) < 2:
            return None

        separator = args[0] if args[0] is not None else ""
        items = args[1] if isinstance(args[1], list) else [args[1]]

        return separator.join(str(item) for item in items if item is not None)

    def _func_split(self, args: List[Any]) -> Optional[List[str]]:
        """Split string by separator."""
        if len(args) < 2 or args[1] is None:
            return None

        separator = args[0] if args[0] is not None else ""
        string = str(args[1])

        return string.split(separator)

    def _func_concat(self, args: List[Any]) -> List[Any]:
        """Concatenate lists."""
        result = []
        for arg in args:
            if isinstance(arg, list):
                result.extend(arg)
        return result

    def _func_merge(self, args: List[Any]) -> Dict[str, Any]:
        """Merge maps with proper handling of resolved values."""
        result = {}

        for arg in args:
            if isinstance(arg, dict):
                # All values should already be resolved by _deep_resolve_function_argument
                result.update(arg)
            else:
                print(f"Warning: merge() argument is not a dict: {type(arg)} - {arg}")

        return result

    def _func_lookup(self, args: List[Any]) -> Optional[Any]:
        """Lookup value in map."""
        if len(args) < 2:
            return None

        map_obj = args[0]
        key = args[1]
        default = args[2] if len(args) > 2 else None

        if isinstance(map_obj, dict):
            return map_obj.get(key, default)

        return default

    def _func_format(self, args: List[Any]) -> Optional[str]:
        """Format string."""
        if not args or args[0] is None:
            return None

        fmt = str(args[0])
        values = args[1:]

        try:
            return fmt % tuple(values)
        except Exception:
            return None

    def _func_lower(self, args: List[Any]) -> Optional[str]:
        """Convert to lowercase."""
        if not args or args[0] is None:
            return None

        return str(args[0]).lower()

    def _func_upper(self, args: List[Any]) -> Optional[str]:
        """Convert to uppercase."""
        if not args or args[0] is None:
            return None

        return str(args[0]).upper()

    def _func_replace(self, args: List[Any]) -> Optional[str]:
        """Replace substring."""
        if len(args) < 3:
            return None

        string = str(args[0]) if args[0] is not None else ""
        old = str(args[1]) if args[1] is not None else ""
        new = str(args[2]) if args[2] is not None else ""

        return string.replace(old, new)

    def _func_length(self, args: List[Any]) -> Optional[int]:
        """Get length of list/map/string."""
        if not args or args[0] is None:
            return 0

        return len(args[0])

    def _func_keys(self, args: List[Any]) -> Optional[List[str]]:
        """Get keys of a map."""
        if not args or not isinstance(args[0], dict):
            return None

        return list(args[0].keys())

    def _func_values(self, args: List[Any]) -> Optional[List[Any]]:
        """Get values of a map."""
        if not args or not isinstance(args[0], dict):
            return None

        return list(args[0].values())

    def _func_element(self, args: List[Any]) -> Optional[Any]:
        """Get element at index from list."""
        if len(args) < 2 or not isinstance(args[0], list):
            return None

        try:
            index = int(args[1])
            return args[0][index]
        except (ValueError, IndexError):
            return None

    def _func_flatten(self, args: List[Any]) -> List[Any]:
        """Flatten a list of lists."""
        if not args or not isinstance(args[0], list):
            return []

        def flatten_recursive(lst):
            result = []
            for item in lst:
                if isinstance(item, list):
                    result.extend(flatten_recursive(item))
                else:
                    result.append(item)
            return result

        return flatten_recursive(args[0])

    def _func_distinct(self, args: List[Any]) -> List[Any]:
        """Return list with unique elements."""
        if not args or not isinstance(args[0], list):
            return []

        seen = set()
        result = []
        for item in args[0]:
            # For unhashable types, use string representation
            try:
                key = (
                    item
                    if isinstance(item, (str, int, float, bool, type(None)))
                    else str(item)
                )
                if key not in seen:
                    seen.add(key)
                    result.append(item)
            except Exception:
                result.append(item)

        return result

    def _func_compact(self, args: List[Any]) -> List[Any]:
        """Remove null/empty values from list."""
        if not args or not isinstance(args[0], list):
            return []

        return [item for item in args[0] if item not in (None, "", [])]

    def _func_contains(self, args: List[Any]) -> Optional[bool]:
        """Check if list contains value."""
        if len(args) < 2:
            return None

        if isinstance(args[0], list):
            return args[1] in args[0]

        return False

    def _func_min(self, args: List[Any]) -> Optional[Any]:
        """Return minimum value."""
        if not args:
            return None

        # Filter out None values
        valid_args = [arg for arg in args if arg is not None]

        if not valid_args:
            return None

        try:
            return min(valid_args)
        except Exception:
            return None

    def _func_max(self, args: List[Any]) -> Optional[Any]:
        """Return maximum value."""
        if not args:
            return None

        # Filter out None values
        valid_args = [arg for arg in args if arg is not None]

        if not valid_args:
            return None

        try:
            return max(valid_args)
        except Exception:
            return None

    def _func_range(self, args: List[Any]) -> List[int]:
        """Generate a range of numbers."""
        if not args:
            return []

        try:
            if len(args) == 1:
                return list(range(int(args[0])))
            elif len(args) == 2:
                return list(range(int(args[0]), int(args[1])))
            elif len(args) >= 3:
                return list(range(int(args[0]), int(args[1]), int(args[2])))
        except Exception:
            return []

        return []

    def _func_cidrsubnet(self, args: List[Any]) -> Optional[str]:
        """Calculate a subnet address within a given IP network address prefix."""
        if len(args) < 3:
            return None

        # This is a simplified implementation
        # In a real implementation, you'd use ipaddress library
        try:
            base_cidr = str(args[0])
            # newbits = int(args[1])
            netnum = int(args[2])

            # For now, return a placeholder
            # A real implementation would use ipaddress.ip_network
            return f"{base_cidr}/subnet-{netnum}"
        except Exception:
            return None

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _resolve_variables(self):
        """Resolve all variables with their default or provided values."""
        for var_block in self.module._global_variable_index.values():
            var_name = var_block.name

            # Skip if already in terraform_vars
            if var_name in self.terraform_vars:
                continue

            # Use default if available
            default_attr = var_block.attributes.get("default")
            if default_attr and not default_attr.value.is_computed:
                resolved = self._resolve_attribute_value(default_attr.value)
                self.terraform_vars[var_name] = resolved

    def _resolve_locals(self):
        """Resolve all local values with support for self-references."""
        # Multiple passes to handle dependencies and self-references
        max_passes = 10
        unresolved_locals = set(self.module._global_local_index.keys())

        for _ in range(max_passes):
            if not unresolved_locals:
                break

            resolved_this_pass = set()

            for local_target in list(unresolved_locals):
                local_block = self.module._global_local_index[local_target]
                local_name = local_block.name
                value_attr = local_block.attributes.get("value")

                if not value_attr:
                    resolved_this_pass.add(local_target)
                    continue

                # For map values, try to resolve individual fields
                if value_attr.value.value_type == AttributeType.MAP:
                    partial_resolved = {}
                    all_resolved = True

                    # Store partial state for self-references
                    self._partial_locals[local_target] = partial_resolved

                    for key, val in value_attr.value.raw_value.items():
                        try:
                            resolved_val = self._resolve_nested_value(val)
                            partial_resolved[key] = resolved_val
                        except CircularDependencyError:
                            # Can't resolve this field yet due to circular dependency
                            all_resolved = False
                        except Exception as e:
                            print(f"Error resolving local {local_name}.{key}: {e}")
                            partial_resolved[key] = val
                            all_resolved = False

                    # Update partial locals with what we've resolved
                    self._partial_locals[local_target] = partial_resolved

                    if all_resolved:
                        value_attr.value.resolved_value = partial_resolved
                        value_attr.value.is_fully_resolved = True
                        resolved_this_pass.add(local_target)
                else:
                    try:
                        # Try to resolve non-map values
                        resolved = self._resolve_attribute_value(value_attr.value)
                        value_attr.value.resolved_value = resolved
                        value_attr.value.is_fully_resolved = True
                        resolved_this_pass.add(local_target)
                    except CircularDependencyError:
                        # Can't resolve yet, try next pass
                        pass
                    except Exception as e:
                        print(f"Error resolving local {local_name}: {e}")
                        resolved_this_pass.add(local_target)

            # Remove resolved locals from unresolved set
            unresolved_locals -= resolved_this_pass

            # If nothing was resolved this pass, we have unresolvable circular dependencies
            if not resolved_this_pass and unresolved_locals:
                print(f"Warning: Could not resolve locals: {unresolved_locals}")
                break

    def _resolve_block(self, block: TerraformBlock):
        """Resolve all attributes in a block."""
        for attr in block.attributes.values():
            if not attr.value.is_fully_resolved:
                try:
                    self._resolve_attribute_value(attr.value)
                except Exception as e:
                    print(
                        f"Error resolving attribute {attr.name} in {block.address}: {e}"
                    )

            # Recursively resolve nested attributes
            self._resolve_nested_attributes(attr)

    def _resolve_nested_attributes(self, attr: TerraformAttribute):
        """Recursively resolve nested attributes."""
        for nested_attr in attr.nested_attributes.values():
            if not nested_attr.value.is_fully_resolved:
                try:
                    self._resolve_attribute_value(nested_attr.value)
                except Exception as e:
                    print(f"Error resolving nested attribute {nested_attr.name}: {e}")
            self._resolve_nested_attributes(nested_attr)

    def _block_to_dict(self, block: TerraformBlock) -> Dict[str, Any]:
        """Convert a block to a dictionary representation."""
        result = {}
        for attr_name, attr in block.attributes.items():
            if attr.value.is_fully_resolved:
                result[attr_name] = attr.value.resolved_value
            else:
                result[attr_name] = attr.value.raw_value
        return result

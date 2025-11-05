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
        cache_key = reference.full_reference
        if cache_key in self._resolution_cache:
            return self._resolution_cache[cache_key]

        if cache_key in self._resolution_stack:
            print(
                f"Warning: Circular dependency detected: {' -> '.join(self._resolution_stack)} -> {cache_key}"
            )
            return None

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
            # Function call
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
        """Resolve a nested value (in lists/maps) recursively."""
        if isinstance(value, str):
            if "${" in value:
                refs = self._extract_references_from_string(value)
                resolved = self._resolve_interpolation(value, refs)
                if "${" in resolved and resolved != value:
                    return self._resolve_nested_value(resolved)
                return resolved
            return value

        elif isinstance(value, list):
            return [self._resolve_nested_value(item) for item in value]

        elif isinstance(value, dict):
            return {k: self._resolve_nested_value(v) for k, v in value.items()}

        return value

    def _resolve_interpolation(
        self, template: str, references: List[TerraformReference]
    ) -> str:
        """Resolve a string with interpolations."""
        result = template

        # Find all interpolations
        pattern = r"\$\{([^}]+)\}"
        matches = re.finditer(pattern, template)

        for match in matches:
            expression = match.group(1)
            interpolation = match.group(0)

            # Try to resolve the expression
            resolved_value = self._resolve_expression(expression)

            if resolved_value is not None:
                # Replace interpolation with resolved value
                result = result.replace(interpolation, str(resolved_value))

        return result

    def _resolve_expression(self, expression: str) -> Optional[Any]:
        """Resolve an expression (reference, function, or combination)."""
        expression = expression.strip()

        # Try as reference
        from tfkit.inspector.parser import TerraformParser

        parser = TerraformParser()

        refs = parser._find_references_in_expression(expression)
        if refs and expression in refs:
            # Direct reference
            ref = parser._parse_reference(expression)
            if ref:
                return self.resolve_reference(ref)

        # Try as function
        func = parser._parse_function_call(expression)
        if func:
            return self._evaluate_function(func)

        # Complex expression - can't resolve
        return None

    def _extract_references_from_string(self, s: str) -> List[TerraformReference]:
        """Extract references from a string."""
        from tfkit.inspector.parser import TerraformParser

        parser = TerraformParser()

        refs = []
        pattern = r"\$\{([^}]+)\}"
        matches = re.findall(pattern, s)

        for match in matches:
            ref_strs = parser._find_references_in_expression(match)
            for ref_str in ref_strs:
                ref = parser._parse_reference(ref_str)
                if ref:
                    refs.append(ref)

        return refs

    # ========================================================================
    # FUNCTION EVALUATION
    # ========================================================================

    def _evaluate_function(self, func: TerraformFunction) -> Optional[Any]:
        """Evaluate a Terraform function."""
        resolved_args = []
        for arg in func.arguments:
            if isinstance(arg, TerraformReference):
                resolved_arg = self.resolve_reference(arg)
                resolved_args.append(resolved_arg)
            elif isinstance(arg, TerraformFunction):
                resolved_arg = self._evaluate_function(arg)
                resolved_args.append(resolved_arg)
            else:
                # For complex structures like maps/lists, resolve any nested references
                resolved_arg = self._resolve_nested_structure(arg)
                resolved_args.append(resolved_arg)

        result = None

        try:
            if func.name == "merge":
                result = self._func_merge(resolved_args)
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

            func.evaluated_value = result
            func.is_evaluable = result is not None
            return result

        except Exception as e:
            print(f"Error evaluating function {func.name}: {e}")
            return None

    def _resolve_nested_structure(self, value: Any) -> Any:
        """Resolve references in nested structures (maps, lists)."""
        if isinstance(value, dict):
            return {k: self._resolve_nested_structure(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_nested_structure(item) for item in value]
        elif isinstance(value, str) and "${" in value:
            # Try to resolve interpolations in strings
            refs = self._extract_references_from_string(value)
            return self._resolve_interpolation(value, refs)
        else:
            return value

    # Function implementations
    def _func_file(self, args: List[Any]) -> Optional[str]:
        """Read file content."""
        if not args:
            return None

        file_path = Path(self.module.root_path) / args[0]
        try:
            return file_path.read_text()
        except Exception:
            return None

    def _func_filebase64(self, args: List[Any]) -> Optional[str]:
        """Read file content as base64."""
        if not args:
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
        if not args:
            return None

        try:
            return json.loads(args[0])
        except Exception:
            return None

    def _func_join(self, args: List[Any]) -> Optional[str]:
        """Join list with separator."""
        if len(args) < 2:
            return None

        separator = args[0]
        items = args[1] if isinstance(args[1], list) else [args[1]]

        return separator.join(str(item) for item in items)

    def _func_split(self, args: List[Any]) -> Optional[List[str]]:
        """Split string by separator."""
        if len(args) < 2:
            return None

        separator = args[0]
        string = args[1]

        return string.split(separator)

    def _func_concat(self, args: List[Any]) -> List[Any]:
        """Concatenate lists."""
        result = []
        for arg in args:
            if isinstance(arg, list):
                result.extend(arg)
        return result

    def _func_merge(self, args: List[Any]) -> Dict[str, Any]:
        """Merge maps."""
        result = {}
        for arg in args:
            if isinstance(arg, dict):
                result.update(arg)
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
        if not args:
            return None

        fmt = args[0]
        values = args[1:]

        try:
            return fmt % tuple(values)
        except Exception:
            return None

    def _func_lower(self, args: List[Any]) -> Optional[str]:
        """Convert to lowercase."""
        if not args:
            return None

        return str(args[0]).lower()

    def _func_upper(self, args: List[Any]) -> Optional[str]:
        """Convert to uppercase."""
        if not args:
            return None

        return str(args[0]).upper()

    def _func_replace(self, args: List[Any]) -> Optional[str]:
        """Replace substring."""
        if len(args) < 3:
            return None

        string = args[0]
        old = args[1]
        new = args[2]

        return str(string).replace(str(old), str(new))

    def _func_length(self, args: List[Any]) -> Optional[int]:
        """Get length of list/map/string."""
        if not args:
            return None

        return len(args[0])

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
        """Resolve all local values."""
        for local_block in self.module._global_local_index.values():
            value_attr = local_block.attributes.get("value")
            if value_attr and not value_attr.value.is_fully_resolved:
                self._resolve_attribute_value(value_attr.value)

    def _resolve_block(self, block: TerraformBlock):
        """Resolve all attributes in a block."""
        for attr in block.attributes.values():
            if not attr.value.is_fully_resolved:
                self._resolve_attribute_value(attr.value)

            # Recursively resolve nested attributes
            self._resolve_nested_attributes(attr)

    def _resolve_nested_attributes(self, attr: TerraformAttribute):
        """Recursively resolve nested attributes."""
        for nested_attr in attr.nested_attributes.values():
            if not nested_attr.value.is_fully_resolved:
                self._resolve_attribute_value(nested_attr.value)
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

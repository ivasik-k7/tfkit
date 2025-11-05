"""
Enhanced Terraform Parser with comprehensive metadata extraction.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from tfkit.inspector.models import (
    AttributeType,
    AttributeValue,
    ReferenceType,
    SourceLocation,
    TerraformAttribute,
    TerraformBlock,
    TerraformFile,
    TerraformFunction,
    TerraformModule,
    TerraformObjectType,
    TerraformReference,
)


class TerraformParser:
    """Enhanced Terraform parser with full metadata extraction."""

    def __init__(self):
        self._file_cache: Dict[str, List[str]] = {}

        self.terraform_functions = {
            "file",
            "filebase64",
            "templatefile",
            "jsonencode",
            "jsondecode",
            "yamlencode",
            "yamldecode",
            "base64encode",
            "base64decode",
            "join",
            "split",
            "concat",
            "lookup",
            "element",
            "length",
            "merge",
            "flatten",
            "distinct",
            "keys",
            "values",
            "zipmap",
            "format",
            "formatlist",
            "regex",
            "regexall",
            "replace",
            "substr",
            "trim",
            "trimprefix",
            "trimsuffix",
            "lower",
            "upper",
            "title",
            "chomp",
            "indent",
            "tostring",
            "tonumber",
            "tobool",
            "tolist",
            "toset",
            "tomap",
            "try",
            "can",
            "coalesce",
            "compact",
            "contains",
            "index",
            "reverse",
            "slice",
            "sort",
            "sum",
            "min",
            "max",
            "ceil",
            "floor",
            "abs",
            "log",
            "pow",
            "signum",
            "parseint",
            "cidrhost",
            "cidrnetmask",
            "cidrsubnet",
            "cidrsubnets",
            "timestamp",
            "timeadd",
            "formatdate",
            "range",
            "chunklist",
            "setintersection",
            "setproduct",
            "setsubtract",
            "setunion",
            "anytrue",
            "alltrue",
            "one",
            "sensitive",
            "nonsensitive",
        }

    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================

    def _cache_file(self, file_path: str):
        """Cache file content for line number lookups."""
        if file_path in self._file_cache:
            return

        try:
            with open(file_path, encoding="utf-8") as f:
                self._file_cache[file_path] = f.readlines()
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not cache file {file_path}: {e}")
            self._file_cache[file_path] = []

    def _get_file_lines(self, file_path: str) -> List[str]:
        """Get cached file lines."""
        self._cache_file(file_path)
        return self._file_cache.get(file_path, [])

    # ========================================================================
    # LINE NUMBER DETECTION
    # ========================================================================

    def _find_block_line(
        self, file_path: str, block_type: str, labels: List[str]
    ) -> Optional[int]:
        """Find the line number where a block starts."""
        lines = self._get_file_lines(file_path)

        # Build search pattern
        if labels:
            label_pattern = r"\s+".join(f'"{re.escape(label)}"' for label in labels)
            pattern = rf"^\s*{re.escape(block_type)}\s+{label_pattern}\s*\{{"
        else:
            pattern = rf"^\s*{re.escape(block_type)}\s*\{{"

        for line_num, line in enumerate(lines, 1):
            if re.search(pattern, line):
                return line_num

        return None

    def _find_attribute_line(
        self,
        file_path: str,
        start_line: int,
        attribute_name: str,
        end_line: Optional[int] = None,
    ) -> Optional[int]:
        """Find the line number of an attribute within a block."""
        lines = self._get_file_lines(file_path)

        if start_line < 1 or start_line > len(lines):
            return None

        # Determine search range
        if end_line is None:
            end_line = self._find_block_end(file_path, start_line)

        # Pattern for attribute assignment
        pattern = rf"^\s*{re.escape(attribute_name)}\s*="

        for line_num in range(start_line, min(end_line + 1, len(lines) + 1)):
            if re.search(pattern, lines[line_num - 1]):
                return line_num

        return None

    def _find_block_end(self, file_path: str, start_line: int) -> int:
        """Find the closing brace of a block."""
        lines = self._get_file_lines(file_path)

        if start_line < 1 or start_line > len(lines):
            return start_line

        brace_depth = 0

        for line_num in range(start_line, len(lines) + 1):
            line = lines[line_num - 1]
            brace_depth += line.count("{") - line.count("}")

            if brace_depth == 0 and line_num > start_line:
                return line_num

        return len(lines)

    # ========================================================================
    #  REFERENCE EXTRACTION
    # ========================================================================

    def _extract_references(self, value: Any) -> List[TerraformReference]:
        """
        extract all Terraform references from any value type.
        This is the main entry point for reference extraction.
        """
        seen_refs = set()
        references = []

        def add_unique_ref(ref: TerraformReference):
            if ref and ref.full_reference not in seen_refs:
                seen_refs.add(ref.full_reference)
                references.append(ref)

        self._extract_references_recursive(value, add_unique_ref)

        return references

    def _extract_references_recursive(self, value: Any, add_ref_callback):
        """Recursively extract references from any value type."""
        if value is None:
            return

        if isinstance(value, str):
            self._extract_from_string(value, add_ref_callback)

        elif isinstance(value, dict):
            for k, v in value.items():
                # Keys can also contain references in Terraform
                self._extract_references_recursive(k, add_ref_callback)
                self._extract_references_recursive(v, add_ref_callback)

        elif isinstance(value, (list, tuple)):
            for item in value:
                self._extract_references_recursive(item, add_ref_callback)

        elif isinstance(value, set):
            for item in value:
                self._extract_references_recursive(item, add_ref_callback)

    def _extract_from_string(self, value: str, add_ref_callback):
        """Extract all references from a string value."""
        if not value or not isinstance(value, str):
            return

        # 1. Extract direct references (no interpolation)
        # e.g., "var.environment", "local.vpc_id", "aws_vpc.main.id"
        for ref_str in self._find_all_reference_patterns(value):
            ref = self._parse_reference(ref_str)
            if ref:
                add_ref_callback(ref)

        # 2. Extract from interpolations: ${...}
        interpolation_pattern = r"\$\{([^}]+)\}"
        for match in re.finditer(interpolation_pattern, value):
            interpolation_content = match.group(1)

            # Extract references from the interpolation content
            for ref_str in self._find_all_reference_patterns(interpolation_content):
                ref = self._parse_reference(ref_str)
                if ref:
                    add_ref_callback(ref)

            # Handle nested interpolations
            if "${" in interpolation_content:
                self._extract_from_string(interpolation_content, add_ref_callback)

        # 3. Extract from for expressions: for x in collection : expression
        for_pattern = r"\bfor\s+\w+\s+in\s+([^:]+):"
        for match in re.finditer(for_pattern, value):
            collection_expr = match.group(1).strip()
            for ref_str in self._find_all_reference_patterns(collection_expr):
                ref = self._parse_reference(ref_str)
                if ref:
                    add_ref_callback(ref)

        # 4. Extract from function calls
        self._extract_from_functions(value, add_ref_callback)

        # 5. Extract from conditional expressions: condition ? true_val : false_val
        conditional_pattern = r"([^?]+)\?([^:]+):(.+)"
        conditional_match = re.search(conditional_pattern, value)
        if conditional_match:
            for group in conditional_match.groups():
                for ref_str in self._find_all_reference_patterns(group):
                    ref = self._parse_reference(ref_str)
                    if ref:
                        add_ref_callback(ref)

    def _find_all_reference_patterns(self, text: str) -> List[str]:
        """
        Find all Terraform reference patterns in text.
        Returns list of reference strings like "var.name", "local.value", etc.
        """
        if not text:
            return []

        references = []

        # Comprehensive reference patterns
        patterns = [
            # var.name or var.name.attribute.path
            r"\bvar\.([a-zA-Z_][a-zA-Z0-9_-]*)(?:\.([a-zA-Z_][a-zA-Z0-9_-]*))*",
            # local.name or local.name.attribute.path
            r"\blocal\.([a-zA-Z_][a-zA-Z0-9_-]*)(?:\.([a-zA-Z_][a-zA-Z0-9_-]*))*",
            # module.name or module.name.output or module.name.output.attr
            r"\bmodule\.([a-zA-Z_][a-zA-Z0-9_-]*)(?:\.([a-zA-Z_][a-zA-Z0-9_-]*))*",
            # data.type.name or data.type.name.attribute
            r"\bdata\.([a-zA-Z_][a-zA-Z0-9_-]*)\.([a-zA-Z_][a-zA-Z0-9_-]*)(?:\.([a-zA-Z_][a-zA-Z0-9_-]*))*",
            # resource_type.name or resource_type.name.attribute
            # Must be careful not to match function names or keywords
            r"\b([a-z][a-z0-9]*_[a-z0-9_]+)\.([a-zA-Z_][a-zA-Z0-9_-]*)(?:\.([a-zA-Z_][a-zA-Z0-9_-]*))*",
            # path.module, path.root, path.cwd
            r"\bpath\.(module|root|cwd)",
            # terraform.workspace
            r"\bterraform\.(workspace)",
            # count.index
            r"\bcount\.(index)",
            # each.key, each.value
            r"\beach\.(key|value)",
            # self.attribute
            r"\bself\.([a-zA-Z_][a-zA-Z0-9_-]*)(?:\.([a-zA-Z_][a-zA-Z0-9_-]*))*",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                ref_str = match.group(0)

                # Skip if this looks like it's part of a larger identifier
                start_pos = match.start()
                end_pos = match.end()

                # Check character before
                if start_pos > 0 and text[start_pos - 1].isalnum():
                    continue

                # Check character after
                if end_pos < len(text) and text[end_pos].isalnum():
                    continue

                # Skip if it's inside a string literal (simple check)
                if self._is_in_string_literal(text, start_pos):
                    continue

                references.append(ref_str)

        return references

    def _is_in_string_literal(self, text: str, position: int) -> bool:
        """Check if a position in text is inside a string literal."""
        in_string = False
        string_char = None
        escape_next = False

        for i in range(position):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None

        return in_string

    def _extract_from_functions(self, text: str, add_ref_callback):
        """Extract references from function calls."""
        # Find all function calls: function_name(args)
        function_pattern = r"([a-z_][a-z0-9_]*)\s*\(([^)]*(?:\([^)]*\))*[^)]*)\)"

        for match in re.finditer(function_pattern, text, re.IGNORECASE | re.DOTALL):
            func_name = match.group(1)
            args_str = match.group(2)

            if func_name not in self.terraform_functions:
                continue

            # Extract references from function arguments
            for ref_str in self._find_all_reference_patterns(args_str):
                ref = self._parse_reference(ref_str)
                if ref:
                    add_ref_callback(ref)

            # Recursively extract from nested structures in arguments
            self._extract_from_string(args_str, add_ref_callback)

    def _parse_reference(self, ref_string: str) -> Optional[TerraformReference]:
        """
        Parse a Terraform reference string into TerraformReference object.
        """
        if not ref_string:
            return None

        parts = ref_string.split(".")

        if len(parts) < 2:
            return None

        prefix = parts[0]

        # Variable reference: var.name or var.name.attr
        if prefix == "var":
            return TerraformReference(
                reference_type=ReferenceType.VARIABLE,
                target=f"var.{parts[1]}",
                attribute_path=parts[2:] if len(parts) > 2 else [],
                full_reference=ref_string,
            )

        if prefix == "local":
            return TerraformReference(
                reference_type=ReferenceType.LOCAL,
                target=f"local.{parts[1]}",
                attribute_path=parts[2:] if len(parts) > 2 else [],
                full_reference=ref_string,
            )

        # Module reference: module.name.output
        if prefix == "module":
            return TerraformReference(
                reference_type=ReferenceType.MODULE,
                target=f"module.{parts[1]}",
                attribute_path=parts[2:] if len(parts) > 2 else [],
                full_reference=ref_string,
            )

        # Data source reference: data.type.name.attr
        if prefix == "data":
            if len(parts) >= 3:
                return TerraformReference(
                    reference_type=ReferenceType.DATA_SOURCE,
                    target=f"data.{parts[1]}.{parts[2]}",
                    attribute_path=parts[3:] if len(parts) > 3 else [],
                    full_reference=ref_string,
                )

        # Path reference: path.module, path.root, path.cwd
        if prefix == "path":
            return TerraformReference(
                reference_type=ReferenceType.PATH,
                target=ref_string,
                attribute_path=[],
                full_reference=ref_string,
            )

        # Terraform reference: terraform.workspace
        if prefix == "terraform":
            return TerraformReference(
                reference_type=ReferenceType.TERRAFORM,
                target=ref_string,
                attribute_path=[],
                full_reference=ref_string,
            )

        # Count/each reference
        if prefix in ("count", "each"):
            ref_type = ReferenceType.COUNT if prefix == "count" else ReferenceType.EACH
            return TerraformReference(
                reference_type=ref_type,
                target=ref_string,
                attribute_path=[],
                full_reference=ref_string,
            )

        # Self reference
        if prefix == "self":
            return TerraformReference(
                reference_type=ReferenceType.SELF,
                target=ref_string,
                attribute_path=[],
                full_reference=ref_string,
            )

        if "_" in prefix and len(parts) >= 2:
            return TerraformReference(
                reference_type=ReferenceType.RESOURCE,
                target=f"{parts[0]}.{parts[1]}",
                attribute_path=parts[2:] if len(parts) > 2 else [],
                full_reference=ref_string,
            )

        return None

    # ========================================================================
    # FUNCTION PARSING
    # ========================================================================

    def _parse_function_call(self, expression: str) -> Optional[TerraformFunction]:
        """
        Parse a Terraform function call.
        """
        expression = expression.strip()

        # Pattern: function_name(arguments)
        pattern = r"^([a-z][a-z0-9_]*)\s*\((.*)\)$"
        match = re.match(pattern, expression, re.DOTALL)

        if not match:
            return None

        func_name = match.group(1)
        args_str = match.group(2).strip()

        if func_name not in self.terraform_functions:
            return None

        # Parse arguments
        arguments = self._parse_function_arguments(args_str)

        return TerraformFunction(
            name=func_name,
            arguments=arguments,
            raw_expression=expression,
            is_evaluable=func_name
            in {
                "merge",
                "jsonencode",
                "yamlencode",
                "join",
                "format",
                "lower",
                "upper",
                "replace",
                "concat",
                "lookup",
                "length",
            },
        )

    def _parse_function_arguments(self, args_str: str) -> List[Any]:
        """Parse function arguments with proper nested structure handling."""
        if not args_str.strip():
            return []

        arguments = []
        current_arg = []
        depth = 0
        in_string = False
        string_char = None
        escape_next = False

        for char in args_str:
            if escape_next:
                current_arg.append(char)
                escape_next = False
                continue

            if char == "\\":
                current_arg.append(char)
                escape_next = True
                continue

            # Handle strings
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
                current_arg.append(char)
            elif char == string_char and in_string:
                in_string = False
                string_char = None
                current_arg.append(char)
            elif in_string:
                current_arg.append(char)

            # Handle brackets and parentheses
            elif char in "([{":
                depth += 1
                current_arg.append(char)
            elif char in ")]}":
                depth -= 1
                current_arg.append(char)

            # Handle comma separation
            elif char == "," and depth == 0 and not in_string:
                arg_str = "".join(current_arg).strip()
                if arg_str:
                    arguments.append(self._parse_argument_value(arg_str))
                current_arg = []
            else:
                current_arg.append(char)

        # Add the last argument
        if current_arg:
            arg_str = "".join(current_arg).strip()
            if arg_str:
                arguments.append(self._parse_argument_value(arg_str))

        return arguments

    def _parse_argument_value(self, arg_str: str) -> Any:
        """Parse a single function argument value."""
        arg_str = arg_str.strip()

        # Try to parse as reference
        refs = self._find_all_reference_patterns(arg_str)
        if refs and len(refs) == 1 and refs[0] == arg_str:
            ref = self._parse_reference(arg_str)
            if ref:
                return ref

        # Try to parse as nested function
        if "(" in arg_str and ")" in arg_str:
            func = self._parse_function_call(arg_str)
            if func:
                return func

        # Try to parse as string (quoted)
        if (arg_str.startswith('"') and arg_str.endswith('"')) or (
            arg_str.startswith("'") and arg_str.endswith("'")
        ):
            return arg_str[1:-1]

        # Try to parse as number
        try:
            if "." in arg_str:
                return float(arg_str)
            else:
                return int(arg_str)
        except ValueError:
            pass

        # Try to parse as boolean
        if arg_str.lower() in ("true", "false"):
            return arg_str.lower() == "true"

        # Try to parse as null
        if arg_str.lower() in ("null", "none"):
            return None

        # Default: return as string
        return arg_str

    # ========================================================================
    # ATTRIBUTE VALUE PARSING
    # ========================================================================

    def _determine_value_type(self, value: Any) -> AttributeType:
        """Determine the type of a value."""
        if value is None:
            return AttributeType.NULL

        if isinstance(value, bool):
            return AttributeType.BOOL

        if isinstance(value, (int, float)):
            return AttributeType.NUMBER

        if isinstance(value, str):
            # Check for interpolation
            if "${" in value:
                # Check if it's a function inside interpolation
                interpolation_match = re.search(r"\$\{(.+)\}", value)
                if interpolation_match:
                    inner_content = interpolation_match.group(1).strip()
                    if self._parse_function_call(inner_content):
                        return AttributeType.FUNCTION
                return AttributeType.INTERPOLATION

            # Check for direct function call (without interpolation)
            if self._parse_function_call(value):
                return AttributeType.FUNCTION

            # Check for direct reference (without interpolation)
            refs = self._find_all_reference_patterns(value)
            if refs and len(refs) == 1 and refs[0] == value.strip():
                return AttributeType.REFERENCE

            return AttributeType.STRING

        if isinstance(value, list):
            return AttributeType.LIST

        if isinstance(value, dict):
            return AttributeType.MAP

        if isinstance(value, set):
            return AttributeType.SET

        return AttributeType.STRING

    def _parse_attribute_value(
        self, value: Any, file_path: str, line_number: Optional[int] = None
    ) -> AttributeValue:
        """Parse an attribute value with full metadata."""
        value_type = self._determine_value_type(value)

        references = self._extract_references(value)

        functions = []
        if isinstance(value, str):
            if "${" in value:
                interpolation_match = re.search(r"\$\{(.+)\}", value)
                if interpolation_match:
                    inner_content = interpolation_match.group(1).strip()
                    func = self._parse_function_call(inner_content)
                    if func:
                        functions.append(func)
            else:
                func = self._parse_function_call(value)
                if func:
                    functions.append(func)

        has_interpolation = isinstance(value, str) and "${" in value

        source_location = None
        if line_number:
            source_location = SourceLocation(
                file_path=file_path, line_start=line_number, line_end=line_number
            )

        return AttributeValue(
            raw_value=value,
            value_type=value_type,
            references=references,
            functions=functions,
            has_interpolation=has_interpolation,
            source_location=source_location,
        )

    # ========================================================================
    # BLOCK PARSING
    # ========================================================================

    def _parse_block(
        self,
        block_type: str,
        block_data: Dict[str, Any],
        file_path: str,
        labels: Optional[List[str]] = None,
    ) -> TerraformBlock:
        """Parse a Terraform block with full metadata."""
        labels = labels or []

        # Determine object type
        obj_type = self._get_object_type(block_type)

        # Extract resource type and name
        resource_type = None
        name = None

        if obj_type in (TerraformObjectType.RESOURCE, TerraformObjectType.DATA_SOURCE):
            if len(labels) >= 2:
                resource_type = labels[0]
                name = labels[1]
        elif obj_type in (
            TerraformObjectType.MODULE,
            TerraformObjectType.VARIABLE,
            TerraformObjectType.OUTPUT,
            TerraformObjectType.LOCAL,
        ):
            if labels:
                name = labels[0]

        # Find block line number
        block_line = self._find_block_line(file_path, block_type, labels)

        # Create source location
        source_location = None
        if block_line:
            end_line = self._find_block_end(file_path, block_line)
            source_location = SourceLocation(
                file_path=file_path, line_start=block_line, line_end=end_line
            )

        # Parse attributes
        attributes = {}
        count_attr = None
        for_each_attr = None
        depends_on = []
        lifecycle = {}

        for key, value in block_data.items():
            # Find attribute line number
            attr_line = None
            if block_line:
                attr_line = self._find_attribute_line(file_path, block_line, key)

            # Parse attribute value
            attr_value = self._parse_attribute_value(value, file_path, attr_line)

            # Check for meta-arguments
            if key == "count":
                count_attr = attr_value
                continue
            elif key == "for_each":
                for_each_attr = attr_value
                continue
            elif key == "depends_on":
                depends_on = value if isinstance(value, list) else [value]
                continue
            elif key == "lifecycle":
                lifecycle = value if isinstance(value, dict) else {}
                continue
            elif key == "provider":
                continue

            # Create attribute
            attribute = TerraformAttribute(name=key, value=attr_value)
            attributes[key] = attribute

        # Create block
        return TerraformBlock(
            block_type=obj_type,
            resource_type=resource_type,
            name=name,
            labels=labels,
            attributes=attributes,
            count=count_attr,
            for_each=for_each_attr,
            depends_on=depends_on,
            lifecycle=lifecycle,
            source_location=source_location,
        )

    def _get_object_type(self, block_type: str) -> TerraformObjectType:
        """Convert block type string to TerraformObjectType."""
        type_map = {
            "resource": TerraformObjectType.RESOURCE,
            "data": TerraformObjectType.DATA_SOURCE,
            "module": TerraformObjectType.MODULE,
            "variable": TerraformObjectType.VARIABLE,
            "output": TerraformObjectType.OUTPUT,
            "locals": TerraformObjectType.LOCAL,
            "provider": TerraformObjectType.PROVIDER,
            "terraform": TerraformObjectType.TERRAFORM,
        }

        return type_map.get(block_type, TerraformObjectType.UNKNOWN)

    # ========================================================================
    # FILE PARSING
    # ========================================================================

    def parse_file(self, file_path: str) -> TerraformFile:
        """Parse a Terraform file and extract all metadata."""
        # Cache file for line number lookups
        self._cache_file(file_path)

        # Parse file content
        if file_path.endswith(".tf.json"):
            parsed_data = self._parse_json_file(file_path)
        else:
            parsed_data = self._parse_hcl_file(file_path)

        if not parsed_data:
            return TerraformFile(file_path=file_path)

        blocks = []

        # Parse resources
        for resource_item in parsed_data.get("resource", []):
            for resource_type, resources in resource_item.items():
                for resource_name, resource_data in resources.items():
                    block = self._parse_block(
                        "resource",
                        resource_data,
                        file_path,
                        labels=[resource_type, resource_name],
                    )
                    blocks.append(block)

        # Parse data sources
        for data_item in parsed_data.get("data", []):
            for data_type, data_sources in data_item.items():
                for data_name, data_data in data_sources.items():
                    block = self._parse_block(
                        "data",
                        data_data,
                        file_path,
                        labels=[data_type, data_name],
                    )
                    blocks.append(block)

        # Parse modules
        for module_item in parsed_data.get("module", []):
            for module_name, module_data in module_item.items():
                block = self._parse_block(
                    "module", module_data, file_path, labels=[module_name]
                )
                blocks.append(block)

        # Parse variables
        for var_item in parsed_data.get("variable", []):
            for var_name, var_data in var_item.items():
                block = self._parse_block(
                    "variable", var_data, file_path, labels=[var_name]
                )
                blocks.append(block)

        # Parse outputs
        for output_item in parsed_data.get("output", []):
            for output_name, output_data in output_item.items():
                block = self._parse_block(
                    "output", output_data, file_path, labels=[output_name]
                )
                blocks.append(block)

        # Parse locals
        for locals_data in parsed_data.get("locals", []):
            for local_name, local_value in locals_data.items():
                block = self._parse_block(
                    "locals", {"value": local_value}, file_path, labels=[local_name]
                )
                blocks.append(block)

        # Parse providers
        for provider_item in parsed_data.get("provider", []):
            for provider_name, provider_data in provider_item.items():
                block = self._parse_block(
                    "provider", provider_data, file_path, labels=[provider_name]
                )
                blocks.append(block)

        # Parse terraform blocks
        for terraform_item in parsed_data.get("terraform", []):
            block = self._parse_block("terraform", terraform_item, file_path, labels=[])
            blocks.append(block)

        return TerraformFile(file_path=file_path, blocks=blocks)

    def _parse_hcl_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse HCL file using python-hcl2."""
        try:
            import hcl2

            with open(file_path, encoding="utf-8") as f:
                return hcl2.load(f)
        except ImportError:
            print(
                "Error: python-hcl2 not installed. Install with: pip install python-hcl2"
            )
            return None
        except Exception as e:
            print(f"Error parsing HCL file {file_path}: {e}")
            return None

    def _parse_json_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse JSON Terraform file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error parsing JSON file {file_path}: {e}")
            return None

    # ========================================================================
    # MODULE PARSING
    # ========================================================================

    def parse_module(self, root_path: str, recursive: bool = False) -> TerraformModule:
        """
        Parse an entire Terraform module (directory of .tf files).

        Args:
            root_path: Path to the module directory
            recursive: Whether to recursively parse subdirectories

        Returns:
            TerraformModule with all files and blocks
        """
        root = Path(root_path)
        files = []

        patterns = ["*.tf", "*.tf.json"]

        def collect_files(directory: Path):
            for pattern in patterns:
                for tf_file in directory.glob(pattern):
                    try:
                        parsed_file = self.parse_file(str(tf_file))
                        files.append(parsed_file)
                    except Exception as e:
                        print(f"Warning: Failed to parse {tf_file}: {e}")

        collect_files(root)

        if recursive:
            for subdir in root.rglob("*"):
                if subdir.is_dir() and subdir != root:
                    collect_files(subdir)

        return TerraformModule(root_path=str(root), files=files)

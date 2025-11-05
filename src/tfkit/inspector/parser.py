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

        # Terraform function registry (subset of common functions)
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
    # REFERENCE PARSING
    # ========================================================================

    def _parse_reference(self, ref_string: str) -> Optional[TerraformReference]:
        """
        Parse a Terraform reference string.

        Examples:
            var.environment -> Variable reference
            local.vpc_id -> Local reference
            aws_vpc.main.id -> Resource reference
            module.vpc.vpc_id -> Module reference
            data.aws_ami.ubuntu.id -> Data source reference
        """
        parts = ref_string.split(".")

        if len(parts) < 2:
            return None

        prefix = parts[0]

        # Variable reference: var.name
        if prefix == "var":
            return TerraformReference(
                reference_type=ReferenceType.VARIABLE,
                target=f"var.{parts[1]}",
                attribute_path=parts[2:] if len(parts) > 2 else [],
                full_reference=ref_string,
            )

        # Local reference: local.name
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

        # Resource reference: type.name.attr
        if len(parts) >= 2:
            return TerraformReference(
                reference_type=ReferenceType.RESOURCE,
                target=f"{parts[0]}.{parts[1]}",
                attribute_path=parts[2:] if len(parts) > 2 else [],
                full_reference=ref_string,
            )

        return None

    def _extract_references(self, value: Any) -> List[TerraformReference]:
        """Extract all Terraform references from any value type comprehensively."""
        references = []

        if value is None:
            return references

        if isinstance(value, str):
            references.extend(self._extract_references_from_string(value))

        elif isinstance(value, list):
            for item in value:
                references.extend(self._extract_references(item))

        elif isinstance(value, dict):
            for k, v in value.items():
                references.extend(self._extract_references(k))
                references.extend(self._extract_references(v))

        elif isinstance(value, (int, float, bool)):
            # Primitive types don't contain references
            pass

        else:
            try:
                for item in value:
                    references.extend(self._extract_references(item))
            except TypeError:
                pass

        seen = set()
        unique_references = []
        for ref in references:
            if ref.full_reference not in seen:
                seen.add(ref.full_reference)
                unique_references.append(ref)

        return unique_references

    def _extract_references_from_string(self, value: str) -> List[TerraformReference]:
        """Extract all references from a string value."""
        references = []

        if not value or not isinstance(value, str):
            return references

        direct_refs = self._find_references_in_expression(value)
        for ref_str in direct_refs:
            ref = self._parse_reference(ref_str)
            if ref:
                references.append(ref)

        interpolation_pattern = r"\$\{([^}]+)\}"
        interpolation_matches = re.findall(interpolation_pattern, value)

        for interpolation_content in interpolation_matches:
            inner_refs = self._find_references_in_expression(interpolation_content)
            for ref_str in inner_refs:
                ref = self._parse_reference(ref_str)
                if ref:
                    references.append(ref)

            if "${" in interpolation_content:
                references.extend(
                    self._extract_references_from_string(interpolation_content)
                )

        function_refs = self._extract_references_from_functions(value)
        references.extend(function_refs)

        heredoc_refs = self._extract_references_from_heredoc(value)
        references.extend(heredoc_refs)

        return references

    def _extract_references_from_functions(
        self, value: str
    ) -> List[TerraformReference]:
        """Extract references from function calls within strings."""
        references = []

        # Look for function calls and extract references from their arguments
        function_pattern = r"([a-z_][a-z0-9_]*)\s*\(([^)]*)\)"
        function_matches = re.finditer(
            function_pattern, value, re.IGNORECASE | re.DOTALL
        )

        for match in function_matches:
            func_name = match.group(1)
            args_str = match.group(2)

            if func_name == "templatefile":
                args = self._split_function_arguments(args_str)
                if len(args) >= 2:
                    vars_arg = args[1].strip()
                    references.extend(self._extract_references_from_string(vars_arg))

            elif func_name == "format":
                args = self._split_function_arguments(args_str)
                for arg in args[1:]:
                    arg = arg.strip()
                    references.extend(self._extract_references_from_string(arg))

            elif func_name == "join":
                args = self._split_function_arguments(args_str)
                if len(args) >= 2:
                    list_arg = args[1].strip()
                    references.extend(self._extract_references_from_string(list_arg))

        return references

    def _extract_references_from_heredoc(self, value: str) -> List[TerraformReference]:
        """Extract references from HEREDOC syntax."""
        references = []

        heredoc_pattern = r"<<-?\s*\w+\s*\n(.*?)\n\s*\w+"
        heredoc_matches = re.finditer(heredoc_pattern, value, re.DOTALL)

        for match in heredoc_matches:
            heredoc_content = match.group(1)
            references.extend(self._extract_references_from_string(heredoc_content))

        return references

    def _split_function_arguments(self, args_str: str) -> List[str]:
        """Split function arguments respecting nested structures."""
        args = []
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
                escape_next = True
                current_arg.append(char)
                continue

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

            elif char in "([{":
                depth += 1
                current_arg.append(char)
            elif char in ")]}":
                depth -= 1
                current_arg.append(char)

            elif char == "," and depth == 0 and not in_string:
                args.append("".join(current_arg).strip())
                current_arg = []
            else:
                current_arg.append(char)

        if current_arg:
            args.append("".join(current_arg).strip())

        return args

    def _find_references_in_expression(self, expression: str) -> List[str]:
        """Find all Terraform references in an expression with comprehensive patterns."""
        references = []

        patterns = [
            # Variable references: var.name, var.name.attr
            r"\bvar\.[a-zA-Z_][a-zA-Z0-9_-]*(?:\.[a-zA-Z_][a-zA-Z0-9_-]*)*\b",
            # Local references: local.name, local.name.attr
            r"\blocal\.[a-zA-Z_][a-zA-Z0-9_-]*(?:\.[a-zA-Z_][a-zA-Z0-9_-]*)*\b",
            # Module references: module.name, module.name.output
            r"\bmodule\.[a-zA-Z_][a-zA-Z0-9_-]*(?:\.[a-zA-Z_][a-zA-Z0-9_-]*)*\b",
            # Data source references: data.type.name, data.type.name.attr
            r"\bdata\.[a-zA-Z_][a-zA-Z0-9_-]*\.[a-zA-Z_][a-zA-Z0-9_-]*(?:\.[a-zA-Z_][a-zA-Z0-9_-]*)*\b",
            # Resource references: type.name, type.name.attr
            r"\b[a-z_][a-z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_-]*(?:\.[a-zA-Z_][a-zA-Z0-9_-]*)*\b",
            # Path references: path.module, path.root, path.cwd
            r"\bpath\.[a-z]+\b",
            # Terraform references: terraform.workspace
            r"\bterraform\.[a-z]+\b",
            # Count references: count.index
            r"\bcount\.[a-z]+\b",
            # Each references: each.key, each.value
            r"\beach\.[a-z]+\b",
            # Self references: self.attr
            r"\bself\.[a-zA-Z_][a-zA-Z0-9_-]*(?:\.[a-zA-Z_][a-zA-Z0-9_-]*)*\b",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, expression)
            references.extend(matches)

        filtered_references = []
        for ref in references:
            if re.search(r"[a-zA-Z]" + re.escape(ref) + r"[a-zA-Z]", expression):
                continue
            if self._is_inside_string_literal(expression, ref):
                continue
            filtered_references.append(ref)

        return filtered_references

    def _is_inside_string_literal(self, expression: str, substring: str) -> bool:
        """Check if a substring appears inside a string literal in an expression."""
        in_string = False
        string_char = None
        escape_next = False

        i = 0
        while i < len(expression):
            char = expression[i]

            if escape_next:
                escape_next = False
                i += 1
                continue

            if char == "\\":
                escape_next = True
                i += 1
                continue

            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None

            if expression[i : i + len(substring)] == substring and in_string:
                return True

            i += 1

        return False

    def _find_references_in_expression(self, expression: str) -> List[str]:
        """Find all Terraform references in an expression."""
        # Pattern for Terraform references
        pattern = r"\b(var\.[a-zA-Z0-9_]+|local\.[a-zA-Z0-9_]+|module\.[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*|data\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*|[a-z][a-z0-9_]*\.[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*|path\.[a-z]+|terraform\.[a-z]+|count\.[a-z]+|each\.[a-z]+|self\.[a-zA-Z0-9_]+)"

        matches = re.findall(pattern, expression)
        return matches

    # ========================================================================
    # FUNCTION PARSING
    # ========================================================================

    def _parse_function_call(self, expression: str) -> Optional[TerraformFunction]:
        """
        Parse a Terraform function call.

        Example: file("path/to/file") -> TerraformFunction(name="file", arguments=["path/to/file"])
        """
        expression = expression.strip()

        # Pattern: function_name(arguments)
        pattern = r"^([a-z][a-z0-9_]*)\s*\((.*)\)$"
        match = re.match(pattern, expression, re.DOTALL)

        if not match:
            return None

        func_name = match.group(1)
        args_str = match.group(2).strip()

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
        args_str = args_str.strip()
        if not args_str:
            return []

        arguments = []
        current_arg = []
        depth = 0
        in_string = False
        string_char = None
        escape_next = False

        i = 0
        while i < len(args_str):
            char = args_str[i]

            if escape_next:
                current_arg.append(char)
                escape_next = False
                i += 1
                continue

            if char == "\\":
                current_arg.append(char)
                escape_next = True
                i += 1
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

            # Handle comma separation (only at depth 0, not in strings)
            elif char == "," and depth == 0 and not in_string:
                arg_str = "".join(current_arg).strip()
                if arg_str:
                    arguments.append(self._parse_argument_value(arg_str))
                current_arg = []
            else:
                current_arg.append(char)

            i += 1

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
        refs = self._find_references_in_expression(arg_str)
        if refs and len(refs) == 1 and refs[0] == arg_str:
            ref = self._parse_reference(arg_str)
            if ref:
                return ref

        # Try to parse as nested function
        if "(" in arg_str and ")" in arg_str:
            func = self._parse_function_call(arg_str)
            if func:
                return func

        # Try to parse as map/object
        if arg_str.startswith("{") and arg_str.endswith("}"):
            try:
                # Try to parse as JSON-like structure
                # Replace Terraform interpolation with placeholders
                temp_str = re.sub(r"\$\{[^}]+\}", '"INTERPOLATION"', arg_str)
                parsed = json.loads(temp_str)
                return parsed
            except json.JSONDecodeError:
                # If JSON parsing fails, try to parse as Terraform map
                return self._parse_terraform_map(arg_str)

        # Try to parse as list
        if arg_str.startswith("[") and arg_str.endswith("]"):
            try:
                temp_str = re.sub(r"\$\{[^}]+\}", '"INTERPOLATION"', arg_str)
                parsed = json.loads(temp_str)
                return parsed
            except json.JSONDecodeError:
                pass

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

        # Default: return as string (might contain interpolations)
        return arg_str

    def _parse_terraform_map(self, map_str: str) -> Dict[str, Any]:
        """Parse a Terraform map expression."""
        # Remove outer braces
        content = map_str[1:-1].strip()
        result = {}

        if not content:
            return result

        current_key = []
        current_value = []
        depth = 0
        in_string = False
        string_char = None
        escape_next = False
        parsing_key = True

        i = 0
        while i < len(content):
            char = content[i]

            if escape_next:
                if parsing_key:
                    current_key.append(char)
                else:
                    current_value.append(char)
                escape_next = False
                i += 1
                continue

            if char == "\\":
                escape_next = True
                if parsing_key:
                    current_key.append(char)
                else:
                    current_value.append(char)
                i += 1
                continue

            # Handle strings
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None

            # Handle brackets
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1

            # Handle equals sign (key-value separator)
            if char == "=" and depth == 0 and not in_string and parsing_key:
                parsing_key = False
                # Skip whitespace after equals
                i += 1
                while i < len(content) and content[i].isspace():
                    i += 1
                continue

            # Handle comma (entry separator)
            if char == "," and depth == 0 and not in_string and not parsing_key:
                key_str = "".join(current_key).strip()
                value_str = "".join(current_value).strip()

                if key_str:
                    # Remove quotes from key if present
                    if (key_str.startswith('"') and key_str.endswith('"')) or (
                        key_str.startswith("'") and key_str.endswith("'")
                    ):
                        key_str = key_str[1:-1]

                    result[key_str] = self._parse_argument_value(value_str)

                current_key = []
                current_value = []
                parsing_key = True
                i += 1
                continue

            if parsing_key:
                current_key.append(char)
            else:
                current_value.append(char)

            i += 1

        # Handle the last key-value pair
        if current_key and current_value:
            key_str = "".join(current_key).strip()
            value_str = "".join(current_value).strip()

            if (key_str.startswith('"') and key_str.endswith('"')) or (
                key_str.startswith("'") and key_str.endswith("'")
            ):
                key_str = key_str[1:-1]

            result[key_str] = self._parse_argument_value(value_str)

        return result

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
            if "${" in value:
                interpolation_content = re.search(r"\$\{(.+)\}", value)
                if interpolation_content:
                    inner_content = interpolation_content.group(1).strip()
                    if self._parse_function_call(inner_content):
                        return AttributeType.FUNCTION
                return AttributeType.INTERPOLATION

            refs = self._find_references_in_expression(value)
            if refs and value.strip() in refs:
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
                interpolation_content = re.search(r"\$\{(.+)\}", value)
                if interpolation_content:
                    inner_content = interpolation_content.group(1).strip()
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

        # Extract resource type and name for resources/data sources
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
                # Provider alias
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
        """
        Parse a Terraform file and extract all metadata.

        Args:
            file_path: Path to the .tf or .tf.json file

        Returns:
            TerraformFile with all blocks and metadata
        """
        # Cache file for line number lookups
        self._cache_file(file_path)

        # Parse file content
        if file_path.endswith(".tf.json"):
            parsed_data = self._parse_json_file(file_path)
        else:
            parsed_data = self._parse_hcl_file(file_path)

        if not parsed_data:
            return TerraformFile(file_path=file_path)

        # Extract blocks
        blocks = []

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

        for output_item in parsed_data.get("data", []):
            for name, data in output_item.items():
                block = self._parse_block("data", data, file_path, labels=[name])
                blocks.append(block)

        for output_item in parsed_data.get("module", []):
            for name, data in output_item.items():
                block = self._parse_block("module", data, file_path, labels=[name])
                blocks.append(block)

        for output_item in parsed_data.get("variable", []):
            for name, data in output_item.items():
                block = self._parse_block("variable", data, file_path, labels=[name])
                blocks.append(block)

        for output_item in parsed_data.get("output", []):
            for name, data in output_item.items():
                block = self._parse_block("output", data, file_path, labels=[name])
                blocks.append(block)

        for locals_data in parsed_data.get("locals", []):
            for local_name, local_value in locals_data.items():
                block = self._parse_block(
                    "locals", {"value": local_value}, file_path, labels=[local_name]
                )
                blocks.append(block)

        for provider_item in parsed_data.get("provider", []):
            for provider_name, provider_data in provider_item.items():
                block = self._parse_block(
                    "provider",
                    provider_data,
                    file_path,
                    labels=[provider_name],
                )
                blocks.append(block)

        for terraform_item in parsed_data.get("terraform", []):
            block = self._parse_block(
                "terraform",
                terraform_item,
                file_path,
                labels=[],
            )
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

    def parse_module(self, root_path: str, recursive: bool = True) -> TerraformModule:
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
                if subdir.is_dir():
                    collect_files(subdir)

        return TerraformModule(root_path=str(root), files=files)

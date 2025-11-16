import logging
from pathlib import Path
from typing import Any, Dict, List

from tfkit.parser.models import (
    BlockParsingStrategy,
    SourceLocation,
    TerraformLocal,
    TerraformObjectType,
)

logger = logging.getLogger(__name__)


class LocalsParsingStrategy(BlockParsingStrategy):
    """
    Recursive ``locals`` parser.

    - Name format:  locals.<key>.<key>...
    - Only map keys become TerraformLocal objects
    - List elements are **ignored** (no `.[index]` entries)
    """

    def can_parse(self, block_type: str) -> bool:
        return block_type in (TerraformObjectType.LOCAL.value, "locals")

    # --------------------------------------------------------------------- #
    # Public entry point
    # --------------------------------------------------------------------- #
    def parse(
        self,
        block_type: str,
        block_name: str,
        block_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformLocal"]:
        if not isinstance(block_data, dict):
            logger.error(
                f"Unexpected data type for 'locals' block in {file_path}: {type(block_data)}"
            )
            return []

        locals_dict = block_data
        if "locals" in block_data:
            locals_dict = block_data["locals"]
            if isinstance(locals_dict, list) and locals_dict:
                locals_dict = locals_dict[0]

        if not isinstance(locals_dict, dict):
            logger.error(f"Malformed 'locals' block in {file_path}: expected dict")
            return []

        block_loc = self.extract_source_location(
            file_path=file_path,
            block_name="locals {",
            raw_content=raw_content,
        )

        local_objects: List[TerraformLocal] = []
        for top_name, value in locals_dict.items():
            self._walk_local(
                value=value,
                path_parts=[top_name],
                raw_content=raw_content,
                file_path=file_path,
                block_loc=block_loc,
                local_objects=local_objects,
            )

        return local_objects

    # --------------------------------------------------------------------- #
    # Recursive walker – only descends into dicts
    # --------------------------------------------------------------------- #
    def _walk_local(
        self,
        value: Any,
        path_parts: List[str],
        raw_content: str,
        file_path: Path,
        block_loc: SourceLocation,
        local_objects: List[TerraformLocal],
    ) -> None:
        # Full name: <key>.<key>...
        full_name = ".".join(path_parts)

        # Precise source location
        loc = self._locate_key_value(
            key=path_parts[-1],
            raw_content=raw_content,
            block_start=block_loc.start_line,
            block_end=block_loc.end_line,
            file_path=file_path,
        )

        raw_code = self.extract_raw_code(raw_content, loc)

        # Create TerraformLocal
        local_obj = TerraformLocal(
            object_type=TerraformObjectType.LOCAL,
            raw_code=raw_code,
            value=value,
            name=full_name,
            source_location=loc,
            attributes={},
        )
        local_objects.append(local_obj)

        if isinstance(value, dict):
            for k, v in value.items():
                self._walk_local(
                    value=v,
                    path_parts=path_parts + [k],
                    raw_content=raw_content,
                    file_path=file_path,
                    block_loc=block_loc,
                    local_objects=local_objects,
                )

    # --------------------------------------------------------------------- #
    # Source location finder (FIXED)
    # --------------------------------------------------------------------- #
    def _locate_key_value(
        self,
        key: str,
        raw_content: str,
        block_start: int,
        block_end: int,
        file_path: Path,
    ) -> SourceLocation:
        from tfkit.parser.models import SourceLocation

        lines = raw_content.split("\n")
        start_idx = max(0, block_start - 1)
        end_idx = min(len(lines), block_end)

        assignment_line = -1
        for i in range(start_idx, end_idx):
            if key in lines[i] and "=" in lines[i]:
                assignment_line = i
                break

        if assignment_line == -1:
            return SourceLocation(
                file_path=file_path,
                start_line=block_start,
                end_line=block_end,
            )

        start_line = assignment_line + 1
        end_line = assignment_line + 1

        brace = bracket = paren = 0
        line = lines[assignment_line]
        brace += line.count("{") - line.count("}")
        bracket += line.count("[") - line.count("]")
        paren += line.count("(") - line.count(")")

        if brace > 0 or bracket > 0 or paren > 0:
            for j in range(assignment_line + 1, end_idx):
                brace += lines[j].count("{") - lines[j].count("}")
                bracket += lines[j].count("[") - lines[j].count("]")
                paren += lines[j].count("(") - lines[j].count(")")

                if brace <= 0 and bracket <= 0 and paren <= 0:
                    end_line = j + 1
                    break

        return SourceLocation(
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
        )

import logging
from pathlib import Path
from typing import Any, Dict, List

from tfkit.parser.base import BlockParsingStrategy
from tfkit.parser.models import (
    # SourceLocation,
    TerraformMoved,
    TerraformObjectType,
)

logger = logging.getLogger(__name__)


class MovedParsingStrategy(BlockParsingStrategy):
    """
    Strategy for parsing 'moved' blocks.

    Moved blocks are used for refactoring - they tell Terraform that a resource
    or module has moved to a new address.

    Example Terraform moved block:
        moved {
          from = aws_instance.old_name
          to   = aws_instance.new_name
        }

        moved {
          from = module.old_module
          to   = module.new_module
        }
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles 'moved' blocks."""
        return block_type == TerraformObjectType.MOVED.value

    def parse(
        self,
        block_type: str,
        block_name: str,
        block_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformMoved"]:
        """
        Parse a moved block.

        HCL2 structure: {"from": "...", "to": "..."}

        Note: moved blocks don't have a name, so block_name will be "moved"
        """
        if not isinstance(block_data, dict):
            logger.error(
                f"Unexpected data type for 'moved' block in {file_path}: {type(block_data)}"
            )
            return []

        # Extract from and to addresses
        from_address = block_data.get("from")
        to_address = block_data.get("to")

        # Convert to string if necessary
        if from_address is not None:
            from_address = str(from_address)
        if to_address is not None:
            to_address = str(to_address)

        # Extract source location
        source_location = self.extract_source_location(
            file_path=file_path,
            block_name="moved {",
            raw_content=raw_content,
        )
        raw_code = self.extract_raw_code(raw_content, source_location)

        # Collect any additional attributes (rare, but possible)
        remaining_attrs = {}
        for key, val in block_data.items():
            if key not in ("from", "to"):
                remaining_attrs[key] = val

        moved_object = TerraformMoved(
            object_type=TerraformObjectType.MOVED,
            name="",  # Moved blocks don't have names
            source_location=source_location,
            raw_code=raw_code,
            attributes=remaining_attrs,
            from_address=from_address,
            to_address=to_address,
        )

        return [moved_object]

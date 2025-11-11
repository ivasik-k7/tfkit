import logging
from pathlib import Path
from typing import Any, Dict, List

from tfkit.parser.models import (
    BlockParsingStrategy,
    TerraformDataSource,
    # SourceLocation,
    TerraformObjectType,
)

logger = logging.getLogger(__name__)


class DataSourceParsingStrategy(BlockParsingStrategy):
    """
    Strategy for parsing 'data' blocks.

    Example Terraform data source:
        data "aws_ami" "ubuntu" {
          most_recent = true
          owners      = ["099720109477"] # Canonical

          filter {
            name   = "name"
            values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
          }
        }
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles 'data' blocks."""
        return (
            block_type == TerraformObjectType.DATA_SOURCE.value or block_type == "data"
        )

    def parse(
        self,
        block_type: str,
        block_name: str,
        block_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformDataSource"]:
        """
        Parse a data source block.

        HCL2 structure: {"aws_ami": {"ubuntu": {...attributes...}}}

        Returns:
            List containing a single TerraformDataSource object
        """
        if not isinstance(block_data, dict):
            logger.error(
                f"Unexpected data type for 'data' block in {file_path}: {type(block_data)}"
            )
            return []

        # Extract data source type and name from block structure
        if len(block_data) != 1:
            logger.error(
                f"Malformed 'data' block in {file_path}: expected single data source type"
            )
            return []

        data_type = list(block_data.keys())[0]
        data_source_data = block_data[data_type]

        if not isinstance(data_source_data, dict) or len(data_source_data) != 1:
            logger.error(
                f"Malformed 'data' block in {file_path}: expected single data source name"
            )
            return []

        data_name = list(data_source_data.keys())[0]
        attributes = data_source_data[data_name]

        if not isinstance(attributes, dict):
            logger.error(
                f"Malformed 'data' block in {file_path}: expected dict of attributes"
            )
            return []

        # Extract source location
        source_location = self.extract_source_location(
            file_path=file_path,
            block_name=f'data "{data_type}" "{data_name}"',
            raw_content=raw_content,
        )

        raw_code = self.extract_raw_code(raw_content, source_location)

        # Extract meta-arguments
        depends_on = attributes.pop("depends_on", [])
        count = attributes.pop("count", None)
        for_each = attributes.pop("for_each", None)

        # Extract provider if specified
        provider = attributes.pop("provider", None)

        # Create the data source object
        data_source = TerraformDataSource(
            object_type=TerraformObjectType.DATA_SOURCE,
            raw_code=raw_code,
            name=data_name,
            data_type=data_type,
            provider=provider,
            depends_on=depends_on,
            count=count,
            for_each=for_each,
            source_location=source_location,
        )

        return [data_source]

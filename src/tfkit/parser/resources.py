import logging
from pathlib import Path
from typing import Any, Dict, List

from tfkit.parser.models import (
    BlockParsingStrategy,
    # SourceLocation,
    TerraformObjectType,
    TerraformResource,
)

logger = logging.getLogger(__name__)


class ResourceParsingStrategy(BlockParsingStrategy):
    """
    Strategy for parsing 'resource' blocks.

    Example Terraform resource:
        resource "aws_instance" "web" {
          ami           = "ami-12345678"
          instance_type = "t2.micro"

          tags = {
            Name = "web-server"
          }

          lifecycle {
            create_before_destroy = true
          }
        }
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles 'resource' blocks."""
        return (
            block_type == TerraformObjectType.RESOURCE.value or block_type == "resource"
        )

    def parse(
        self,
        block_type: str,
        block_name: str,
        block_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformResource"]:
        """
        Parse a resource block.

        HCL2 structure: {"aws_instance": {"web": {...attributes...}}}

        Returns:
            List containing a single TerraformResource object
        """
        if not isinstance(block_data, dict):
            logger.error(
                f"Unexpected data type for 'resource' block in {file_path}: {type(block_data)}"
            )
            return []

        # Extract resource type and name from block structure
        if len(block_data) != 1:
            logger.error(
                f"Malformed 'resource' block in {file_path}: expected single resource type"
            )
            return []

        resource_type = list(block_data.keys())[0]
        resource_data = block_data[resource_type]

        if not isinstance(resource_data, dict) or len(resource_data) != 1:
            logger.error(
                f"Malformed 'resource' block in {file_path}: expected single resource name"
            )
            return []

        resource_name = list(resource_data.keys())[0]
        attributes = resource_data[resource_name]

        if not isinstance(attributes, dict):
            logger.error(
                f"Malformed 'resource' block in {file_path}: expected dict of attributes"
            )
            return []

        # Extract source location
        source_location = self.extract_source_location(
            file_path=file_path,
            block_name=f'resource "{resource_type}" "{resource_name}"',
            raw_content=raw_content,
        )

        raw_code = self.extract_raw_code(raw_content, source_location)

        # Extract meta-arguments
        depends_on = attributes.pop("depends_on", [])
        count = attributes.pop("count", None)
        for_each = attributes.pop("for_each", None)
        lifecycle = attributes.pop("lifecycle", {})
        provisioners = attributes.pop("provisioner", [])

        # Extract provider if specified
        provider = attributes.pop("provider", None)

        # Create the resource object
        resource = TerraformResource(
            object_type=TerraformObjectType.RESOURCE,
            raw_code=raw_code,
            name=resource_name,
            resource_type=resource_type,
            provider=provider,
            depends_on=depends_on,
            count=count,
            for_each=for_each,
            lifecycle=lifecycle,
            provisioners=provisioners,
            source_location=source_location,
        )

        return [resource]

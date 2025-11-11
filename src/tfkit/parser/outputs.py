"""
Parsing strategy for Terraform output blocks.

Example Terraform output:
    output "instance_ip" {
      description = "The public IP of the instance"
      value       = aws_instance.example.public_ip
      sensitive   = true
      depends_on  = [aws_instance.example]
    }
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from tfkit.parser.base import BlockParsingStrategy
from tfkit.parser.models import (
    TerraformObjectType,
    TerraformOutput,
)

logger = logging.getLogger(__name__)


class OutputParsingStrategy(BlockParsingStrategy):
    """
    Strategy for parsing 'output' blocks.

    Example Terraform outputs:
        output "instance_ip" {
          description = "The public IP of the instance"
          value       = aws_instance.main.public_ip
          sensitive   = false
        }

        output "vpc_id" {
          value = module.vpc.vpc_id
          depends_on = [module.vpc]
        }
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles 'output' blocks."""
        return block_type == TerraformObjectType.OUTPUT.value

    def parse(
        self,
        block_type: str,
        block_name: str,
        block_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformOutput"]:
        """
        Parse an output block.

        HCL2 structure: {"output_name": {"value": "...", "description": "..."}}
        block_name = output name (e.g., "instance_ip")
        block_data = {"instance_ip": {"value": "...", "description": "..."}}
        """
        if not isinstance(block_data, dict):
            logger.error(
                f"Unexpected data type for 'output' block in {file_path}: {type(block_data)}"
            )
            return []

        if len(block_data) == 0:
            logger.error(f"Empty output block data in {file_path}")
            return []

        # Extract output attributes
        output_attrs = block_data.get(block_name, {})

        if not isinstance(output_attrs, dict):
            logger.error(
                f"Malformed output '{block_name}' in {file_path}: attributes not a dict"
            )
            return []

        # Extract source location
        source_location = self.extract_source_location(
            file_path=file_path,
            block_name=f'output "{block_name}"',
            raw_content=raw_content,
        )
        raw_code = self.extract_raw_code(raw_content, source_location)

        # Extract specific output attributes
        value = output_attrs.get("value")
        description = output_attrs.get("description")
        if description is not None:
            description = str(description)

        sensitive = output_attrs.get("sensitive", False)
        depends_on = output_attrs.get("depends_on", [])

        # Ensure depends_on is a list
        if not isinstance(depends_on, list):
            depends_on = [depends_on] if depends_on else []

        # Collect remaining attributes
        remaining_attrs = {}
        for key, val in output_attrs.items():
            if key not in ("value", "description", "sensitive", "depends_on"):
                remaining_attrs[key] = val

        output_object = TerraformOutput(
            object_type=TerraformObjectType.OUTPUT,
            name=block_name,
            source_location=source_location,
            raw_code=raw_code,
            attributes=remaining_attrs,
            value=value,
            description=description,
            sensitive=sensitive,
            depends_on=depends_on,
        )

        return [output_object]

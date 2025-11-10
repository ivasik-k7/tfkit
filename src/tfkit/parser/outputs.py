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
    Fixes the 'list object has no attribute items' error and ensures robust
    extraction of value, description, sensitive, and depends_on.
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles 'output' blocks."""
        return block_type == TerraformObjectType.OUTPUT.value

    def parse(
        self,
        block_name: str,
        block_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformOutput"]:
        # --- FIX: Normalize block_data from List[Dict] to Dict ---
        normalized_data: Dict[str, Any]
        if isinstance(block_data, list):
            if not block_data or not isinstance(block_data[0], dict):
                logger.error(
                    f"Malformed 'output' block data in {file_path}: Expected Dict, got {type(block_data)}"
                )
                return []

            # The output block is implicitly singular
            normalized_data = block_data[0]
        elif isinstance(block_data, dict):
            normalized_data = block_data
        else:
            logger.error(
                f"Unexpected data type for 'output' block in {file_path}: {type(block_data)}"
            )
            return []
        # --- End Fix ---

        # 1. Determine Source Location and Raw Code
        source_location = self.extract_source_location(
            file_path=file_path,
            block_name=f'output "{block_name}"',
            raw_content=raw_content,
        )
        raw_code = self.extract_raw_code(raw_content, source_location)

        # 2. Initialize core attributes
        value: Any = None
        description: Optional[str] = None
        sensitive: Any = False  # Keep as Any to preserve HCL expression if present
        depends_on: List[str] = []

        remaining_attributes: Dict[str, Any] = {}

        # 3. Extract and map specific output arguments
        for key, attr_value in normalized_data.items():
            if key == "value":
                # MANDATORY: The output value. Stored as Any (can be string, number, expression, map, etc.)
                value = attr_value

            elif key == "description":
                # Ensure description is a string
                description = str(attr_value) if attr_value is not None else None

            elif key == "sensitive":
                # Store the value directly. Can be True/False, or an expression (string)
                sensitive = attr_value

            elif key == "depends_on":
                # Depends_on is officially an array of strings in Terraform
                # but HCL parsers might flatten a single element.
                if isinstance(attr_value, list):
                    depends_on = [str(d) for d in attr_value]
                elif isinstance(attr_value, str):
                    depends_on = [attr_value]
                else:
                    logger.warning(
                        f"'depends_on' for output '{block_name}' must be string or list of strings. Got {type(attr_value)}"
                    )

            else:
                # Capture any other unrecognized attributes
                remaining_attributes[key] = attr_value

        # 4. Mandatory Field Check (Optional: For strict validation)
        if value is None:
            logger.warning(
                f"Output '{block_name}' in {file_path} is missing the required 'value' argument."
            )

        # 5. Create and return the TerraformOutput object
        output_object = TerraformOutput(
            object_type=TerraformObjectType.OUTPUT,
            name=block_name,
            source_location=source_location,
            raw_code=raw_code,
            attributes=remaining_attributes,
            # Output-specific fields
            value=value,
            description=description,
            sensitive=sensitive,
            depends_on=depends_on,
        )

        return [output_object]

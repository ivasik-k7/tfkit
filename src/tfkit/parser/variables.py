"""
Parsing strategy for Terraform variable blocks.

Example Terraform variable:
    variable "instance_type" {
      description = "EC2 instance type"
      type        = string
      default     = "t2.micro"
      sensitive   = false
      nullable    = true

      validation {
        condition     = contains(["t2.micro", "t2.small"], var.instance_type)
        error_message = "Instance type must be t2.micro or t2.small."
      }

      validation {
        condition     = length(var.instance_type) > 0
        error_message = "Instance type cannot be empty."
      }
    }
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from tfkit.parser.base import BlockParsingStrategy
from tfkit.parser.models import (
    # SourceLocation,
    TerraformObjectType,
    TerraformVariable,
)

logger = logging.getLogger(__name__)


class VariableParsingStrategy(BlockParsingStrategy):
    """
    Strategy for parsing 'variable' blocks, covering all official arguments
    and nested 'validation' blocks, with enhanced robustness against parser output formats.
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles 'variable' blocks."""
        return block_type == TerraformObjectType.VARIABLE.value

    def parse(
        self,
        block_name: str,
        block_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformVariable"]:
        normalized_data: Dict[str, Any]
        if isinstance(block_data, list):
            if not block_data or not isinstance(block_data[0], dict):
                logger.error(
                    f"Malformed 'variable' block data in {file_path}: Expected Dict, got {type(block_data)}"
                )
                return []

            # Use the first element, which contains the variable's attributes
            normalized_data = block_data[0]
        elif isinstance(block_data, dict):
            normalized_data = block_data
        else:
            logger.error(
                f"Unexpected data type for 'variable' block in {file_path}: {type(block_data)}"
            )
            return []
        source_location = self.extract_source_location(
            file_path=file_path,
            block_name=f'variable "{block_name}"',
            raw_content=raw_content,
        )
        raw_code = self.extract_raw_code(raw_content, source_location)

        # 2. Initialize core attributes
        variable_type: Any = None
        default: Any = None
        description: Optional[str] = None
        sensitive: Any = False  # Keep as Any to preserve HCL expression if present
        nullable: Any = True  # Keep as Any to preserve HCL expression if present
        validation_blocks: List[Dict[str, Any]] = []

        remaining_attributes: Dict[str, Any] = {}

        # 3. Iterate over normalized_data to extract specific variable arguments
        for key, value in normalized_data.items():
            if key == "type":
                variable_type = value

            elif key == "default":
                default = value

            elif key == "description":
                # Ensure description is stored as a simple string, if possible
                description = str(value) if value is not None else None

            elif key == "sensitive":
                # Store the value directly (boolean, string expression, or raw token)
                sensitive = value

            elif key == "nullable":
                # Store the value directly (boolean, string expression, or raw token)
                nullable = value

            elif key == "validation":
                # Validation can be a single dict (single validation block) or a list of dicts.
                if isinstance(value, list):
                    for validation_block in value:
                        if self._is_valid_validation_block(validation_block):
                            validation_blocks.append(validation_block)
                        else:
                            logger.warning(
                                f"Skipping malformed validation block for variable '{block_name}' in {file_path}"
                            )

                elif self._is_valid_validation_block(value):
                    # Handle the case where only one validation block is present as a dict
                    validation_blocks.append(value)

            else:
                remaining_attributes[key] = value

        variable_object = TerraformVariable(
            object_type=TerraformObjectType.VARIABLE,
            name=block_name,
            source_location=source_location,
            raw_code=raw_code,
            attributes=remaining_attributes,
            # Variable-specific fields
            variable_type=variable_type,
            default=default,
            description=description,
            sensitive=sensitive,
            nullable=nullable,
            validation=validation_blocks,
        )

        return [variable_object]

    def _is_valid_validation_block(self, data: Any) -> bool:
        """
        Ensures a validation block is a dictionary and contains the two required keys.
        """
        if isinstance(data, dict):
            # Keys must be present, values can be expressions (Any)
            return "condition" in data and "error_message" in data
        return False

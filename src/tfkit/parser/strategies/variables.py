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
from typing import Any, Dict, List, Optional

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
    and nested 'validation' blocks.

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
        }
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles 'variable' blocks."""
        return block_type == TerraformObjectType.VARIABLE.value

    def parse(
        self,
        block_type: str,  # nullable
        block_name: str,
        block_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformVariable"]:
        """
        Parse a variable block.

        Args:
            block_type: The block type (should be "variable")
            block_name: The variable name extracted from HCL structure
            block_data: The nested dictionary containing variable attributes
            file_path: Path to the file being parsed
            raw_content: Raw file content for source location extraction

        Returns:
            List containing a single TerraformVariable object
        """
        if not isinstance(block_data, dict):
            logger.error(
                f"Unexpected data type for 'variable' block in {file_path}: {type(block_data)}"
            )
            return []

        if len(block_data) == 0:
            logger.error(f"Empty variable block data in {file_path}")
            return []

        var_attributes = block_data.get(block_name, {})

        if not isinstance(var_attributes, dict):
            logger.error(
                f"Malformed variable '{block_name}' in {file_path}: attributes not a dict"
            )
            return []

        source_location = self.extract_source_location(
            file_path=file_path,
            block_name=f'variable "{block_name}"',
            raw_content=raw_content,
        )
        raw_code = self.extract_raw_code(raw_content, source_location)

        variable_type: Any = None
        default: Any = None
        description: Optional[str] = None
        sensitive: Any = False
        nullable: Any = True
        validation_blocks: List[Dict[str, Any]] = []
        remaining_attributes: Dict[str, Any] = {}

        for key, value in var_attributes.items():
            if key == "type":
                variable_type = value
            elif key == "default":
                default = value
            elif key == "description":
                description = str(value) if value is not None else None
            elif key == "sensitive":
                sensitive = value
            elif key == "nullable":
                nullable = value
            elif key == "validation":
                if isinstance(value, list):
                    for validation_block in value:
                        if self._is_valid_validation_block(validation_block):
                            validation_blocks.append(validation_block)
                        else:
                            logger.warning(
                                f"Skipping malformed validation block for variable '{block_name}' in {file_path}"
                            )
                elif self._is_valid_validation_block(value):
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
        """Ensure a validation block is a dictionary with required keys."""
        if isinstance(data, dict):
            return "condition" in data and "error_message" in data
        return False

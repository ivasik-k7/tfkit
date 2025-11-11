"""
Parsing strategy for Terraform configuration blocks.

Example Terraform block:
    terraform {
      required_version = ">= 1.0"

      required_providers {
        aws = {
          source  = "hashicorp/aws"
          version = "~> 4.0"
        }
        random = {
          source  = "hashicorp/random"
          version = "3.1.0"
        }
      }

      backend "s3" {
        bucket = "my-terraform-state"
        key    = "prod/terraform.tfstate"
        region = "us-east-1"
      }

      cloud {
        organization = "my-org"
        workspaces {
          name = "my-workspace"
        }
      }

      experiments = [module_variable_optional_attrs]
    }
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from tfkit.parser.base import BlockParsingStrategy
from tfkit.parser.models import (
    TerraformObjectType,
    TerraformRootConfig,
)

logger = logging.getLogger(__name__)


class TerraformRootConfigParsingStrategy(BlockParsingStrategy):
    """
    Strategy for parsing the singular 'terraform' configuration block.
    Fixes the 'list object has no attribute items' error by normalizing
    the input block data and ensures robustness for nested blocks.
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles the 'terraform' block."""
        return block_type == TerraformObjectType.TERRAFORM_BLOCK.value

    def parse(
        self,
        block_type: str,  # nullable
        block_name: str,
        block_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformRootConfig"]:
        # The block_type is implicitly "terraform" here.
        block_type = TerraformObjectType.TERRAFORM_BLOCK.value

        normalized_data: Dict[str, Any]
        if isinstance(block_data, list):
            if not block_data or not isinstance(block_data[0], dict):
                logger.error(
                    f"Malformed '{block_type}' block data in {file_path}: Expected List[Dict], got {type(block_data)}"
                )
                return []

            normalized_data = block_data[0]
        elif isinstance(block_data, dict):
            normalized_data = block_data
        else:
            logger.error(
                f"Unexpected data type for '{block_type}' block in {file_path}: {type(block_data)}"
            )
            return []

        source_location = self.extract_source_location(
            file_path=file_path,
            block_name=block_type,  # "terraform"
            raw_content=raw_content,
        )
        raw_code = self.extract_raw_code(raw_content, source_location)

        required_version: Optional[str] = None
        required_providers: Dict[str, Any] = {}
        backend: Optional[Dict[str, Any]] = None
        cloud: Optional[Dict[str, Any]] = None
        experiments: List[str] = []

        remaining_attributes = {}

        for key, attr_value in normalized_data.items():
            if key == "required_version":
                required_version = str(attr_value)

            elif key == "required_providers":
                required_providers = self._normalize_nested_block(
                    attr_value, "required_providers", file_path
                )

            elif key == "backend":
                backend = self._normalize_nested_block(attr_value, "backend", file_path)

            elif key == "cloud":
                cloud = self._normalize_nested_block(attr_value, "cloud", file_path)

            elif key == "experiments":
                if isinstance(attr_value, list):
                    experiments = [str(e) for e in attr_value]
                elif isinstance(attr_value, str):
                    experiments = [attr_value]

            else:
                remaining_attributes[key] = attr_value

        root_config_object = TerraformRootConfig(
            object_type=TerraformObjectType.TERRAFORM_BLOCK,
            name="",
            source_location=source_location,
            raw_code=raw_code,
            attributes=remaining_attributes,
            required_version=required_version,
            required_providers=required_providers,
            backend=backend,
            cloud=cloud,
            experiments=experiments,
        )

        return [root_config_object]

    def _normalize_nested_block(
        self, attr_value: Any, block_name: str, file_path: Path
    ) -> Dict[str, Any]:
        """Helper to safely extract the configuration dictionary from a nested block."""
        if isinstance(attr_value, dict):
            return attr_value

        if isinstance(attr_value, list):
            if len(attr_value) >= 1 and isinstance(attr_value[0], dict):
                if len(attr_value) > 1:
                    logger.warning(
                        f"Multiple '{block_name}' blocks found in {file_path}. Using the first one."
                    )
                return attr_value[0]

        if attr_value is not None:
            logger.error(
                f"Malformed '{block_name}' block in {file_path}: Expected Dict or List[Dict], got {type(attr_value)}"
            )

        return {}

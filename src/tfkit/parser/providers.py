import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from tfkit.parser.models import (
    BlockParsingStrategy,
    SourceLocation,
    TerraformObjectType,
    TerraformProvider,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ProviderParsingStrategy(BlockParsingStrategy):
    """
    Strategy for parsing 'provider' blocks.

    Example Terraform providers:
        provider "aws" {
          region = var.aws_region
        }

        provider "google" {
          project = "my-project"
          region  = var.gcp_region
          alias   = "g2"
        }

        provider "azurerm" {
          features {}
          subscription_id = var.azure_subscription_id
        }
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles 'provider' blocks."""
        return block_type == TerraformObjectType.PROVIDER.value

    def parse(
        self,
        block_type: str,
        block_name: str,
        block_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformProvider"]:
        """
        Parse a provider block.

        HCL2 structure: {"provider_type": {attributes}}
        block_type = 'provider'
        block_name = 'provider' (usually)
        block_data = {"aws": {"region": "...", "alias": "..."}}
        """
        if not isinstance(block_data, dict):
            logger.error(
                f"Unexpected data type for 'provider' block in {file_path}: {type(block_data)}"
            )
            return []

        if len(block_data) == 0:
            logger.error(f"Empty provider block data in {file_path}")
            return []

        try:
            provider_type, provider_config = next(iter(block_data.items()))
        except StopIteration:
            logger.error(f"Could not iterate over provider block data in {file_path}")
            return []

        if not isinstance(provider_config, dict):
            logger.warning(
                f"Provider config for '{provider_type}' is not a dict. Treating attributes as empty."
            )
            provider_config = {}

        alias = provider_config.get("alias")
        version = provider_config.get("version")

        if alias:
            provider_name = f"{provider_type}.{alias}"
        else:
            provider_name = provider_type

        search_pattern = f'provider "{provider_type}"'

        source_location: SourceLocation = self.extract_source_location(
            file_path=file_path,
            block_name=search_pattern,
            raw_content=raw_content,
        )

        if alias:
            raw_code = self.extract_raw_code(raw_content, source_location)
            if "alias" not in raw_code or (
                f'"{alias}"' not in raw_code and f"= {alias}" not in raw_code
            ):
                lines = raw_content.split("\n")
                for i in range(source_location.end_line, len(lines)):
                    if search_pattern in lines[i]:
                        temp_location = self.extract_source_location(
                            file_path=file_path,
                            block_name=search_pattern,
                            raw_content=raw_content,
                            start_hint=i,
                        )
                        temp_raw = self.extract_raw_code(raw_content, temp_location)
                        if "alias" in temp_raw and (
                            f'"{alias}"' in temp_raw or f"= {alias}" in temp_raw
                        ):
                            source_location = temp_location
                            break

        raw_code = self.extract_raw_code(raw_content, source_location)

        configuration_attrs = {
            key: value
            for key, value in provider_config.items()
            if key not in ("alias", "version")
        }

        provider_object = TerraformProvider(
            object_type=TerraformObjectType.PROVIDER,
            name=provider_name,
            source_location=source_location,
            raw_code=raw_code,
            attributes=configuration_attrs,
            alias=alias,
            version=version,
        )

        return [provider_object]

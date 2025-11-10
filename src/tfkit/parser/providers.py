from pathlib import Path
from typing import Any, Dict, List, Optional

from tfkit.parser.models import (
    BlockParsingStrategy,
    TerraformObjectType,
    TerraformProvider,
)


class ProviderParsingStrategy(BlockParsingStrategy):
    """
    Strategy for parsing 'provider' blocks, handling configuration attributes
    and the optional 'alias' argument for multiple configurations of the same type.
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles 'provider' blocks."""
        return block_type == TerraformObjectType.PROVIDER.value

    def parse(
        self,
        block_name: str,
        block_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformProvider"]:
        """
        Parses a single 'provider' block (e.g., 'provider "aws" {}')
        into a TerraformProvider object.
        """

        source_location = self.extract_source_location(
            file_path=file_path,
            block_name=f'provider "{block_name}"',
            raw_content=raw_content,
        )
        raw_code = self.extract_raw_code(raw_content, source_location)

        provider_name: str = block_name  # e.g., "aws"
        alias: Optional[str] = None

        provider_attributes: Dict[str, Any] = {}

        # 3. Extract and map specific provider arguments
        for key, attr_value in block_data.items():
            if key == "alias":
                # CRUCIAL: Captures the alias, which makes the provider definition unique.
                # The alias is mandatory for the block to be a non-default provider instance.
                # Assuming the value is a string (HCL requires string or string expression)
                alias = str(attr_value)

            elif key == "version":
                # Provider-specific attribute, but often handled like a meta-argument
                # We store it in attributes for generic access.
                provider_attributes[key] = attr_value

            elif key == "configuration_aliases":
                # For blocks that support multiple configuration aliases (less common, usually for modules)
                # We capture this structure in the attributes.
                provider_attributes[key] = attr_value

            else:
                # All other keys are provider-specific configuration attributes
                # (e.g., "region", "access_key", "secret_key", "profile")
                provider_attributes[key] = attr_value

        provider_object = TerraformProvider(
            object_type=TerraformObjectType.PROVIDER,
            name=provider_name,
            source_location=source_location,
            raw_code=raw_code,
            attributes=provider_attributes,
            provider_name=provider_name,
            alias=alias,
        )

        return [provider_object]

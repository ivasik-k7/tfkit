# They should import the core models from the parent package (e.g., from ..models import ResourceModel)
from .data_sources import DataSourceParsingStrategy
from .locals import LocalsParsingStrategy
from .modules import ModuleParsingStrategy
from .moved import MovedParsingStrategy
from .outputs import OutputParsingStrategy
from .providers import ProviderParsingStrategy
from .resources import ResourceParsingStrategy
from .terraform_block import TerraformRootConfigParsingStrategy
from .variables import VariableParsingStrategy

__all__ = [
    "CheckStrategy",
    "DataSourceStrategy",
    "LocalsParsingStrategy",
    "ModuleParsingStrategy",
    "MovedParsingStrategy",
    "OutputStrategy",
    "ProviderParsingStrategy",
    "ResourceStrategy",
    "TerraformBlockStrategy",
    "VariableStrategy",
]

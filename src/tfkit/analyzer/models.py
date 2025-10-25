"""Data models for Terraform analysis."""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List


class ResourceType(Enum):
    RESOURCE = "resource"
    DATA = "data"
    MODULE = "module"
    VARIABLE = "variable"
    OUTPUT = "output"
    PROVIDER = "provider"
    TERRAFORM = "terraform"


@dataclass
class TerraformObject:
    type: ResourceType
    name: str
    full_name: str
    attributes: Dict[str, Any]
    dependencies: List[str]
    file_path: str
    line_number: int


@dataclass
class TerraformProject:
    resources: Dict[str, TerraformObject]
    data_sources: Dict[str, TerraformObject]
    modules: Dict[str, TerraformObject]
    variables: Dict[str, TerraformObject]
    outputs: Dict[str, TerraformObject]
    providers: Dict[str, TerraformObject]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resources": {k: asdict(v) for k, v in self.resources.items()},
            "data_sources": {k: asdict(v) for k, v in self.data_sources.items()},
            "modules": {k: asdict(v) for k, v in self.modules.items()},
            "variables": {k: asdict(v) for k, v in self.variables.items()},
            "outputs": {k: asdict(v) for k, v in self.outputs.items()},
            "providers": {k: asdict(v) for k, v in self.providers.items()},
        }

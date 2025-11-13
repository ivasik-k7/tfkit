from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set

from tfkit.graph.models import LinkType


class DependencyType(Enum):
    """Types of dependencies between Terraform objects"""

    DIRECT = "direct"
    IMPLICIT = "implicit"
    EXPLICIT = "explicit"
    MODULE = "module"
    PROVIDER = "provider"
    PROVIDER_CONFIG = "provider_config"
    MOVED = "moved"
    CONFIGURATION = "configuration"
    DATA_REFERENCE = "data_reference"
    OUTPUT = "output"
    TERRAFORM_BLOCK = "terraform_block"


@dataclass
class TerraformDependency:
    source_address: str
    target_address: str
    dependency_type: DependencyType
    attribute_path: Optional[str] = None

    def __hash__(self):
        return hash((self.source_address, self.target_address, self.dependency_type))

    def __eq__(self, other):
        if not isinstance(other, TerraformDependency):
            return False
        return (
            self.source_address == other.source_address
            and self.target_address == other.target_address
            and self.dependency_type == other.dependency_type
        )

    def to_link_type(self) -> LinkType:
        mapping = {
            DependencyType.DIRECT: LinkType.DIRECT,
            DependencyType.IMPLICIT: LinkType.IMPLICIT,
            DependencyType.EXPLICIT: LinkType.EXPLICIT,
            DependencyType.PROVIDER_CONFIG: LinkType.PROVIDER_CONFIG,
            DependencyType.MODULE: LinkType.MODULE_CALL,
            DependencyType.CONFIGURATION: LinkType.CONFIGURATION,
            DependencyType.DATA_REFERENCE: LinkType.DATA_REFERENCE,
            DependencyType.OUTPUT: LinkType.EXPORT,
            DependencyType.PROVIDER: LinkType.PROVIDER_RELATIONSHIP,
            DependencyType.TERRAFORM_BLOCK: LinkType.PROVIDER_RELATIONSHIP,
            DependencyType.MOVED: LinkType.LIFECYCLE,
        }
        return mapping.get(self.dependency_type, LinkType.IMPLICIT)


@dataclass
class ObjectDependencies:
    address: str
    depends_on: Set[TerraformDependency] = field(default_factory=set)
    referenced_by: Set[TerraformDependency] = field(default_factory=set)

    def add_dependency(self, dependency: TerraformDependency):
        self.depends_on.add(dependency)

    def add_reference(self, dependency: TerraformDependency):
        self.referenced_by.add(dependency)

    def get_all_dependencies(self) -> Set[str]:
        return {dep.target_address for dep in self.depends_on}

    def get_all_references(self) -> Set[str]:
        return {dep.source_address for dep in self.referenced_by}

    def get_dependencies_by_type(self, dep_type: DependencyType) -> Set[str]:
        return {
            dep.target_address
            for dep in self.depends_on
            if dep.dependency_type == dep_type
        }

    def get_references_by_type(self, dep_type: DependencyType) -> Set[str]:
        return {
            dep.source_address
            for dep in self.referenced_by
            if dep.dependency_type == dep_type
        }

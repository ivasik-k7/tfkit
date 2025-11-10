"""
Base models and abstract classes for Terraform parsing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union


class TerraformObjectType(Enum):
    """Enum for different Terraform object types."""

    RESOURCE = "resource"
    DATA_SOURCE = "data"
    MODULE = "module"
    VARIABLE = "variable"
    OUTPUT = "output"
    LOCAL = "local"
    PROVIDER = "provider"
    TERRAFORM_BLOCK = "terraform"
    MOVED = "moved"
    IMPORT = "import"
    CHECK = "check"


@dataclass
class SourceLocation:
    """Represents the location of an object in source code."""

    file_path: Path
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = 0

    def __str__(self) -> str:
        return f"{self.file_path}:{self.start_line}-{self.end_line}"


class BlockParsingStrategy(ABC):
    """Abstract base class for specific Terraform block parsing strategies."""

    @abstractmethod
    def can_parse(self, block_type: str) -> bool:
        """Check if this strategy can parse the given block type."""
        pass

    @abstractmethod
    def parse(
        self,
        block_type: str,
        block_name: str,
        block_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["BaseTerraformObject"]:
        """Parse the block and return list of parsed objects."""
        pass

    def extract_source_location(
        self,
        file_path: Path,
        block_name: str,
        raw_content: str,
        start_hint: int = 0,
    ) -> SourceLocation:
        """
        Extract source location information from raw content.
        This is a helper method for strategies to determine line numbers.
        """
        lines = raw_content.split("\n")
        start_line = 0
        end_line = 0

        for i, line in enumerate(lines[start_hint:], start=start_hint):
            if block_name in line or (
                block_name == "terraform" and "terraform {" in line
            ):
                start_line = i + 1
                brace_count = 0
                for j in range(i, len(lines)):
                    brace_count += lines[j].count("{") - lines[j].count("}")
                    if brace_count == 0 and lines[j].count("}") > 0:
                        end_line = j + 1
                        break
                break

        if end_line == 0:
            end_line = start_line

        return SourceLocation(
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
        )

    def extract_raw_code(
        self,
        raw_content: str,
        source_location: SourceLocation,
    ) -> str:
        lines = raw_content.split("\n")
        if source_location.start_line > 0 and source_location.end_line > 0:
            start = source_location.start_line - 1
            end = source_location.end_line
            return "\n".join(lines[start:end])
        return ""

    def extract_meta_attributes(self, block_data: Dict[str, Any]) -> Dict[str, Any]:
        meta_attrs = {}
        meta_keys = [
            "count",
            "for_each",
            "depends_on",
            "provider",
            "lifecycle",
            "provisioner",
            "providers",
        ]

        for key in meta_keys:
            if key in block_data:
                meta_attrs[key] = block_data[key]

        return meta_attrs


@dataclass
class BaseTerraformObject(ABC):
    """
    Abstract base class for all Terraform objects.
    Holds common, non-block-specific attributes.
    """

    object_type: TerraformObjectType
    name: str
    source_location: SourceLocation
    raw_code: str
    attributes: Dict[str, Any] = field(default_factory=dict)

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get attribute value with optional default."""
        return self.attributes.get(key, default)

    @abstractmethod
    def validate(self) -> bool:
        """Validate the parsed object structure."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary representation."""
        pass


@dataclass
class TerraformResource(BaseTerraformObject):
    """Represents a Terraform resource block."""

    resource_type: Optional[str] = None
    provider: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    count: Optional[Union[int, str]] = None
    for_each: Optional[Any] = None
    lifecycle: Dict[str, Any] = field(default_factory=dict)
    provisioners: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self.object_type = TerraformObjectType.RESOURCE

    def validate(self) -> bool:
        """Validate resource has required fields."""
        return bool(self.resource_type and self.name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.object_type.value,
            "resource_type": self.resource_type,
            "name": self.name,
            "provider": self.provider,
            "attributes": self.attributes,
            "depends_on": self.depends_on,
            "count": self.count,
            "for_each": self.for_each,
            "lifecycle": self.lifecycle,
            "provisioners": self.provisioners,
            "source_location": str(self.source_location),
        }


@dataclass
class TerraformDataSource(BaseTerraformObject):
    """Represents a Terraform data source block."""

    data_type: Optional[str] = None
    provider: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    count: Optional[Union[int, str]] = None
    for_each: Optional[Any] = None

    def __post_init__(self):
        self.object_type = TerraformObjectType.DATA_SOURCE

    def validate(self) -> bool:
        """Validate data source has required fields."""
        return bool(self.data_type and self.name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.object_type.value,
            "data_type": self.data_type,
            "name": self.name,
            "provider": self.provider,
            "attributes": self.attributes,
            "depends_on": self.depends_on,
            "count": self.count,
            "for_each": self.for_each,
            "source_location": str(self.source_location),
        }


@dataclass
class TerraformVariable(BaseTerraformObject):
    """Represents a Terraform variable block."""

    variable_type: Optional[str] = None
    default: Any = None
    description: Optional[str] = None
    sensitive: bool = False
    nullable: bool = True
    validation: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self.object_type = TerraformObjectType.VARIABLE

    def validate(self) -> bool:
        """Validate variable has required fields."""
        return bool(self.name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.object_type.value,
            "name": self.name,
            "variable_type": self.variable_type,
            "default": self.default,
            "description": self.description,
            "sensitive": self.sensitive,
            "nullable": self.nullable,
            "validation": self.validation,
            "attributes": self.attributes,
            "source_location": str(self.source_location),
        }


@dataclass
class TerraformOutput(BaseTerraformObject):
    """Represents a Terraform output block."""

    value: Optional[Any] = None
    description: Optional[str] = None
    sensitive: bool = False
    depends_on: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.object_type = TerraformObjectType.OUTPUT

    def validate(self) -> bool:
        """Validate output has required fields."""
        return bool(self.name and self.value is not None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.object_type.value,
            "name": self.name,
            "value": self.value,
            "description": self.description,
            "sensitive": self.sensitive,
            "depends_on": self.depends_on,
            "attributes": self.attributes,
            "source_location": str(self.source_location),
        }


class TerraformLocal(BaseTerraformObject):
    """Represents a Terraform local value block."""

    value: Any

    def __post_init__(self):
        self.object_type = TerraformObjectType.LOCAL

    def validate(self) -> bool:
        return bool(self.name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.object_type.value,
            "name": self.name,
            "value": self.value,
            "attributes": self.attributes,
            "source_location": str(self.source_location),
        }


@dataclass
class TerraformProvider(BaseTerraformObject):
    """Represents a Terraform provider block."""

    alias: Optional[str] = None
    version: Optional[str] = None

    def __post_init__(self):
        self.object_type = TerraformObjectType.PROVIDER
        self.provider_name = self.name  # Type (e.g., 'aws', 'google')
        self.name = self.alias or self.provider_name  # The effective block name/alias

    def validate(self) -> bool:
        """Validate provider has required fields (the type)."""
        return bool(self.provider_name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.object_type.value,
            "provider_name": self.provider_name,
            "alias": self.alias,
            "version": self.version,
            "attributes": self.attributes,
            "source_location": str(self.source_location),
        }


@dataclass
class TerraformRootConfig(BaseTerraformObject):
    """Represents a 'terraform' configuration block."""

    required_version: Optional[str] = None
    required_providers: Dict[str, Any] = field(default_factory=dict)
    backend: Optional[Dict[str, Any]] = None
    cloud: Optional[Dict[str, Any]] = None
    experiments: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.object_type = TerraformObjectType.TERRAFORM_BLOCK
        self.name = ""

    def validate(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.object_type.value,
            "required_version": self.required_version,
            "required_providers": self.required_providers,
            "backend": self.backend,
            "cloud": self.cloud,
            "experiments": self.experiments,
            "attributes": self.attributes,
            "source_location": str(self.source_location),
        }


@dataclass
class TerraformModule(BaseTerraformObject):
    """Represents a call to an external module."""

    source: Optional[str] = None
    version: Optional[str] = None
    # Meta-arguments (valid for module calls)
    depends_on: List[str] = field(default_factory=list)
    count: Optional[Union[int, str]] = None
    for_each: Optional[Any] = None
    providers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.object_type = TerraformObjectType.MODULE

    def validate(self) -> bool:
        """Validate module call has required fields (name and source)."""
        return bool(self.name and self.source)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.object_type.value,
            "name": self.name,
            "source": self.source,
            "version": self.version,
            "attributes": self.attributes,
            "depends_on": self.depends_on,
            "count": self.count,
            "for_each": self.for_each,
            "providers": self.providers,
            "source_location": str(self.source_location),
        }


@dataclass
class TerraformMoved(BaseTerraformObject):
    """Represents a Terraform moved configuration block."""

    from_address: Optional[str] = None
    to_address: Optional[str] = None

    def __post_init__(self):
        self.object_type = TerraformObjectType.MOVED
        self.name = ""

    def validate(self) -> bool:
        """Validate moved block has required fields."""
        return bool(self.from_address and self.to_address)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.object_type.value,
            "from": self.from_address,
            "to": self.to_address,
            "attributes": self.attributes,
            "source_location": str(self.source_location),
        }


@dataclass
class TerraformCatalog:
    """
    Represents the complete parsed structure of a Terraform configuration
    (a root module or child module), providing powerful lookup methods.
    """

    root_path: Path
    resources: List[Any] = field(default_factory=list)
    data_sources: List[Any] = field(default_factory=list)
    variables: List[Any] = field(default_factory=list)
    outputs: List[Any] = field(default_factory=list)
    locals: List[Any] = field(default_factory=list)
    providers: List[Any] = field(default_factory=list)
    terraform_blocks: List[Any] = field(default_factory=list)
    modules: List[Any] = field(default_factory=list)
    moved_blocks: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Internal map for quick lookup: {address: BaseTerraformObject}
    # Using the full address (e.g., 'resource.aws_s3_bucket.main') as the key is the most robust approach.
    _address_map: Dict[str, "BaseTerraformObject"] = field(default_factory=dict)

    # Map to hold block classes for filtering (requires explicit import/definition)
    _type_to_list_map: Dict[TerraformObjectType, str] = field(
        init=False, default_factory=dict
    )

    def __post_init__(self):
        self._type_to_list_map = {
            TerraformObjectType.RESOURCE: "resources",
            TerraformObjectType.DATA_SOURCE: "data_sources",
            TerraformObjectType.VARIABLE: "variables",
            TerraformObjectType.OUTPUT: "outputs",
            TerraformObjectType.LOCAL: "locals",
            TerraformObjectType.PROVIDER: "providers",
            TerraformObjectType.TERRAFORM_BLOCK: "terraform_blocks",
            TerraformObjectType.MODULE: "modules",
            TerraformObjectType.MOVED: "moved_blocks",
        }

        # Repopulate the map if objects were passed initially
        for obj in self.get_all_objects():
            self._add_to_map(obj)

    def _generate_address_key(self, obj: "BaseTerraformObject") -> str:
        """
        Helper to create a consistent, unique key for the address map, reflecting
        the block's primary canonical address in the configuration.
        """
        obj_type_value = obj.object_type.value

        if obj_type_value == TerraformObjectType.TERRAFORM_BLOCK.value:
            return obj_type_value  # 'terraform'

        if obj_type_value in (
            TerraformObjectType.MOVED.value,
            TerraformObjectType.IMPORT.value,
            TerraformObjectType.CHECK.value,
        ):
            return f"{obj_type_value}::{str(obj.source_location)}"

        if obj_type_value == TerraformObjectType.PROVIDER.value:
            # Providers are accessed via provider.type or provider.type.alias.
            # We use the type + alias (if present) to ensure uniqueness of the block definition.
            # Assuming the TerraformProvider class has 'provider_name' and 'alias'.
            provider_type = getattr(obj, "provider_name", obj.name)  # e.g., 'aws'
            alias = getattr(obj, "alias", None)

            if alias:
                # Canonical address for aliased provider is provider.type.alias
                return f"{obj_type_value}.{provider_type}.{alias}"

            # Canonical address for non-aliased provider is provider.type
            return f"{obj_type_value}.{provider_type}"

        # Local Blocks (Handles Properties within the block)
        if obj_type_value == TerraformObjectType.LOCAL.value:
            # Here, 'obj.name' is the property name (e.g., 'vpc_id') inside the 'locals {}' block.
            return f"{obj_type_value}.{obj.name}"

        # Resource/Data Blocks (e.g., resource.aws_s3_bucket.main)
        block_type_name = getattr(obj, "resource_type", getattr(obj, "data_type", None))

        if block_type_name:
            # Structure: block_type.resource_type.name (e.g., resource.aws_s3_bucket.main)
            return f"{obj_type_value}.{block_type_name}.{obj.name}"

        # Simple Types (e.g., variable.name, output.name, module.name)
        # Structure: block_type.name (e.g., variable.region, module.vpc)
        return f"{obj_type_value}.{obj.name}"

    def _add_to_map(self, obj: "BaseTerraformObject") -> None:
        """Helper to populate the internal address map."""
        key = self._generate_address_key(obj)
        self._address_map[key] = obj

    def add_object(self, obj: "BaseTerraformObject") -> None:
        """
        Add a parsed object to the appropriate list and update the internal map.
        """
        list_name = self._type_to_list_map.get(obj.object_type)
        if list_name:
            getattr(self, list_name).append(obj)
            self._add_to_map(obj)
        else:
            # Handle unmapped types if necessary
            pass

    def get_all_objects(self) -> List["BaseTerraformObject"]:
        """Get all parsed objects as a flat list."""
        # Use the internal map to ensure consistency and avoid direct list manipulation complexity
        return list(self._address_map.values())

    # --- New/Reworked Powerful Methods ---

    def get_by_address(self, address: str) -> Optional["BaseTerraformObject"]:
        """
        Reworked to retrieve a block using a simplified/canonical address format.

        Args:
            address: The full resource or block address (e.g., 'aws_s3_bucket.main', 'variable.vpc_cidr').

        Returns:
            The matching BaseTerraformObject or None.
        """
        # This implementation requires a more complex check because user-provided addresses
        # often omit the top-level block type (resource. or data.).

        # 1. Check for full internal address key match (e.g., 'resource.aws_s3_bucket.main')
        if address in self._address_map:
            return self._address_map[address]

        # 2. Heuristic check for common short formats (e.g., 'aws_s3_bucket.main')
        parts = address.split(".")

        if len(parts) >= 2:
            name = parts[-1]
            resource_type_name = parts[-2]

            # Check Resource format: aws_s3_bucket.main (type.name)
            # Must check all possible prefixes: 'resource.aws_s3_bucket.main'
            for obj in self.resources:
                if (
                    getattr(obj, "resource_type", "") == resource_type_name
                    and obj.name == name
                ):
                    return obj

            # Check Data Source format: aws_ami.latest (type.name)
            # Must check all possible prefixes: 'data.aws_ami.latest'
            for obj in self.data_sources:
                if (
                    getattr(obj, "data_type", "") == resource_type_name
                    and obj.name == name
                ):
                    return obj

            # Check simple types: variable.name, output.name, module.name
            # The structure is blocktype.name, so we can check against all types
            for obj_list in [
                self.variables,
                self.outputs,
                self.locals,
                self.modules,
                self.providers,
            ]:
                for obj in obj_list:
                    if obj.object_type.value == resource_type_name and obj.name == name:
                        return obj

        return None

    def filter_objects(
        self,
        object_types: Optional[
            Union[
                TerraformObjectType,
                List[TerraformObjectType],
                Type["BaseTerraformObject"],
                List[Type["BaseTerraformObject"]],
            ]
        ] = None,
        condition: Optional[Callable[["BaseTerraformObject"], bool]] = None,
    ) -> List["BaseTerraformObject"]:
        """
        Retrieve a list of objects filtered by type (Enum or class) and/or a custom condition.
        """

        temp_objects = self.get_all_objects()

        # 1. Type filtering (Handles both Enum and Class types)
        if object_types:
            if not isinstance(object_types, list):
                object_types = [object_types]

            filter_enums = []

            for t in object_types:
                if isinstance(t, TerraformObjectType):
                    filter_enums.append(t)
                elif hasattr(t, "object_type") and isinstance(
                    t.object_type, TerraformObjectType
                ):
                    # Use the object_type attribute from the class itself
                    filter_enums.append(t.object_type)

            if filter_enums:
                type_values = {t.value for t in filter_enums}
                temp_objects = [
                    obj for obj in temp_objects if obj.object_type.value in type_values
                ]
            else:
                # If only block classes were passed, use isinstance() as a fallback
                temp_objects = [
                    obj
                    for obj in temp_objects
                    if any(
                        isinstance(obj, t) for t in object_types if isinstance(t, type)
                    )
                ]

        # 2. Condition filtering
        if condition:
            return [obj for obj in temp_objects if condition(obj)]
        else:
            return temp_objects

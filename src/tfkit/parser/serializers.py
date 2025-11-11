"""
Serialization module for TerraformCatalog and related objects.
"""

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class TerraformSerializer:
    """Main serializer for TerraformCatalog objects."""

    @staticmethod
    def serialize_object(obj: Any) -> Any:
        """
        Recursively serialize any Terraform object to primitive types.
        """
        if obj is None:
            return None

        # Handle basic types
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Handle Path objects
        if isinstance(obj, Path):
            return str(obj)

        # Handle Enum objects - convert to their value
        if isinstance(obj, Enum):
            return obj.value

        # Handle lists
        if isinstance(obj, (list, tuple)):
            return [TerraformSerializer.serialize_item(item) for item in obj]

        # Handle dictionaries
        if isinstance(obj, dict):
            return {
                str(k): TerraformSerializer.serialize_item(v) for k, v in obj.items()
            }

        # Handle Terraform objects with to_dict method
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            # Call to_dict and then serialize the result
            obj_dict = obj.to_dict()
            return TerraformSerializer.serialize_item(obj_dict)

        # Handle dataclasses (fallback)
        if is_dataclass(obj):
            return TerraformSerializer.serialize_dataclass(obj)

        # Handle objects with __dict__ (fallback)
        if hasattr(obj, "__dict__"):
            return TerraformSerializer.serialize_object_dict(obj)

        # Fallback: convert to string
        return str(obj)

    @staticmethod
    def serialize_item(item: Any) -> Any:
        """Alias for serialize_object for better readability."""
        return TerraformSerializer.serialize_object(item)

    @staticmethod
    def serialize_dataclass(dc_obj: Any) -> Dict[str, Any]:
        """Serialize a dataclass object."""
        result = {}

        # Use dataclass fields for proper serialization
        if is_dataclass(dc_obj):
            for field_name, field_value in asdict(dc_obj).items():
                # Skip internal fields
                if field_name.startswith("_"):
                    continue
                result[field_name] = TerraformSerializer.serialize_item(field_value)

        return result

    @staticmethod
    def serialize_object_dict(obj: Any) -> Dict[str, Any]:
        """Serialize a regular object using its __dict__."""
        result = {}

        for attr_name, attr_value in obj.__dict__.items():
            # Skip private attributes and methods
            if attr_name.startswith("_") or callable(attr_value):
                continue

            result[attr_name] = TerraformSerializer.serialize_item(attr_value)

        return result


class JSONSerializer:
    """JSON-specific serialization for Terraform objects."""

    @staticmethod
    def dump(catalog: Any, file_path: Path, indent: int = 2) -> None:
        """Serialize catalog to JSON file."""
        serialized = TerraformSerializer.serialize_object(catalog)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=indent, ensure_ascii=False, default=str)

    @staticmethod
    def dumps(catalog: Any, indent: int = 2) -> str:
        """Serialize catalog to JSON string."""
        serialized = TerraformSerializer.serialize_object(catalog)
        return json.dumps(serialized, indent=indent, ensure_ascii=False, default=str)


class YAMLSerializer:
    """YAML-specific serialization."""

    @staticmethod
    def dump(catalog: Any, file_path: Path) -> None:
        """Serialize catalog to YAML file."""
        serialized = TerraformSerializer.serialize_object(catalog)

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(
                serialized,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    @staticmethod
    def dumps(catalog: Any) -> str:
        """Serialize catalog to YAML string."""
        serialized = TerraformSerializer.serialize_object(catalog)
        return yaml.dump(
            serialized, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


def serialize_to_json(
    catalog: Any, file_path: Optional[Path] = None, indent: int = 2
) -> Optional[str]:
    """Convenience function to serialize to JSON file or string."""
    if file_path:
        JSONSerializer.dump(catalog, file_path, indent)
        return None
    else:
        return JSONSerializer.dumps(catalog, indent)


def serialize_to_yaml(catalog: Any, file_path: Optional[Path] = None) -> Optional[str]:
    """Convenience function to serialize to YAML file or string."""
    if file_path:
        YAMLSerializer.dump(catalog, file_path)
        return None
    else:
        return YAMLSerializer.dumps(catalog)

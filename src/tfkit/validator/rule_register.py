# Updated rule_register.py with flexible resource type handling
import importlib
import pkgutil
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type

from tfkit.validator.models import (
    ValidationCategory,
    ValidationIssue,
    ValidationSeverity,
)


class RuleScope(Enum):
    RESOURCE_SPECIFIC = "resource_specific"
    GENERIC = "generic"
    PROJECT_LEVEL = "project_level"


class ValidationRule(ABC):
    """Base class for all validation rules"""

    def __init__(self):
        self.rule_id: str = ""
        self.description: str = ""
        self.category: ValidationCategory = ValidationCategory.SYNTAX
        self.severity: ValidationSeverity = ValidationSeverity.ERROR
        self.suggestion: str = ""
        self.scope: RuleScope = RuleScope.GENERIC
        self.resource_types: Set[str] = set()  # Use strings for flexibility
        self.condition: Optional[Callable[[Any], bool]] = None
        self.enabled: bool = True
        self.priority: int = 0  # Higher priority rules run first

    @abstractmethod
    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        """Validate a resource and return list of issues"""
        pass

    def _create_issue(self, resource: Any, message: str = None) -> ValidationIssue:
        """Helper method to create validation issues"""
        if message is None:
            message = self.description

        resource_name = "unknown"
        if hasattr(resource, "attributes") and resource.attributes:
            resource_name = resource.attributes.get("name", "unknown")
        elif hasattr(resource, "name"):
            resource_name = resource.name

        # Get file path and line number safely
        file_path = getattr(resource, "file_path", "unknown")
        line_number = getattr(resource, "line_number", 1)
        resource_type = getattr(resource, "type", "unknown")

        return ValidationIssue(
            severity=self.severity,
            category=self.category,
            rule_id=self.rule_id,
            message=message,
            file_path=file_path,
            line_number=line_number,
            resource_name=resource_name,
            resource_type=resource_type,
            suggestion=self.suggestion,
        )

    def applies_to(self, resource_type: str) -> bool:
        """Check if this rule applies to the given resource type"""
        if not self.enabled:
            return False

        if self.scope == RuleScope.GENERIC:
            return True
        if self.scope == RuleScope.PROJECT_LEVEL:
            return False

        return resource_type in self.resource_types

    def __lt__(self, other):
        """Allow sorting by priority"""
        return self.priority > other.priority  # Higher priority first


class RuleRegistry:
    """Optimized central registry for validation rules with caching"""

    def __init__(self):
        self._rules: Dict[str, ValidationRule] = {}
        self._rules_by_category: Dict[ValidationCategory, List[ValidationRule]] = (
            defaultdict(list)
        )
        self._rules_by_resource: Dict[str, List[ValidationRule]] = defaultdict(list)
        self._generic_rules: List[ValidationRule] = []
        self._project_rules: List[ValidationRule] = []

        # Cache for frequently accessed rule combinations
        self._cache: Dict[tuple, List[ValidationRule]] = {}
        self._cache_enabled: bool = True

    def register(self, rule: ValidationRule) -> None:
        """Register a validation rule with optimized indexing"""
        if rule.rule_id in self._rules:
            raise ValueError(f"Rule {rule.rule_id} already registered")

        self._rules[rule.rule_id] = rule
        self._rules_by_category[rule.category].append(rule)

        # Index by scope for fast retrieval
        if rule.scope == RuleScope.GENERIC:
            self._generic_rules.append(rule)
        elif rule.scope == RuleScope.PROJECT_LEVEL:
            self._project_rules.append(rule)
        elif rule.scope == RuleScope.RESOURCE_SPECIFIC:
            for resource_type in rule.resource_types:
                self._rules_by_resource[resource_type].append(rule)

        # Clear cache when new rule is added
        self._cache.clear()

        # Sort rules by priority
        self._sort_rules()

    def _sort_rules(self):
        """Sort all rule lists by priority"""
        for rules in self._rules_by_category.values():
            rules.sort()
        for rules in self._rules_by_resource.values():
            rules.sort()
        self._generic_rules.sort()
        self._project_rules.sort()

    def unregister(self, rule_id: str) -> bool:
        """Unregister a rule"""
        if rule_id not in self._rules:
            return False

        rule = self._rules.pop(rule_id)

        if rule.category in self._rules_by_category:
            self._rules_by_category[rule.category].remove(rule)

        # Remove from scope-specific indexes
        if rule.scope == RuleScope.GENERIC:
            self._generic_rules.remove(rule)
        elif rule.scope == RuleScope.PROJECT_LEVEL:
            self._project_rules.remove(rule)
        elif rule.scope == RuleScope.RESOURCE_SPECIFIC:
            for resource_type in rule.resource_types:
                self._rules_by_resource[resource_type].remove(rule)

        self._cache.clear()
        return True

    def get_rules_for_resource(
        self, resource_type: str, category: Optional[ValidationCategory] = None
    ) -> List[ValidationRule]:
        """Get all applicable rules for a resource type with caching"""

        # Check cache first
        cache_key = (resource_type, category)
        if self._cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        rules = []

        for rule in self._generic_rules:
            if rule.enabled and (category is None or rule.category == category):
                rules.append(rule)

        if resource_type in self._rules_by_resource:
            for rule in self._rules_by_resource[resource_type]:
                if rule.enabled and (category is None or rule.category == category):
                    rules.append(rule)

        # Cache the result
        if self._cache_enabled:
            self._cache[cache_key] = rules

        return rules

    def get_project_rules(
        self, category: Optional[ValidationCategory] = None
    ) -> List[ValidationRule]:
        """Get all project-level rules"""
        if category is None:
            return [r for r in self._project_rules if r.enabled]
        return [r for r in self._project_rules if r.enabled and r.category == category]

    def get_rules_by_category(
        self, category: ValidationCategory
    ) -> List[ValidationRule]:
        """Get all enabled rules for a specific category"""
        return [r for r in self._rules_by_category[category] if r.enabled]

    def get_all_rules(self) -> List[ValidationRule]:
        """Get all registered rules"""
        return list(self._rules.values())

    def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        """Get a specific rule by ID"""
        return self._rules.get(rule_id)

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a specific rule"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            self._cache.clear()
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a specific rule"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            self._cache.clear()
            return True
        return False

    def clear_cache(self):
        """Clear the rule cache"""
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "total_rules": len(self._rules),
            "enabled_rules": sum(1 for r in self._rules.values() if r.enabled),
            "generic_rules": len(self._generic_rules),
            "project_rules": len(self._project_rules),
            "resource_specific_rules": len(self._rules)
            - len(self._generic_rules)
            - len(self._project_rules),
            "cache_size": len(self._cache),
            "categories": {
                cat.value: len(rules) for cat, rules in self._rules_by_category.items()
            },
        }


rule_registry = RuleRegistry()


def register_rule(rule_class: Type[ValidationRule]) -> Type[ValidationRule]:
    instance = rule_class()
    rule_registry.register(instance)
    return rule_class


class RuleLoader:
    """Automatic rule discovery and loading"""

    @staticmethod
    def load_rules_from_package(package_name: str) -> int:
        """
        Automatically discover and load all rules from a package

        Args:
            package_name: Name of the package containing rule modules

        Returns:
            Number of rules loaded
        """
        initial_count = len(rule_registry.get_all_rules())

        try:
            package = importlib.import_module(package_name)
            package_path = Path(package.__file__).parent

            # Discover all Python modules in the package
            for _, module_name, is_pkg in pkgutil.iter_modules([str(package_path)]):
                if not is_pkg and not module_name.startswith("_"):
                    full_module_name = f"{package_name}.{module_name}"
                    try:
                        importlib.import_module(full_module_name)
                    except Exception as e:
                        print(f"Warning: Failed to load module {full_module_name}: {e}")

        except Exception as e:
            print(f"Error loading rules from package {package_name}: {e}")

        final_count = len(rule_registry.get_all_rules())
        return final_count - initial_count

    @staticmethod
    def load_rules_from_directory(directory: Path) -> int:
        """
        Load all rule files from a directory

        Args:
            directory: Path to directory containing rule files

        Returns:
            Number of rules loaded
        """
        initial_count = len(rule_registry.get_all_rules())

        if not directory.exists():
            print(f"Warning: Directory {directory} does not exist")
            return 0

        for file_path in directory.glob("**/*.py"):
            if file_path.name.startswith("_"):
                continue

            try:
                relative_path = file_path.relative_to(directory.parent)
                module_name = str(relative_path.with_suffix("")).replace("/", ".")
                importlib.import_module(module_name)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

        final_count = len(rule_registry.get_all_rules())
        return final_count - initial_count

    @staticmethod
    def load_rule_class(rule_class: Type[ValidationRule]) -> bool:
        """
        Manually load a specific rule class

        Args:
            rule_class: The rule class to instantiate and register

        Returns:
            True if successful, False otherwise
        """
        try:
            instance = rule_class()
            rule_registry.register(instance)
            return True
        except Exception as e:
            print(f"Error loading rule class {rule_class.__name__}: {e}")
            return False

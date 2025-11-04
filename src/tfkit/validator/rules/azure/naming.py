import re
from typing import Any, List

from tfkit.validator.models import (
    ValidationCategory,
    ValidationIssue,
    ValidationSeverity,
)
from tfkit.validator.rule_register import (
    RuleScope,
    ValidationRule,
    register_rule,
)


# === GENERIC NAMING RULES ===
@register_rule
class AzureNamingLengthRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-NAMING-001"
        self.description = "Resource names should follow Azure length constraints"
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Ensure resource name length is within Azure limits"
        self.scope = RuleScope.GENERIC
        self.resource_types = set()

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        name = resource.attributes.get("name", "")
        resource_type = resource.type

        # Define max lengths for common Azure resources
        max_lengths = {
            "azurerm_storage_account": 24,
            "azurerm_virtual_machine": 15,
            "azurerm_resource_group": 90,
            "azurerm_virtual_network": 64,
            "azurerm_subnet": 80,
            "azurerm_network_interface": 80,
            "azurerm_public_ip": 80,
            "azurerm_network_security_group": 80,
            "azurerm_key_vault": 24,
            "azurerm_sql_server": 63,
            "azurerm_sql_database": 128,
            "azurerm_app_service": 60,
            "azurerm_app_service_plan": 40,
            "azurerm_container_registry": 50,
            "azurerm_kubernetes_cluster": 63,
        }

        max_length = max_lengths.get(resource_type, 64)  # Default to 64
        if len(name) > max_length:
            return [
                self._create_issue(
                    resource,
                    f"Name '{name}' exceeds maximum length of {max_length} characters",
                )
            ]
        return []


@register_rule
class AzureNamingCharactersRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-NAMING-002"
        self.description = "Azure resource names should use only allowed characters"
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.ERROR
        self.suggestion = (
            "Use only alphanumeric characters, hyphens, and underscores where allowed"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {
            "azurerm_virtual_machine",
            "azurerm_storage_account",
            "azurerm_resource_group",
            "azurerm_virtual_network",
            "azurerm_subnet",
            "azurerm_network_interface",
            "azurerm_network_security_group",
            "azurerm_public_ip",
            "azurerm_sql_server",
            "azurerm_sql_database",
            "azurerm_key_vault",
            "azurerm_app_service",
            "azurerm_app_service_plan",
            "azurerm_container_registry",
            "azurerm_kubernetes_cluster",
        }

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # Safely get the resource name
        name = ""
        try:
            if hasattr(resource, "attributes") and resource.attributes:
                name = resource.attributes.get("name", "")
            elif hasattr(resource, "name"):
                name = resource.name
        except Exception:
            return []  # Skip if we can't get the name

        # Skip empty names or interpolated names
        if not name or "${" in str(name):
            return []

        resource_type = getattr(resource, "type", "unknown")

        # Define character patterns for different Azure resource types
        patterns = {
            "azurerm_storage_account": r"^[a-z0-9]+$",
            "default": r"^[a-zA-Z0-9-_]+$",
        }

        pattern = patterns.get(resource_type, patterns["default"])
        if not re.match(pattern, str(name)):
            return [
                self._create_issue(
                    resource,
                    f"Name '{name}' contains invalid characters for {resource_type}",
                )
            ]
        return []


@register_rule
class AzureNamingStartEndRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-NAMING-003"
        self.description = "Resource names should not start or end with hyphens"
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Remove leading and trailing hyphens from resource names"
        self.scope = RuleScope.GENERIC
        self.resource_types = set()

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        name = resource.attributes.get("name", "")

        if name.startswith("-") or name.endswith("-"):
            return [
                self._create_issue(
                    resource, f"Name '{name}' should not start or end with hyphens"
                )
            ]
        return []


@register_rule
class AzureNamingConsecutiveHyphensRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-NAMING-004"
        self.description = "Resource names should not contain consecutive hyphens"
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Remove consecutive hyphens from resource names"
        self.scope = RuleScope.GENERIC
        self.resource_types = set()

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        name = resource.attributes.get("name", "")

        if "--" in name:
            return [
                self._create_issue(
                    resource, f"Name '{name}' contains consecutive hyphens"
                )
            ]
        return []


# === STORAGE ACCOUNT NAMING RULES ===
@register_rule
class AzureStorageAccountNamingRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-NAMING-101"
        self.description = (
            "Storage account names must be 3-24 chars, lowercase alphanumeric"
        )
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Use 3-24 lowercase letters and numbers only"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_storage_account"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        name = resource.attributes.get("name", "")
        issues = []

        if len(name) < 3 or len(name) > 24:
            issues.append(
                self._create_issue(
                    resource,
                    f"Storage account name must be 3-24 characters, got {len(name)}",
                )
            )

        if not re.match(r"^[a-z0-9]+$", name):
            issues.append(
                self._create_issue(
                    resource,
                    "Storage account name must contain only lowercase letters and numbers",
                )
            )

        return issues


@register_rule
class AzureStorageAccountGlobalUniquenessRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-NAMING-102"
        self.description = "Storage account names must be globally unique"
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Include unique identifiers in storage account names"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_storage_account"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        name = resource.attributes.get("name", "")

        # Check for common generic names that likely conflict
        generic_names = ["storage", "mystorage", "account", "sa", "storageaccount"]
        if name.lower() in generic_names:
            return [
                self._create_issue(
                    resource,
                    "Storage account name is too generic and likely not globally unique",
                )
            ]

        return []


# === VIRTUAL MACHINE NAMING RULES ===
@register_rule
class AzureVMNamingLengthRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-NAMING-201"
        self.description = (
            "VM names must be 1-15 characters for Windows, 1-64 for Linux"
        )
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Keep VM names under 15 characters for compatibility"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_virtual_machine"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        name = resource.attributes.get("name", "")

        if len(name) > 15:
            return [
                self._create_issue(
                    resource,
                    "VM name should be 15 characters or less for Windows compatibility",
                )
            ]
        return []


@register_rule
class AzureVMNamingConventionRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-NAMING-202"
        self.description = "VM names should follow naming convention"
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Use convention: {env}-{location}-{role}-{instance} or similar"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_virtual_machine"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        name = resource.attributes.get("name", "")

        # Check for basic structure (at least 2 segments separated by hyphens)
        if "-" not in name or len(name.split("-")) < 2:
            return [
                self._create_issue(
                    resource,
                    "VM name should follow structured naming convention with hyphens",
                )
            ]
        return []


# === NETWORK RESOURCE NAMING RULES ===
@register_rule
class AzureVNetNamingRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-NAMING-301"
        self.description = (
            "Virtual Network names should indicate purpose and environment"
        )
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Use format: vnet-{env}-{region}-{purpose}"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_virtual_network"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        name = resource.attributes.get("name", "")

        if not name.startswith("vnet-"):
            return [
                self._create_issue(
                    resource, "Virtual Network name should start with 'vnet-' prefix"
                )
            ]
        return []

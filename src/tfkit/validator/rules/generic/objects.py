"""Terraform Configuration Rules"""

import re
from typing import Any, Dict, List

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


# === TERRAFORM BLOCK RULES ===
@register_rule
class TerraformRequiredVersionRule(ValidationRule):
    """Terraform block should specify required_version"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-CONFIG-001"
        self.description = "Terraform block should specify required_version"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Add required_version constraint to terraform block"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"terraform"}
        self.priority = 20

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        required_version = resource.attributes.get("required_version")
        if not required_version:
            return [self._create_issue(resource)]
        return []


@register_rule
class TerraformBackendRule(ValidationRule):
    """Terraform should have backend configuration"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-CONFIG-002"
        self.description = (
            "Terraform should have backend configuration for state management"
        )
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Configure backend (s3, azurerm, gcs) for remote state storage"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"terraform"}
        self.priority = 15

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        backend = resource.attributes.get("backend")
        if not backend:
            return [self._create_issue(resource)]
        return []


@register_rule
class TerraformProviderRequirementsRule(ValidationRule):
    """Terraform should have provider requirements configuration"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-CONFIG-003"
        self.description = "Terraform should use required_providers block"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Use required_providers block to explicitly declare provider versions"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"terraform"}
        self.priority = 10

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        required_providers = resource.attributes.get("required_providers")
        if not required_providers:
            return [self._create_issue(resource)]
        return []


# === PROVIDER RULES ===
@register_rule
class ProviderVersionConstraintRule(ValidationRule):
    """Providers should have version constraints"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-PROVIDER-001"
        self.description = "Providers should have version constraints"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Add version constraint to provider configuration"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"provider"}
        self.priority = 20

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # Skip if version is set in required_providers
        if hasattr(resource, "alias") or "alias" in getattr(resource, "attributes", {}):
            return []

        version = resource.attributes.get("version")
        if not version:
            return [self._create_issue(resource)]
        return []


@register_rule
class ProviderConfigurationRule(ValidationRule):
    """Providers should have proper configuration"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-PROVIDER-002"
        self.description = "Cloud providers should have region/zone configuration"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = (
            "Set region for AWS, location for Azure, or region/zone for GCP"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"provider"}
        self.priority = 15

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        provider_name = getattr(resource, "name", "")

        # Check for region configuration based on provider
        attributes = resource.attributes or {}

        if provider_name == "aws" and not attributes.get("region"):
            return [
                self._create_issue(
                    resource, "AWS provider missing region configuration"
                )
            ]
        elif provider_name == "azurerm" and not attributes.get("features"):
            return [
                self._create_issue(resource, "Azure provider missing features block")
            ]
        elif (
            provider_name == "google"
            and not attributes.get("region")
            and not attributes.get("zone")
        ):
            return [
                self._create_issue(
                    resource, "Google provider missing region/zone configuration"
                )
            ]

        return []


# === VARIABLE RULES ===
@register_rule
class VariableDescriptionRule(ValidationRule):
    """Variables should have descriptions"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-VARIABLE-001"
        self.description = "Variables should have descriptions"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Add description to all variables"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"variable"}
        self.priority = 10

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        description = resource.attributes.get("description")
        if not description:
            return [self._create_issue(resource)]
        return []


@register_rule
class VariableTypeConstraintRule(ValidationRule):
    """Variables should have type constraints"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-VARIABLE-002"
        self.description = "Variables should have type constraints"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Add type constraint to variables (string, number, bool, list, map, etc.)"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"variable"}
        self.priority = 15

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        type_constraint = resource.attributes.get("type")
        if not type_constraint:
            return [self._create_issue(resource)]
        return []


@register_rule
class VariableDefaultValueRule(ValidationRule):
    """Variables should have default values when appropriate"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-VARIABLE-003"
        self.description = "Optional variables should have default values"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Add default values for optional variables"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"variable"}
        self.priority = 5

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # Check if variable is optional (no default but not required)
        default = resource.attributes.get("default")
        nullable = resource.attributes.get("nullable", True)

        if default is None and nullable:
            variable_name = getattr(resource, "name", "unknown")
            # Skip common required variables that shouldn't have defaults
            required_vars = {
                "access_key",
                "secret_key",
                "token",
                "password",
                "private_key",
            }
            if variable_name not in required_vars:
                return [
                    self._create_issue(
                        resource,
                        f"Variable '{variable_name}' might benefit from a default value",
                    )
                ]
        return []


@register_rule
class VariableNamingConventionRule(ValidationRule):
    """Variables should follow naming conventions"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-VARIABLE-004"
        self.description = "Variables should follow snake_case naming convention"
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Use snake_case for variable names (e.g., 'instance_count' not 'instanceCount')"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"variable"}
        self.priority = 10

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        variable_name = getattr(resource, "name", "")

        # Check for snake_case convention
        if variable_name and not re.match(r"^[a-z][a-z0-9_]*[a-z0-9]?$", variable_name):
            return [
                self._create_issue(
                    resource, f"Variable name '{variable_name}' should use snake_case"
                )
            ]

        # Check for uppercase letters (indicating camelCase)
        if variable_name and any(c.isupper() for c in variable_name):
            return [
                self._create_issue(
                    resource,
                    f"Variable name '{variable_name}' should use snake_case, not camelCase",
                )
            ]

        return []


# === OUTPUT RULES ===
@register_rule
class OutputDescriptionRule(ValidationRule):
    """Outputs should have descriptions"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-OUTPUT-001"
        self.description = "Outputs should have descriptions"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Add description to all outputs"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"output"}
        self.priority = 10

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        description = resource.attributes.get("description")
        if not description:
            return [self._create_issue(resource)]
        return []


@register_rule
class OutputSensitiveRule(ValidationRule):
    """Outputs containing sensitive data should be marked sensitive"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-OUTPUT-002"
        self.description = "Outputs with sensitive data should be marked sensitive"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Mark outputs containing passwords, keys, or tokens as sensitive"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"output"}
        self.priority = 20

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        output_name = getattr(resource, "name", "").lower()
        sensitive = resource.attributes.get("sensitive", False)

        # Check for common sensitive output names
        sensitive_keywords = {
            "password",
            "secret",
            "key",
            "token",
            "credential",
            "private",
            "certificate",
            "ssh_key",
            "pem",
            "jwt",
            "api_key",
        }

        has_sensitive_keyword = any(
            keyword in output_name for keyword in sensitive_keywords
        )
        if has_sensitive_keyword and not sensitive:
            return [
                self._create_issue(
                    resource,
                    f"Output '{output_name}' might contain sensitive data and should be marked sensitive",
                )
            ]

        return []


# === LOCAL RULES ===
@register_rule
class LocalValueComplexityRule(ValidationRule):
    """Local values should not be overly complex"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-LOCAL-001"
        self.description = "Local values should not contain overly complex expressions"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Consider breaking complex local expressions into multiple locals or variables"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"local"}
        self.priority = 5

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # This would require parsing the expression complexity
        # For now, we'll check for very long expressions
        expression = str(resource.attributes.get("expression", ""))

        # Count interpolations as a proxy for complexity
        interpolation_count = expression.count("${")
        if interpolation_count > 5:
            return [
                self._create_issue(
                    resource,
                    f"Local value has {interpolation_count} interpolations - consider simplifying",
                )
            ]

        return []


@register_rule
class LocalNamingConventionRule(ValidationRule):
    """Local values should follow naming conventions"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-LOCAL-002"
        self.description = "Local values should follow snake_case naming convention"
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Use snake_case for local value names"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"local"}
        self.priority = 10

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        local_name = getattr(resource, "name", "")

        if local_name and not re.match(r"^[a-z][a-z0-9_]*[a-z0-9]?$", local_name):
            return [
                self._create_issue(
                    resource, f"Local name '{local_name}' should use snake_case"
                )
            ]

        return []


# === MODULE RULES ===
@register_rule
class ModuleSourceRule(ValidationRule):
    """Modules should use versioned sources"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-MODULE-001"
        self.description = "Modules should use versioned sources"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Use version constraints in module sources (git tags, version pins)"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"module"}
        self.priority = 25

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        source = resource.attributes.get("source", "")
        version = resource.attributes.get("version")

        # Check for common source types that should be versioned
        if source and not version:
            if (
                source.startswith(("git::", "github.com", "bitbucket.org", "git@"))
                and "?ref=" not in source
            ):
                return [
                    self._create_issue(
                        resource, f"Module source '{source}' should specify a version"
                    )
                ]

        return []


@register_rule
class ModuleNamingConventionRule(ValidationRule):
    """Modules should follow naming conventions"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-MODULE-002"
        self.description = "Module calls should follow naming conventions"
        self.category = ValidationCategory.NAMING
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Use descriptive names for module calls"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"module"}
        self.priority = 10

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        module_name = getattr(resource, "name", "")

        # Check for overly generic module names
        generic_names = {"module", "main", "test", "example", "default"}
        if module_name in generic_names:
            return [
                self._create_issue(
                    resource, f"Module name '{module_name}' is too generic"
                )
            ]

        # Check for snake_case
        if module_name and not re.match(r"^[a-z][a-z0-9_]*[a-z0-9]?$", module_name):
            return [
                self._create_issue(
                    resource, f"Module name '{module_name}' should use snake_case"
                )
            ]

        return []


# === DATA SOURCE RULES ===
@register_rule
class DataSourceFilterRule(ValidationRule):
    """Data sources should use proper filters"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-DATA-001"
        self.description = "Data sources should use specific filters"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Use specific filters in data sources to avoid ambiguous results"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"data"}
        self.priority = 15

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # Check for data sources that typically require filters
        resource_type = getattr(resource, "type", "")

        if resource_type in {
            "aws_ami",
            "aws_instance",
            "azurerm_resource_group",
            "google_compute_image",
        }:
            # These data sources should have specific filters
            filters = resource.attributes.get("filter")
            if not filters:
                return [
                    self._create_issue(
                        resource, f"Data source {resource_type} should use filters"
                    )
                ]

        return []


# === GENERAL TERRAFORM RULES ===
@register_rule
class TerraformFileStructureRule(ValidationRule):
    """Terraform files should follow standard structure"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-STRUCTURE-001"
        self.description = (
            "Terraform configuration should follow standard file structure"
        )
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Follow standard Terraform file structure: main.tf, variables.tf, outputs.tf, terraform.tfvars"
        self.scope = RuleScope.PROJECT_LEVEL
        self.priority = 5

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        issues = []

        # Check for common file structure patterns
        if hasattr(project, "file_paths"):
            file_paths = project.file_paths
            has_main_tf = any("main.tf" in path for path in file_paths)
            has_variables_tf = any("variables.tf" in path for path in file_paths)
            has_outputs_tf = any("outputs.tf" in path for path in file_paths)

            if not has_main_tf:
                issues.append(self._create_issue(resource, "Missing main.tf file"))
            if not has_variables_tf:
                issues.append(self._create_issue(resource, "Missing variables.tf file"))
            if not has_outputs_tf:
                issues.append(self._create_issue(resource, "Missing outputs.tf file"))

        return issues


@register_rule
class TerraformStateRule(ValidationRule):
    """Terraform state should not be committed"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-STATE-001"
        self.description = (
            "Terraform state files should not be committed to version control"
        )
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Add .tfstate and .tfstate.backup to .gitignore"
        self.scope = RuleScope.PROJECT_LEVEL
        self.priority = 30

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # This would typically check for .gitignore or similar
        # For now, this is a placeholder for state file validation
        return []


@register_rule
class TerraformDocumentationRule(ValidationRule):
    """Terraform configurations should have documentation"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-DOCS-001"
        self.description = (
            "Terraform configurations should include README and documentation"
        )
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Add README.md describing the infrastructure and how to use the Terraform code"
        self.scope = RuleScope.PROJECT_LEVEL
        self.priority = 5

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        issues = []

        # Check for README file
        if hasattr(project, "file_paths"):
            file_paths = project.file_paths
            has_readme = any("README" in path for path in file_paths)

            if not has_readme:
                issues.append(
                    self._create_issue(resource, "Missing README documentation")
                )

        return issues


# === CODE QUALITY RULES ===
@register_rule
class TerraformFormatRule(ValidationRule):
    """Terraform code should be properly formatted"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-QUALITY-001"
        self.description = "Terraform code should be formatted with terraform fmt"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Run 'terraform fmt' to format the code consistently"
        self.scope = RuleScope.PROJECT_LEVEL
        self.priority = 10

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # This would typically check formatting with terraform fmt
        # For now, this is a placeholder for formatting validation
        return []


@register_rule
class TerraformValidationRule(ValidationRule):
    """Terraform configuration should pass terraform validate"""

    def __init__(self):
        super().__init__()
        self.rule_id = "TF-QUALITY-002"
        self.description = "Terraform configuration should pass validation"
        self.category = ValidationCategory.SYNTAX
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Run 'terraform validate' to check for syntax errors"
        self.scope = RuleScope.PROJECT_LEVEL
        self.priority = 40

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # This would typically run terraform validate
        # For now, this is a placeholder for syntax validation
        return []

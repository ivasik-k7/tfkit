import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from tfkit.validator.models import (
    ValidationCategory,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)
from tfkit.validator.rule_register import RuleLoader, rule_registry


@dataclass
class ValidatorConfig:
    """Configuration for the validator"""

    strict: bool = False
    ignore_rules: Set[str] = field(default_factory=set)
    parallel: bool = True
    max_workers: int = 4
    enable_caching: bool = True
    fail_fast: bool = False
    timeout_per_rule: Optional[float] = None
    auto_load_rules: bool = True
    rules_package: str = "tfkit.validator.rules"
    # New: Filter which resource types to validate
    validate_cloud_resources_only: bool = True
    skip_interpolated_names: bool = True


class TerraformValidator:
    """
    Enhanced validator with cloud resource filtering and safe validation
    """

    def __init__(self, config: Optional[ValidatorConfig] = None):
        self.config = config or ValidatorConfig()
        self.rule_registry = rule_registry
        self._initialized = False
        self._stats: Dict[str, Any] = {}

    def initialize(self) -> None:
        """Initialize the validator by loading rules"""
        if self._initialized:
            return

        if self.config.auto_load_rules:
            loaded = RuleLoader.load_rules_from_package(self.config.rules_package)
            print(f"Loaded {loaded} validation rules")

        self._initialized = True

    def validate(
        self,
        project,
        check_categories: Optional[Set[ValidationCategory]] = None,
        specific_resources: Optional[Set[str]] = None,
    ) -> ValidationResult:
        """
        Validate Terraform project using registered rules with cloud resource filtering
        """
        self.initialize()

        start_time = time.time()
        result = ValidationResult()

        if check_categories is None:
            check_categories = set(ValidationCategory)

        # Collect only cloud resources to validate
        resources_to_validate = self._collect_cloud_resources(
            project, specific_resources
        )

        if self.config.parallel and len(resources_to_validate) > 1:
            self._validate_parallel(
                resources_to_validate, project, check_categories, result
            )
        else:
            self._validate_sequential(
                resources_to_validate, project, check_categories, result
            )

        if self.config.fail_fast and result.errors:
            return result

        self._validate_project_level(project, check_categories, result)

        self._stats = {
            "duration": time.time() - start_time,
            "resources_validated": len(resources_to_validate),
            "rules_executed": self._stats.get("rules_executed", 0),
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "info": len(result.info),
        }

        return result

    def _collect_cloud_resources(
        self, project, specific_resources: Optional[Set[str]]
    ) -> List[Any]:
        """Collect only cloud resources that need validation"""
        resources = []

        # Only check actual resources, not Terraform constructs
        if hasattr(project, "resources"):
            for resource in project.resources.values():
                if self._should_validate_resource(resource, specific_resources):
                    resources.append(resource)

        return resources

    def _should_validate_resource(
        self, resource: Any, specific_resources: Optional[Set[str]]
    ) -> bool:
        """Determine if a resource should be validated"""
        resource_type = getattr(
            resource, "type", getattr(resource, "resource_type", "")
        )

        # Skip if specific resources are specified and this isn't one of them
        if specific_resources and resource_type not in specific_resources:
            return False

        # Skip Terraform constructs if we're only validating cloud resources
        if self.config.validate_cloud_resources_only:
            terraform_constructs = {
                "variable",
                "output",
                "local",
                "provider",
                "module",
                "terraform",
                "data",
            }
            if any(
                resource_type.value.startswith(construct)
                for construct in terraform_constructs
            ):
                return False

        # Skip resources with interpolated names if configured
        if self.config.skip_interpolated_names:
            resource_name = self._get_resource_name(resource)
            if resource_name and ("${" in resource_name or "}" in resource_name):
                return False

        return True

    def _get_resource_name(self, resource: Any) -> str:
        """Safely get resource name"""
        try:
            if hasattr(resource, "attributes") and resource.attributes:
                return resource.attributes.get("name", "")
            elif hasattr(resource, "name"):
                return resource.name
            return ""
        except Exception:
            return ""

    def _validate_sequential(
        self,
        resources: List[Any],
        project: Any,
        check_categories: Set[ValidationCategory],
        result: ValidationResult,
    ) -> None:
        """Validate resources sequentially"""
        for resource in resources:
            if self.config.fail_fast and result.errors:
                break
            self._validate_resource_safely(resource, project, check_categories, result)

    def _validate_parallel(
        self,
        resources: List[Any],
        project: Any,
        check_categories: Set[ValidationCategory],
        result: ValidationResult,
    ) -> None:
        """Validate resources in parallel"""
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_resource = {
                executor.submit(
                    self._validate_resource_safe, resource, project, check_categories
                ): resource
                for resource in resources
            }

            for future in as_completed(future_to_resource):
                if self.config.fail_fast and result.errors:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                try:
                    issues = future.result(timeout=self.config.timeout_per_rule)
                    self._process_issues(issues, result)
                except Exception as e:
                    resource = future_to_resource[future]
                    error_issue = self._create_error_issue(
                        f"Parallel validation failed: {str(e)}", resource
                    )
                    result.errors.append(error_issue)

    def _validate_resource_safe(
        self, resource: Any, project: Any, check_categories: Set[ValidationCategory]
    ) -> List[ValidationIssue]:
        """Thread-safe resource validation with error handling"""
        issues = []
        resource_type = getattr(
            resource, "type", getattr(resource, "resource_type", "unknown")
        )

        # Skip if resource type indicates it's not a cloud resource
        if self._is_terraform_construct(resource_type):
            return issues

        for category in check_categories:
            rules = self.rule_registry.get_rules_for_resource(resource_type, category)

            for rule in rules:
                if rule.rule_id in self.config.ignore_rules:
                    continue

                if not self._should_apply_rule(rule, resource_type):
                    continue

                try:
                    rule_issues = rule.validate(resource, project)
                    issues.extend(rule_issues)
                    self._stats["rules_executed"] = (
                        self._stats.get("rules_executed", 0) + 1
                    )

                except Exception as e:
                    error_issue = self._create_error_issue(
                        f"Rule {rule.rule_id} failed: {str(e)}", resource
                    )
                    issues.append(error_issue)

        return issues

    def _validate_resource_safely(
        self,
        resource: Any,
        project: Any,
        check_categories: Set[ValidationCategory],
        result: ValidationResult,
    ) -> None:
        """Safely validate a single resource"""
        issues = self._validate_resource_safe(resource, project, check_categories)
        self._process_issues(issues, result)

    def _is_terraform_construct(self, resource_type: str) -> bool:
        """Check if resource type is a Terraform construct rather than cloud resource"""
        constructs = {
            "variable",
            "output",
            "local",
            "provider",
            "module",
            "terraform",
            "data",
        }
        return any(
            resource_type.value.startswith(construct) for construct in constructs
        )

    def _should_apply_rule(self, rule: Any, resource_type: str) -> bool:
        """Determine if a rule should be applied to a resource type"""
        # Skip Azure rules for AWS/GCP resources and vice versa
        if rule.rule_id.startswith("AZURE-") and not resource_type.value.startswith(
            "azurerm_"
        ):
            return False
        if rule.rule_id.startswith("AWS-") and not resource_type.startswith("aws_"):
            return False
        if rule.rule_id.startswith("GCP-") and not resource_type.startswith("google_"):
            return False

        return True

    def _validate_project_level(
        self,
        project: Any,
        check_categories: Set[ValidationCategory],
        result: ValidationResult,
    ) -> None:
        """Run project-level validation rules"""
        for category in check_categories:
            project_rules = self.rule_registry.get_project_rules(category)

            for rule in project_rules:
                if rule.rule_id in self.config.ignore_rules:
                    continue

                try:
                    issues = rule.validate(None, project)
                    self._process_issues(issues, result)
                    self._stats["rules_executed"] = (
                        self._stats.get("rules_executed", 0) + 1
                    )

                except Exception as e:
                    error_issue = ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SYNTAX,
                        rule_id="VALIDATOR-ERROR",
                        message=f"Project rule {rule.rule_id} failed: {str(e)}",
                        file_path="project",
                        line_number=1,
                        resource_name="project",
                        resource_type="project",
                    )
                    result.errors.append(error_issue)

    def _process_issues(
        self, issues: List[ValidationIssue], result: ValidationResult
    ) -> None:
        """Process validation issues and add to result"""
        for issue in issues:
            if self.config.strict and issue.severity == ValidationSeverity.WARNING:
                issue.severity = ValidationSeverity.ERROR

            if issue.severity == ValidationSeverity.ERROR:
                result.errors.append(issue)
            elif issue.severity == ValidationSeverity.WARNING:
                result.warnings.append(issue)
            else:
                result.info.append(issue)

    def _create_error_issue(self, message: str, resource: Any) -> ValidationIssue:
        """Create an error issue for validation failures"""
        return ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.SYNTAX,
            rule_id="VALIDATOR-ERROR",
            message=message,
            file_path=getattr(resource, "file_path", "unknown"),
            line_number=getattr(resource, "line_number", 1),
            resource_name=self._get_resource_name(resource),
            resource_type=getattr(
                resource, "type", getattr(resource, "resource_type", "unknown")
            ),
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            **self._stats,
            "registry_stats": self.rule_registry.get_stats(),
        }

    def reset_cache(self) -> None:
        """Clear all caches"""
        self.rule_registry.clear_cache()

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a specific rule"""
        return self.rule_registry.enable_rule(rule_id)

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a specific rule"""
        return self.rule_registry.disable_rule(rule_id)

    def list_available_rules(self) -> List[Dict[str, Any]]:
        """List all available rules with their metadata"""
        return [
            {
                "rule_id": rule.rule_id,
                "description": rule.description,
                "category": rule.category.value,
                "severity": rule.severity.value,
                "scope": rule.scope.value,
                "enabled": rule.enabled,
                "priority": rule.priority,
            }
            for rule in self.rule_registry.get_all_rules()
        ]

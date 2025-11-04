"""AWS tagging rules"""

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


@register_rule
class RequiredTagsRule(ValidationRule):
    """Ensure required tags are present on AWS resources"""

    TAGGABLE_RESOURCES = {
        "aws_instance",
        "aws_s3_bucket",
        "aws_db_instance",
        "aws_lambda_function",
    }

    REQUIRED_TAGS = {"Environment", "Owner", "Project", "CostCenter"}

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-TAG-001"
        self.description = "AWS resources must have required tags"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = f"Add required tags: {', '.join(self.REQUIRED_TAGS)}"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = self.TAGGABLE_RESOURCES
        self.priority = 10

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        issues = []

        tags = getattr(resource, "tags", {})
        if not isinstance(tags, dict):
            tags = {}

        missing_tags = self.REQUIRED_TAGS - set(tags.keys())

        if missing_tags:
            issues.append(
                ValidationIssue(
                    severity=self.severity,
                    category=self.category,
                    rule_id=self.rule_id,
                    message=f"Missing required tags: {', '.join(sorted(missing_tags))}",
                    file_path=getattr(resource, "file_path", "unknown"),
                    line_number=getattr(resource, "line_number", 1),
                    resource_name=getattr(resource, "name", "unknown"),
                    resource_type=getattr(resource, "resource_type", "unknown"),
                    suggestion=self.suggestion,
                )
            )

        return issues

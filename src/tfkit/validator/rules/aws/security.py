"""AWS security rules"""

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
class S3BucketPublicAccessRule(ValidationRule):
    """Ensure S3 buckets block public access"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-S3-SEC-001"
        self.description = "S3 buckets should block public access"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Enable block_public_acls, block_public_policy, ignore_public_acls, restrict_public_buckets"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_s3_bucket"}
        self.priority = 20

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        issues = []

        public_access_block = getattr(
            resource, "public_access_block_configuration", None
        )

        if not public_access_block:
            issues.append(
                ValidationIssue(
                    severity=self.severity,
                    category=self.category,
                    rule_id=self.rule_id,
                    message="S3 bucket does not have public access block configuration",
                    file_path=getattr(resource, "file_path", "unknown"),
                    line_number=getattr(resource, "line_number", 1),
                    resource_name=getattr(resource, "name", "unknown"),
                    resource_type="aws_s3_bucket",
                    suggestion=self.suggestion,
                )
            )

        return issues


@register_rule
class SecurityGroupIngressRule(ValidationRule):
    """Check security group ingress rules"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-SG-SEC-001"
        self.description = "Security groups should not allow unrestricted ingress"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Restrict ingress to specific IP ranges or security groups"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_security_group"}
        self.priority = 20

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        issues = []

        ingress_rules = getattr(resource, "ingress", [])

        for idx, rule in enumerate(ingress_rules):
            cidr_blocks = rule.get("cidr_blocks", [])

            if "0.0.0.0/0" in cidr_blocks:
                issues.append(
                    ValidationIssue(
                        severity=self.severity,
                        category=self.category,
                        rule_id=self.rule_id,
                        message=f"Security group allows unrestricted ingress on port {rule.get('from_port', 'unknown')}",
                        file_path=getattr(resource, "file_path", "unknown"),
                        line_number=getattr(resource, "line_number", 1) + idx,
                        resource_name=getattr(resource, "name", "unknown"),
                        resource_type="aws_security_group",
                        suggestion=self.suggestion,
                    )
                )

        return issues

"""AWS Compute Rules"""

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


# === EC2 INSTANCE RULES ===
@register_rule
class EC2InstanceNamingConventionRule(ValidationRule):
    """EC2 instances should follow naming conventions"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-EC2-001"
        self.description = "EC2 instances should follow naming conventions"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Use naming pattern: {env}-{app}-{role}-{sequence}"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_instance"}
        self.priority = 10

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        tags = resource.attributes.get("tags", {})
        instance_name = tags.get("Name", "")

        if not instance_name:
            return [self._create_issue(resource, "EC2 instance missing Name tag")]

        # Check naming convention: at least 3 segments separated by hyphens
        name_parts = instance_name.split("-")
        if len(name_parts) < 3:
            return [
                self._create_issue(
                    resource,
                    "EC2 instance name should follow convention: env-app-role-sequence",
                )
            ]

        return []


@register_rule
class EC2InstanceTypeOptimizationRule(ValidationRule):
    """EC2 instances should use cost-effective instance types"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-EC2-002"
        self.description = "EC2 instances should use appropriate instance types"
        self.category = ValidationCategory.COST
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Consider using current generation instance types (t3, m5, c5, etc.)"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_instance"}
        self.priority = 15

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        instance_type = resource.attributes.get("instance_type", "")
        issues = []

        # Flag legacy instance types
        legacy_types = ["t1", "m1", "m2", "c1", "c3", "r3", "i2"]
        if any(instance_type.startswith(legacy) for legacy in legacy_types):
            issues.append(
                self._create_issue(
                    resource,
                    f"Instance type {instance_type} is legacy, consider upgrading",
                )
            )

        # Flag potentially over-provisioned instances for general workloads
        over_provisioned = ["m5.8xlarge", "c5.9xlarge", "r5.12xlarge", "m5.16xlarge"]
        if instance_type in over_provisioned:
            issues.append(
                self._create_issue(
                    resource, f"Instance type {instance_type} may be over-provisioned"
                )
            )

        return issues


@register_rule
class EC2InstanceEBSOptimizedRule(ValidationRule):
    """EC2 instances should be EBS-optimized when using EBS"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-EC2-003"
        self.description = (
            "EC2 instances should be EBS-optimized for better EBS performance"
        )
        self.category = ValidationCategory.PERFORMANCE
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Set ebs_optimized = true for better EBS performance"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_instance"}
        self.priority = 20

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        ebs_optimized = resource.attributes.get("ebs_optimized")

        # Check if instance has EBS volumes
        root_block_device = resource.attributes.get("root_block_device", {})
        ebs_block_devices = resource.attributes.get("ebs_block_device", [])

        has_ebs_volumes = root_block_device or ebs_block_devices

        if has_ebs_volumes and not ebs_optimized:
            return [self._create_issue(resource)]

        return []


@register_rule
class EC2InstanceDetailedMonitoringRule(ValidationRule):
    """EC2 instances should have detailed monitoring enabled"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-EC2-004"
        self.description = "EC2 instances should have detailed monitoring enabled"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Set monitoring = true for detailed CloudWatch monitoring"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_instance"}
        self.priority = 25

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        monitoring = resource.attributes.get("monitoring")
        if not monitoring:
            return [self._create_issue(resource)]
        return []


@register_rule
class EC2InstanceTenancyRule(ValidationRule):
    """EC2 instances should use appropriate tenancy"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-EC2-005"
        self.description = "EC2 instances should use shared tenancy for cost efficiency"
        self.category = ValidationCategory.COST
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Use tenancy = 'default' for shared tenancy unless dedicated required"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_instance"}
        self.priority = 15

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        tenancy = resource.attributes.get("tenancy", "default")
        if tenancy == "dedicated":
            return [
                self._create_issue(
                    resource, "Dedicated tenancy may incur additional costs"
                )
            ]
        return []


# === AUTO SCALING GROUP RULES ===
@register_rule
class ASGHealthCheckRule(ValidationRule):
    """Auto Scaling Groups should have proper health checks"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-ASG-001"
        self.description = "Auto Scaling Groups should configure proper health checks"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Set health_check_type = 'ELB' and appropriate grace period"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_autoscaling_group"}
        self.priority = 20

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        health_check_type = resource.attributes.get("health_check_type", "EC2")
        health_check_grace_period = resource.attributes.get(
            "health_check_grace_period", 300
        )

        issues = []

        if health_check_type == "EC2":
            issues.append(
                self._create_issue(
                    resource,
                    "Consider using ELB health checks for better application health monitoring",
                )
            )

        if health_check_grace_period < 300:
            issues.append(
                self._create_issue(
                    resource,
                    "Health check grace period may be too short for application startup",
                )
            )

        return issues


@register_rule
class ASGInstanceRefreshRule(ValidationRule):
    """Auto Scaling Groups should have instance refresh enabled"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-ASG-002"
        self.description = "Auto Scaling Groups should enable instance refresh"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Configure instance_refresh for automated instance updates"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_autoscaling_group"}
        self.priority = 15

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        instance_refresh = resource.attributes.get("instance_refresh")
        if not instance_refresh:
            return [self._create_issue(resource)]
        return []


@register_rule
class ASGCapacityRebalanceRule(ValidationRule):
    """Auto Scaling Groups should enable capacity rebalance"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-ASG-003"
        self.description = (
            "Auto Scaling Groups should enable capacity rebalance for Spot instances"
        )
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Set capacity_rebalance = true when using Spot instances"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_autoscaling_group"}
        self.priority = 20

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        mixed_instances_policy = resource.attributes.get("mixed_instances_policy", {})
        capacity_rebalance = resource.attributes.get("capacity_rebalance")

        # Check if using Spot instances
        if mixed_instances_policy:
            launch_template = mixed_instances_policy.get("launch_template", {})
            override = launch_template.get("override", [])
            has_spot = any(
                "InstanceRequirements" in str(ov) or "Spot" in str(ov)
                for ov in override
            )

            if has_spot and not capacity_rebalance:
                return [self._create_issue(resource)]

        return []


# === LAUNCH TEMPLATE RULES ===
@register_rule
class LaunchTemplateLatestVersionRule(ValidationRule):
    """Launch Templates should use $Latest version or specific version"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-LT-001"
        self.description = "Launch Templates should specify version"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Use launch_template version = '$Latest' or specific version number"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_launch_template"}
        self.priority = 10

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # This rule primarily applies to resources using launch templates
        # For the template itself, we can check if it has proper configuration
        return []


@register_rule
class LaunchTemplateMetadataRule(ValidationRule):
    """Launch Templates should configure instance metadata"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-LT-002"
        self.description = "Launch Templates should configure instance metadata options"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Set metadata_options for http_tokens and http_endpoint"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_launch_template"}
        self.priority = 25

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        metadata_options = resource.attributes.get("metadata_options", {})
        if not metadata_options:
            return [
                self._create_issue(
                    resource, "Launch template missing metadata_options configuration"
                )
            ]
        return []


# === EBS VOLUME RULES ===
@register_rule
class EBSVolumeTypeRule(ValidationRule):
    """EBS volumes should use appropriate volume types"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-EBS-001"
        self.description = "EBS volumes should use gp3 for better price-performance"
        self.category = ValidationCategory.COST
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Use volume_type = 'gp3' for general purpose workloads"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_ebs_volume"}
        self.priority = 20

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        volume_type = resource.attributes.get("type", "gp2")
        if volume_type == "gp2":
            return [
                self._create_issue(
                    resource,
                    "Consider using gp3 volume type for better performance and lower cost",
                )
            ]
        return []


@register_rule
class EBSVolumeSizeRule(ValidationRule):
    """EBS volumes should have appropriate sizing"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-EBS-002"
        self.description = "EBS volumes should be appropriately sized"
        self.category = ValidationCategory.COST
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Right-size EBS volumes to match workload requirements"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_ebs_volume"}
        self.priority = 15

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        size = resource.attributes.get("size", 0)
        volume_type = resource.attributes.get("type", "")

        issues = []

        # Check for very small volumes that might be insufficient
        if size < 8 and volume_type != "io2":
            issues.append(
                self._create_issue(
                    resource, "EBS volume size may be too small for most workloads"
                )
            )

        # Check for potentially over-provisioned volumes
        if size > 1000 and volume_type in ["gp2", "gp3"]:
            issues.append(
                self._create_issue(
                    resource, "Consider if this large EBS volume is necessary"
                )
            )

        return issues


# === LOAD BALANCER RULES ===
@register_rule
class LBCrossZoneRule(ValidationRule):
    """Load Balancers should enable cross-zone load balancing"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-LB-001"
        self.description = "Load Balancers should enable cross-zone load balancing"
        self.category = ValidationCategory.PERFORMANCE
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Set enable_cross_zone_load_balancing = true for better distribution"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_lb", "aws_elb"}
        self.priority = 20

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        enable_cross_zone = resource.attributes.get("enable_cross_zone_load_balancing")
        if enable_cross_zone is False:
            return [self._create_issue(resource)]
        return []


@register_rule
class LBDropInvalidHeadersRule(ValidationRule):
    """Application Load Balancers should drop invalid headers"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-LB-002"
        self.description = "ALB should drop invalid HTTP headers"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Set drop_invalid_header_fields = true"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"aws_lb"}
        self.priority = 15

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        load_balancer_type = resource.attributes.get("load_balancer_type", "")
        drop_invalid_headers = resource.attributes.get("drop_invalid_header_fields")

        if load_balancer_type == "application" and not drop_invalid_headers:
            return [self._create_issue(resource)]
        return []


# === TAGGING RULES ===
@register_rule
class ComputeResourceTaggingRule(ValidationRule):
    """Compute resources should have proper tags"""

    def __init__(self):
        super().__init__()
        self.rule_id = "AWS-COMPUTE-TAG-001"
        self.description = "Compute resources should have required tags"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Add tags: Environment, Owner, Project, CostCenter"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {
            "aws_instance",
            "aws_autoscaling_group",
            "aws_launch_template",
            "aws_lb",
            "aws_elb",
        }
        self.priority = 5

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        tags = resource.attributes.get("tags", {})
        required_tags = {"Environment", "Owner", "Project"}
        missing_tags = required_tags - set(tags.keys())

        if missing_tags:
            return [
                self._create_issue(
                    resource,
                    f"Missing required tags: {', '.join(sorted(missing_tags))}",
                )
            ]
        return []

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


# === COMPUTE INSTANCE RULES ===
@register_rule
class GoogleInstanceShieldedVMRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "GCP-VM-001"
        self.description = "Compute instance should use Shielded VM"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Set shielded_instance_config with enable_secure_boot = true"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"google_compute_instance"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        shielded_config = resource.attributes.get("shielded_instance_config", {})
        if not shielded_config.get("enable_secure_boot"):
            return [self._create_issue(resource)]
        return []


@register_rule
class GoogleInstancePublicIPRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "GCP-VM-002"
        self.description = "Compute instance should not have public IP in production"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Remove access_config block or set nat_ip = null"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"google_compute_instance"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        network_interfaces = resource.attributes.get("network_interface", [])
        for ni in network_interfaces:
            access_configs = ni.get("access_config", [])
            for ac in access_configs:
                if ac.get("nat_ip"):
                    return [self._create_issue(resource)]
        return []


@register_rule
class GoogleInstanceDiskEncryptionRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "GCP-VM-003"
        self.description = (
            "Compute instance disks should be encrypted with customer-managed keys"
        )
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Set disk_encryption_key with kms_key_self_link"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"google_compute_instance"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        try:
            boot_disk = resource.attributes.get("boot_disk", {})
            if isinstance(boot_disk, list):
                boot_disk = boot_disk[0] if boot_disk else {}

            disk_encryption_key = boot_disk.get("disk_encryption_key", {})
            if not disk_encryption_key.get("kms_key_self_link"):
                return [self._create_issue(resource)]
        except (AttributeError, IndexError, KeyError):
            pass
        return []


@register_rule
class GoogleInstanceServiceAccountRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "GCP-VM-004"
        self.description = "Compute instance should use specific service account"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Set service_account with minimal required scopes"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"google_compute_instance"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        service_account = resource.attributes.get("service_account", {})
        if not service_account.get("email"):
            return [self._create_issue(resource)]
        return []


# === COMPUTE NETWORK RULES ===
@register_rule
class GoogleNetworkRoutingModeRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "GCP-NET-001"
        self.description = "VPC network should use regional routing mode"
        self.category = ValidationCategory.BEST_PRACTICES
        self.severity = ValidationSeverity.INFO
        self.suggestion = "Set routing_mode = 'REGIONAL' for better performance"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"google_compute_network"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        routing_mode = resource.attributes.get("routing_mode")
        if routing_mode != "REGIONAL":
            return [self._create_issue(resource)]
        return []


# === COMPUTE SUBNETWORK RULES ===
@register_rule
class GoogleSubnetPrivateGoogleAccessRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "GCP-SUBNET-001"
        self.description = "Subnetwork should enable Private Google Access"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Set private_ip_google_access = true"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"google_compute_subnetwork"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        private_google_access = resource.attributes.get("private_ip_google_access")
        if not private_google_access:
            return [self._create_issue(resource)]
        return []


@register_rule
class GoogleSubnetFlowLogsRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "GCP-SUBNET-002"
        self.description = "Subnetwork should enable VPC Flow Logs"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Set log_config with enable = true"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"google_compute_subnetwork"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        log_config = resource.attributes.get("log_config", {})
        if not log_config.get("enable"):
            return [self._create_issue(resource)]
        return []

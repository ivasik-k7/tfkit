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


# === VIRTUAL MACHINE SECURITY RULES ===
@register_rule
class AzureVMDiskEncryptionRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-001"
        self.description = "Virtual Machine disks should be encrypted"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Enable Azure Disk Encryption or use encrypted managed disks"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_virtual_machine"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        extensions = resource.attributes.get("storage_image_reference", [])
        has_encryption_extension = any(
            ext.get("type") == "AzureDiskEncryption" for ext in extensions
        )

        os_disk = resource.attributes.get("storage_os_disk", {})
        data_disks = resource.attributes.get("storage_data_disk", [])

        is_encrypted = (
            has_encryption_extension
            or os_disk.get("encryption_settings")
            or any(disk.get("encryption_settings") for disk in data_disks)
        )

        if not is_encrypted:
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureVMManagedIdentityRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-002"
        self.description = "Virtual Machine should use Managed Identity"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Enable System Assigned Managed Identity or User Assigned Identity"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_virtual_machine"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        identity = resource.attributes.get("identity", {})
        if not identity or identity.get("type") == "None":
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureVMJITAccessRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-003"
        self.description = "Virtual Machine should have Just-In-Time access enabled"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Enable JIT VM access in Azure Security Center"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_virtual_machine"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # This would typically check for JIT configuration
        # For Terraform, this might be a recommendation rather than direct validation
        return []


@register_rule
class AzureVMSSHKeyRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-004"
        self.description = "Linux VMs should use SSH keys instead of passwords"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = (
            "Use SSH key authentication and disable password authentication"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_virtual_machine"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        os_type = (
            resource.attributes.get("storage_os_disk", {}).get("os_type", "").lower()
        )
        if os_type == "linux":
            admin_password = resource.attributes.get("admin_password")
            disable_password_auth = resource.attributes.get(
                "disable_password_authentication"
            )

            if admin_password and not disable_password_auth:
                return [self._create_issue(resource)]
        return []


# === NETWORK SECURITY RULES ===
@register_rule
class AzureNSGSSHPortRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-101"
        self.description = "NSG should restrict SSH access (port 22)"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Restrict SSH port to specific IP ranges or use bastion host"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_network_security_group"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        security_rules = resource.attributes.get("security_rule", [])

        for rule in security_rules:
            if (
                rule.get("destination_port_range") == "22"
                and rule.get("access") == "Allow"
                and rule.get("direction") == "Inbound"
                and rule.get("source_address_prefix") in ["*", "0.0.0.0/0", "Internet"]
            ):
                return [self._create_issue(resource)]
        return []


@register_rule
class AzureNSGRDPPortRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-102"
        self.description = "NSG should restrict RDP access (port 3389)"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Restrict RDP port to specific IP ranges or use bastion host"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_network_security_group"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        security_rules = resource.attributes.get("security_rule", [])

        for rule in security_rules:
            if (
                rule.get("destination_port_range") == "3389"
                and rule.get("access") == "Allow"
                and rule.get("direction") == "Inbound"
                and rule.get("source_address_prefix") in ["*", "0.0.0.0/0", "Internet"]
            ):
                return [self._create_issue(resource)]
        return []


@register_rule
class AzureNSGDefaultRulesRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-103"
        self.description = "NSG should have explicit deny-all rule at the end"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Add explicit deny-all rule as the last security rule"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_network_security_group"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        security_rules = resource.attributes.get("security_rule", [])

        has_deny_all = any(
            rule.get("access") == "Deny"
            and rule.get("source_address_prefix") in ["*", "0.0.0.0/0"]
            and rule.get("destination_address_prefix") in ["*", "0.0.0.0/0"]
            and rule.get("priority", 0) > 4000  # Typically high priority for deny rules
            for rule in security_rules
        )

        if not has_deny_all:
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureSubnetNSGRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-104"
        self.description = "Subnet should have Network Security Group associated"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Associate a Network Security Group with the subnet"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_subnet"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        nsg_id = resource.attributes.get("network_security_group_id")
        if not nsg_id:
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureVNetDDOSProtectionRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-105"
        self.description = "Virtual Network should have DDoS protection enabled"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Enable DDoS protection plan for the virtual network"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_virtual_network"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        ddos_protection = resource.attributes.get("ddos_protection_plan", {})
        if not ddos_protection.get("enable"):
            return [self._create_issue(resource)]
        return []


# === STORAGE SECURITY RULES ===
@register_rule
class AzureStorageHTTPSRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-201"
        self.description = "Storage account should require secure transfer (HTTPS)"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Set enable_https_traffic_only to true"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_storage_account"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        https_only = resource.attributes.get("enable_https_traffic_only")
        if not https_only:
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureStorageEncryptionRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-202"
        self.description = "Storage account should have encryption enabled"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Enable storage service encryption"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_storage_account"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        encryption = resource.attributes.get("encryption", {})
        if not encryption or not encryption.get("enabled", True):
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureStorageNetworkRulesRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-203"
        self.description = "Storage account should restrict network access"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Configure network_rules to restrict access to specific networks"
        )
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_storage_account"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        network_rules = resource.attributes.get("network_rules", {})
        default_action = network_rules.get("default_action", "Allow")

        if default_action == "Allow":
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureStorageInfrastructureEncryptionRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-204"
        self.description = (
            "Storage account should have infrastructure encryption enabled"
        )
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Enable infrastructure encryption for double encryption"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_storage_account"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        encryption = resource.attributes.get("encryption", {})
        infrastructure_encryption = encryption.get("infrastructure_encryption_enabled")

        if not infrastructure_encryption:
            return [self._create_issue(resource)]
        return []


# === DATABASE SECURITY RULES ===
@register_rule
class AzureSQLServerTLSRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-301"
        self.description = "SQL Server should require TLS 1.2 or higher"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Set minimal_tls_version to 1.2"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_sql_server"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        min_tls_version = resource.attributes.get("minimal_tls_version", "1.0")
        if min_tls_version in ["1.0", "1.1"]:
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureSQLDatabaseTDERule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-302"
        self.description = (
            "SQL Database should have Transparent Data Encryption enabled"
        )
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Enable Transparent Data Encryption"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_sql_database"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        transparent_data_encryption = resource.attributes.get(
            "transparent_data_encryption", {}
        )
        if not transparent_data_encryption or not transparent_data_encryption.get(
            "enabled", True
        ):
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureSQLFirewallRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-303"
        self.description = "SQL Server should restrict firewall rules"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Avoid allowing 0.0.0.0/0 in SQL firewall rules"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_sql_firewall_rule"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        start_ip = resource.attributes.get("start_ip_address")
        end_ip = resource.attributes.get("end_ip_address")

        if start_ip == "0.0.0.0" and end_ip == "255.255.255.255":
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureSQLAuditingRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-304"
        self.description = "SQL Server should have auditing enabled"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Enable SQL Server auditing and threat detection"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_sql_server"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        extended_auditing_policy = resource.attributes.get("extended_auditing_policy")
        if not extended_auditing_policy:
            return [self._create_issue(resource)]
        return []


# === KEY VAULT SECURITY RULES ===
@register_rule
class AzureKeyVaultFirewallRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-401"
        self.description = "Key Vault should have firewall enabled"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Enable Key Vault firewall and restrict network access"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_key_vault"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        network_acls = resource.attributes.get("network_acls", {})
        default_action = network_acls.get("default_action", "Allow")

        if default_action == "Allow":
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureKeyVaultPurgeProtectionRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-402"
        self.description = "Key Vault should have purge protection enabled"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Enable purge protection to prevent accidental deletion"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_key_vault"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        purge_protection_enabled = resource.attributes.get("purge_protection_enabled")
        if not purge_protection_enabled:
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureKeyVaultSoftDeleteRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-403"
        self.description = "Key Vault should have soft delete enabled"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Enable soft delete for Key Vault"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_key_vault"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        soft_delete_enabled = resource.attributes.get("soft_delete_enabled")
        if not soft_delete_enabled:
            return [self._create_issue(resource)]
        return []


# === APP SERVICE SECURITY RULES ===
@register_rule
class AzureAppServiceHTTPSRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-501"
        self.description = "App Service should require HTTPS only"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Set https_only to true"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_app_service"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        https_only = resource.attributes.get("https_only")
        if not https_only:
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureAppServiceMinTLSRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-502"
        self.description = "App Service should use minimum TLS 1.2"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Set min_tls_version to 1.2"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_app_service"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        min_tls_version = resource.attributes.get("min_tls_version", "1.0")
        if min_tls_version in ["1.0", "1.1"]:
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureAppServiceIdentityRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-503"
        self.description = "App Service should use Managed Identity"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Enable Managed Identity for secure credential management"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_app_service"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        identity = resource.attributes.get("identity", {})
        if not identity or identity.get("type") == "None":
            return [self._create_issue(resource)]
        return []


# === AKS SECURITY RULES ===
@register_rule
class AzureAKSRBACRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-601"
        self.description = "AKS cluster should have RBAC enabled"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.ERROR
        self.suggestion = "Enable RBAC for AKS cluster"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_kubernetes_cluster"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        rbac_enabled = resource.attributes.get("role_based_access_control_enabled")
        if not rbac_enabled:
            return [self._create_issue(resource)]
        return []


@register_rule
class AzureAKSAPIServerAuthorizedIPsRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-602"
        self.description = "AKS API server should restrict authorized IP ranges"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Configure API server authorized IP ranges"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_kubernetes_cluster"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        api_server_authorized_ip_ranges = resource.attributes.get(
            "api_server_authorized_ip_ranges", []
        )
        if not api_server_authorized_ip_ranges:
            return [self._create_issue(resource)]
        return []


# === MONITORING & LOGGING SECURITY RULES ===
@register_rule
class AzureDiagnosticSettingsRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-701"
        self.description = "Critical resources should have diagnostic settings enabled"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Enable diagnostic settings for monitoring and auditing"
        self.scope = RuleScope.GENERIC
        self.resource_types = {
            "azurerm_key_vault",
            "azurerm_sql_server",
            "azurerm_storage_account",
            "azurerm_virtual_machine",
        }

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # This would check for associated diagnostic settings
        # For now, this is a placeholder for actual diagnostic settings validation
        return []


@register_rule
class AzureLogRetentionRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-702"
        self.description = (
            "Log analytics workspace should have adequate retention period"
        )
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Set retention period to at least 365 days for compliance"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_log_analytics_workspace"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        retention_in_days = resource.attributes.get("retention_in_days", 0)
        if retention_in_days < 365:
            return [self._create_issue(resource)]
        return []


# === IDENTITY & ACCESS SECURITY RULES ===
@register_rule
class AzureRoleAssignmentLeastPrivilegeRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-801"
        self.description = "Role assignments should follow principle of least privilege"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = "Avoid using built-in roles with broad permissions"
        self.scope = RuleScope.RESOURCE_SPECIFIC
        self.resource_types = {"azurerm_role_assignment"}

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        # role_definition_id = resource.attributes.get("role_definition_id", "")
        role_definition_name = resource.attributes.get("role_definition_name", "")

        # High-privilege built-in roles to avoid
        high_privilege_roles = [
            "Owner",
            "Contributor",
            "User Access Administrator",
            "Owner",
        ]

        if any(role in role_definition_name for role in high_privilege_roles):
            return [self._create_issue(resource)]
        return []


# === COMPLIANCE & GOVERNANCE RULES ===
@register_rule
class AzureResourceTagsRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-901"
        self.description = "Resources should have required security tags"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Add security-related tags like confidentiality, compliance, owner"
        )
        self.scope = RuleScope.GENERIC
        self.resource_types = set()

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        tags = resource.attributes.get("tags", {})
        security_tags = [
            "confidentiality",
            "compliance",
            "owner",
            "data-classification",
        ]
        missing_tags = [tag for tag in security_tags if tag not in tags]

        if missing_tags:
            return [
                self._create_issue(
                    resource, f"Missing security tags: {', '.join(missing_tags)}"
                )
            ]
        return []


@register_rule
class AzureResourceLocationRule(ValidationRule):
    def __init__(self):
        super().__init__()
        self.rule_id = "AZURE-SECURITY-902"
        self.description = "Resources should be deployed in approved regions"
        self.category = ValidationCategory.SECURITY
        self.severity = ValidationSeverity.WARNING
        self.suggestion = (
            "Deploy resources in compliant regions based on data residency requirements"
        )
        self.scope = RuleScope.GENERIC
        self.resource_types = set()

    def validate(self, resource: Any, project: Any) -> List[ValidationIssue]:
        location = resource.attributes.get("location", "")

        # Example: Restrict to specific compliant regions
        compliant_regions = ["eastus", "westeurope", "canadacentral", "australiaeast"]

        if location.lower() not in compliant_regions:
            return [
                self._create_issue(
                    resource, f"Resource in non-compliant region: {location}"
                )
            ]
        return []

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set

# --- Updated Imports ---
# Assumes your models are in files relative to this one
try:
    from ..analyzer.models import ResourceType, TerraformObject
    from ..analyzer.project import TerraformProject
except ImportError:
    # Fallback for flat structure
    from analyzer.models import ResourceType, TerraformObject, TerraformProject

try:
    from .models import (
        ValidationCategory,
        ValidationIssue,
        ValidationResult,
        ValidationSeverity,
    )
except ImportError:
    from validator.models import (
        ValidationCategory,
        ValidationIssue,
        ValidationResult,
        ValidationSeverity,
    )


class TerraformRule(ABC):
    """
    Abstract Base Class for all Terraform validation rules.
    Each rule is a self-contained check.
    """

    rule_id: str = "TF_BASE_000"
    description: str = "Base rule description"
    category: ValidationCategory = ValidationCategory.SYNTAX
    severity: ValidationSeverity = ValidationSeverity.ERROR
    suggestion: str = "No suggestion available."

    @abstractmethod
    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        """
        The core validation logic.

        Args:
            project: The entire parsed Terraform project.

        Returns:
            A list of ValidationIssue objects found by this rule.
        """
        pass

    def _create_issue(
        self,
        resource: TerraformObject,
        message: Optional[str] = None,
        severity: Optional[ValidationSeverity] = None,
    ) -> ValidationIssue:
        """Helper to create a ValidationIssue from this rule."""
        return ValidationIssue(
            severity=severity or self.severity,
            category=self.category,
            rule_id=self.rule_id,
            message=message or self.description,
            file_path=resource.file_path,
            line_number=resource.line_number,
            resource_name=resource.full_name,
            resource_type=resource.resource_type,
            suggestion=self.suggestion,
        )


class TerraformValidator:
    """
    Validates Terraform configurations by running a set of rules.
    This class is now a "rule runner" and does not contain
    any hardcoded validation logic itself.
    """

    def __init__(self, strict: bool = False, ignore_rules: Optional[List[str]] = None):
        """
        Initialize the validator.

        Args:
            strict: Enable strict validation mode (e.g., treat warnings as errors).
            ignore_rules: List of rule IDs to ignore (e.g., ["TF030"]).
        """
        self.strict = strict
        self.ignore_rules = set(ignore_rules or [])

        # --- FIX ---
        # Initialize ValidationResult with the required empty lists.
        self.result = ValidationResult(passed=[], warnings=[], errors=[], info=[])
        # --- END FIX ---

        self._rule_registry: List[TerraformRule] = self._discover_rules()

    def _discover_rules(self) -> List[TerraformRule]:
        """Finds and initializes all TerraformRule subclasses."""
        # (This method remains the same as my previous answer)
        rule_classes = [
            # Syntax Rules
            ModuleMissingSourceRule,
            ResourceMissingAttributesRule,
            # Reference Rules
            UndefinedReferenceRule,
            CircularDependencyRule,
            UnusedVariableRule,
            # Best Practice Rules
            MissingVariableDescriptionRule,
            MissingVariableTypeRule,
            MissingOutputDescriptionRule,
            TerraformVersionPinningRule,
            ProviderVersionPinningRule,
            ModuleVersionPinningRule,
            ResourceMissingTagsRule,
            # Naming Rules
            ResourceNamingConventionRule,
            # Security Rules
            SecurityGroupUnrestrictedIngressRule,
            SecurityGroupUnrestrictedEgressRule,
            S3BucketPublicAclRule,
            S3BucketEncryptionDisabledRule,
            S3BucketVersioningDisabledRule,
            IamPolicyWildcardActionRule,
            IamPolicyWildcardResourceRule,
            RdsInstancePubliclyAccessibleRule,
            RdsInstanceEncryptionDisabledRule,
            HardcodedSecretRule,
            # new
            DeprecatedResourceTypeRule,
            DeprecatedAttributeRule,
            ExcessiveCountRule,
            LargeInlineDataRule,
            InvalidResourceTypeRule,
            DuplicateResourceNameRule,
            UnusedOutputRule,
            SelfReferenceRule,
        ]
        return [RuleClass() for RuleClass in rule_classes]

    def validate(
        self,
        project: TerraformProject,
        check_syntax: bool = True,
        check_references: bool = True,
        check_best_practices: bool = True,
        check_security: bool = True,
        check_naming: bool = True,
    ) -> ValidationResult:
        """
        Run validation checks on the Terraform project.
        ...
        """

        # --- FIX ---
        # Reset results for this run by initializing with empty lists.
        self.result = ValidationResult(passed=[], warnings=[], errors=[], info=[])
        # --- END FIX ---

        # Map categories to the check flags
        category_map = {
            ValidationCategory.SYNTAX: check_syntax,
            ValidationCategory.REFERENCE: check_references,
            ValidationCategory.BEST_PRACTICE: check_best_practices,
            ValidationCategory.SECURITY: check_security,
            ValidationCategory.NAMING: check_naming,
        }

        for rule in self._rule_registry:
            if rule.rule_id in self.ignore_rules:
                continue

            if not category_map.get(rule.category, True):
                continue

            try:
                issues = rule.validate(project)
                if not issues:
                    pass
                else:
                    for issue in issues:
                        if self.strict and issue.severity == ValidationSeverity.WARNING:
                            issue.severity = ValidationSeverity.ERROR

                        # Use the model's add_issue method if it exists
                        # (otherwise, append directly)
                        if hasattr(self.result, "add_issue"):
                            self.result.add_issue(issue)
                        else:
                            if issue.severity == ValidationSeverity.ERROR:
                                self.result.errors.append(issue)
                            elif issue.severity == ValidationSeverity.WARNING:
                                self.result.warnings.append(issue)
                            else:
                                self.result.info.append(issue)

            except Exception as e:
                issue = ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SYNTAX,
                    rule_id="TF_RULE_ERROR",
                    message=f"Error executing rule {rule.rule_id}: {e}",
                    file_path="<validator>",
                    line_number=1,  # Add line_number as it's required
                )
                if hasattr(self.result, "add_issue"):
                    self.result.add_issue(issue)
                else:
                    self.result.errors.append(issue)

        total_rules_run = 0
        for rule in self._rule_registry:
            if rule.rule_id not in self.ignore_rules and category_map.get(
                rule.category, True
            ):
                total_rules_run += 1

        # Calculate total issues
        total_issues = (
            len(self.result.errors) + len(self.result.warnings) + len(self.result.info)
        )
        passed_check_count = total_rules_run - total_issues

        # Use add_passed method if it exists
        if hasattr(self.result, "add_passed"):
            self.result.add_passed(f"{passed_check_count} checks passed.")
        else:
            self.result.passed.append(f"{passed_check_count} checks passed.")

        return self.result


#
# === SYNTAX RULES ===
#
class ModuleMissingSourceRule(TerraformRule):
    rule_id = "TF002"
    description = "Module missing required 'source' attribute"
    category = ValidationCategory.SYNTAX
    severity = ValidationSeverity.ERROR
    suggestion = "Add a 'source' attribute to the module block."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for _, module in project.modules.items():
            if not module.source:
                issues.append(self._create_issue(module))
        return issues


class ResourceMissingAttributesRule(TerraformRule):
    rule_id = "TF001"
    description = "Resource block is empty or has no attributes"
    category = ValidationCategory.SYNTAX
    severity = ValidationSeverity.WARNING
    suggestion = "Add required configuration attributes or remove the empty block."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for _, resource in project.resources.items():
            # This logic remains the same
            if not resource.attributes:
                issues.append(self._create_issue(resource))
        return issues


#
# === REFERENCE RULES ===
#
class UndefinedReferenceRule(TerraformRule):
    rule_id = "TF010"
    description = "Reference to undefined resource, variable, or local"
    category = ValidationCategory.REFERENCE
    severity = ValidationSeverity.ERROR
    suggestion = "Ensure the referenced item is defined and spelled correctly."

    INTERPOLATION_REGEX = re.compile(
        r'\${([^{}]*)}|"\s*(var|local|module|data\.[^"]*)\s*"'
    )

    def __init__(self):
        self._available_refs: Set[str] = set()

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        self._available_refs = self._get_available_references(project)

        # Use your project's `all_objects` property
        for _, item in project.all_objects.items():
            # Skip vars, locals (they don't have refs in the same way)
            if item.type in [ResourceType.VARIABLE, ResourceType.LOCAL]:
                continue
            issues.extend(self._check_item_dependencies(item, project))

        return issues

    def _get_available_references(self, project: TerraformProject) -> Set[str]:
        # Uses your project's .keys() which are the full_names
        refs = set()
        refs.update(project.variables.keys())
        refs.update(project.locals.keys())
        refs.update(project.resources.keys())
        refs.update(project.data_sources.keys())
        refs.update(project.modules.keys())
        # Add common built-in references
        refs.update(
            [
                "self",
                "count.index",
                "each.key",
                "each.value",
                "path.module",
                "path.root",
                "path.cwd",
                "terraform.workspace",
            ]
        )
        return refs

    def _check_item_dependencies(
        self, item: TerraformObject, project: TerraformProject
    ) -> List[ValidationIssue]:
        local_issues = []

        # 1. Check explicit 'dependencies' list from your model
        for dep in item.dependencies:
            ref = self._normalize_reference(dep)
            if not self._reference_exists(ref):
                # --- Updated Field ---
                msg = f"'{item.full_name}' has explicit 'depends_on' to undefined reference: {dep}"
                local_issues.append(self._create_issue(item, message=msg))

        # 2. Check implicit dependencies in attributes
        attr_str = json.dumps(item.attributes)

        for match in self.INTERPOLATION_REGEX.finditer(attr_str):
            ref_full = match.group(1) or match.group(2)
            if not ref_full:
                continue

            potential_refs = re.findall(r"[\w\.-]+", ref_full)

            for ref_part in potential_refs:
                if not (
                    ref_part.startswith("var.")
                    or ref_part.startswith("local.")
                    or ref_part.startswith("module.")
                    or ref_part.startswith("data.")
                    or any(ref_part.startswith(res) for res in project.resources.keys())
                ):
                    continue

                ref = self._normalize_reference(ref_part)
                if not self._reference_exists(ref):
                    # --- Updated Field ---
                    msg = f"'{item.full_name}' has an implicit reference to undefined item: {ref_part}"
                    local_issues.append(self._create_issue(item, message=msg))
        return local_issues

    def _normalize_reference(self, ref: str) -> str:
        """Strips attributes/indices from a reference string."""
        ref = ref.split("[", 1)[0].strip()  # Remove index access
        parts = ref.split(".")

        if not parts:
            return ref

        # `var.foo`, `local.bar`
        if parts[0] in ["var", "local"] and len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        # `module.foo`
        if parts[0] == "module" and len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        # `data.aws_iam_policy.foo`
        if parts[0] == "data" and len(parts) >= 3:
            return f"data.{parts[1]}.{parts[2]}"
        # `aws_instance.foo`
        if len(parts) == 2:
            return f"{parts[0]}.{parts[1]}"
        # Built-ins
        if parts[0] in ["self", "path", "terraform", "count", "each"]:
            return ref

        # Fallback for resource.name.attribute
        if len(parts) > 2:
            return f"{parts[0]}.{parts[1]}"

        return ref

    def _reference_exists(self, ref: str) -> bool:
        """Checks if a normalized reference exists."""
        if ref in self._available_refs:
            return True

        # Handle splat expressions 'aws_instance.foo.*'
        if ref.endswith(".*"):
            if ref[:-2] in self._available_refs:
                return True

        return False


class CircularDependencyRule(TerraformRule):
    rule_id = "TF012"
    description = "Circular dependency detected between resources"
    category = ValidationCategory.REFERENCE
    severity = ValidationSeverity.ERROR
    suggestion = "Refactor resources to break the circular dependency."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        # --- Use Built-in Method ---
        # Leverage the method from your TerraformProject model
        cycles = project.get_circular_dependencies()

        for cycle in cycles:
            # We can't point to a single object, so we create an issue
            # without the helper
            cycle_path = " -> ".join(cycle)

            # Try to find the file/line of the first item in the cycle
            first_obj = project.find_object(cycle[0])
            file_path = first_obj.file_path if first_obj else "<multiple>"
            line_num = first_obj.line_number if first_obj else 1

            issues.append(
                ValidationIssue(
                    severity=self.severity,
                    category=self.category,
                    rule_id=self.rule_id,
                    message=f"Circular dependency detected: {cycle_path}",
                    file_path=file_path,
                    line_number=line_num,
                    resource_name=cycle[0],  # Report against the first item
                    suggestion=self.suggestion,
                )
            )
        return issues


class UnusedVariableRule(TerraformRule):
    rule_id = "TF013"
    description = "Variable is defined but not used"
    category = ValidationCategory.REFERENCE
    severity = ValidationSeverity.INFO
    suggestion = "Remove the unused variable definition."

    def __init__(self):
        self._used_vars: Set[str] = set()

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        self._used_vars = set()

        # 1. Find all variable uses in all objects (including outputs)
        for item in project.all_objects.values():
            attr_str = json.dumps(item.attributes)
            for match in re.finditer(r"var\.(\w+)", attr_str):
                self._used_vars.add(match.group(1))

        # 2. Check against definitions
        for _, var in project.variables.items():
            # --- Updated Field ---
            # 'var.name' is 'my_var', which matches the regex capture
            if var.name not in self._used_vars:
                issues.append(self._create_issue(var))

        return issues


#
# === BEST PRACTICE RULES ===
#
class MissingVariableDescriptionRule(TerraformRule):
    rule_id = "TF021"
    description = "Variable is missing a 'description' attribute"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.INFO
    suggestion = "Add a 'description' to the variable to document its purpose."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for _, var in project.variables.items():
            # --- Updated Field ---
            if not var.description:
                issues.append(self._create_issue(var))
        return issues


class MissingVariableTypeRule(TerraformRule):
    rule_id = "TF022"
    description = "Variable is missing a 'type' constraint"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = "Add a 'type' constraint for better validation and clarity (e.g., type = string)."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for _, var in project.variables.items():
            # --- Updated Field ---
            if not var.variable_type:
                issues.append(self._create_issue(var))
        return issues


class MissingOutputDescriptionRule(TerraformRule):
    rule_id = "TF023"
    description = "Output is missing a 'description' attribute"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.INFO
    suggestion = "Add a 'description' to the output to document its purpose."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for _, output in project.outputs.items():
            # --- Updated Field ---
            if not output.description:
                issues.append(self._create_issue(output))
        return issues


class TerraformVersionPinningRule(TerraformRule):
    rule_id = "TF100"
    description = (
        "Terraform block missing 'required_version' or uses a permissive version"
    )
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = "Pin the Terraform version (e.g., 'required_version = \"~> 1.5\"')."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        # --- Updated Field ---
        # Use 'terraform_blocks' dict
        if not project.terraform_blocks:
            # This could be an issue itself, but for this rule, we just exit.
            return []

        # Check all terraform blocks, though usually there's one
        for tf_block in project.terraform_blocks.values():
            req_version = tf_block.attributes.get("required_version")
            if not req_version:
                issues.append(
                    self._create_issue(
                        tf_block, message="Terraform block missing 'required_version'"
                    )
                )
            elif str(req_version) in ["> 0", "latest", "*", ">= 0"]:
                issues.append(
                    self._create_issue(
                        tf_block,
                        message=f"Terraform 'required_version' ({req_version}) is too permissive.",
                    )
                )
        return issues


class ProviderVersionPinningRule(TerraformRule):
    rule_id = "TF101"
    description = "Provider configuration missing version constraint"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = "Pin all provider versions in 'required_providers' (e.g., 'version = \"~> 4.0\"')."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        # --- Updated Field ---
        if not project.terraform_blocks:
            return []

        # Check all terraform blocks
        for tf_block in project.terraform_blocks.values():
            required_providers = tf_block.attributes.get("required_providers")
            if not isinstance(required_providers, dict):
                continue

            for name, config in required_providers.items():
                if isinstance(config, dict) and not config.get("version"):
                    msg = f"Provider '{name}' in '{tf_block.full_name}' is missing a 'version' constraint."
                    # Point to the terraform block itself
                    issues.append(self._create_issue(tf_block, message=msg))
        return issues


class ModuleVersionPinningRule(TerraformRule):
    rule_id = "TF102"
    description = "Module 'source' uses a non-pinned reference (e.g., 'main' branch)"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = (
        "Pin module 'source' to a specific tag or version (e.g., '..._?ref=v1.2.3_')."
    )

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for _, module in project.modules.items():
            source = module.source or ""

            if source.startswith("git@") or source.startswith("https://"):
                if "?ref=" not in source:
                    msg = f"Module '{module.full_name}' Git source is not pinned to a specific ref/tag."
                    issues.append(self._create_issue(module, message=msg))

            elif re.match(r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$", source):
                if not module.attributes.get("version"):
                    # --- Updated Field ---
                    msg = f"Module '{module.full_name}' from registry is missing a 'version' constraint."
                    issues.append(self._create_issue(module, message=msg))
        return issues


class ResourceNamingConventionRule(TerraformRule):
    rule_id = "TF040"
    description = "Resource name does not follow snake_case convention"
    category = ValidationCategory.NAMING
    severity = ValidationSeverity.INFO
    suggestion = "Use lowercase letters, numbers, and underscores (snake_case) for resource names."

    SNAKE_CASE_REGEX = re.compile(r"^[a-z0-9_]+$")

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        # Check resources, data, vars, outputs, modules
        # 'locals' often use camelCase, so we skip them.
        items_to_check = {
            **project.resources,
            **project.data_sources,
            **project.variables,
            **project.outputs,
            **project.modules,
        }

        for full_name, item in items_to_check.items():
            # --- Updated Fields ---
            # Your model's 'name' field is the declared name (e.g., 'my_instance')
            # This is much cleaner!
            declared_name = item.name

            if not self.SNAKE_CASE_REGEX.match(declared_name):
                # 'item.type.value' gives 'resource', 'variable', etc.
                msg = f"{item.type.value.capitalize()} '{item.full_name}' name part '{declared_name}' does not follow snake_case convention."
                issues.append(self._create_issue(item, message=msg))
        return issues


#
# === SECURITY RULES ===
#
class SecurityGroupUnrestrictedIngressRule(TerraformRule):
    rule_id = "TF030"
    description = "Security group allows unrestricted ingress (0.0.0.0/0 or ::/0)"
    category = ValidationCategory.SECURITY
    severity = ValidationSeverity.ERROR
    suggestion = "Restrict ingress to specific, trusted IP ranges."

    UNRESTRICTED_CIDRS = {"0.0.0.0/0", "::/0"}

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for _, resource in project.resources.items():
            if resource.resource_type == "aws_security_group":
                rules = resource.attributes.get("ingress", [])
                if not isinstance(rules, list):
                    continue
                for i, rule in enumerate(rules):
                    if isinstance(rule, dict):
                        cidrs = set(
                            rule.get("cidr_blocks", [])
                            + rule.get("ipv6_cidr_blocks", [])
                        )
                        if not cidrs.isdisjoint(self.UNRESTRICTED_CIDRS):
                            msg = f"Security group '{resource.full_name}' has unrestricted ingress in inline rule #{i}."
                            issues.append(self._create_issue(resource, message=msg))

            elif resource.resource_type in [
                "aws_security_group_rule",
                "aws_vpc_security_group_ingress_rule",
            ]:
                if resource.attributes.get("type", "ingress") == "ingress":
                    cidrs = set(
                        resource.attributes.get("cidr_blocks", [])
                        + resource.attributes.get("ipv6_cidr_blocks", [])
                    )
                    if not cidrs.isdisjoint(self.UNRESTRICTED_CIDRS):
                        issues.append(self._create_issue(resource))
        return issues


class SecurityGroupUnrestrictedEgressRule(TerraformRule):
    rule_id = "TF103"
    description = "Security group allows unrestricted egress (0.0.0.0/0 or ::/0)"
    category = ValidationCategory.SECURITY
    severity = ValidationSeverity.WARNING

    UNRESTRICTED_CIDRS = {"0.0.0.0/0", "::/0"}

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for _, resource in project.resources.items():
            if resource.resource_type == "aws_security_group":
                rules = resource.attributes.get("egress", [])
                if not isinstance(rules, list):
                    continue
                for i, rule in enumerate(rules):
                    if isinstance(rule, dict):
                        cidrs = set(
                            rule.get("cidr_blocks", [])
                            + rule.get("ipv6_cidr_blocks", [])
                        )
                        if not cidrs.isdisjoint(self.UNRESTRICTED_CIDRS):
                            # --- Updated Field ---
                            msg = f"Security group '{resource.full_name}' has unrestricted egress in inline rule #{i}."
                            issues.append(self._create_issue(resource, message=msg))

            elif resource.resource_type in [
                "aws_security_group_rule",
                "aws_vpc_security_group_egress_rule",
            ]:
                if resource.attributes.get("type") == "egress":
                    cidrs = set(
                        resource.attributes.get("cidr_blocks", [])
                        + resource.attributes.get("ipv6_cidr_blocks", [])
                    )
                    if not cidrs.isdisjoint(self.UNRESTRICTED_CIDRS):
                        issues.append(self._create_issue(resource))
        return issues


class S3BucketPublicAclRule(TerraformRule):
    rule_id = "TF031"
    description = "S3 bucket has a public ACL"
    category = ValidationCategory.SECURITY
    severity = ValidationSeverity.ERROR
    suggestion = "Set ACL to 'private'. Use 'aws_s3_bucket_public_access_block' and bucket policies for access."

    PUBLIC_ACLS = {"public-read", "public-read-write", "website"}

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for name, resource in project.resources.items():
            if resource.resource_type == "aws_s3_bucket":
                acl = resource.attributes.get("acl")
                if acl in self.PUBLIC_ACLS:
                    issues.append(self._create_issue(resource))

            elif resource.resource_type == "aws_s3_bucket_acl":
                acl = resource.attributes.get("acl")
                if acl in self.PUBLIC_ACLS:
                    issues.append(self._create_issue(resource))
        return issues


class S3BucketEncryptionDisabledRule(TerraformRule):
    rule_id = "TF032"
    description = "S3 bucket server-side encryption is not configured"
    category = ValidationCategory.SECURITY
    severity = ValidationSeverity.WARNING
    suggestion = "Enable server-side encryption by adding a 'server_side_encryption_configuration' block."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for name, resource in project.resources.items():
            if resource.resource_type == "aws_s3_bucket":
                encryption = resource.attributes.get(
                    "server_side_encryption_configuration"
                )
                if not isinstance(encryption, dict) or not encryption:
                    issues.append(self._create_issue(resource))
        return issues


class S3BucketVersioningDisabledRule(TerraformRule):
    rule_id = "TF033"
    description = "S3 bucket versioning is not enabled"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.INFO
    suggestion = "Enable versioning for data protection and recovery by setting 'versioning.enabled = true'."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for name, resource in project.resources.items():
            if resource.resource_type == "aws_s3_bucket":
                versioning = resource.attributes.get("versioning")
                if not isinstance(versioning, dict) or not versioning.get("enabled"):
                    issues.append(self._create_issue(resource))
        return issues


class IamPolicyWildcardActionRule(TerraformRule):
    rule_id = "TF034"
    description = "IAM policy allows all actions ('Action: \"*\"')"
    category = ValidationCategory.SECURITY
    severity = ValidationSeverity.ERROR
    suggestion = "Follow the principle of least privilege. Specify exact actions instead of using '*'."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        return self._validate_policy(project, self._check_action)

    def _check_action(
        self, stmt: Dict, resource: TerraformObject
    ) -> Optional[ValidationIssue]:
        actions = stmt.get("Action", [])
        if not isinstance(actions, list):
            actions = [actions]
        if "*" in actions or any(a.strip() == "*" for a in actions):
            # --- Updated Field ---
            msg = f"IAM policy '{resource.full_name}' contains 'Action: *'"
            return self._create_issue(resource, message=msg)
        return None

    def _validate_policy(
        self, project: TerraformProject, check_func
    ) -> List[ValidationIssue]:
        issues = []
        for name, resource in project.resources.items():
            if (
                not resource.resource_type
                or "aws_iam_" not in resource.resource_type
                or "policy" not in resource.resource_type
            ):
                continue

            policy_str = resource.attributes.get("policy")
            if (
                not policy_str
                or not isinstance(policy_str, str)
                or not policy_str.strip().startswith("{")
            ):
                continue

            try:
                policy_doc = json.loads(policy_str)
                statements = policy_doc.get("Statement", [])
                if not isinstance(statements, list):
                    statements = [statements]

                for stmt in statements:
                    if stmt.get("Effect", "Allow") != "Allow":
                        continue

                    issue = check_func(stmt, resource)
                    if issue:
                        issues.append(issue)

            except json.JSONDecodeError:
                pass
        return issues


class IamPolicyWildcardResourceRule(IamPolicyWildcardActionRule):
    rule_id = "TF035"
    description = "IAM policy applies to all resources ('Resource: \"*\"')"
    category = ValidationCategory.SECURITY
    severity = ValidationSeverity.WARNING
    suggestion = "Limit policy to specific ARNs. Avoid using 'Resource: *'."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        return self._validate_policy(project, self._check_resource)

    def _check_resource(
        self, stmt: Dict, resource: TerraformObject
    ) -> Optional[ValidationIssue]:
        resources = stmt.get("Resource", [])
        if not isinstance(resources, list):
            resources = [resources]
        if "*" in resources or any(r.strip() == "*" for r in resources):
            # --- Updated Field ---
            msg = f"IAM policy '{resource.full_name}' contains 'Resource: *'"
            return self._create_issue(resource, message=msg)
        return None


class RdsInstancePubliclyAccessibleRule(TerraformRule):
    rule_id = "TF036"
    description = "RDS instance is publicly accessible"
    category = ValidationCategory.SECURITY
    severity = ValidationSeverity.ERROR
    suggestion = "Set 'publicly_accessible = false' and access the DB via a VPC."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for name, resource in project.resources.items():
            if resource.resource_type in [
                "aws_db_instance",
                "aws_rds_cluster_instance",
            ]:
                if resource.attributes.get("publicly_accessible") is True:
                    issues.append(self._create_issue(resource))
        return issues


class RdsInstanceEncryptionDisabledRule(TerraformRule):
    rule_id = "TF037"
    description = "RDS instance storage encryption is not enabled"
    category = ValidationCategory.SECURITY
    severity = ValidationSeverity.WARNING
    suggestion = "Set 'storage_encrypted = true' for data-at-rest protection."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for name, resource in project.resources.items():
            if resource.resource_type == "aws_db_instance":
                if resource.attributes.get("storage_encrypted") is False:
                    if not resource.attributes.get("replicate_source_db"):
                        issues.append(self._create_issue(resource))
        return issues


class HardcodedSecretRule(TerraformRule):
    rule_id = "TF038"
    description = "Potential hardcoded secret detected in resource attribute"
    category = ValidationCategory.SECURITY
    severity = ValidationSeverity.ERROR
    suggestion = "Use variables (from .tfvars or env) or a secret manager."

    SECRET_KEY_REGEX = re.compile(
        r"password|secret|token|api_key|access_key|private_key|key_material|client_secret",
        re.IGNORECASE,
    )
    VALUE_WHITELIST = {"", "true", "false", "1", "0", "null", "none"}

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        all_items = {**project.resources, **project.modules}

        for name, item in all_items.items():
            issues.extend(self._check_attributes(item, item.attributes))
        return issues

    def _check_attributes(
        self, item: TerraformObject, attrs: Any
    ) -> List[ValidationIssue]:
        """Recursively scan attributes for hardcoded secrets."""
        local_issues = []
        if isinstance(attrs, dict):
            for key, value in attrs.items():
                if self.SECRET_KEY_REGEX.search(key):
                    if self._is_hardcoded_secret(value):
                        msg = f"Potential hardcoded secret in attribute '{key}' of '{item.full_name}'"
                        local_issues.append(self._create_issue(item, message=msg))

                local_issues.extend(self._check_attributes(item, value))

        elif isinstance(attrs, list):
            for value in attrs:
                local_issues.extend(self._check_attributes(item, value))

        return local_issues

    def _is_hardcoded_secret(self, value: Any) -> bool:
        if not isinstance(value, str) or value in self.VALUE_WHITELIST:
            return False

        val_str = value.strip()

        # Check if it's an interpolation or reference
        if (
            val_str.startswith("${")
            or val_str.startswith("var.")
            or val_str.startswith("local.")
            or val_str.startswith("data.")
            or val_str.startswith("module.")
            or val_str.startswith("file(")
            or val_str.startswith("templatefile(")
            or val_str.startswith("nonsensitive(")
        ):
            return False

        return True


#
# === DEPRECATION RULES ===
#
class DeprecatedResourceTypeRule(TerraformRule):
    rule_id = "TF060"
    description = "Resource type is deprecated"
    category = ValidationCategory.DEPRECATION
    severity = ValidationSeverity.WARNING
    suggestion = "Update to the recommended replacement resource type."

    DEPRECATED_RESOURCES = {
        "aws_s3_bucket_policy": "Use aws_s3_bucket with policy attribute or separate aws_s3_bucket_policy resource",
        "aws_alb": "Use aws_lb instead",
        "aws_alb_listener": "Use aws_lb_listener instead",
        "aws_alb_target_group": "Use aws_lb_target_group instead",
        "azurerm_virtual_machine": "Use azurerm_linux_virtual_machine or azurerm_windows_virtual_machine",
        "google_compute_instance_group_manager": "Use google_compute_region_instance_group_manager for regional resources",
    }

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        for name, resource in project.resources.items():
            if resource.resource_type in self.DEPRECATED_RESOURCES:
                suggestion = self.DEPRECATED_RESOURCES[resource.resource_type]
                msg = f"Resource type '{resource.resource_type}' is deprecated. {suggestion}"
                issues.append(self._create_issue(resource, message=msg))

        return issues


class DeprecatedAttributeRule(TerraformRule):
    rule_id = "TF061"
    description = "Resource uses deprecated attribute"
    category = ValidationCategory.DEPRECATION
    severity = ValidationSeverity.WARNING
    suggestion = "Update to use the recommended attribute."

    DEPRECATED_ATTRIBUTES = {
        "aws_instance": {
            "ebs_block_device": "Use separate aws_ebs_volume and aws_volume_attachment resources",
        },
        "aws_db_instance": {
            "name": "Use aws_db_database resource instead for RDS database creation",
        },
        "aws_security_group": {
            "ingress": "Use separate aws_security_group_rule resources for better management",
            "egress": "Use separate aws_security_group_rule resources for better management",
        },
    }

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        for name, resource in project.resources.items():
            if resource.resource_type in self.DEPRECATED_ATTRIBUTES:
                deprecated_attrs = self.DEPRECATED_ATTRIBUTES[resource.resource_type]
                for attr_name, suggestion in deprecated_attrs.items():
                    if attr_name in resource.attributes:
                        msg = f"Attribute '{attr_name}' in '{resource.full_name}' is deprecated. {suggestion}"
                        issues.append(self._create_issue(resource, message=msg))

        return issues


#
# === PERFORMANCE RULES ===
#
class ExcessiveCountRule(TerraformRule):
    rule_id = "TF070"
    description = "Resource uses excessive count value"
    category = ValidationCategory.PERFORMANCE
    severity = ValidationSeverity.WARNING
    suggestion = "Consider using modules or for_each for better organization with large resource counts."

    MAX_RECOMMENDED_COUNT = 50

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        for name, resource in project.resources.items():
            count_value = resource.attributes.get("count")

            if (
                isinstance(count_value, int)
                and count_value > self.MAX_RECOMMENDED_COUNT
            ):
                msg = f"Resource '{resource.full_name}' has count={count_value} which may impact performance"
                issues.append(self._create_issue(resource, message=msg))

        return issues


class LargeInlineDataRule(TerraformRule):
    rule_id = "TF071"
    description = "Resource contains large inline data"
    category = ValidationCategory.PERFORMANCE
    severity = ValidationSeverity.INFO
    suggestion = (
        "Consider using external files with templatefile() or file() functions."
    )

    MAX_INLINE_LENGTH = 1000

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        for name, resource in project.resources.items():
            for attr_name, attr_value in resource.attributes.items():
                if (
                    isinstance(attr_value, str)
                    and len(attr_value) > self.MAX_INLINE_LENGTH
                ):
                    # Skip if it's already using file() or templatefile()
                    if "file(" not in attr_value and "templatefile(" not in attr_value:
                        msg = f"Attribute '{attr_name}' in '{resource.full_name}' contains {len(attr_value)} characters of inline data"
                        issues.append(self._create_issue(resource, message=msg))

        return issues


class InvalidResourceTypeRule(TerraformRule):
    rule_id = "TF003"
    description = "Resource type format is invalid"
    category = ValidationCategory.SYNTAX
    severity = ValidationSeverity.ERROR
    suggestion = "Resource type must be in format 'provider_resourcetype' (e.g., 'aws_instance')."

    VALID_TYPE_REGEX = re.compile(r"^[a-z][a-z0-9]*_[a-z][a-z0-9_]*$")

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for _, resource in project.resources.items():
            if resource.resource_type and not self.VALID_TYPE_REGEX.match(
                resource.resource_type
            ):
                msg = f"Resource type '{resource.resource_type}' has invalid format"
                issues.append(self._create_issue(resource, message=msg))
        return issues


class DuplicateResourceNameRule(TerraformRule):
    rule_id = "TF004"
    description = "Duplicate resource name detected"
    category = ValidationCategory.SYNTAX
    severity = ValidationSeverity.ERROR
    suggestion = "Ensure each resource has a unique name within its type."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        seen = {}

        for _, resource in project.resources.items():
            key = f"{resource.resource_type}.{resource.name}"
            if key in seen:
                msg = f"Duplicate resource name: {key} (also defined in {seen[key]})"
                issues.append(self._create_issue(resource, message=msg))
            else:
                seen[key] = resource.file_path

        return issues


class UnusedOutputRule(TerraformRule):
    rule_id = "TF014"
    description = "Output is defined but its value references undefined resources"
    category = ValidationCategory.REFERENCE
    severity = ValidationSeverity.WARNING
    suggestion = (
        "Ensure output values reference valid resources or remove unused outputs."
    )

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        available_refs = set()
        available_refs.update(project.resources.keys())
        available_refs.update(project.data_sources.keys())
        available_refs.update(project.modules.keys())
        available_refs.update(project.locals.keys())

        for _, output in project.outputs.items():
            value_str = json.dumps(output.attributes.get("value", ""))
            has_valid_ref = False

            for ref_type in ["data.", "module.", "local."]:
                if ref_type in value_str:
                    has_valid_ref = True
                    break

            for res_name in project.resources.keys():
                if res_name in value_str:
                    has_valid_ref = True
                    break

            if not has_valid_ref and value_str and value_str != '""':
                msg = f"Output '{output.full_name}' may not reference valid resources"
                issues.append(self._create_issue(output, message=msg))

        return issues


class SelfReferenceRule(TerraformRule):
    rule_id = "TF015"
    description = "Resource contains a self-reference without using 'self'"
    category = ValidationCategory.REFERENCE
    severity = ValidationSeverity.ERROR
    suggestion = (
        "Use 'self' keyword for self-references within provisioners or connections."
    )

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        for _, resource in project.resources.items():
            attr_str = json.dumps(resource.attributes)

            if resource.full_name in attr_str and "self." not in attr_str:
                depends_on = resource.attributes.get("depends_on", [])
                if resource.full_name not in depends_on:
                    msg = f"Resource '{resource.full_name}' appears to reference itself"
                    issues.append(self._create_issue(resource, message=msg))

        return issues


#
# === BEST PRACTICE RULES ===
#
class MissingVariableDescriptionRule(TerraformRule):
    rule_id = "TF021"
    description = "Variable is missing a 'description' attribute"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.INFO
    suggestion = "Add a 'description' to the variable to document its purpose."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for name, var in project.variables.items():
            if not var.description:
                issues.append(self._create_issue(var))
        return issues


class MissingVariableTypeRule(TerraformRule):
    rule_id = "TF022"
    description = "Variable is missing a 'type' constraint"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = "Add a 'type' constraint for better validation and clarity (e.g., type = string)."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for name, var in project.variables.items():
            if not var.variable_type:
                issues.append(self._create_issue(var))
        return issues


class MissingOutputDescriptionRule(TerraformRule):
    rule_id = "TF023"
    description = "Output is missing a 'description' attribute"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.INFO
    suggestion = "Add a 'description' to the output to document its purpose."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for name, output in project.outputs.items():
            if not output.description:
                issues.append(self._create_issue(output))
        return issues


class TerraformVersionPinningRule(TerraformRule):
    rule_id = "TF100"
    description = (
        "Terraform block missing 'required_version' or uses a permissive version"
    )
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = "Pin the Terraform version (e.g., 'required_version = \"~> 1.5\"')."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        if not project.terraform_blocks:
            return []

        for tf_block in project.terraform_blocks.values():
            req_version = tf_block.attributes.get("required_version")
            if not req_version:
                issues.append(
                    self._create_issue(
                        tf_block, message="Terraform block missing 'required_version'"
                    )
                )
            elif str(req_version) in ["> 0", "latest", "*", ">= 0"]:
                issues.append(
                    self._create_issue(
                        tf_block,
                        message=f"Terraform 'required_version' ({req_version}) is too permissive.",
                    )
                )
        return issues


class ProviderVersionPinningRule(TerraformRule):
    rule_id = "TF101"
    description = "Provider configuration missing version constraint"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = "Pin all provider versions in 'required_providers' (e.g., 'version = \"~> 4.0\"')."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        if not project.terraform_blocks:
            return []

        for tf_block in project.terraform_blocks.values():
            required_providers = tf_block.attributes.get("required_providers")
            if not isinstance(required_providers, dict):
                continue

            for name, config in required_providers.items():
                if isinstance(config, dict) and not config.get("version"):
                    msg = f"Provider '{name}' in '{tf_block.full_name}' is missing a 'version' constraint."
                    issues.append(self._create_issue(tf_block, message=msg))
        return issues


class ModuleVersionPinningRule(TerraformRule):
    rule_id = "TF102"
    description = "Module 'source' uses a non-pinned reference (e.g., 'main' branch)"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = (
        "Pin module 'source' to a specific tag or version (e.g., '..._?ref=v1.2.3_')."
    )

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for name, module in project.modules.items():
            source = module.source or ""

            if source.startswith("git@") or source.startswith("https://"):
                if "?ref=" not in source:
                    msg = f"Module '{module.full_name}' Git source is not pinned to a specific ref/tag."
                    issues.append(self._create_issue(module, message=msg))

            elif re.match(r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$", source):
                if not module.attributes.get("version"):
                    msg = f"Module '{module.full_name}' from registry is missing a 'version' constraint."
                    issues.append(self._create_issue(module, message=msg))
        return issues


class ResourceMissingTagsRule(TerraformRule):
    rule_id = "TF020"
    description = "Resource is missing 'tags' attribute"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = "Add 'tags' for cost allocation, automation, and resource management."

    TAGGABLE_RESOURCE_TYPES = {
        "aws_instance",
        "aws_s3_bucket",
        "aws_vpc",
        "aws_subnet",
        "aws_security_group",
        "aws_db_instance",
        "aws_lambda_function",
        "aws_ecs_cluster",
        "aws_ecs_service",
        "aws_elb",
        "aws_alb",
        "aws_nat_gateway",
        "aws_iam_role",
        "aws_iam_policy",
        "azurerm_resource_group",
        "azurerm_virtual_network",
        "azurerm_virtual_machine",
        "azurerm_storage_account",
        "azurerm_kubernetes_cluster",
        "google_compute_instance",
        "google_storage_bucket",
        "google_compute_network",
        "google_sql_database_instance",
        "google_container_cluster",
    }

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []
        for name, resource in project.resources.items():
            if resource.resource_type in self.TAGGABLE_RESOURCE_TYPES:
                tags = resource.attributes.get("tags")
                if not isinstance(tags, dict) or not tags:
                    issues.append(self._create_issue(resource))
        return issues


class MissingProviderRule(TerraformRule):
    rule_id = "TF024"
    description = "Resources exist but no provider is configured"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = "Add provider configuration blocks for all providers used."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        if not project.resources:
            return []

        providers_used = set()
        for resource in project.resources.values():
            if resource.resource_type:
                provider = resource.resource_type.split("_")[0]
                providers_used.add(provider)

        providers_configured = set()
        for provider in project.providers.values():
            providers_configured.add(provider.name)

        # Also check terraform block for required_providers
        for tf_block in project.terraform_blocks.values():
            req_providers = tf_block.attributes.get("required_providers", {})
            if isinstance(req_providers, dict):
                providers_configured.update(req_providers.keys())

        missing = providers_used - providers_configured

        if missing:
            # Create issue on first resource using missing provider
            for name, resource in project.resources.items():
                if resource.resource_type:
                    provider = resource.resource_type.split("_")[0]
                    if provider in missing:
                        msg = f"Provider '{provider}' is used but not configured"
                        issues.append(self._create_issue(resource, message=msg))
                        missing.remove(provider)
                        if not missing:
                            break

        return issues


class CountAndForEachRule(TerraformRule):
    rule_id = "TF025"
    description = "Resource uses both 'count' and 'for_each'"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.ERROR
    suggestion = "Use either 'count' or 'for_each', not both."

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        for name, resource in project.resources.items():
            has_count = "count" in resource.attributes
            has_for_each = "for_each" in resource.attributes

            if has_count and has_for_each:
                msg = (
                    f"Resource '{resource.full_name}' uses both 'count' and 'for_each'"
                )
                issues.append(self._create_issue(resource, message=msg))

        return issues


class VariableValidationRule(TerraformRule):
    rule_id = "TF026"
    description = "Variable has type constraint but no validation rules"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.INFO
    suggestion = "Add validation rules to enforce constraints on variable values."

    SENSITIVE_TYPES = {"string", "list", "map", "object"}

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        for name, var in project.variables.items():
            if var.variable_type and var.variable_type in self.SENSITIVE_TYPES:
                validation = var.attributes.get("validation")
                if not validation:
                    msg = f"Variable '{var.full_name}' with type '{var.variable_type}' has no validation rules"
                    issues.append(
                        self._create_issue(
                            var, message=msg, severity=ValidationSeverity.INFO
                        )
                    )

        return issues


class OutputSensitiveRule(TerraformRule):
    rule_id = "TF027"
    description = "Output may contain sensitive data but is not marked sensitive"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.WARNING
    suggestion = "Mark outputs containing sensitive data with 'sensitive = true'."

    SENSITIVE_KEYWORDS = {"password", "secret", "token", "key", "private", "credential"}

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        for name, output in project.outputs.items():
            if output.sensitive:
                continue

            # Check if output name suggests sensitive data
            output_name_lower = output.name.lower()
            if any(keyword in output_name_lower for keyword in self.SENSITIVE_KEYWORDS):
                msg = f"Output '{output.full_name}' may contain sensitive data but is not marked sensitive"
                issues.append(self._create_issue(output, message=msg))

        return issues


class LocalValueComplexityRule(TerraformRule):
    rule_id = "TF028"
    description = "Local value has excessive complexity"
    category = ValidationCategory.BEST_PRACTICE
    severity = ValidationSeverity.INFO
    suggestion = (
        "Consider breaking down complex local values into multiple simpler ones."
    )

    MAX_NESTED_DEPTH = 5

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        for name, local in project.locals.items():
            depth = self._get_nesting_depth(local.attributes)
            if depth > self.MAX_NESTED_DEPTH:
                msg = f"Local value '{local.full_name}' has nesting depth of {depth}, consider simplifying"
                issues.append(self._create_issue(local, message=msg))

        return issues

    def _get_nesting_depth(self, obj: Any, current_depth: int = 0) -> int:
        if not isinstance(obj, (dict, list)):
            return current_depth

        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._get_nesting_depth(v, current_depth + 1) for v in obj.values()
            )

        if isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._get_nesting_depth(item, current_depth + 1) for item in obj)

        return current_depth


#
# === COST RULES ===
#
class UntaggedResourcesRule(TerraformRule):
    rule_id = "TF080"
    description = "Resource lacks cost allocation tags"
    category = ValidationCategory.COST
    severity = ValidationSeverity.WARNING
    suggestion = "Add cost allocation tags like 'Environment', 'Project', 'CostCenter' for better cost tracking."

    REQUIRED_COST_TAGS = {"Environment", "Project", "Owner", "CostCenter"}
    TAGGABLE_TYPES = {
        "aws_instance",
        "aws_db_instance",
        "aws_s3_bucket",
        "aws_ebs_volume",
        "aws_lambda_function",
        "aws_ecs_cluster",
        "aws_eks_cluster",
        "azurerm_virtual_machine",
        "azurerm_storage_account",
        "google_compute_instance",
        "google_storage_bucket",
    }

    def validate(self, project: TerraformProject) -> List[ValidationIssue]:
        issues = []

        for name, resource in project.resources.items():
            if resource.resource_type not in self.TAGGABLE_TYPES:
                continue

            tags = resource.attributes.get("tags", {})
            if not isinstance(tags, dict):
                continue

            # Check for at least one cost allocation tag
            tag_keys = set(tags.keys())
            missing_tags = self.REQUIRED_COST_TAGS - tag_keys

            if len(missing_tags) == len(self.REQUIRED_COST_TAGS):
                msg = f"Resource '{resource.full_name}' lacks cost allocation tags (consider: {', '.join(self.REQUIRED_COST_TAGS)})"
                issues.append(self._create_issue(resource, message=msg))

        return issues

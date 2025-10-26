import re
from typing import Dict, List, Optional, Set

from tfkit.analyzer.models import TerraformProject
from tfkit.validator.models import (
    ValidationCategory,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)


class TerraformValidator:
    """Validates Terraform configurations."""

    def __init__(self, strict: bool = False, ignore_rules: Optional[List[str]] = None):
        """
        Initialize validator.

        Args:
            strict: Enable strict validation mode
            ignore_rules: List of rule IDs to ignore
        """
        self.strict = strict
        self.ignore_rules = set(ignore_rules or [])
        self.result = ValidationResult(passed=[], warnings=[], errors=[], info=[])

    def validate(
        self,
        project: TerraformProject,
        check_syntax: bool = True,
        check_references: bool = True,
        check_best_practices: bool = False,
        check_security: bool = False,
    ) -> ValidationResult:
        """
        Run validation checks on Terraform project.

        Args:
            project: Terraform project to validate
            check_syntax: Perform syntax validation
            check_references: Validate resource references
            check_best_practices: Check best practices compliance
            check_security: Run security checks

        Returns:
            ValidationResult with all issues found
        """
        if check_syntax:
            self._validate_syntax(project)

        if check_references:
            self._validate_references(project)

        if check_best_practices:
            self._validate_best_practices(project)

        if check_security:
            self._validate_security(project)

        return self.result

    def _add_issue(self, issue: ValidationIssue):
        """Add issue to results if not ignored."""
        if issue.rule_id in self.ignore_rules:
            return

        if issue.severity == ValidationSeverity.ERROR:
            self.result.errors.append(issue)
        elif issue.severity == ValidationSeverity.WARNING:
            self.result.warnings.append(issue)
        else:
            self.result.info.append(issue)

    def _validate_syntax(self, project: TerraformProject):
        """Validate HCL syntax and structure."""
        checks_passed = []

        for name, resource in project.resources.items():
            if not resource.attributes:
                self._add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SYNTAX,
                        rule_id="TF001",
                        message="Resource has no configuration attributes",
                        file_path=resource.file_path,
                        line_number=resource.line_number,
                        resource_name=name,
                        suggestion="Add required configuration attributes to the resource block",
                    )
                )
            else:
                checks_passed.append(f"Resource {name} has valid configuration")

        for name, module in project.modules.items():
            if not module.attributes.get("source"):
                self._add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SYNTAX,
                        rule_id="TF002",
                        message="Module missing required 'source' attribute",
                        file_path=module.file_path,
                        line_number=module.line_number,
                        resource_name=name,
                        suggestion="Add 'source' attribute to module block",
                    )
                )
            else:
                checks_passed.append(f"Module {name} has valid source")

        # Check variable definitions
        for name, variable in project.variables.items():
            if not variable.attributes:
                self._add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.SYNTAX,
                        rule_id="TF003",
                        message="Variable has no type or description",
                        file_path=variable.file_path,
                        line_number=variable.line_number,
                        resource_name=name,
                        suggestion="Add 'type' and 'description' to variable definition",
                    )
                )
            else:
                checks_passed.append(f"Variable {name} is properly defined")

        if checks_passed:
            self.result.passed.append(
                f"Syntax validation passed ({len(checks_passed)} checks)"
            )

    def _validate_references(self, project: TerraformProject):
        """Validate resource and variable references."""
        checks_passed = []

        # Build set of all available references
        available_refs = set()
        available_refs.update(project.resources.keys())
        available_refs.update(project.data_sources.keys())
        available_refs.update(project.modules.keys())
        available_refs.update(project.variables.keys())
        available_refs.update(project.outputs.keys())

        # Check resource dependencies
        for name, resource in project.resources.items():
            for dep in resource.dependencies:
                # Clean up dependency reference
                dep_clean = self._normalize_reference(dep)

                if dep_clean and not self._reference_exists(dep_clean, available_refs):
                    self._add_issue(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category=ValidationCategory.REFERENCE,
                            rule_id="TF010",
                            message=f"Reference to undefined resource or variable: {dep}",
                            file_path=resource.file_path,
                            line_number=resource.line_number,
                            resource_name=name,
                            suggestion=f"Ensure {dep} is defined in your configuration",
                        )
                    )
                else:
                    checks_passed.append(f"{name} references are valid")

        # Check output dependencies
        for name, output in project.outputs.items():
            for dep in output.dependencies:
                dep_clean = self._normalize_reference(dep)

                if dep_clean and not self._reference_exists(dep_clean, available_refs):
                    self._add_issue(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category=ValidationCategory.REFERENCE,
                            rule_id="TF011",
                            message=f"Output references undefined resource: {dep}",
                            file_path=output.file_path,
                            line_number=output.line_number,
                            resource_name=name,
                            suggestion=f"Ensure {dep} is defined before using it in output",
                        )
                    )

        # Check for circular dependencies
        circular = self._detect_circular_dependencies(project)
        if circular:
            for cycle in circular:
                self._add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.REFERENCE,
                        rule_id="TF012",
                        message=f"Circular dependency detected: {' -> '.join(cycle)}",
                        file_path="<multiple>",
                        line_number=1,
                        suggestion="Refactor resources to break the circular dependency",
                    )
                )

        if checks_passed:
            self.result.passed.append(
                f"Reference validation passed ({len(checks_passed)} resources checked)"
            )

    def _validate_best_practices(self, project: TerraformProject):
        """Check best practices compliance."""
        checks_passed = []

        # Check for resource tagging
        untagged_resources = []
        for name, resource in project.resources.items():
            if self._should_have_tags(name):
                tags = resource.attributes.get("tags")
                if not tags:
                    untagged_resources.append(name)
                    self._add_issue(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category=ValidationCategory.BEST_PRACTICE,
                            rule_id="TF020",
                            message="Resource missing tags",
                            file_path=resource.file_path,
                            line_number=resource.line_number,
                            resource_name=name,
                            suggestion="Add tags for better resource management and cost tracking",
                        )
                    )
                else:
                    checks_passed.append(f"{name} has proper tags")

        # Check variable descriptions
        for name, variable in project.variables.items():
            attrs = variable.attributes
            if not attrs.get("description"):
                self._add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category=ValidationCategory.BEST_PRACTICE,
                        rule_id="TF021",
                        message="Variable missing description",
                        file_path=variable.file_path,
                        line_number=variable.line_number,
                        resource_name=name,
                        suggestion="Add description to document variable purpose",
                    )
                )
            else:
                checks_passed.append(f"{name} has description")

            # Check variable type definition
            if not attrs.get("type"):
                self._add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.BEST_PRACTICE,
                        rule_id="TF022",
                        message="Variable missing type constraint",
                        file_path=variable.file_path,
                        line_number=variable.line_number,
                        resource_name=name,
                        suggestion="Add type constraint for better validation",
                    )
                )

        # Check output descriptions
        for name, output in project.outputs.items():
            if not output.attributes.get("description"):
                self._add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category=ValidationCategory.BEST_PRACTICE,
                        rule_id="TF023",
                        message="Output missing description",
                        file_path=output.file_path,
                        line_number=output.line_number,
                        resource_name=name,
                        suggestion="Add description to document output purpose",
                    )
                )

        # Check naming conventions
        self._check_naming_conventions(project)

        if checks_passed:
            self.result.passed.append(
                f"Best practices validation completed ({len(checks_passed)} compliant)"
            )

    def _validate_security(self, project: TerraformProject):
        """Run security validation checks."""
        checks_passed = []

        for name, resource in project.resources.items():
            attrs = resource.attributes

            # Check AWS security groups
            if "aws_security_group" in name:
                self._check_security_group(name, resource, attrs)
                checks_passed.append(f"Security group {name} checked")

            # Check S3 buckets
            if "aws_s3_bucket" in name:
                self._check_s3_bucket(name, resource, attrs)
                checks_passed.append(f"S3 bucket {name} checked")

            # Check IAM policies
            if "aws_iam" in name and "policy" in name:
                self._check_iam_policy(name, resource, attrs)
                checks_passed.append(f"IAM policy {name} checked")

            # Check RDS instances
            if "aws_db_instance" in name or "aws_rds" in name:
                self._check_rds_instance(name, resource, attrs)
                checks_passed.append(f"RDS instance {name} checked")

            # Check for hardcoded secrets
            self._check_hardcoded_secrets(name, resource, attrs)

        if checks_passed:
            self.result.passed.append(
                f"Security validation completed ({len(checks_passed)} resources checked)"
            )

    def _check_security_group(self, name: str, resource, attrs: Dict):
        """Check security group configuration."""
        ingress_rules = attrs.get("ingress", [])
        if isinstance(ingress_rules, list):
            for rule in ingress_rules:
                if isinstance(rule, dict):
                    cidr_blocks = rule.get("cidr_blocks", [])
                    if "0.0.0.0/0" in cidr_blocks or "::/0" in cidr_blocks:
                        self._add_issue(
                            ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                category=ValidationCategory.SECURITY,
                                rule_id="TF030",
                                message="Security group allows unrestricted ingress (0.0.0.0/0)",
                                file_path=resource.file_path,
                                line_number=resource.line_number,
                                resource_name=name,
                                suggestion="Restrict ingress to specific IP ranges or use VPC security",
                            )
                        )

    def _check_s3_bucket(self, name: str, resource, attrs: Dict):
        """Check S3 bucket security configuration."""
        # Check for public access
        acl = attrs.get("acl")
        if acl in ["public-read", "public-read-write"]:
            self._add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SECURITY,
                    rule_id="TF031",
                    message="S3 bucket has public ACL",
                    file_path=resource.file_path,
                    line_number=resource.line_number,
                    resource_name=name,
                    suggestion="Use private ACL and configure bucket policies for controlled access",
                )
            )

        # Check for encryption
        server_side_encryption = attrs.get("server_side_encryption_configuration")
        if not server_side_encryption:
            self._add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.SECURITY,
                    rule_id="TF032",
                    message="S3 bucket encryption not configured",
                    file_path=resource.file_path,
                    line_number=resource.line_number,
                    resource_name=name,
                    suggestion="Enable server-side encryption for data at rest",
                )
            )

        # Check for versioning
        versioning = attrs.get("versioning")
        if not versioning or not versioning.get("enabled"):
            self._add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category=ValidationCategory.SECURITY,
                    rule_id="TF033",
                    message="S3 bucket versioning not enabled",
                    file_path=resource.file_path,
                    line_number=resource.line_number,
                    resource_name=name,
                    suggestion="Enable versioning for data protection and recovery",
                )
            )

    def _check_iam_policy(self, name: str, resource, attrs: Dict):
        """Check IAM policy for overly permissive permissions."""
        policy = attrs.get("policy")
        if policy and isinstance(policy, str):
            # Check for wildcard actions
            if '"Action": "*"' in policy or '"Action":"*"' in policy:
                self._add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SECURITY,
                        rule_id="TF034",
                        message="IAM policy allows all actions (*)",
                        file_path=resource.file_path,
                        line_number=resource.line_number,
                        resource_name=name,
                        suggestion="Use principle of least privilege and specify exact actions",
                    )
                )

            # Check for wildcard resources
            if '"Resource": "*"' in policy or '"Resource":"*"' in policy:
                self._add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.SECURITY,
                        rule_id="TF035",
                        message="IAM policy applies to all resources (*)",
                        file_path=resource.file_path,
                        line_number=resource.line_number,
                        resource_name=name,
                        suggestion="Limit policy to specific resources",
                    )
                )

    def _check_rds_instance(self, name: str, resource, attrs: Dict):
        """Check RDS instance security configuration."""
        # Check for public accessibility
        publicly_accessible = attrs.get("publicly_accessible")
        if publicly_accessible:
            self._add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SECURITY,
                    rule_id="TF036",
                    message="RDS instance is publicly accessible",
                    file_path=resource.file_path,
                    line_number=resource.line_number,
                    resource_name=name,
                    suggestion="Set publicly_accessible = false and use VPC for access",
                )
            )

        # Check for encryption
        storage_encrypted = attrs.get("storage_encrypted")
        if not storage_encrypted:
            self._add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.SECURITY,
                    rule_id="TF037",
                    message="RDS instance storage not encrypted",
                    file_path=resource.file_path,
                    line_number=resource.line_number,
                    resource_name=name,
                    suggestion="Enable storage_encrypted for data at rest protection",
                )
            )

    def _check_hardcoded_secrets(self, name: str, resource, attrs: Dict):
        """Check for hardcoded secrets in configuration."""
        attrs_str = str(attrs).lower()

        # Check for potential secrets
        secret_patterns = [
            (r"password\s*=\s*['\"](?!var\.|data\.)(.+)['\"]", "password"),
            (r"secret\s*=\s*['\"](?!var\.|data\.)(.+)['\"]", "secret"),
            (r"api[_-]?key\s*=\s*['\"](?!var\.|data\.)(.+)['\"]", "API key"),
            (r"access[_-]?key\s*=\s*['\"](?!var\.|data\.)(.+)['\"]", "access key"),
        ]

        for pattern, secret_type in secret_patterns:
            if re.search(pattern, attrs_str, re.IGNORECASE):
                self._add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SECURITY,
                        rule_id="TF038",
                        message=f"Potential hardcoded {secret_type} detected",
                        file_path=resource.file_path,
                        line_number=resource.line_number,
                        resource_name=name,
                        suggestion=f"Use variables or secret management service for {secret_type}",
                    )
                )

    def _check_naming_conventions(self, project: TerraformProject):
        """Check resource naming conventions."""
        for name, resource in project.resources.items():
            # Extract resource name (after the type)
            parts = name.split(".", 1)
            if len(parts) == 2:
                resource_name = parts[1]

                # Check snake_case convention
                if not re.match(r"^[a-z][a-z0-9_]*$", resource_name):
                    self._add_issue(
                        ValidationIssue(
                            severity=ValidationSeverity.INFO,
                            category=ValidationCategory.NAMING,
                            rule_id="TF040",
                            message="Resource name doesn't follow snake_case convention",
                            file_path=resource.file_path,
                            line_number=resource.line_number,
                            resource_name=name,
                            suggestion="Use lowercase letters, numbers, and underscores only",
                        )
                    )

    def _should_have_tags(self, resource_name: str) -> bool:
        """Determine if a resource should have tags."""
        taggable_resources = [
            "aws_instance",
            "aws_s3_bucket",
            "aws_vpc",
            "aws_subnet",
            "aws_security_group",
            "aws_db_instance",
            "aws_lambda_function",
            "aws_ecs_cluster",
            "aws_ecs_service",
            "aws_elasticache_cluster",
            "azure_virtual_machine",
            "azurerm_resource_group",
            "google_compute_instance",
        ]

        return any(tag_type in resource_name for tag_type in taggable_resources)

    def _normalize_reference(self, ref: str) -> str:
        """Normalize a reference for comparison."""
        # Remove attribute access
        if "." in ref:
            parts = ref.split(".")
            if len(parts) >= 2:
                # Keep only resource type and name
                return ".".join(parts[:2])
        return ref

    def _reference_exists(self, ref: str, available_refs: Set[str]) -> bool:
        """Check if a reference exists in available references."""
        if ref in available_refs:
            return True

        # Check partial matches for complex references
        for available in available_refs:
            if ref.startswith(available):
                return True

        return False

    def _detect_circular_dependencies(
        self, project: TerraformProject
    ) -> List[List[str]]:
        """Detect circular dependencies in the project."""
        # Build adjacency list
        graph = {}
        all_resources = {**project.resources, **project.modules}

        for name, resource in all_resources.items():
            graph[name] = [
                dep
                for dep in resource.dependencies
                if self._normalize_reference(dep) in all_resources
            ]

        # Find cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                neighbor_clean = self._normalize_reference(neighbor)
                if neighbor_clean not in visited:
                    if dfs(neighbor_clean, path.copy()):
                        return True
                elif neighbor_clean in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor_clean)
                    cycles.append(path[cycle_start:] + [neighbor_clean])
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

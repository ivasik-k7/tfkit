from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(Enum):
    """Categories of validation checks"""

    SYNTAX = "syntax"
    REFERENCES = "references"
    BEST_PRACTICES = "best_practices"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    NAMING = "naming"
    COST = "cost"


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""

    severity: ValidationSeverity
    category: ValidationCategory
    rule_id: str
    message: str
    file_path: str
    line_number: int
    resource_name: Optional[str] = None
    resource_type: Optional[str] = None
    suggestion: Optional[str] = None

    column_number: Optional[int] = None
    end_line_number: Optional[int] = None
    end_column_number: Optional[int] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary"""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "rule_id": self.rule_id,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "resource_name": self.resource_name,
            "resource_type": self.resource_type,
            "suggestion": self.suggestion,
            "column_number": self.column_number,
            "end_line_number": self.end_line_number,
            "end_column_number": self.end_column_number,
        }

    def __str__(self) -> str:
        """String representation of the issue."""
        location = f"{self.file_path}:{self.line_number}"
        resource = f" [{self.resource_name}]" if self.resource_name else ""
        return f"{self.severity.value.upper()}: {location}{resource} - {self.message}"


@dataclass
class ValidationResult:
    """Results from validation"""

    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    passed: List[str] = field(default_factory=list)  # List of passed rule IDs

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0

    @property
    def has_info(self) -> bool:
        """Check if there are any info messages"""
        return len(self.info) > 0

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)"""
        return not self.has_errors

    @property
    def total_issues(self) -> int:
        """Get total number of issues"""
        return len(self.errors) + len(self.warnings) + len(self.info)

    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics"""
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "info": len(self.info),
            "passed": len(self.passed),
            "total_checks": len(self.passed),
            "total_issues": self.total_issues,
        }

    def get_issues_by_category(self) -> Dict[ValidationCategory, List[ValidationIssue]]:
        """Group all issues by category"""
        issues_by_category: Dict[ValidationCategory, List[ValidationIssue]] = {}

        all_issues = self.errors + self.warnings + self.info
        for issue in all_issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)

        return issues_by_category

    def get_issues_by_severity(self) -> Dict[ValidationSeverity, List[ValidationIssue]]:
        """Group all issues by severity"""
        return {
            ValidationSeverity.ERROR: self.errors,
            ValidationSeverity.WARNING: self.warnings,
            ValidationSeverity.INFO: self.info,
        }

    def get_issues_by_file(self) -> Dict[str, List[ValidationIssue]]:
        """Group all issues by file path"""
        issues_by_file: Dict[str, List[ValidationIssue]] = {}

        all_issues = self.errors + self.warnings + self.info
        for issue in all_issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)

        return issues_by_file

    def filter_by_category(self, category: ValidationCategory) -> "ValidationResult":
        """Get a new ValidationResult with only issues from specified category"""
        result = ValidationResult()

        result.errors = [e for e in self.errors if e.category == category]
        result.warnings = [w for w in self.warnings if w.category == category]
        result.info = [i for i in self.info if i.category == category]
        result.passed = self.passed.copy()

        return result

    def filter_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get all issues of a specific severity"""
        if severity == ValidationSeverity.ERROR:
            return self.errors
        elif severity == ValidationSeverity.WARNING:
            return self.warnings
        elif severity == ValidationSeverity.INFO:
            return self.info
        return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "summary": self.get_summary(),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "info": [i.to_dict() for i in self.info],
            "passed": self.passed,
        }

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ValidationSeverity(Enum):
    """Validation issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(Enum):
    """Validation check categories."""

    SYNTAX = "syntax"
    REFERENCE = "reference"
    BEST_PRACTICE = "best_practice"
    SECURITY = "security"
    NAMING = "naming"
    DEPRECATION = "deprecation"
    PERFORMANCE = "performance"
    COST = "cost"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    severity: ValidationSeverity
    category: ValidationCategory
    rule_id: str
    message: str
    file_path: str
    line_number: int = 1
    resource_name: Optional[str] = None
    resource_type: Optional[str] = None
    suggestion: Optional[str] = None


def __str__(self) -> str:
    """String representation of the issue."""
    location = f"{self.file_path}:{self.line_number}"
    resource = f" [{self.resource_name}]" if self.resource_name else ""
    return f"{self.severity.value.upper()}: {location}{resource} - {self.message}"


@dataclass
class ValidationResult:
    """Results of validation checks."""

    passed: List[str]
    warnings: List[ValidationIssue]
    errors: List[ValidationIssue]
    info: List[ValidationIssue]

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    @property
    def total_issues(self) -> int:
        """Total number of issues."""
        return len(self.errors) + len(self.warnings) + len(self.info)

    def get_summary(self) -> Dict:
        """Get validation summary."""
        return {
            "total_checks": len(self.passed),
            "total_issues": self.total_issues,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "info": len(self.info),
        }

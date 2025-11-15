__version__ = "0.5.12"
__author__ = "Ivan Kovtun"
__email__ = "kovtun.ivan@proton.me"
__description__ = "Advanced Terraform Intelligence & Analysis Suite"
__url__ = "https://github.com/ivasik-k7/tfkit"
__license__ = "MIT"

from tfkit.analyzer.terraform_analyzer import TerraformAnalyzer
from tfkit.validator.validator import TerraformValidator
from tfkit.visualizer.generator import ReportGenerator

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "__url__",
    "__license__",
    "TerraformAnalyzer",
    "TerraformValidator",
    "ReportGenerator",
]

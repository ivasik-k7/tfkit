import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from tfkit.parser.models import (
    BlockParsingStrategy,
    SourceLocation,
    TerraformModule,
    TerraformObjectType,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ModuleParsingStrategy(BlockParsingStrategy):
    """
    Strategy for parsing 'module' blocks.

    Example Terraform modules:
        module "vpc" {
          source  = "terraform-aws-modules/vpc/aws"
          version = "~> 5.0"

          name = "my-vpc"
          cidr = "10.0.0.0/16"

          azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
          private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
          public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

          enable_nat_gateway = true
          enable_vpn_gateway = true

          tags = {
            Terraform   = "true"
            Environment = "dev"
          }
        }

        module "security_groups" {
          source = "./modules/security-groups"

          vpc_id = module.vpc.vpc_id
          ports  = [80, 443, 22]
        }

        module "eks" {
          source  = "terraform-aws-modules/eks/aws"
          version = "19.0.0"

          cluster_name    = "my-cluster"
          cluster_version = "1.27"

          vpc_id     = module.vpc.vpc_id
          subnet_ids = module.vpc.private_subnets

          depends_on = [module.vpc]
        }
    """

    def can_parse(self, block_type: str) -> bool:
        """This strategy only handles 'module' blocks."""
        return block_type == TerraformObjectType.MODULE.value

    def parse(
        self,
        block_type: str,
        block_name: str,
        block_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformModule"]:
        """
        Parse a module block.

        HCL2 structure: {"module_name": {attributes}}
        block_type = 'module'
        block_name = 'module' (usually)
        block_data = {"vpc": {"source": "...", "version": "...", "name": "..."}}
        """
        if not isinstance(block_data, dict):
            logger.error(
                f"Unexpected data type for 'module' block in {file_path}: {type(block_data)}"
            )
            return []

        if len(block_data) == 0:
            logger.error(f"Empty module block data in {file_path}")
            return []

        try:
            module_instance_name, module_config = next(iter(block_data.items()))
        except StopIteration:
            logger.error(f"Could not iterate over module block data in {file_path}")
            return []

        if not isinstance(module_config, dict):
            logger.warning(
                f"Module config for '{module_instance_name}' is not a dict. Treating attributes as empty."
            )
            module_config = {}

        # Extract meta-arguments and attributes
        source = module_config.get("source")
        version = module_config.get("version")
        depends_on = module_config.get("depends_on", [])
        count = module_config.get("count")
        for_each = module_config.get("for_each")
        providers = module_config.get("providers", {})

        # Handle depends_on which might be a list of references
        if isinstance(depends_on, list):
            # Extract module references from depends_on
            module_dependencies = []
            for dep in depends_on:
                if isinstance(dep, str) and dep.startswith("module."):
                    module_dependencies.append(dep.replace("module.", ""))
            depends_on = module_dependencies
        else:
            depends_on = []

        # Find source location for the module block
        search_pattern = f'module "{module_instance_name}"'

        source_location: SourceLocation = self.extract_source_location(
            file_path=file_path,
            block_name=search_pattern,
            raw_content=raw_content,
        )

        raw_code = self.extract_raw_code(raw_content, source_location)

        # Extract outputs consumed by this module (references to other modules)
        outputs_consumed = self._extract_consumed_outputs(module_config, raw_content)

        # Create the module object
        module_object = TerraformModule(
            object_type=TerraformObjectType.MODULE,
            name=module_instance_name,
            source_location=source_location,
            raw_code=raw_code,
            attributes=module_config,  # Pass all attributes for later processing
            source=source,
            version=version,
            depends_on=depends_on,
            count=count,
            for_each=for_each,
            providers=providers,
        )

        # Post-processing to handle complex source parsing
        self._enhance_module_source_analysis(module_object, raw_content)

        return [module_object]

    def _extract_consumed_outputs(
        self, module_config: Dict[str, Any], raw_content: str
    ) -> List[str]:
        """
        Extract outputs consumed from other modules in the form of module.xxx.yyy references.
        """
        outputs_consumed = []

        def extract_from_value(value: Any) -> List[str]:
            """Recursively extract module output references from any value."""
            references = []

            if isinstance(value, str):
                # Look for patterns like module.vpc.vpc_id, module.eks.cluster_arn, etc.
                import re

                module_ref_pattern = r"module\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)"
                matches = re.findall(module_ref_pattern, value)
                for module_name, output_name in matches:
                    references.append(f"{module_name}.{output_name}")

            elif isinstance(value, list):
                for item in value:
                    references.extend(extract_from_value(item))
            elif isinstance(value, dict):
                for item in value.values():
                    references.extend(extract_from_value(item))

            return references

        # Check all configuration values for module references
        for value in module_config.values():
            outputs_consumed.extend(extract_from_value(value))

        # Also parse raw content for any missed references
        import re

        module_ref_pattern = r"module\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)"
        raw_matches = re.findall(module_ref_pattern, raw_content)
        for module_name, output_name in raw_matches:
            ref = f"{module_name}.{output_name}"
            if ref not in outputs_consumed:
                outputs_consumed.append(ref)

        return list(set(outputs_consumed))  # Remove duplicates

    def _enhance_module_source_analysis(
        self, module: TerraformModule, raw_content: str
    ) -> None:
        """
        Enhance module analysis with additional source parsing from raw content.
        This handles complex source formats that might not be fully captured in the parsed HCL.
        """
        if not module.source:
            return

        # Handle git sources with refs (branches, tags, commits)
        if module.source.startswith("git::"):
            self._parse_git_source(module, raw_content)

        # Handle GitHub shorthand sources
        elif "github.com" in module.source and not module.source.startswith("git::"):
            self._parse_github_source(module)

        # Handle local modules with interpolation
        elif module.source_type.value == "local" and "${" in module.source:
            self._parse_interpolated_local_source(module, raw_content)

    def _parse_git_source(self, module: TerraformModule, raw_content: str) -> None:
        """Parse git sources to extract ref information."""
        try:
            # Extract git URL and ref from source
            source_parts = module.source.split("//")
            if len(source_parts) > 1:
                git_url_part = source_parts[1]

                # Look for ?ref= parameter in raw content
                import re

                ref_pattern = r'ref\s*=\s*"([^"]+)"'
                ref_matches = re.findall(ref_pattern, raw_content)
                if ref_matches:
                    module.version = ref_matches[0]  # Use ref as version

        except Exception as e:
            logger.debug(f"Error parsing git source for module {module.name}: {e}")

    def _parse_github_source(self, module: TerraformModule) -> None:
        """Parse GitHub shorthand sources."""
        try:
            # Handle github.com/owner/repo//path?ref=version format
            if "?" in module.source:
                base_source, query = module.source.split("?", 1)
                module.source = base_source
                # Extract ref from query parameters if present
                if "ref=" in query:
                    import urllib.parse

                    params = urllib.parse.parse_qs(query)
                    if "ref" in params:
                        module.version = params["ref"][0]
        except Exception as e:
            logger.debug(f"Error parsing GitHub source for module {module.name}: {e}")

    def _parse_interpolated_local_source(
        self, module: TerraformModule, raw_content: str
    ) -> None:
        """Handle local sources with variable interpolation."""
        try:
            # Look for the actual path in the raw content
            import re

            source_pattern = r'source\s*=\s*"([^"]*\$[^"]*)"'
            matches = re.findall(source_pattern, raw_content)
            if matches:
                # Try to extract the base path before interpolation
                interpolated_source = matches[0]
                # Remove interpolation parts to get the base path
                base_path = re.sub(r"\$\{[^}]+\}", "", interpolated_source)
                base_path = base_path.replace('"', "").strip()
                if base_path and (
                    base_path.startswith("./") or base_path.startswith("../")
                ):
                    module.source = base_path
        except Exception as e:
            logger.debug(
                f"Error parsing interpolated source for module {module.name}: {e}"
            )

    def parse_multiple_blocks(
        self,
        block_type: str,
        blocks_data: Dict[str, Any],
        file_path: Path,
        raw_content: str,
    ) -> List["TerraformModule"]:
        """
        Parse multiple module blocks from a file.

        Useful when the HCL structure contains multiple module blocks at the same level.
        """
        modules = []

        if not isinstance(blocks_data, dict):
            logger.error(
                f"Unexpected data type for multiple module blocks in {file_path}"
            )
            return modules

        for module_instance_name, module_config in blocks_data.items():
            if not isinstance(module_config, dict):
                logger.warning(
                    f"Skipping invalid module config for '{module_instance_name}'"
                )
                continue

            # Create a single block data structure for the parse method
            single_block_data = {module_instance_name: module_config}

            try:
                parsed_modules = self.parse(
                    block_type=block_type,
                    block_name=module_instance_name,
                    block_data=single_block_data,
                    file_path=file_path,
                    raw_content=raw_content,
                )
                modules.extend(parsed_modules)
            except Exception as e:
                logger.error(
                    f"Failed to parse module '{module_instance_name}' in {file_path}: {e}"
                )
                continue

        return modules

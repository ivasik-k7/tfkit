"""
Main Terraform parser with strategy pattern for different object types.
"""

import fnmatch
import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

import hcl2
import lark

from tfkit.parser.models import BlockParsingStrategy, TerraformCatalog
from tfkit.parser.strategies import (
    DataSourceParsingStrategy,
    LocalsParsingStrategy,
    ModuleParsingStrategy,
    MovedParsingStrategy,
    OutputParsingStrategy,
    ProviderParsingStrategy,
    ResourceParsingStrategy,
    TerraformRootConfigParsingStrategy,
    VariableParsingStrategy,
)

ParsedTerraformModule = TerraformCatalog

logger = logging.getLogger(__name__)


@dataclass
class ParsingConfig:
    cache_dir: Path = Path("./.tfcache")
    enable_cache: bool = True
    max_workers: int = 4
    parse_json: bool = True
    recursive: bool = True
    follow_symlinks: bool = False
    max_file_size_mb: int = 50
    ignore_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ParsingConfig":
        return ParsingConfig(**data)


class FileCache:
    """Cache for parsed file results with content-based invalidation."""

    def __init__(self, cache_dir: Path, enabled: bool = True):
        self.cache_dir = cache_dir
        self.enabled = enabled
        self._lock = Lock()

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file content for cache key."""
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _get_cache_path(self, file_path: Path, file_hash: str) -> Path:
        """Get cache file path."""
        path_hash = hashlib.md5(str(file_path.absolute()).encode()).hexdigest()[:8]
        return self.cache_dir / f"{path_hash}_{file_hash}.json"

    def get(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get cached parsed result if valid."""
        if not self.enabled:
            return None

        try:
            file_hash = self._get_file_hash(file_path)
            cache_path = self._get_cache_path(file_path, file_hash)

            if cache_path.exists():
                with open(cache_path) as f:
                    cached_data = json.load(f)
                    logger.debug(f"Cache hit for {file_path}")
                    return cached_data
        except Exception as e:
            logger.warning(f"Cache read error for {file_path}: {e}")

        return None

    def set(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Cache parsed result."""
        if not self.enabled:
            return

        try:
            with self._lock:
                file_hash = self._get_file_hash(file_path)
                cache_path = self._get_cache_path(file_path, file_hash)

                with open(cache_path, "w") as f:
                    json.dump(data, f, default=str)
                    logger.debug(f"Cached result for {file_path}")
        except Exception as e:
            logger.warning(f"Cache write error for {file_path}: {e}")

    def clear(self) -> None:
        """Clear all cached files."""
        if not self.enabled:
            return

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")


class TerraformParser:
    """
    Main parser class that orchestrates parsing of Terraform files.
    Uses strategy pattern to delegate parsing to specific strategies.
    Enhanced with caching, parallel processing, and optimizations.
    """

    def __init__(self, config: Optional[ParsingConfig] = None):
        self.config = config or ParsingConfig()
        self.strategies: List[BlockParsingStrategy] = []
        self.cache = FileCache(
            cache_dir=self.config.cache_dir, enabled=self.config.enable_cache
        )
        self._strategy_map: Dict[str, BlockParsingStrategy] = {}
        self._register_default_strategies()

    # ------------------------------------------------------------------
    # Strategy registration
    # ------------------------------------------------------------------
    def _register_default_strategies(self):
        """Register all default parsing strategies."""
        self.strategies.extend(
            [
                VariableParsingStrategy(),
                OutputParsingStrategy(),
                TerraformRootConfigParsingStrategy(),
                # Uncomment when the other strategies are ready:
                ResourceParsingStrategy(),
                DataSourceParsingStrategy(),
                LocalsParsingStrategy(),
                ProviderParsingStrategy(),
                ModuleParsingStrategy(),
                MovedParsingStrategy(),
            ]
        )
        self._build_strategy_map()

    def _build_strategy_map(self):
        """Build a map of block types to strategies for fast lookup."""
        self._strategy_map.clear()
        for strategy in self.strategies:
            for block_type in (
                "resource",
                "data",
                "variable",
                "output",
                "locals",
                "provider",
                "terraform",
                "module",
                "moved",
            ):
                if strategy.can_parse(block_type):
                    self._strategy_map[block_type] = strategy

    def register_strategy(self, strategy: BlockParsingStrategy) -> None:
        """Register a custom parsing strategy."""
        self.strategies.append(strategy)
        self._build_strategy_map()

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------
    def parse_directory(
        self,
        directory_path: Path,
        config: Optional[ParsingConfig] = None,
    ) -> TerraformCatalog:
        """
        Parse all Terraform files in a directory with optimizations.

        Returns:
            TerraformCatalog containing all parsed objects
        """
        config = config or self.config

        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")

        catalog = TerraformCatalog(root_path=directory_path)

        tf_files = self._find_terraform_files(directory_path, config)
        if not tf_files:
            logger.warning(f"No Terraform files found in {directory_path}")
            return catalog

        logger.info(f"Found {len(tf_files)} Terraform files to parse")

        if config.max_workers > 1 and len(tf_files) > 1:
            self._parse_parallel(tf_files, catalog, config)
        else:
            self._parse_sequential(tf_files, catalog)

        return catalog

    def parse_file(self, file_path: Path) -> TerraformCatalog:
        """
        Parse a single Terraform file.

        Returns:
            TerraformCatalog containing parsed objects
        """
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        catalog = TerraformCatalog(root_path=file_path.parent)
        self._parse_file(file_path, catalog)
        return catalog

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------
    def _find_terraform_files(
        self,
        directory: Path,
        config: ParsingConfig,
    ) -> List[Path]:
        patterns = ["*.tf"]
        if config.parse_json:
            patterns.append("*.tf.json")

        files: List[Path] = []
        max_size_bytes = config.max_file_size_mb * 1024 * 1024

        for pattern in patterns:
            file_iter = (
                directory.rglob(pattern)
                if config.recursive
                else directory.glob(pattern)
            )
            for file_path in file_iter:
                if self._should_ignore(file_path, config.ignore_patterns):
                    logger.debug(f"Ignoring {file_path} (matches ignore pattern)")
                    continue
                if not config.follow_symlinks and file_path.is_symlink():
                    logger.debug(f"Ignoring symlink {file_path}")
                    continue
                try:
                    if file_path.stat().st_size > max_size_bytes:
                        logger.warning(
                            f"Skipping {file_path} (size > {config.max_file_size_mb}MB)"
                        )
                        continue
                except OSError as e:
                    logger.warning(f"Cannot stat {file_path}: {e}")
                    continue
                files.append(file_path)

        return sorted(files)

    def _should_ignore(self, file_path: Path, ignore_patterns: List[str]) -> bool:
        path_str = str(file_path)
        return any(fnmatch.fnmatch(path_str, pat) for pat in ignore_patterns)

    # ------------------------------------------------------------------
    # Sequential / parallel parsing
    # ------------------------------------------------------------------
    def _parse_sequential(
        self,
        tf_files: List[Path],
        catalog: TerraformCatalog,
    ) -> None:
        for tf_file in tf_files:
            try:
                self._parse_file(tf_file, catalog)
            except Exception as e:
                err = f"Error parsing {tf_file}: {e}"
                catalog.errors.append(err)
                logger.error(err, exc_info=True)

    def _parse_parallel(
        self,
        tf_files: List[Path],
        catalog: TerraformCatalog,
        config: ParsingConfig,
    ) -> None:
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            future_to_file = {
                executor.submit(self._parse_file_isolated, tf_file): tf_file
                for tf_file in tf_files
            }
            for future in as_completed(future_to_file):
                tf_file = future_to_file[future]
                try:
                    file_catalog = future.result()
                    self._merge_results(catalog, file_catalog)
                except Exception as e:
                    err = f"Error parsing {tf_file}: {e}"
                    catalog.errors.append(err)
                    logger.error(err, exc_info=True)

    def _parse_file_isolated(self, file_path: Path) -> TerraformCatalog:
        """Parse a file in isolation (used by parallel workers)."""
        catalog = TerraformCatalog(root_path=file_path.parent)
        self._parse_file(file_path, catalog)
        return catalog

    # ------------------------------------------------------------------
    # Result merging
    # ------------------------------------------------------------------
    def _merge_results(
        self,
        target: TerraformCatalog,
        source: TerraformCatalog,
    ) -> None:
        """Append everything from *source* into *target*."""
        target.resources.extend(source.resources)
        target.data_sources.extend(source.data_sources)
        target.variables.extend(source.variables)
        target.outputs.extend(source.outputs)
        target.locals.extend(source.locals)
        target.providers.extend(source.providers)
        target.terraform_blocks.extend(source.terraform_blocks)
        target.modules.extend(source.modules)
        target.moved_blocks.extend(source.moved_blocks)
        target.errors.extend(source.errors)

        target._address_map.update(source._address_map)

    # ------------------------------------------------------------------
    # Core file parsing
    # ------------------------------------------------------------------
    def _parse_file(
        self,
        file_path: Path,
        catalog: TerraformCatalog,
    ) -> None:
        logger.debug(f"Parsing {file_path}")

        # ---------- CACHE ----------
        cached = self.cache.get(file_path)
        if cached is not None:
            try:
                self._restore_from_cache(cached, catalog, file_path)
                return
            except Exception as e:
                logger.warning(f"Cache restore failed for {file_path}: {e}")

        # ---------- READ ----------
        try:
            with open(file_path, encoding="utf-8") as f:
                raw_content = f.read()
        except Exception as e:
            err = f"Error reading file {file_path}: {e}"
            catalog.errors.append(err)
            logger.error(err, exc_info=True)
            return

        # ---------- PARSE ----------
        if file_path.suffix == ".json":
            parsed_hcl = self._parse_json_file(raw_content, file_path, catalog)
        else:
            parsed_hcl = self._parse_hcl_file(raw_content, file_path, catalog)

        if parsed_hcl is None:
            return

        # ---------- CACHE RESULT ----------
        self.cache.set(
            file_path, {"parsed_hcl": parsed_hcl, "raw_content": raw_content}
        )

        # ---------- PROCESS BLOCKS ----------
        self._process_blocks(parsed_hcl, file_path, raw_content, catalog)

    def _process_blocks(
        self,
        parsed_hcl: Dict[str, Any],
        file_path: Path,
        raw_content: str,
        catalog: TerraformCatalog,
    ) -> None:
        """Process all blocks from parsed HCL."""
        for block_type, block_list in parsed_hcl.items():
            strategy = self._find_strategy_optimized(block_type)
            if not strategy:
                logger.debug(
                    f"No strategy for block type '{block_type}' in {file_path}"
                )
                continue

            # HCL2 returns blocks as a list of dictionaries
            if not isinstance(block_list, list):
                block_list = [block_list]

            for block_item in block_list:
                try:
                    # Extract block name based on block type
                    block_name = self._extract_block_name(block_type, block_item)

                    # Parse the block
                    objects = strategy.parse(
                        block_type=block_type,
                        block_name=block_name,
                        block_data=block_item,
                        file_path=file_path,
                        raw_content=raw_content,
                    )

                    # Add parsed objects to catalog
                    for obj in objects:
                        if obj.validate():
                            catalog.add_object(obj)
                        else:
                            err = (
                                f"Validation failed for {obj.object_type.value} "
                                f"'{obj.name}' in {file_path}"
                            )
                            catalog.errors.append(err)
                            logger.warning(err)
                except Exception as e:
                    err = f"Error parsing {block_type} in {file_path}: {e}"
                    catalog.errors.append(err)
                    logger.error(err, exc_info=True)

    def _extract_block_name(self, block_type: str, block_item: Dict[str, Any]) -> str:
        """Extract the name of a block from its data."""
        # For variables and outputs, the key is the name
        if block_type in ("variable", "output"):
            # HCL2 structure: {"variable": [{"var_name": {...}}]}
            if isinstance(block_item, dict) and len(block_item) > 0:
                return list(block_item.keys())[0]

        # For resources and data sources: {"resource": [{"aws_instance": {"my_instance": {...}}}]}
        elif block_type in ("resource", "data"):
            if isinstance(block_item, dict) and len(block_item) > 0:
                resource_type = list(block_item.keys())[0]
                resource_data = block_item[resource_type]
                if isinstance(resource_data, dict) and len(resource_data) > 0:
                    return list(resource_data.keys())[0]

        # For modules: {"module": [{"module_name": {...}}]}
        elif block_type == "module":
            if isinstance(block_item, dict) and len(block_item) > 0:
                return list(block_item.keys())[0]

        # For terraform, locals, provider blocks, use block type as name
        elif block_type in ("terraform", "locals", "provider"):
            return block_type

        return block_type

    # ------------------------------------------------------------------
    # HCL / JSON parsers
    # ------------------------------------------------------------------
    def _parse_hcl_file(
        self,
        raw_content: str,
        file_path: Path,
        catalog: TerraformCatalog,
    ) -> Optional[Dict[str, Any]]:
        try:
            return hcl2.loads(raw_content)
        except lark.LarkError as e:
            err = f"HCL parsing error in {file_path}: {e}"
            catalog.errors.append(err)
            logger.error(err)
            return None

    def _parse_json_file(
        self,
        raw_content: str,
        file_path: Path,
        catalog: TerraformCatalog,
    ) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(raw_content)
        except json.JSONDecodeError as e:
            err = f"JSON parsing error in {file_path}: {e}"
            catalog.errors.append(err)
            logger.error(err)
            return None

    # ------------------------------------------------------------------
    # Strategy lookup
    # ------------------------------------------------------------------
    def _find_strategy_optimized(
        self, block_type: str
    ) -> Optional[BlockParsingStrategy]:
        strategy = self._strategy_map.get(block_type)
        if strategy:
            return strategy
        for s in self.strategies:
            if s.can_parse(block_type):
                return s
        return None

    # ------------------------------------------------------------------
    # Cache restoration
    # ------------------------------------------------------------------
    def _restore_from_cache(
        self,
        cached_data: Dict[str, Any],
        catalog: TerraformCatalog,
        file_path: Path,
    ) -> None:
        """Restore parsed objects from cache."""
        parsed_hcl = cached_data.get("parsed_hcl")
        raw_content = cached_data.get("raw_content", "")

        if parsed_hcl is None:
            raise ValueError(f"Invalid cache data for {file_path}")

        self._process_blocks(parsed_hcl, file_path, raw_content, catalog)

    # ------------------------------------------------------------------
    # Cache control
    # ------------------------------------------------------------------
    def clear_cache(self) -> None:
        """Clear the parser cache."""
        self.cache.clear()

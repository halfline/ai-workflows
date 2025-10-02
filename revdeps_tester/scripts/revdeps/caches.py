import logging
from typing import Dict, List, Any

class SourcePackageCache:
    """
    Caches source package mappings for performance optimization.

    This class handles the caching of binary package to source package mappings
    to avoid repeated repoquery calls for the same package.
    """

    def __init__(self):
        self._cache: Dict[str, str] = {}

    def get(self, package_name: str) -> str | None:
        """
        Get a cached source package name.

        Args:
            package_name: The binary package name

        Returns:
            The cached source package name, None if not cached, or '' if package not found
        """
        return self._cache.get(package_name)

    def set(self, package_name: str, source_package_name: str | None) -> None:
        """
        Cache a source package mapping.

        Args:
            package_name: The binary package name
            source_package_name: The source package name, or '' if package not found
        """
        self._cache[package_name] = source_package_name
        if source_package_name == '':
            logging.debug(f"   Cached package not found: {package_name} → not found")
        else:
            logging.debug(f"   Cached source package mapping: {package_name} → {source_package_name}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        found_count = sum(1 for result in self._cache.values() if result is not None)
        not_found_count = len(self._cache) - found_count
        return {
            "cache_size": len(self._cache),
            "found_count": found_count,
            "not_found_count": not_found_count,
            "cached_packages": list(sorted(self._cache.keys())),
        }


class FilterCache:
    """
    Caches filter command results for performance optimization.

    This class handles the caching of filter command results to avoid running
    the same filter command multiple times for the same package.
    """

    def __init__(self):
        self._cache: Dict[str, bool] = {}

    def get(self, package_name: str) -> bool | None:
        """
        Get a cached filter result.

        Args:
            package_name: The package name

        Returns:
            The cached filter result (True if package passed filter, False if failed), or None if not cached
        """
        return self._cache.get(package_name)

    def set(self, package_name: str, passed_filter: bool) -> None:
        """
        Cache a filter result.

        Args:
            package_name: The package name
            passed_filter: Whether the package passed the filter (True) or failed (False)
        """
        self._cache[package_name] = passed_filter
        logging.debug(f"   Cached filter result: {package_name} → {'pass' if passed_filter else 'fail'}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        passed_count = sum(1 for result in self._cache.values() if result)
        failed_count = len(self._cache) - passed_count
        return {
            "cache_size": len(self._cache),
            "passed_count": passed_count,
            "failed_count": failed_count,
            "cached_packages": list(sorted(self._cache.keys())),
        }


class DependencyCache:
    """
    Caches dependency query results for performance optimization.

    This class handles the caching of dnf repoquery --whatdepends results to avoid
    repeated calls for the same package. It also tracks whether the cached results
    are partial (limited by max_results) or complete.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, package_name: str) -> List[str] | None:
        """
        Get cached dependencies for a package.

        Args:
            package_name: The package name

        Returns:
            The cached list of dependent packages, or None if not cached
        """
        entry = self._cache.get(package_name)
        if entry is not None:
            return entry["dependents"]
        return None

    def has(self, package_name: str) -> bool:
        """
        Check if a package has any cached results (partial or complete).

        Args:
            package_name: The package name

        Returns:
            True if the package has cached results, False otherwise
        """
        return package_name in self._cache

    def has_all(self, package_name: str) -> bool:
        """
        Check if a package has complete (non-partial) cached results.

        Args:
            package_name: The package name

        Returns:
            True if the package has complete cached results, False otherwise
        """
        entry = self._cache.get(package_name)
        if entry is not None:
            return not entry["partial"]
        return False

    def set(self, package_name: str, dependents: List[str], partial: bool = False) -> None:
        """
        Cache dependency results for a package.

        Args:
            package_name: The package name
            dependents: List of dependent package names
            partial: Whether the results are partial (limited by max_results)
        """
        self._cache[package_name] = {
            "dependents": dependents,
            "partial": partial
        }
        partial_info = " (partial)" if partial else ""
        logging.debug(f"   Cached dependency results: {package_name} → {len(dependents)} dependents{partial_info}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        total_dependents = sum(len(entry["dependents"]) for entry in self._cache.values())
        partial_count = sum(1 for entry in self._cache.values() if entry["partial"])
        complete_count = len(self._cache) - partial_count
        return {
            "cache_size": len(self._cache),
            "total_dependents": total_dependents,
            "complete_count": complete_count,
            "partial_count": partial_count,
            "cached_packages": list(sorted(self._cache.keys())),
        }
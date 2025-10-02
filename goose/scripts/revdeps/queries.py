import logging
import re
import subprocess
import importlib
from typing import Dict, List, Set, Generator, Any

from revdeps.metrics import RepoQueryMetrics
from revdeps.caches import SourcePackageCache, FilterCache, DependencyCache
from revdeps.errors import RepoQueryError, PackageNotFoundError


def generate_direct_dependents(
        package_name: str,
        repository_paths: Dict[str, str],
        metrics: RepoQueryMetrics,
        dependency_cache: DependencyCache,
        verbose: bool = False,
        cache_only: bool = False,
        max_results: int | None = None
    ) -> Generator[str, None, None]:
    """
    Generator that yields direct dependents one at a time.
    """
    logging.debug(f"\n🔍 Finding direct dependents for package: {package_name}")

    if (not cache_only and dependency_cache.has_all(package_name)) or (cache_only and dependency_cache.has(package_name)):
        cached_dependents = dependency_cache.get(package_name)
        logging.debug(f"📋 Dependency cache hit: Dependents for {package_name} → {len(cached_dependents)} dependents")
        count = 0
        for dependent_name in cached_dependents:
            if max_results is not None and count >= max_results:
                break
            yield dependent_name
            count += 1
        return

    if cache_only:
        logging.debug(f"📋 CACHE ONLY MODE: No sufficient cached dependents for {package_name}, skipping repoquery call")
        return

    metrics.log_call("dnf repoquery --whatdepends", package_name)
    try:
        pkg = importlib.import_module('revdeps')
        stdout_content = pkg.dnf(f"repoquery --whatdepends {package_name} --qf '%{{name}}\\n'", repository_paths, verbose)
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.strip() if error.stderr else "Unknown error"
        raise RepoQueryError(
            f"Failed to query reverse dependencies for {package_name!r}: {stderr}"
        )

    seen: Set[str] = set()
    dependents_found = 0
    dependents_list: List[str] = []
    is_partial = False
    count = 0

    for line in stdout_content.splitlines():
        if max_results is not None and count > max_results:
            is_partial = True
            break

        dependent_name = line.strip()
        if dependent_name and dependent_name not in seen:
            seen.add(dependent_name)
            dependents_found += 1
            dependents_list.append(dependent_name)
            logging.debug(f"\n   Found dependent: {dependent_name}")

            if max_results is None or count <= max_results:
                dependency_cache.set(package_name, dependents_list, partial=True)
                yield dependent_name
                count += 1

    dependency_cache.set(package_name, dependents_list, is_partial)
    logging.debug(f"\n   Total direct dependents found for {package_name}: {len(dependents_list)} ({'partial' if is_partial else 'complete'})")


def query_source_package(
        package_name: str,
        repository_paths: Dict[str, str],
        metrics: RepoQueryMetrics,
        source_cache: SourcePackageCache,
        verbose: bool = False,
        allow_missing: bool = False
    ) -> str:
    """
    Query the source package name for a given binary package.
    """

    cached_source_package = source_cache.get(package_name)
    if cached_source_package == '' and not allow_missing:
        logging.debug(f"\n📋 Source cache hit: Package {package_name} → not found")
        raise PackageNotFoundError(package_name)

    if cached_source_package:
        logging.debug(f"\n📋 Source cache hit: Source package for {package_name} → {cached_source_package}")
        return cached_source_package

    logging.debug(f"\n🔍 Querying source package for binary package: {package_name}")

    metrics.log_call("dnf repoquery --qf '%{sourcerpm}'", package_name)
    try:
        pkg = importlib.import_module('revdeps')
        stdout_content = pkg.dnf(f"repoquery {package_name} --qf '%{{sourcerpm}}\\n'", repository_paths, verbose)
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.strip() if error.stderr else "Unknown error"
        raise RepoQueryError(
            f"Failed to query source package for {package_name!r}: {stderr}"
        )

    source_rpm = stdout_content.strip()
    if not source_rpm:
        source_cache.set(package_name, '')
        if allow_missing:
            logging.debug(f"   Package {package_name} not found, but continuing due to --allow-missing")
            return ''
        raise PackageNotFoundError(package_name)

    m = re.match(r'^(?P<name>.*)-[^-]+-[^-]+\.src\.rpm$', source_rpm)
    if not m:
        raise RepoQueryError(
            f"Unexpected source-RPM format for {package_name!r}: {source_rpm!r}"
        )

    source_package_name = m.group("name")
    logging.debug(f"\n   Source package for {package_name}: {source_package_name}")

    source_cache.set(package_name, source_package_name)

    return source_package_name


def query_package_description(
        package_name: str,
        repository_paths: Dict[str, str],
        metrics: RepoQueryMetrics,
        verbose: bool = False
    ) -> str:
    """
    Query the description for a given package.
    """

    logging.debug(f"\n🔍 Querying description for package: {package_name}")

    metrics.log_call("dnf repoquery --qf '%{description}'", package_name)
    try:
        pkg = importlib.import_module('revdeps')
        stdout_content = pkg.dnf(f"repoquery {package_name} --qf %{{description}}", repository_paths, verbose)
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.strip() if error.stderr else "Unknown error"
        raise RepoQueryError(
            f"Failed to query description for {package_name!r}: {stderr}"
        )

    description = stdout_content.strip()
    if description:
        description = " ".join(description.splitlines())

    logging.debug(f"\n   Description for {package_name}: {description}")

    return description


def convert_to_source_packages(
        dependents: Generator[str, None, None],
        repository_paths: Dict[str, str],
        metrics: RepoQueryMetrics,
        source_cache: SourcePackageCache,
        filter_cache: FilterCache,
        max_results: int | None = None,
        verbose: bool = False,
        filter_command: str | None = None,
        allow_missing: bool = False
    ) -> Generator[str, None, None]:
    """
    Generator that converts a stream of binary package names into source package names.
    """
    logging.debug("🔄 Converting binary packages to source packages")

    pkg = importlib.import_module('revdeps')

    source_packages: Set[str] = set()
    converted_count = 0

    for package in dependents:
        if max_results is not None and converted_count >= max_results:
            logging.debug(f"Reached max_results={max_results}, stopping conversion")
            break

        logging.debug(f"   Converting binary package: {package}")
        source_package = pkg.query_source_package(
            package, repository_paths, metrics, source_cache, verbose, allow_missing
        )

        if not source_package:
            logging.debug(f"   Skipping binary package {package} (no source package found)")
            continue

        if source_package not in source_packages:
            source_packages.add(source_package)

            if filter_command:
                if not pkg.run_filter_command(source_package, filter_command, metrics, filter_cache, verbose):
                    logging.debug(f"   Skipping source package {source_package} due to filter command")
                    continue

            converted_count += 1
            logging.debug(f"   New source package found: {source_package}")
            yield source_package
        else:
            logging.debug(f"   Source package already seen: {source_package}")

    logging.debug(f"   Total unique source packages converted: {converted_count}")
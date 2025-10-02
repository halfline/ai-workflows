import logging
from collections import deque
from typing import Dict, List, Set, Any
import importlib

from revdeps.metrics import RepoQueryMetrics
from revdeps.caches import SourcePackageCache, FilterCache, DependencyCache
from revdeps.errors import NoDependentsFoundError


def compute_transitive_closure(
        root_package: str,
        dependents_map: Dict[str, Dict[str, Any]],
        max_results: int | None = None,
        filter_function = None,
    ) -> Dict[str, Dict[str, Any]]:
    """
    Compute the transitive closure of the dependency graph.
    """
    graph: Dict[str, Dict[str, Any]] = {}

    max_root_dependents = max_results - 1 if max_results is not None else None

    for package, entry in dependents_map.items():
        known_packages: Set[str] = set()
        transitive_dependents: List[str] = []
        queue = deque(entry["dependents"])
        is_partial = entry["partial"]

        root_hit_max_dependents = False

        while queue:
            dependent = queue.popleft()

            if dependent in known_packages:
                continue

            if package == root_package and max_root_dependents is not None and len(transitive_dependents) >= max_root_dependents:
                root_hit_max_dependents = True

            if package != root_package or not root_hit_max_dependents:
                known_packages.add(dependent)

                if filter_function is None or filter_function(dependent, transitive_dependents):
                    transitive_dependents.append(dependent)

            if dependent in dependents_map:
                dependent_entry = dependents_map[dependent]
                if dependent_entry["partial"]:
                    is_partial = True

                queue.extend(dependent_entry["dependents"])

            if root_hit_max_dependents:
                is_partial = bool(queue)
                break

        if not max_results or len(graph.keys()) < max_results:
            graph[package] = {
                "dependents": transitive_dependents,
                "partial": is_partial
            }

    return graph


def build_dependents_list(
        package_name: str,
        repository_paths: Dict[str, str],
        show_source_packages: bool,
        source_cache: SourcePackageCache,
        metrics: RepoQueryMetrics,
        filter_cache: FilterCache,
        dependency_cache: DependencyCache,
        max_results: int | None = None,
        verbose: bool = False,
        keep_cycles: bool = False,
        filter_command: str | None = None,
        allow_missing: bool = False
    ) -> List[str]:
    """
    Build a list of dependents for a given package.
    """
    logging.debug(f"🔄 Building dependents list for: {package_name}")
    logging.debug(f"   Show source packages: {show_source_packages}")
    logging.debug(f"   Max results: {max_results}")
    logging.debug(f"   Filter command: {filter_command}")

    pkg = importlib.import_module('revdeps')
    dependents = pkg.generate_direct_dependents(package_name, repository_paths, metrics, dependency_cache, verbose, cache_only=False)

    if show_source_packages:
        dependents = pkg.convert_to_source_packages(
            dependents, repository_paths, metrics, source_cache, filter_cache,
            max_results, verbose, filter_command, allow_missing
        )

    collected_packages: List[str] = []
    discovered_count = 0
    is_partial = False
    for dependent_package in dependents:
        if max_results is not None and discovered_count >= max_results:
            is_partial = True
            break

        if not keep_cycles and package_name == dependent_package:
            continue

        if filter_command:
            if not pkg.run_filter_command(dependent_package, filter_command, metrics, filter_cache, verbose):
                logging.debug(f"   Skipping dependent package {dependent_package} due to filter command")
                continue

        discovered_count += 1
        if max_results is None or discovered_count <= max_results:
            collected_packages.append(dependent_package)

    logging.debug(f"   Total dependents collected: {len(collected_packages)} ({'partial' if is_partial else 'complete'})")

    if len(collected_packages) == 0:
        raise NoDependentsFoundError(package_name)

    return collected_packages


def build_dependents_graph(
        root_package: str,
        repository_paths: Dict[str, str],
        show_source_packages: bool,
        source_cache: SourcePackageCache,
        metrics: RepoQueryMetrics,
        filter_cache: FilterCache,
        dependency_cache: DependencyCache,
        max_results: int | None = None,
        keep_cycles: bool = False,
        verbose: bool = False,
        filter_command: str | None = None,
        allow_missing: bool = False
    ) -> Dict[str, Dict[str, Any]]:
    """
    Build a transitive graph of reverse dependencies for the given package.
    """
    logging.debug(f"🔄 Building dependents graph for: {root_package}")
    logging.debug(f"   Show source packages: {show_source_packages}")
    logging.debug(f"   Max results: {max_results}")
    logging.debug(f"   Filter command: {filter_command}")

    pkg = importlib.import_module('revdeps')

    known_packages: Set[str] = {root_package}
    queue = deque([root_package])
    dependents_map: Dict[str, Dict[str, Any]] = {}
    result_count = 0

    result_limit_hit = False
    while queue:
        package = queue.popleft()
        dependents_list: List[str] = []

        any_filtered_dependents = False
        for dependent in pkg.generate_direct_dependents(
                package, repository_paths, metrics, dependency_cache, verbose,
                cache_only=result_limit_hit
        ):
            if show_source_packages:
                dependent = pkg.query_source_package(
                    dependent,
                    repository_paths,
                    metrics,
                    source_cache,
                    verbose,
                    allow_missing
                )

            if not dependent:
                continue
            if not keep_cycles and dependent in known_packages:
                continue

            if dependent not in known_packages:
                known_packages.add(dependent)
                queue.append(dependent)

            dependent_is_filtered = filter_command and not pkg.run_filter_command(
                dependent,
                filter_command,
                metrics,
                filter_cache,
                verbose
            )

            if not dependent_is_filtered:
                dependents_list.append(dependent)

                if package == root_package and max_results is not None:
                    result_count += 1
                    if result_count >= max_results:
                        result_limit_hit = True
                        break
            else:
                any_filtered_dependents = True

        dependents_map[package] = {"dependents": dependents_list, "partial": result_limit_hit or any_filtered_dependents}

    for package, entry in dependents_map.items():
        has_unknown_dependents = any(dependent not in dependents_map for dependent in entry["dependents"])
        has_partial_dependents = any(not dependency_cache.has_all(dependent) for dependent in entry["dependents"])
        entry["partial"] = entry["partial"] or has_unknown_dependents or has_partial_dependents

    def filter_function(package_name: str, dependents_list: List[str]) -> bool:
        if max_results is not None and len(dependents_list) >= max_results:
            return False

        if not filter_command:
            return True

        return filter_cache.get(package_name) is not False

    if max_results is not None:
        max_results += 1

    dependents_graph = compute_transitive_closure(root_package, dependents_map, max_results, filter_function)

    if not dependents_graph.get(root_package):
        raise NoDependentsFoundError(root_package)

    return dependents_graph
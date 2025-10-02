from typing import Any, Dict, List, Optional

from revdeps.metrics import RepoQueryMetrics
from revdeps.caches import SourcePackageCache, FilterCache, DependencyCache
from revdeps.graph import build_dependents_graph, build_dependents_list


class ReverseDepsClient:
    def __init__(self, repositories: Dict[str, str]):
        self.repositories = repositories
        self.metrics = RepoQueryMetrics()
        self.source_cache = SourcePackageCache()
        self.filter_cache = FilterCache()
        self.dependency_cache = DependencyCache()

    def list_direct_dependents(
        self,
        package_name: str,
        *,
        show_source_packages: bool = False,
        max_results: Optional[int] = None,
        verbose: bool = False,
        keep_cycles: bool = False,
        filter_command: Optional[str] = None,
        allow_missing: bool = False,
    ) -> List[str]:
        return build_dependents_list(
            package_name,
            self.repositories,
            show_source_packages=self.source_cache is not None and show_source_packages,
            source_cache=self.source_cache,
            metrics=self.metrics,
            filter_cache=self.filter_cache,
            dependency_cache=self.dependency_cache,
            max_results=max_results,
            verbose=verbose,
            keep_cycles=keep_cycles,
            filter_command=filter_command,
            allow_missing=allow_missing,
        )

    def build_graph(
        self,
        package_name: str,
        *,
        show_source_packages: bool = False,
        max_results: Optional[int] = None,
        verbose: bool = False,
        keep_cycles: bool = False,
        filter_command: Optional[str] = None,
        allow_missing: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        return build_dependents_graph(
            package_name,
            self.repositories,
            show_source_packages=self.source_cache is not None and show_source_packages,
            source_cache=self.source_cache,
            metrics=self.metrics,
            filter_cache=self.filter_cache,
            dependency_cache=self.dependency_cache,
            max_results=max_results,
            verbose=verbose,
            keep_cycles=keep_cycles,
            filter_command=filter_command,
            allow_missing=allow_missing,
        )


def list_direct_dependents(
    package_name: str,
    repositories: Dict[str, str],
    *,
    show_source_packages: bool = False,
    max_results: Optional[int] = None,
    verbose: bool = False,
    keep_cycles: bool = False,
    filter_command: Optional[str] = None,
    allow_missing: bool = False,
) -> List[str]:
    client = ReverseDepsClient(repositories)
    return client.list_direct_dependents(
        package_name,
        show_source_packages=show_source_packages,
        max_results=max_results,
        verbose=verbose,
        keep_cycles=keep_cycles,
        filter_command=filter_command,
        allow_missing=allow_missing,
    )


def build_dependents_graph_client(
    package_name: str,
    repositories: Dict[str, str],
    *,
    show_source_packages: bool = False,
    max_results: Optional[int] = None,
    verbose: bool = False,
    keep_cycles: bool = False,
    filter_command: Optional[str] = None,
    allow_missing: bool = False,
) -> Dict[str, Dict[str, Any]]:
    client = ReverseDepsClient(repositories)
    return client.build_graph(
        package_name,
        show_source_packages=show_source_packages,
        max_results=max_results,
        verbose=verbose,
        keep_cycles=keep_cycles,
        filter_command=filter_command,
        allow_missing=allow_missing,
    )
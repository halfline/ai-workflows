"""
Reverse dependencies utilities for RPM packages.

This package modularizes logic currently in `find-package-dependents.py`.
"""

from revdeps.metrics import RepoQueryMetrics
from revdeps.caches import SourcePackageCache, FilterCache, DependencyCache
from revdeps.errors import (
	RepoQueryError,
	NoDependentsFoundError,
	PackageNotFoundError,
	EXIT_REPO_QUERY_ERROR,
	EXIT_NO_DEPENDENTS_FOUND,
	EXIT_INVALID_ARGUMENTS,
	EXIT_CACHE_UPDATE_ERROR,
	EXIT_PACKAGE_NOT_FOUND,
)
from revdeps.runner import quote_command, run_command, dnf, update_dnf_cache
from revdeps.repositories import KNOWN_ARCHS, build_repository_paths, derive_repository_id_from_url
from revdeps.queries import (
	generate_direct_dependents,
	query_source_package,
	query_package_description,
	convert_to_source_packages,
)
from revdeps.graph import (
	compute_transitive_closure,
	build_dependents_list,
	build_dependents_graph,
)
from revdeps.filters import run_filter_command
from revdeps.client import ReverseDepsClient, list_direct_dependents, build_dependents_graph_client

__all__ = [
	"RepoQueryMetrics",
	"SourcePackageCache",
	"FilterCache",
	"DependencyCache",
	"RepoQueryError",
	"NoDependentsFoundError",
	"PackageNotFoundError",
	"EXIT_REPO_QUERY_ERROR",
	"EXIT_NO_DEPENDENTS_FOUND",
	"EXIT_INVALID_ARGUMENTS",
	"EXIT_CACHE_UPDATE_ERROR",
	"EXIT_PACKAGE_NOT_FOUND",
	"quote_command",
	"run_command",
	"dnf",
	"update_dnf_cache",
	"KNOWN_ARCHS",
	"build_repository_paths",
	"derive_repository_id_from_url",
	"generate_direct_dependents",
	"query_source_package",
	"query_package_description",
	"convert_to_source_packages",
	"compute_transitive_closure",
	"build_dependents_list",
	"build_dependents_graph",
	"run_filter_command",
	"ReverseDepsClient",
	"list_direct_dependents",
	"build_dependents_graph_client",
]
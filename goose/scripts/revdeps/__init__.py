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
from revdeps.runner import quote_command, run_command, dnf, update_dnf_cache, get_signal_name
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
from revdeps.cli import (
	max_result_type,
	parse_command_line_arguments,
	set_up_logging,
	log_operation,
	collect_package_descriptions,
	generate_output,
	generate_json_output,
	generate_plain_output,
	write_output,
	display_statistics,
)
from revdeps.__main__ import main

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
	"get_signal_name",
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
	"max_result_type",
	"parse_command_line_arguments",
	"set_up_logging",
	"log_operation",
	"collect_package_descriptions",
	"generate_output",
	"generate_json_output",
	"generate_plain_output",
	"write_output",
	"display_statistics",
	"main",
]
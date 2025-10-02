import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from revdeps.repositories import KNOWN_ARCHS
from revdeps.metrics import RepoQueryMetrics
from revdeps.caches import SourcePackageCache, FilterCache, DependencyCache
from revdeps.queries import query_package_description


def max_result_type(value: str) -> int:
    try:
        result = int(value)
    except ValueError:
        result = -1

    if result <= 0:
        raise argparse.ArgumentTypeError(f"result limit must be positive whole number, got: {value}")

    return result


def parse_command_line_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find reverse dependencies of an RPM package."
    )
    parser.add_argument(
        "package_name",
        help="Name of the package to inspect"
    )
    parser.add_argument(
        "--base-url",
        dest="base_url",
        default="http://download.devel.redhat.com/rhel-10/nightly/RHEL-10/latest-RHEL-10",
        help="Base URL for nightly repositories"
    )
    parser.add_argument(
        "--repositories",
        dest="repository_names",
        default="BaseOS,AppStream,CRB",
        help=(
            "Comma-separated list of repository names (relative to base URL) "
            "or full repository URLs.\\n"
            "Examples:\n"
            "  --repositories BaseOS,AppStream,CRB\n"
            "  --repositories BaseOS,https://download.devel.redhat.com/rhel-10/nightly/RHEL-10/latest-RHEL-10/compose/RT/x86_64/os\n"
        )
    )
    parser.add_argument(
        "--arch",
        choices=sorted(KNOWN_ARCHS),
        dest="arch",
        default="x86_64",
        help="CPU architecture (for example: x86_64, s390x)"
    )
    parser.add_argument(
        "--output-file",
        dest="output_file",
        type=Path,
        help="Write output to this file instead of stdout"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include transitive reverse dependencies (default is direct only)"
    )
    parser.add_argument(
        "--source-packages",
        action="store_true",
        help="Convert dependent package names to their source package names"
    )
    parser.add_argument(
        "--max-results",
        type=max_result_type,
        help="Maximum number of results to return (limits both queries and output)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "plain"],
        default="plain",
        help="Output format: json or plain (one per line)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging"
    )

    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="Skip dnf cache update and use existing cache only"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print detailed statistics about repoquery calls and cache usage"
    )
    parser.add_argument(
        "--show-cycles",
        action="store_true",
        help="Show cycles in dependency graph"
    )
    parser.add_argument(
        "--filter-command",
        help="Optional shell command to run on each dependent package to filter results. "
             "The command receives PACKAGE environment variable set to the package name. "
             "If the command returns a non-zero exit code, the package is pruned from output. "
             "Example: --filter-command 'echo $PACKAGE | grep -q \"^kernel$\"'"
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help="Include package descriptions in output. For plain format, descriptions are appended to package names. "
             "For JSON format, descriptions are added as a 'description' field to each package object."
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Redirect all log output to this file instead of stderr"
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Allow missing packages to be non-fatal to operation. "
             "If a package is not found in repositories, continue with empty results instead of exiting with error."
    )
    return parser.parse_args()


def set_up_logging(verbose: bool, log_file: Path | None) -> None:
    level = logging.DEBUG if verbose else logging.INFO

    if log_file:
        logger = logging.getLogger()
        logger.setLevel(level)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(file_handler)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.ERROR)
        stderr_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(stderr_handler)
    else:
        logging.basicConfig(format="%(message)s", level=level)


def log_operation(
        package_name: str,
        all_dependents: bool,
        source_packages: bool,
        max_results: int | None,
        filter_command: str | None,
        output_file: Path | None
    ) -> None:
    operation = "transitive" if all_dependents else "direct"
    package_type = "as source packages" if source_packages else ""
    max_info = f" (max {max_results})" if max_results else ""
    filter_info = f" with filter: {filter_command}" if filter_command else ""
    output_info = f" to \"{output_file}\"" if output_file else ""

    logging.info(
        f"\n🔍 Finding {operation} reverse dependencies of \"{package_name}\" "
        f"{package_type}{max_info}{filter_info}{output_info}\n"
    )


def collect_package_descriptions(
        arguments: argparse.Namespace,
        repositories: Dict[str, str],
        metrics: RepoQueryMetrics,
        dependents_data: List[Dict[str, Any]] | List[str]
    ) -> Dict[str, str]:
    package_descriptions: Dict[str, str] = {}

    if arguments.all:
        all_packages = set()
        for package_entry in dependents_data:
            all_packages.add(package_entry["package"])
            all_packages.update(package_entry["dependents"])

        for package in all_packages:
            description = query_package_description(
                package, repositories, metrics, arguments.verbose
            )
            package_descriptions[package] = description
    else:
        all_packages_to_describe = [arguments.package_name] + dependents_data
        for package in all_packages_to_describe:
            description = query_package_description(
                package, repositories, metrics, arguments.verbose
            )
            package_descriptions[package] = description

    return package_descriptions


def generate_output(
        arguments: argparse.Namespace,
        dependents_data: List[Dict[str, Any]] | List[str],
        package_descriptions: Dict[str, str] | None
    ) -> str:
    if arguments.format == "json":
        return generate_json_output(arguments, dependents_data, package_descriptions)
    else:
        return generate_plain_output(arguments, dependents_data, package_descriptions)


def generate_json_output(
        arguments: argparse.Namespace,
        dependents_data: List[Dict[str, Any]] | List[str],
        package_descriptions: Dict[str, str] | None
    ) -> str:
    if arguments.all:
        output_array = []
        for package_entry in dependents_data:
            package_obj = {"package": package_entry["package"]}
            if arguments.describe and package_descriptions:
                description = package_descriptions.get(package_entry["package"])
                if description:
                    package_obj["description"] = description
            package_obj["dependents"] = package_entry["dependents"]
            if "partial" in package_entry:
                package_obj["partial"] = package_entry["partial"]
            output_array.append(package_obj)
    else:
        output_array = [
            {"package": arguments.package_name, "dependents": dependents_data}
        ]
        if arguments.describe and package_descriptions:
            description = package_descriptions.get(arguments.package_name)
            if description:
                output_array[0]["description"] = description

    return json.dumps(output_array, indent=2)


def generate_plain_output(
        arguments: argparse.Namespace,
        dependents_data: List[Dict[str, Any]] | List[str],
        package_descriptions: Dict[str, str] | None
    ) -> str:
    if arguments.all:
        root_package_entry = None
        for package_entry in dependents_data:
            if package_entry["package"] == arguments.package_name:
                root_package_entry = package_entry
                break

        if root_package_entry:
            collected_packages = root_package_entry["dependents"]
        else:
            collected_packages = []
    else:
        collected_packages = dependents_data

    if arguments.describe and package_descriptions:
        output_lines = []
        for package in collected_packages:
            description = package_descriptions.get(package)
            if description:
                output_lines.append(f"{package}: {description}")
            else:
                output_lines.append(package)
        return "\n".join(output_lines)
    else:
        return "\n".join(collected_packages)


def write_output(output_data: str, output_file: Path | None) -> None:
    logging.debug(f"\n✅ Final output:\n{output_data}\n")
    if output_file:
        output_file.write_text(output_data)
    else:
        print(output_data)


def display_statistics(
        filter_command: str | None,
        metrics: RepoQueryMetrics,
        source_cache: SourcePackageCache,
        filter_cache: FilterCache,
        dependency_cache: DependencyCache
    ) -> None:
    stats = metrics.get_stats()
    print("\n📊 FINAL STATISTICS:", file=sys.stderr)
    print(f"   Total dnf repoquery calls: {stats['total_calls']}", file=sys.stderr)
    print("   Calls by type:", file=sys.stderr)
    for call_type, count in stats["calls_by_type"].items():
        print(f"     {call_type}: {count}", file=sys.stderr)

    if filter_command:
        print(f"   Filter command calls: {stats['filter_calls']}", file=sys.stderr)
        print(f"   Filter command failures: {stats['filter_failures']}", file=sys.stderr)

    source_cache_stats = source_cache.get_stats()
    print(f"   Source package cache size: {source_cache_stats['cache_size']}", file=sys.stderr)
    print(f"   Source package cache hits (found): {source_cache_stats['found_count']}", file=sys.stderr)
    print(f"   Source package cache hits (not found): {source_cache_stats['not_found_count']}", file=sys.stderr)

    if source_cache_stats["cached_packages"]:
        print("   Cached source packages:", file=sys.stderr)
        for package in source_cache_stats["cached_packages"]:
            result = source_cache.get(package)
            if result is None:
                status = "not found"
            else:
                status = f"→ {result}"
            print(f"     {package}: {status}", file=sys.stderr)

    filter_cache_stats = filter_cache.get_stats()
    print(f"   Filter cache size: {filter_cache_stats['cache_size']}", file=sys.stderr)
    print(f"   Filter cache hits (passed): {filter_cache_stats['passed_count']}", file=sys.stderr)
    print(f"   Filter cache hits (failed): {filter_cache_stats['failed_count']}", file=sys.stderr)

    if filter_cache_stats["cached_packages"]:
        print("   Cached filter results:", file=sys.stderr)
        for package in filter_cache_stats["cached_packages"]:
            result = filter_cache.get(package)
            status = "pass" if result else "fail"
            print(f"     {package}: {status}", file=sys.stderr)

    dependency_cache_stats = dependency_cache.get_stats()
    print(f"   Dependency cache size: {dependency_cache_stats['cache_size']}", file=sys.stderr)
    print(f"   Dependency cache total dependents: {dependency_cache_stats['total_dependents']}", file=sys.stderr)
    print(f"   Dependency cache complete results: {dependency_cache_stats['complete_count']}", file=sys.stderr)
    print(f"   Dependency cache partial results: {dependency_cache_stats['partial_count']}", file=sys.stderr)

    if dependency_cache_stats["cached_packages"]:
        print("   Cached dependency results:", file=sys.stderr)
        for package in dependency_cache_stats["cached_packages"]:
            dependents = dependency_cache.get(package)
            if dependents is not None:
                entry = dependency_cache._cache[package]
                partial_info = " (partial)" if entry["partial"] else " (complete)"
                print(f"     {package}: {len(dependents)} dependents{partial_info}", file=sys.stderr)
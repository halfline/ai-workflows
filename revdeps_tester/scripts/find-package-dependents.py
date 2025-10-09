#!/usr/bin/env python3

import logging
import sys
from pathlib import Path
from revdeps import (
    RepoQueryMetrics,
    SourcePackageCache,
    FilterCache,
    DependencyCache,
    RepoQueryError,
    NoDependentsFoundError,
    PackageNotFoundError,
    parse_command_line_arguments,
    set_up_logging,
    log_operation,
    set_up_repositories_and_cache,
    build_dependents_graph,
    build_dependents_list,
    collect_package_descriptions,
    generate_output,
    write_output,
    display_statistics,
)


def main() -> None:
    """
    Main entry point for the package dependents finder.

    Parses command line arguments, sets up repositories, and finds package dependents
    according to the specified options. Outputs results in the requested format.

    Raises:
        SystemExit: On argument validation errors or RepoQueryError
    """
    arguments = parse_command_line_arguments()

    set_up_logging(arguments.verbose, arguments.log_file)

    log_operation(
        arguments.package_name,
        arguments.all,
        arguments.source_packages,
        arguments.max_results,
        arguments.filter_command,
        arguments.output_file
    )

    repositories = set_up_repositories_and_cache(
        arguments.base_url,
        arguments.repository_names,
        arguments.arch,
        arguments.no_refresh,
        arguments.verbose
    )

    metrics = RepoQueryMetrics()
    source_cache = SourcePackageCache()
    filter_cache = FilterCache()
    dependency_cache = DependencyCache()

    try:
        if arguments.all:
            dependents_graph = build_dependents_graph(
                arguments.package_name,
                repositories,
                show_source_packages=arguments.source_packages,
                source_cache=source_cache,
                metrics=metrics,
                filter_cache=filter_cache,
                dependency_cache=dependency_cache,
                max_results=arguments.max_results,
                verbose=arguments.verbose,
                keep_cycles=arguments.show_cycles,
                filter_command=arguments.filter_command,
                allow_missing=arguments.allow_missing,
            )

            dependents_data = []
            for package, entry in dependents_graph.items():
                package_entry = {
                    "package": package,
                    "dependents": entry["dependents"],
                    "partial": entry["partial"]
                }
                dependents_data.append(package_entry)
        else:
            dependents_data = build_dependents_list(
                arguments.package_name,
                repositories,
                show_source_packages=arguments.source_packages,
                source_cache=source_cache,
                metrics=metrics,
                filter_cache=filter_cache,
                dependency_cache=dependency_cache,
                max_results=arguments.max_results,
                verbose=arguments.verbose,
                keep_cycles=arguments.show_cycles,
                filter_command=arguments.filter_command,
                allow_missing=arguments.allow_missing,
            )

        package_descriptions = None
        if arguments.describe:
            logging.debug("🔄 Fetching package descriptions...")
            package_descriptions = collect_package_descriptions(
                arguments.package_name,
                arguments.all,
                repositories,
                metrics,
                dependents_data,
                arguments.verbose,
            )

        output_data = generate_output(
            arguments.format,
            arguments.all,
            arguments.package_name,
            arguments.describe,
            dependents_data,
            package_descriptions,
        )
        write_output(output_data, arguments.output_file)

        if arguments.stats:
            display_statistics(arguments.filter_command, metrics, source_cache, filter_cache, dependency_cache)

    except RepoQueryError as error:
        logging.error("%s", error)
        sys.exit(error.exit_code)
    except NoDependentsFoundError as error:
        if arguments.allow_missing:
            logging.info("%s (continuing with empty results due to --allow-missing)", error)
            if arguments.all:
                dependents_data = [{"package": arguments.package_name, "dependents": [], "partial": False}]
            else:
                dependents_data = []
        else:
            logging.error("%s", error)
            sys.exit(error.exit_code)
    except PackageNotFoundError as error:
        if arguments.allow_missing:
            logging.info("%s (continuing with empty results due to --allow-missing)", error)
            if arguments.all:
                dependents_data = [{"package": arguments.package_name, "dependents": [], "partial": False}]
            else:
                dependents_data = []
        else:
            logging.error("%s", f"Could not query dependents for {arguments.package_name} because repositories are incomplete (at least the {error.package_name} package is missing)")
            sys.exit(error.exit_code)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()

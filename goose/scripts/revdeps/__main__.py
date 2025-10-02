from revdeps.cli import parse_command_line_arguments, set_up_logging, log_operation, collect_package_descriptions, generate_output, write_output, display_statistics
from revdeps.metrics import RepoQueryMetrics
from revdeps.caches import SourcePackageCache, FilterCache, DependencyCache
from revdeps.repositories import build_repository_paths
from revdeps.runner import update_dnf_cache
from revdeps.graph import build_dependents_graph, build_dependents_list
from revdeps.errors import RepoQueryError, NoDependentsFoundError, PackageNotFoundError

import logging
import sys


def main() -> None:
    args = parse_command_line_arguments()
    set_up_logging(args.verbose, args.log_file)

    log_operation(
        args.package_name,
        args.all,
        args.source_packages,
        args.max_results,
        args.filter_command,
        args.output_file,
    )

    repositories = build_repository_paths(args.base_url, args.repository_names, args.arch)
    if not args.no_refresh:
        update_dnf_cache(repositories, args.verbose)
    else:
        logging.info("⏭️  Skipping dnf cache update (using existing cache)")

    metrics = RepoQueryMetrics()
    source_cache = SourcePackageCache()
    filter_cache = FilterCache()
    dependency_cache = DependencyCache()

    try:
        if args.all:
            dependents_graph = build_dependents_graph(
                args.package_name,
                repositories,
                show_source_packages=args.source_packages,
                source_cache=source_cache,
                metrics=metrics,
                filter_cache=filter_cache,
                dependency_cache=dependency_cache,
                max_results=args.max_results,
                verbose=args.verbose,
                keep_cycles=args.show_cycles,
                filter_command=args.filter_command,
                allow_missing=args.allow_missing,
            )

            dependents_data = []
            for package, entry in dependents_graph.items():
                package_entry = {
                    "package": package,
                    "dependents": entry["dependents"],
                    "partial": entry["partial"],
                }
                dependents_data.append(package_entry)
        else:
            dependents_data = build_dependents_list(
                args.package_name,
                repositories,
                show_source_packages=args.source_packages,
                source_cache=source_cache,
                metrics=metrics,
                filter_cache=filter_cache,
                dependency_cache=dependency_cache,
                max_results=args.max_results,
                verbose=args.verbose,
                keep_cycles=args.show_cycles,
                filter_command=args.filter_command,
                allow_missing=args.allow_missing,
            )

        package_descriptions = None
        if args.describe:
            logging.debug("🔄 Fetching package descriptions...")
            package_descriptions = collect_package_descriptions(
                args, repositories, metrics, dependents_data
            )

        output_data = generate_output(args, dependents_data, package_descriptions)
        write_output(output_data, args.output_file)

        if args.stats:
            display_statistics(args.filter_command, metrics, source_cache, filter_cache, dependency_cache)

    except RepoQueryError as error:
        logging.error("%s", error)
        sys.exit(error.exit_code)
    except NoDependentsFoundError as error:
        if args.allow_missing:
            logging.info("%s (continuing with empty results due to --allow-missing)", error)
            if args.all:
                dependents_data = [{"package": args.package_name, "dependents": [], "partial": False}]
            else:
                dependents_data = []
        else:
            logging.error("%s", error)
            sys.exit(error.exit_code)
    except PackageNotFoundError as error:
        if args.allow_missing:
            logging.info("%s (continuing with empty results due to --allow-missing)", error)
            if args.all:
                dependents_data = [{"package": args.package_name, "dependents": [], "partial": False}]
            else:
                dependents_data = []
        else:
            logging.error("%s", f"Could not query dependents for {args.package_name} because repositories are incomplete (at least the {error.package_name} package is missing)")
            sys.exit(error.exit_code)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
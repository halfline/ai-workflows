import logging
from typing import Dict, Any

from revdeps.metrics import RepoQueryMetrics
from revdeps.caches import FilterCache
from revdeps.runner import run_command


def run_filter_command(package_name: str, filter_command: str, metrics: RepoQueryMetrics, filter_cache: FilterCache, verbose: bool = False) -> bool:
    """
    Run a filter command on a package to determine if it should be included.

    Args:
        package_name: The package name to check
        filter_command: The shell command to run
        metrics: Metrics object to track filter command usage
        filter_cache: Cache object to store filter results
        verbose: Whether to enable verbose logging

    Returns:
        True if the command succeeds (package should be included), False otherwise
    """
    if not filter_command or not filter_command.strip():
        return True

    cached_result = filter_cache.get(package_name)
    if cached_result is not None:
        logging.debug(f"📋 Filter cache hit: Filter result for {package_name} → {'pass' if cached_result else 'fail'}")
        return cached_result

    logging.debug(f"🔍 Running filter command on package: {package_name}")

    try:
        result = run_command(
            filter_command,
            extra_environment={"PACKAGE": package_name}
        )

        success = result["return_code"] == 0
        metrics.log_filter_call(package_name, success)

        filter_cache.set(package_name, success)

        if success:
            logging.debug(f"   ✅ Filter command succeeded for {package_name}")
        else:
            logging.debug(f"   ❌ Filter command failed for {package_name} (exit code: {result['return_code']})")

        return success

    except Exception as e:
        logging.debug(f"   💥 Filter command error for {package_name}: {e}")
        metrics.log_filter_call(package_name, False)
        filter_cache.set(package_name, False)
        return False
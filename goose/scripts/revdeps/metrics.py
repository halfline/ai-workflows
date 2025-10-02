from typing import Dict, Any

class RepoQueryMetrics:
    """
    Tracks metrics for dnf repoquery calls.

    This class focuses purely on metrics gathering:
    - Call counting by type
    - Statistics generation
    """

    def __init__(self):
        self._call_count: int = 0
        self._calls_by_type: Dict[str, int] = {}
        self._filter_calls: int = 0
        self._filter_failures: int = 0

    def log_call(self, purpose: str, package_name: str) -> None:
        """
        Log a dnf repoquery call with detailed information.

        Args:
            purpose: The purpose of the repoquery call (e.g., 'find_direct_dependents')
            package_name: The package being queried
        """
        self._call_count += 1
        self._calls_by_type[purpose] = self._calls_by_type.get(purpose, 0) + 1

    def log_filter_call(self, package_name: str, success: bool) -> None:
        """
        Log a filter command call.

        Args:
            package_name: The package being filtered
            success: Whether the filter command succeeded
        """
        self._filter_calls += 1
        if not success:
            self._filter_failures += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics about dnf repoquery usage.

        Returns:
            Dictionary containing statistics about dnf repoquery calls
        """
        return {
            "total_calls": self._call_count,
            "calls_by_type": self._calls_by_type.copy(),
            "filter_calls": self._filter_calls,
            "filter_failures": self._filter_failures,
        }
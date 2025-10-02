from typing import Any

EXIT_REPO_QUERY_ERROR = 1
EXIT_NO_DEPENDENTS_FOUND = 2
EXIT_INVALID_ARGUMENTS = 3
EXIT_CACHE_UPDATE_ERROR = 4
EXIT_PACKAGE_NOT_FOUND = 5

class RepoQueryError(Exception):
    """Raised when a dnf repoquery call fails or returns invalid data."""

    def __init__(self, message: str, exit_code: int = EXIT_REPO_QUERY_ERROR):
        super().__init__(message)
        self.exit_code = exit_code


class NoDependentsFoundError(Exception):
    """Raised when no dependents are found for a package."""

    def __init__(self, package_name: str):
        super().__init__(f"No dependents found for package: {package_name}")
        self.package_name = package_name
        self.exit_code = EXIT_NO_DEPENDENTS_FOUND


class PackageNotFoundError(Exception):
    """Raised when a package is not found in the repositories."""

    def __init__(self, package_name: str):
        super().__init__(f"Package not found in repositories: {package_name}")
        self.package_name = package_name
        self.exit_code = EXIT_PACKAGE_NOT_FOUND
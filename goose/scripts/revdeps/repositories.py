"""
Repository-related utilities for RPM packages.
"""

import logging
import os
import re
from hashlib import sha256
from typing import Dict
from urllib.parse import urlparse

from revdeps.errors import EXIT_INVALID_ARGUMENTS
from revdeps.runner import update_dnf_cache


KNOWN_ARCHS = ["x86_64", "aarch64", "ppc64le", "s390x"]


def derive_repository_id_from_url(url: str) -> str:
    """
    Generate a unique repository ID from a URL.

    Args:
        url: Repository URL

    Returns:
        Repository ID string
    """
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split('/') if part]

    # Try to find a meaningful name from the path
    name = None
    for part in reversed(path_parts):
        if part not in ['os', 'tree', 'source', 'x86_64', 'aarch64', 'ppc64le', 's390x']:
            name = part
            break

    if not name:
        name = parsed.netloc.replace('.', '_')

    # Add a hash suffix to ensure uniqueness
    hash_suffix = sha256(url.encode()).hexdigest()[:8]
    return f"{name}_{hash_suffix}"


def build_repository_paths(base_url: str, repository_names: str, arch: str) -> Dict[str, str]:
    """
    Build repository paths from base URL and repository names.

    Args:
        base_url: Base URL for nightly repositories
        repository_names: Comma-separated list of repository names
        arch: CPU architecture

    Returns:
        Dictionary mapping repository IDs to URLs

    Raises:
        SystemExit: If repository_names is empty
    """
    if not repository_names:
        logging.error("No repository names provided")
        raise SystemExit(EXIT_INVALID_ARGUMENTS)

    repositories = {}
    for name in repository_names.split(','):
        if re.match(r'^https?://', name):
            repo_id = derive_repository_id_from_url(name)
            repositories[repo_id] = name
        else:
            base = base_url.rstrip('/')
            repo_url = f"{base}/compose/{name}/{arch}/os/"
            repositories[name] = repo_url

            source_url = f"{base}/compose/{name}/source/tree/"
            repositories[f"{name}-sources"] = source_url

    return repositories


def set_up_repositories_and_cache(
        base_url: str,
        repository_names: str,
        arch: str,
        no_refresh: bool,
        verbose: bool
    ) -> Dict[str, str]:
    """
    Set up repositories and update dnf cache if needed.

    Args:
        base_url: Base URL for nightly repositories
        repository_names: Comma-separated list of repository names
        arch: CPU architecture
        no_refresh: Whether to skip dnf cache update
        verbose: Whether to enable verbose logging

    Returns:
        Dictionary mapping repository IDs to URLs
    """
    repositories = build_repository_paths(base_url, repository_names, arch)

    if not no_refresh:
        update_dnf_cache(repositories, verbose)
    else:
        logging.info("⏭️  Skipping dnf cache update (using existing cache)")

    return repositories
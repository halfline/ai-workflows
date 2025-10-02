import logging
import os
import re
import shlex
import signal
import subprocess
import importlib
from typing import Dict, List, Any

from revdeps.errors import RepoQueryError, EXIT_CACHE_UPDATE_ERROR


def get_signal_name(signal_num: int) -> str:
    """
    Get the name of a signal number.
    """
    try:
        return signal.Signals(signal_num).name
    except ValueError:
        return f"SIG{signal_num}"


def quote_command(args):
    """
    Join a list of arguments into a command string, only quoting arguments
    that would be semantically different if left unquoted.
    """
    quoted_args = []

    for arg in args:
        if not arg:
            quoted_args.append(shlex.quote(arg))
            continue

        try:
            if shlex.split(arg) == [arg]:
                quoted_args.append(arg)
            else:
                quoted_args.append(shlex.quote(arg))
        except ValueError:
            quoted_args.append(shlex.quote(arg))

    return ' '.join(quoted_args)


def run_command(command: List[str] | str, extra_environment: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    Run a command and log output.
    """
    if isinstance(command, list):
        command_string = quote_command(command)
    else:
        command_string = command

    logging.debug(f"\n        ❯ {command_string}")

    environment = None
    if extra_environment:
        environment = os.environ.copy()
        environment.update(extra_environment)

    result = subprocess.run(
        command_string,
        env=environment,
        capture_output=True,
        shell=True,
        text=True
    )

    for line in result.stderr.splitlines():
        if line.strip():
            logging.debug(f"        {line.strip()}")

    for line in result.stdout.splitlines():
        if line.strip():
            logging.debug(f"        {line.strip()}")

    if result.returncode < 0:
        signal_name = get_signal_name(abs(result.returncode))
        logging.debug(f"        Process killed by signal {abs(result.returncode)} ({signal_name})")
    else:
        logging.debug(f"        Process exited with code {result.returncode}")

    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, command,
            result.stdout,
            result.stderr
        )

    return {"return_code": result.returncode, "output": result.stdout}


def dnf(command: str, repository_paths: Dict[str, str], verbose: bool = False, cache_only: bool = True) -> str:
    """
    Execute a dnf command with repository setup and return stdout content.
    """
    command_parts = shlex.split(command)
    full_command = ["dnf"] + command_parts

    full_command.extend(["--disablerepo=*"])
    if not verbose:
        full_command.append("--quiet")
    if cache_only:
        full_command.append("--cacheonly")
    for repository_id, repository_url in repository_paths.items():
        full_command.append(f"--repofrompath=repo-{repository_id},{repository_url}")
    for repository_id in repository_paths:
        full_command.append(f"--enablerepo=repo-{repository_id}")

    # Resolve run_command dynamically from the revdeps package to honor patches
    pkg = importlib.import_module('revdeps')
    result = pkg.run_command(full_command)
    return result["output"].strip()


def update_dnf_cache(repository_paths: Dict[str, str], verbose: bool = False) -> None:
    """
    Update dnf cache for all repositories once upfront.
    """
    logging.debug("🔄 Updating dnf cache for all repositories...")

    try:
        result = dnf("makecache --refresh", repository_paths, verbose, cache_only=False)
        logging.debug("✅ Dnf cache updated successfully")
        logging.debug(f"Cache update output: {result}")
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.strip() if error.stderr else "Unknown error"
        raise RepoQueryError(f"Failed to update dnf cache: {stderr}", EXIT_CACHE_UPDATE_ERROR)
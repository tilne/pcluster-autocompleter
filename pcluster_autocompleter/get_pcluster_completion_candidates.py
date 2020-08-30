#!/usr/bin/env python
"""Get tab-completion candidates for a pcluster command."""

import argparse
import json
import logging
import os
import re
import subprocess as sp
from typing import Callable, Dict, List

import pkg_resources

from pcluster.config.pcluster_config import PclusterConfig  # type: ignore

from pcluster_autocompleter.utils import config_logger, CACHE_PATH

# TODO: implement file locking for this
# TODO: handle region
LOG_PATH = "/tmp/pcluster-completions-log.txt"
LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subcommand_plus_args", nargs="*")
    return parser.parse_args()


def _get_pcluster_commands() -> List[str]:
    """
    Parse the available pcluster commands from the help message.

    The portion of the output we're looking for looks like this:

    ```
    positional arguments:
     {create,update,delete,start,stop,status,list,instances,ssh,createami,configure,version,dcv}
    ```
    """
    help_output = sp.check_output("pcluster --help".split()).decode()
    have_seen_line_before_commands_list = False
    for line in [l.strip() for l in help_output.splitlines()]:
        if have_seen_line_before_commands_list:
            commands_line_match = re.search(r'\{((.+,)+.+)\}', line)
            if not commands_line_match:
                LOGGER.debug("Did not find commands line in `pcluster --help` output")
                return []
            return commands_line_match.group(1).split(",")
        elif re.search(r'positional arguments:', line):
            have_seen_line_before_commands_list = True
    LOGGER.debug("Did not find commands line precursor in `pcluster --help` output")
    return []


def _populate_clusters_list_cache_file() -> None:
    """Populate CACHE_PATH with list of clusters for current region."""
    # TODO: get rid of this function after initial development.
    clusters = {
        "us-east-1": [
            {"name": "clusterOne", "status": "CREATE_COMPLETE", "cli_version": "2.8.0"},
            {"name": "clusterTwo", "status": "CREATE_COMPLETE", "cli_version": "2.8.0"},
            {"name": "clusterThree", "status": "CREATE_COMPLETE", "cli_version": "2.8.0"},
        ],
    }
    with open(CACHE_PATH, "w") as cache_file:
        json.dump(clusters, cache_file)


def _parse_region_and_config_from_subcommand_args(argv: List[str]) -> Dict[str, str]:
    """Return the region and config file path args in argv if they're there."""
    argv_parser = argparse.ArgumentParser(add_help=False)
    argv_parser.add_argument("-c", "--config")
    argv_parser.add_argument("-r", "--region")
    return vars(argv_parser.parse_known_args(argv))


def _get_region_to_use(argv: List[str]) -> str:
    """Make a best-effort attempt to figure out which region we should query for resources."""
    # TODO: is there a way to do this without replicating logic in the CLI?
    # Order or precedence:
    # 1) CLI arg (-r,--region)
    # 2) config file (which will first try the AWS_DEFAULT_REGION envrion)
    argv_options = _parse_region_and_config_from_subcommand_args(argv)
    if argv_options.get("region"):
        return argv_options["region"]
    # Initialize config object so it can do figure out the rest and set AWS_DEFAULT_REGION
    # TODO: do this without the config?
    # TODO: add option to config constructor to avoid full initialization (which invokes a lot of network calls)
    PclusterConfig.init_aws(argv_options.get("config"))
    return os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def _get_list_of_clusters_for_region(region: str) -> List[str]:
    if not os.path.exists(CACHE_PATH):
        _populate_clusters_list_cache_file()  # TODO: return empty list, let daemon populate
    with open(CACHE_PATH) as cache_file:
        return [cluster.get("name") for cluster in json.load(cache_file).get(region)]


def _get_list_of_clusters(subcommand: str, argv: List[str]) -> List[str]:
    """Return list of clusters from cached file."""
    # TODO: turn this into a decorator that's used by the appropriate subcommands
    region = _get_region_to_use(argv)
    clusters = _get_list_of_clusters_for_region(region)
    # TODO: filter on cluster state based on command?
    LOGGER.debug(f"Found the following active clusters in {region}: {' '.join(clusters)}")
    return clusters


def _get_completions_for_createami_subcommand(subcommand: str, argv: List[str]) -> List[str]:
    """TODO: implement me."""
    return []


def _get_completions_for_dcv_subcommand(subcommand: str, argv: List[str]) -> List[str]:
    """TODO: implement me."""
    return []


def _get_pcluster_version() -> str:
    """Get the version of the pcluster CLI in use."""
    version = pkg_resources.get_distribution("aws-parallelcluster").version
    LOGGER.debug(f"Detected aws-parallelcluster version: {version}")
    return version


def _parse_cli_options_from_help_message(subcommand: str) -> List[str]:
    """Parse CLI options from output produced by running `pcluster {subcommand} --help`."""
    help_message = sp.check_output(f"pcluster {subcommand} --help".split()).decode()
    options = []
    # this regex should match lines of help message output with short and long options
    # examples:
    #      -r REGION, --region REGION
    #      -nr, --norollback     Disables stack rollback on error.
    #      --keep-logs           Keep cluster's CloudWatch log group data after deleting.
    pattern = r'\s+(-[a-zA-Z]+)?(\s+([A-Z_]+))?,?\s(--[a-zA-Z-]+)(\s([A-Z_]+))?'
    short_option_capture_group = 1
    long_option_capture_group = 4
    # The following capture groups aren't used yet
    # short_option_arg_capture_group = 3
    # long_option_arg_capture_group = 6
    for line in help_message.splitlines():
        match = re.search(pattern, line)
        if match:
            # TODO: append something that can be used to decide whether an option requires
            #       a positional arg.
            for capture_group in (short_option_capture_group, long_option_capture_group):
                if match.group(capture_group):
                    options.append(match.group(capture_group))
    LOGGER.debug(
        f"Parsed the following options from the `pcluster {subcommand}` help message: {options}"
    )
    return options


def _get_cli_options_for_subcommand(subcommand: str) -> List[str]:
    """Parse a list of valid CLI options for `pcluster {subcommand}` from the help message."""
    # TODO write this info to a file since it doesn't change for a given version
    version = _get_pcluster_version()
    options = _parse_cli_options_from_help_message(subcommand)
    LOGGER.debug(
        f"Found the following CLI options for `pcluster {subcommand}` in v{version}: {options}"
    )
    return options


def _get_completions_for_pcluster_subcommand(subcommand_argv: List[str]) -> List[str]:
    """
    Get completions for the given pcluster subcommand.

    :subcommand_argv: list of strings where the first item is a pcluster subcommand and
                      the remaining items are the args that have been passed to that
                      subcommand thus far
    """
    # TODO: also suggest positional args specific to each command
    _no_completions_function: Callable[[str, List[str]], List[str]] = lambda subcommand, argv: []
    subcommands_that_require_cluster_names = [
        "update", "delete", "start", "stop", "status", "instances", "ssh", "dcv"
    ]
    subcommand_to_completions_getter = {
        "create": _no_completions_function,
        "update": _no_completions_function,
        "delete": _no_completions_function,
        "start": _no_completions_function,
        "stop": _no_completions_function,
        "status": _no_completions_function,
        "list": _no_completions_function,
        "instances": _no_completions_function,
        # TODO: Not allowed to pass region of config for `pcluster ssh`, but
        #       _get_list_of_clusters_for_region will still look for it in the command line.
        #       Create a wrapper around it?
        "ssh": _no_completions_function,
        "createami": _get_completions_for_createami_subcommand,
        "configure": _no_completions_function,
        "version": _no_completions_function,
        "dcv": _get_completions_for_dcv_subcommand,
    }
    subcommand = subcommand_argv[0]
    LOGGER.debug(f"Getting completions for `pcluster {subcommand}`")
    if subcommand not in subcommand_to_completions_getter:
        LOGGER.error(f"No completion suggestions available for `pcluster {subcommand}`")
        return []
    completions = _get_cli_options_for_subcommand(subcommand)
    completions.extend(
        subcommand_to_completions_getter[subcommand](subcommand, subcommand_argv[1:])
    )
    if subcommand in subcommands_that_require_cluster_names:
        completions.extend(_get_list_of_clusters(subcommand, subcommand_argv[1:]))
    LOGGER.debug(f"Found the following completions for `pcluster {subcommand}`: {completions}")
    return completions


def main() -> None:
    config_logger(LOGGER, LOG_PATH)
    LOGGER.debug("pcluster completion script starting")
    args = parse_args()
    if args.subcommand_plus_args:
        completions = _get_completions_for_pcluster_subcommand(args.subcommand_plus_args)
    else:
        completions = _get_pcluster_commands()
    print("\n".join(completions))

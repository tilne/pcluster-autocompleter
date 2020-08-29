#!/usr/bin/env python
"""Get tab-completion candidates for a pcluster command."""

import argparse
import logging
import os
import re
import subprocess as sp
from typing import Callable, Dict, List, Optional

from pcluster.config.pcluster_config import PclusterConfig  # type: ignore

from pcluster_autocompleter.utils import config_logger

# TODO: implement file locking for this
# TODO: handle region
CLUSTERS_LIST_CACHE_FILE = "/tmp/pcluster-completion-candidates-cluster-list.txt"
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
    """
    Populate CLUSTERS_LIST_CACHE_FILE with list of clusters for current region.

    This should be avoided whenever possible, since it requires running `pcluster list`,
    which is an awfully slow process to wait for during interactive tab-completion.
    """
    # pcluster_list_lines = sp.check_output("pcluster list".split()).decode().splitlines()
    # clusters = [pcluster_list_line.split()[0] for pcluster_list_line in pcluster_list_lines]
    # TODO: get rid of this line when need for offline testing is gone
    clusters = ["clusterOne", "clusterTwo", "clusterThree"]
    with open(CLUSTERS_LIST_CACHE_FILE, "w") as clusters_list_cache_file:
        for cluster in clusters:
            clusters_list_cache_file.write(f"{cluster}\n")


def _parse_region_and_config_from_subcommand_args(argv: List[str]) -> Dict[str, str]:
    """Return the region and config file path args in argv if they're there."""
    argv_parser = argparse.ArgumentParser(add_help=False)
    argv_parser.add_argument("-c", "--config")
    argv_parser.add_argument("-r", "--region")
    return vars(argv_parser.parse_known_args(argv))


def _get_region_to_use(argv: List[str]) -> Optional[str]:
    """Make a best-effort attempt to figure out which region we should query for resources."""
    # TODO: is there a way to do this without replicating logic in the CLI?
    # Order or precedence:
    # 1) CLI arg (-r,--region)
    # 2) config file (which will first try the AWS_DEFAULT_REGION envrion)
    argv_options = _parse_region_and_config_from_subcommand_args(argv)
    if argv_options.get("region"):
        return argv_options.get("region")
    # Initialize config object so it can do figure out the rest and set AWS_DEFAULT_REGION
    # TODO: do this without the config?
    # TODO: add option to config constructor to avoid full initialization (which invokes a lot of network calls)
    PclusterConfig.init_aws(argv_options.get("config"))
    return os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def _get_list_of_clusters(subcommand: str, argv: List[str]) -> List[str]:
    """Return list of clusters from cached file."""
    region = _get_region_to_use(argv)
    # TODO: use the above region to read the cached JSON file the daemon maintains
    # TODO: turn this into a decorator that's used by the appropriate subcommands
    if not os.path.exists(CLUSTERS_LIST_CACHE_FILE):
        _populate_clusters_list_cache_file()
    clusters = []
    with open(CLUSTERS_LIST_CACHE_FILE) as cluster_names_file:
        clusters = [cluster_name_line.strip() for cluster_name_line in cluster_names_file]
    LOGGER.debug(f"Found the following active clusters: {' '.join(clusters)}")
    return clusters


def _get_completions_for_createami_subcommand(subcommand: str, argv: List[str]) -> List[str]:
    """TODO: implement me."""
    return []


def _get_completions_for_dcv_subcommand(subcommand: str, argv: List[str]) -> List[str]:
    """TODO: implement me."""
    return []


def _get_completions_for_pcluster_subcommand(subcommand_argv: List[str]) -> List[str]:
    """
    Get completions for the given pcluster subcommand.

    :subcommand_argv: list of strings where the first item is a pcluster subcommand and
                      the remaining items are the args that have been passed to that
                      subcommand thus far
    """
    # TODO: also suggest positional args specific to each command
    _no_completions_function: Callable[[str, List[str]], List[str]] = lambda subcommand, argv: []
    subcommand_to_completions_getter = {
        "create": _no_completions_function,
        "update": _get_list_of_clusters,
        "delete": _get_list_of_clusters,
        "start": _get_list_of_clusters,
        "stop": _get_list_of_clusters,
        "status": _get_list_of_clusters,
        "list": _no_completions_function,
        "instances": _get_list_of_clusters,
        # TODO: Not allowed to pass region of config for `pcluster ssh`, but _get_list_of_clusters
        #       will still look for it in the command line. Create a wrapper around it?
        "ssh": _get_list_of_clusters,
        "createami": _get_completions_for_createami_subcommand,
        "configure": _no_completions_function,
        "version": _no_completions_function,
        "dcv": _get_completions_for_dcv_subcommand,
    }
    subcommand = subcommand_argv[0]
    if subcommand not in subcommand_to_completions_getter:
        LOGGER.error(f"No completion suggestions available for `pcluster {subcommand}`")
        return []
    LOGGER.debug(f"Getting completions for `pcluster {subcommand}`")
    return subcommand_to_completions_getter[subcommand](subcommand, subcommand_argv[1:])


def main() -> None:
    config_logger(LOGGER, LOG_PATH)
    LOGGER.debug("pcluster completion script starting")
    args = parse_args()
    if args.subcommand_plus_args:
        completions = _get_completions_for_pcluster_subcommand(args.subcommand_plus_args)
    else:
        completions = _get_pcluster_commands()
    print("\n".join(completions))

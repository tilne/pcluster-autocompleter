#!/usr/bin/env python
"""Get tab-completion candidates for a pcluster command."""

import argparse
import errno
import logging
import os
import re
import subprocess as sp
from logging.handlers import RotatingFileHandler

# TODO: implement file locking for this
# TODO: handle region
CLUSTERS_LIST_CACHE_FILE = "/tmp/pcluster-completion-candidates-cluster-list.txt"
LOGGER = logging.getLogger(__name__)


def config_logger():
    logfile = "/tmp/pcluster-completions-log.txt"
    try:
        os.makedirs(os.path.dirname(logfile))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise  # can safely ignore EEXISTS for this purpose...

    log_file_handler = RotatingFileHandler(logfile, maxBytes=5 * 1024 * 1024, backupCount=1)
    log_file_handler.setLevel(logging.DEBUG)
    log_file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")
    )
    LOGGER.addHandler(log_file_handler)
    LOGGER.setLevel(logging.DEBUG)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subcommand_plus_args", nargs="*")
    return parser.parse_args()


def _get_pcluster_commands():
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


def _populate_clusters_list_cache_file():
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


def _get_list_of_clusters(subcommand, argv):
    """Return list of clusters from cached file."""
    # TODO: turn this into a decorator that's used by the appropriate subcommands
    if not os.path.exists(CLUSTERS_LIST_CACHE_FILE):
        _populate_clusters_list_cache_file()
    clusters = []
    with open(CLUSTERS_LIST_CACHE_FILE) as cluster_names_file:
        clusters = [cluster_name_line.strip() for cluster_name_line in cluster_names_file]
    LOGGER.debug(f"Found the following active clusters: {' '.join(clusters)}")
    return clusters


def _get_completions_for_createami_subcommand(subcommand, argv):
    """TODO: implement me."""
    return []


def _get_completions_for_dcv_subcommand(subcommand, argv):
    """TODO: implement me."""
    return []


def _get_completions_for_pcluster_subcommand(subcommand_argv):
    """
    Get completions for the given pcluster subcommand.

    :subcommand_argv: list of strings where the first item is a pcluster subcommand and
                      the remaining items are the args that have been passed to that
                      subcommand thus far
    """
    # TODO: also suggest positional args specific to each command
    _no_completions_function = lambda subcommand, argv: []
    subcommand_to_completions_getter = {
        "create": _no_completions_function,
        "update": _get_list_of_clusters,
        "delete": _get_list_of_clusters,
        "start": _get_list_of_clusters,
        "stop": _get_list_of_clusters,
        "status": _get_list_of_clusters,
        "list": _no_completions_function,
        "instances": _get_list_of_clusters,
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


def main():
    config_logger()
    LOGGER.debug("pcluster completion script starting")
    args = parse_args()
    if args.subcommand_plus_args:
        completions = _get_completions_for_pcluster_subcommand(args.subcommand_plus_args)
    else:
        completions = _get_pcluster_commands()
    print("\n".join(completions))


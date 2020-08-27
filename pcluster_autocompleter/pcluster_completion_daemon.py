#!/usr/bin/env python
"""
Periodically call `pcluster list` in all known regions and cache the results for use by the
script that provides tab-completion suggestions for the pcluster CLI.
"""

import json
import logging
import subprocess as sp
import time
from datetime import datetime, timedelta

from utils import config_logger


# TODO: make this stuff configurable
LOOP_TIME_IN_SECONDS = 600  # start another loop every 10 minutes
LOG_PATH = "/tmp/pcluster-completions-daemon-log.txt"
LOGGER = logging.getLogger(__name__)
REGIONS = [
    # TODO: read this dynamically if static values aren't configured in config?
    "eu-west-1",
    "eu-west-2",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
]
CACHE_PATH = "/tmp/pcluster-completions-daemon-cache.txt"


def _parse_fields_from_pcluster_list_line(output_line):
    """Parse the fields from a line of `pcluster list` output."""
    fields = output_line.strip().split()

    # Expected format for a given line is `<name> <status> <CLI version>
    # If there are fewer fields than expected, assume that the existing fields are the
    # expected ones, and append a None for the missing ones. (TODO: what if they're all missing?)
    # Similarly, if there are too many assume the existing ones are as expected.
    expected_num_fields = 3
    if len(fields) != expected_num_fields:
        LOGGER.warning(
            "Following line of output from `pcluster list` has {len(fields)} fields rather than the expected "
            "{expected_num_fields}: {ouput_line.strip()}"
        )
        if len(fields) < expected_num_fields:
            fields.extend(["" for _ in range(expected_num_fields - len(fields))])
        else:
            fields = fields[:3]

    return {"name": fields[0], "status": fields[1], "cli_version": fields[2]}


def _parse_pcluster_list_output(output):
    """Parse the output from `pcluster list` and return a list of clusters."""
    return [_parse_fields_from_pcluster_list_line(output_line) for output_line in output.splitlines()]


def _get_active_clusters_for_region(region):
    # TODO: handle no network connection
    output = sp.check_output(["pcluster list", "-r", region, "--help"], shell=True).decode()
    return _parse_pcluster_list_output(output)


def _get_active_clusters_for_all_regions():
    return [{"region": region, "clusters": _get_active_clusters_for_region(region)} for region in REGIONS]


def _write_cluster_info_to_cache(clusters_info):
    # TODO: file locking
    # TODO: is it ever necessary to update existing info rather than dumping the new info?
    with open(CACHE_PATH, "w") as cache_file:
        json.dump(clusters_info, cache_file)


def _cache_active_clusters_for_all_regions():
    active_clusters = _get_active_clusters_for_all_regions()
    _write_cluster_info_to_cache(active_clusters)


def _poll_cluster_statuses():
    while True:
        next_loop_start_time = datetime.now() + timedelta(seconds=LOOP_TIME_IN_SECONDS)
        _cache_active_clusters_for_all_regions()
        seconds_until_next_loop = (datetime.now() - next_loop_start_time).total_seconds()
        time.sleep(seconds_until_next_loop)


def main():
    config_logger(LOGGER, LOG_PATH)
    _poll_cluster_statuses()

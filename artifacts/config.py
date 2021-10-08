# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
API for The Things Stack configuration files.
"""

import yaml

class Config():
    """ API for The Things Stack configuration files """

    # File structure demanded by The Things Stack
    DOCKER_COMPOSE_YAML = 'docker-compose.yml'
    STACK_CONFIG_YAML = './config/stack/ttn-lw-stack-docker.yml'

    def get_docker_compose_yaml(self):
        """ Gets Docker compose file as a YAML object """
        with open(self.DOCKER_COMPOSE_YAML, encoding="utf-8") as docker_compose_file:
            return yaml.safe_load(docker_compose_file)

    def get_stack_config_yaml(self):
        """ Gets The Things Stack configuration file as a YAML object """
        with open(self.STACK_CONFIG_YAML, encoding="utf-8") as stack_config_file:
            return yaml.safe_load(stack_config_file)

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Shares TLS certificates with The Things Stack Docker container.
"""

import os
from config import Config

config = Config()
stack_config_yaml = config.get_stack_config_yaml()
docker_compose_yaml = config.get_docker_compose_yaml()

# If using local TLS secrets (within our artifacts), we need to make them accessible
# to the user that runs The Things Stack in the Docker container
if stack_config_yaml['tls']['source'] == 'file':
    print('Modifying permissions of local TLS secrets')

    os.chown(docker_compose_yaml['secrets']['ca.pem']['file'], 886, 886)
    os.chown(docker_compose_yaml['secrets']['cert.pem']['file'], 886, 886)
    os.chown(docker_compose_yaml['secrets']['key.pem']['file'], 886, 886)

# If using Acme Lets Encrypt certificates, we need a directory to hold them and
# we need to make that accessible to the user that runs The Things Stack in the Docker container
if stack_config_yaml['tls']['source'] == 'acme':
    print('Creating acme directory')
    os.mkdir('acme')
    os.chown('acme', 886, 886)

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Creates a minimal configuration needed to successfully deploy the component for a
given domain name or IP address. It is intended to only be used on the default
TTS configuration in the repository, for quick-start non-production purposes.
Normally the user should hand configure the stack instead. Note: the default
configuration is suitable only for x86-compatible Linux hosts.

Example execution:
python3 create_config_minimal.py example.com
"""

import argparse
import secrets

STACK_CONFIG_YAML = 'tts-config/config/stack/ttn-lw-stack-docker.yml'
DEFAULT_DOMAIN = 'thethings.example.com'

parser = argparse.ArgumentParser(description='Create minimal TTS configuration file')
parser.add_argument('domain', help='Domain name or IP address of deployed TTS (Example: example.com)')
args = parser.parse_args()

with open(STACK_CONFIG_YAML, 'r', encoding="utf-8") as stack_config_file:
    stack_config_file_str = stack_config_file.read()

stack_config_file_str = stack_config_file_str.replace(DEFAULT_DOMAIN, args.domain)
stack_config_file_str = stack_config_file_str.replace("block-key: ''", "block-key: '{}'".format(secrets.token_hex(32)))
stack_config_file_str = stack_config_file_str.replace("hash-key: ''", "hash-key: '{}'".format(secrets.token_hex(64)))
stack_config_file_str = stack_config_file_str.replace("client-secret: 'console'",
                                                      "client-secret: '{}'".format(secrets.token_hex(32)))

with open(STACK_CONFIG_YAML, 'w', encoding="utf-8") as stack_config_file:
    stack_config_file.write(stack_config_file_str)

print('{} updated with minimal configuration'.format(STACK_CONFIG_YAML))

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the create_config_minimal.py script
"""
import runpy
import sys

STACK_CONFIG_YAML = 'tts-config/config/stack/ttn-lw-stack-docker.yml'
DEFAULT_DOMAIN_NAME = 'thethings.example.com'
DEFAULT_KEY = ''
DEFAULT_SECRET = 'console'
DOMAIN_NAME = 'mydomain.com'
FAKE_SECRET='deadface'

def config(domain, key, secret):
    """ Create a configuration fragment """
    config_str =\
    f"""
    is:
    email:
        sender-address: 'noreply@{domain}'
        network:
        console-url: 'https://{domain}/console'
    http:
    cookie:
        block-key: '{key}'
        hash-key: '{key}'
    console:
    oauth:
        client-secret: '{secret}'
    """

    return config_str

def check_config(mocker, config_in, config_expected):
    """ Check that the config is correctly changed or not """
    file = mocker.patch('builtins.open', mocker.mock_open(read_data=config_in))
    mocker.patch('secrets.token_hex', return_value=FAKE_SECRET)
    sys.argv[1:] = [DOMAIN_NAME]
    runpy.run_module('create_config_minimal')

    file.assert_any_call(STACK_CONFIG_YAML, 'r', encoding="utf-8")
    file.assert_any_call(STACK_CONFIG_YAML, 'w', encoding="utf-8")
    handle = file()
    handle.write.assert_called_once_with(config_expected)

def test_create_config_minimal_default(mocker):
    """ Confirm that the default config is correctly updated """
    config_before = config(DEFAULT_DOMAIN_NAME, DEFAULT_KEY, DEFAULT_SECRET)
    config_after = config(DOMAIN_NAME, FAKE_SECRET, FAKE_SECRET)
    check_config(mocker, config_before, config_after)

def test_create_config_minimal_non_default(mocker):
    """ Confirm that the config is only updated if it's default """
    config_minimal = config(DOMAIN_NAME, FAKE_SECRET, FAKE_SECRET)
    check_config(mocker, config_minimal, config_minimal)

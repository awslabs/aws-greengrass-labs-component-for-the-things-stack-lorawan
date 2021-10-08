# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the artifacts.share_certs module
"""
import runpy
import sys

DOCKER_COMPOSE_YAML = 'docker-compose.yml'
STACK_CONFIG_YAML = './config/stack/ttn-lw-stack-docker.yml'

def test_tls_source_file(mocker):
    """ Confirm that local TLS files are shared """
    os_mkdir = mocker.patch('os.mkdir')
    os_chown = mocker.patch('os.chown')
    open_file = mocker.patch('builtins.open', mocker.mock_open(read_data='tls:\n  source: file\n'\
        'secrets:\n  ca.pem:\n    file: ./ca.pem\n  cert.pem:\n    file: ./cert.pem\n  key.pem:\n    file: ./key.pem'))
    sys.path.append('artifacts')
    runpy.run_module('artifacts.share_certs')
    open_file.assert_any_call(DOCKER_COMPOSE_YAML, encoding="utf-8")
    open_file.assert_any_call(STACK_CONFIG_YAML, encoding="utf-8")
    os_chown.assert_any_call('./ca.pem', 886, 886)
    os_chown.assert_any_call('./cert.pem', 886, 886)
    os_chown.assert_any_call('./key.pem', 886, 886)
    os_mkdir.assert_not_called()

def test_tls_source_acme(mocker):
    """ Confirm that the Acme directory is created and shared """
    os_mkdir = mocker.patch('os.mkdir')
    os_chown = mocker.patch('os.chown')
    sys.path.append('artifacts')
    open_file = mocker.patch('builtins.open', mocker.mock_open(read_data='tls:\n  source: acme'))
    runpy.run_module('artifacts.share_certs')
    open_file.assert_any_call(DOCKER_COMPOSE_YAML, encoding="utf-8")
    open_file.assert_any_call(STACK_CONFIG_YAML, encoding="utf-8")
    os_chown.assert_called_with('acme', 886, 886)
    os_mkdir.assert_called_with('acme')

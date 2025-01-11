# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the artifacts.install module
"""
import runpy
import sys
import subprocess
import json
import pytest

ADMIN_PASS = 'foobar'
ADMIN_EMAIL = 'user@blah.com'
SERVER = 'https://foobar'
CONSOLE_OAUTH_SECRET = 'consolesecret'
NOC_OAUTH_SECRET = 'nocsecret'
DCS_OAUTH_SECRET = 'dcssecret'
DOCKER_COMPOSE_ENTERPRISE = '\nservices:\n  stack:\n    image: thethingsindustries/lorawan-stack:latest\n'
DOCKER_COMPOSE_OPEN_SOURCE = '\nservices:\n  stack:\n    image: thethingsnetwork/lorawan-stack:latest\n'
STACK_CONFIG_SINGLE =\
f"""
console:
  ui:
    canonical-url: {SERVER}/console
  oauth:
    client-secret: {CONSOLE_OAUTH_SECRET}
noc:
  ui:
    canonical-url: {SERVER}/noc
  oauth:
    client-secret: {NOC_OAUTH_SECRET}
dcs:
  ui:
    canonical-url: {SERVER}/claim
  oauth:
    client-secret: {DCS_OAUTH_SECRET}
"""


def secret_json():
    """ Create secret as a JSON dictionary """
    secret_string = '{"admin-password":"' + ADMIN_PASS + '","admin-email":"' + ADMIN_EMAIL +\
                    '","docker-compose.yml":"foo","config/stack/ttn-lw-stack-docker.yml":"bar"}'

    return json.loads(secret_string)

def check_output_assert(mock_check_output, extra_args, should_be_called=True):
    """ Confirm whether command correctly issued or not """
    args = ['docker', 'compose', 'run', '--rm', 'stack']
    args.extend(extra_args)

    try:
        mock_check_output.assert_any_call(args, shell=False, stderr=subprocess.STDOUT, timeout=60)

        if not should_be_called:
            pytest.fail(f'{args}\nCommand executed when it should not have been')
    except AssertionError as e:
        if should_be_called:
            pytest.fail(e)

def check_install(mocker, enterprise=True):
    """ Confirm that the stack installs correctly """
    sys.path.append('artifacts')
    get_secret = mocker.patch('secret.get_secret', return_value=secret_json())
    os_makedirs = mocker.patch('os.makedirs')
    subprocess_check_output = mocker.patch('subprocess.check_output')
    contents = DOCKER_COMPOSE_ENTERPRISE if enterprise else DOCKER_COMPOSE_OPEN_SOURCE
    file = mocker.patch('builtins.open', mocker.mock_open(read_data=contents + STACK_CONFIG_SINGLE))
    sys.argv[1:] = ['my_secret_arn']
    runpy.run_module('artifacts.install')

    get_secret.assert_called_once()
    os_makedirs.assert_any_call('config/stack', exist_ok=True)
    file.assert_any_call('docker-compose.yml', encoding="utf-8")
    file.assert_any_call('./config/stack/ttn-lw-stack-docker.yml', encoding="utf-8")

    check_output_assert(subprocess_check_output, ['is-db', 'migrate'])
    check_output_assert(subprocess_check_output, ['is-db', 'create-admin-user', '--id', 'admin',
                                                  '--password', ADMIN_PASS, '--email', ADMIN_EMAIL])
    check_output_assert(subprocess_check_output, ['is-db', 'create-oauth-client', '--id', 'cli',
                                                  '--name', 'Command Line Interface', '--owner', 'admin',
                                                  '--no-secret', '--redirect-uri', 'local-callback',
                                                  '--redirect-uri', 'code'])
    check_output_assert(subprocess_check_output, ['is-db', 'create-oauth-client', '--id', 'console',
                                                  '--name', 'Console', '--owner', 'admin',
                                                  '--secret', CONSOLE_OAUTH_SECRET, '--redirect-uri',
                                                  f'{SERVER}/console/oauth/callback', '--redirect-uri',
                                                  '/console/oauth/callback', '--logout-redirect-uri',
                                                  f'{SERVER}/console',
                                                  '--logout-redirect-uri', '/console'])

    # Installation steps that should only occur for Enterprise
    check_output_assert(subprocess_check_output, ['storage-db', 'init'], should_be_called=enterprise)
    check_output_assert(subprocess_check_output, ['noc-db', 'init'], should_be_called=enterprise)
    check_output_assert(subprocess_check_output, ['is-db', 'create-tenant'], should_be_called=enterprise)
    check_output_assert(subprocess_check_output, ['is-db', 'create-oauth-client', '--id', 'noc',
                                                  '--name', 'Network Operations Center', '--owner', 'admin',
                                                  '--secret', NOC_OAUTH_SECRET, '--redirect-uri',
                                                  f'{SERVER}/noc/oauth/callback', '--redirect-uri',
                                                  '/noc/oauth/callback', '--logout-redirect-uri',
                                                  f'{SERVER}/noc',
                                                  '--logout-redirect-uri', '/noc'],
                                                  should_be_called=enterprise)
    check_output_assert(subprocess_check_output, ['is-db', 'create-oauth-client', '--id', 'device-claiming',
                                                  '--name', 'Device Claiming Server', '--owner', 'admin',
                                                  '--secret', DCS_OAUTH_SECRET, '--redirect-uri',
                                                  f'{SERVER}/claim/oauth/callback', '--redirect-uri',
                                                  '/claim/oauth/callback', '--logout-redirect-uri',
                                                  f'{SERVER}/claim',
                                                  '--logout-redirect-uri', '/claim'],
                                                  should_be_called=enterprise)

def check_output_exception(mocker, mock_exception):
    """ Confirm subprocess.check_output exception handling """
    sys.path.append('artifacts')
    get_secret = mocker.patch('secret.get_secret', return_value=secret_json())
    os_makedirs = mocker.patch('os.makedirs')
    subprocess_check_output = mocker.patch('subprocess.check_output', side_effect=mock_exception)
    contents = DOCKER_COMPOSE_OPEN_SOURCE
    file = mocker.patch('builtins.open', mocker.mock_open(read_data=contents + STACK_CONFIG_SINGLE))
    sys.argv[1:] = ['my_secret_arn']

    # Exception should be caught and result in sys.exit(1)
    with pytest.raises(SystemExit) as system_exit:
        runpy.run_module('artifacts.install')
        assert system_exit.type == SystemExit
        assert system_exit.code == 1

    get_secret.assert_called_once()
    os_makedirs.assert_any_call('config/stack', exist_ok=True)
    file.assert_any_call('docker-compose.yml', encoding="utf-8")
    file.assert_any_call('./config/stack/ttn-lw-stack-docker.yml', encoding="utf-8")
    check_output_assert(subprocess_check_output, ['is-db', 'migrate'])

def test_stack_enterprise(mocker):
    """ Confirm that an enterprise deployment installs correctly """
    check_install(mocker, enterprise=True)

def test_stack_open_source(mocker):
    """ Confirm that an open source deployment installs correctly """
    check_install(mocker, enterprise=False)

def test_install_missing_argument():
    """ Confirm that the install fails if the secret ARN argument is missing  """
    sys.path.append('artifacts')

    # Don't pass any arguments
    sys.argv[1:] = []

    with pytest.raises(SystemExit) as system_exit:
        runpy.run_module('artifacts.install')
        assert system_exit.type == SystemExit
        assert system_exit.code == 1

def test_check_output_exception_called_process(mocker):
    """ Check catching of subprocess.CalledProcessError exception from subprocess.check_output() call """
    check_output_exception(mocker, subprocess.CalledProcessError('mocked command', 60, 'mocked output'.encode('utf-8')))

def test_check_output_exception_timeout(mocker):
    """ Check catching of subprocess.TimeoutExpired exception from subprocess.check_output() call """
    check_output_exception(mocker, subprocess.TimeoutExpired(1, 'mocked command', 'mocked output'.encode('utf-8')))

def test_check_output_exception(mocker):
    """ Check catching of general Exception from subprocess.check_output() call """
    check_output_exception(mocker, Exception('mocked exception'))

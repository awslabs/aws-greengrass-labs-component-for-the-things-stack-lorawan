# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Initializes and installs The Things Stack LoRaWAN component on the Greengrass edge runtime.

Example execution:
python3 install.py arn:aws:secretsmanager:REGION:ACCOUNT:secret:greengrass-tts-lorawan-ID
"""

import sys
import os
import subprocess
import shlex
from config import Config
from secret import get_secret

KEY_ADMIN_PASS = 'admin-password'
KEY_ADMIN_EMAIL = 'admin-email'

def create_files_from_secret():
    """ Extracts files from the configuration secret and creates them on disk """
    print('Creating files from secret')
    for key, value in secret.items():
        if key not in (KEY_ADMIN_PASS, KEY_ADMIN_EMAIL):
            print(f'Creating {key}')
            if '/' in key:
                os.makedirs(os.path.dirname(key), exist_ok=True)
            with open(key, 'w', encoding="utf-8") as file:
                file.write(value)

def run_command(command, alternate_message=None):
    """ Runs a command in a subprocess """
    print(command if alternate_message is None else alternate_message)
    success = False

    args = shlex.split(command)

    try:
        output = subprocess.check_output(args, shell=False, stderr=subprocess.STDOUT, timeout=60).decode("utf-8")
        print(output)
        success = True
    except subprocess.CalledProcessError as e:
        print(f'CalledProcessError: Return code = {e.returncode}\n{e.output.decode("utf-8")}')
    except subprocess.TimeoutExpired as e:
        print(f'TimeoutExpired: \n{e.output.decode("utf-8")}')
    except Exception as e:
        print(f'Exception:\n{e}')

    if not success:
        sys.exit(1)


if len(sys.argv) == 1:
    print('Secret ARN argument is missing', file=sys.stderr)
    sys.exit(1)

# Get the secure configuration from Secret Manager
secret = get_secret(sys.argv[1])

print('getcwd: ', os.getcwd())

create_files_from_secret()

config = Config()
stack_config_yaml = config.get_stack_config_yaml()
docker_compose_yaml = config.get_docker_compose_yaml()

# Determine if this is an Enterprise deployment (instead of Open Source)
enterprise_deployment = docker_compose_yaml['services']['stack']['image'].startswith('thethingsindustries')

# Determine if multi-tenancy is enabled (only available for Enterprise deployments)
multi_tenant = enterprise_deployment and 'tenancy' in stack_config_yaml and\
                'base-domains' in stack_config_yaml['tenancy']

# We'll register the OAuth clients for all tenants (if multi-tenant is enabled)
oauth_all_tenants = ' --tenant-id NULL' if multi_tenant else ''

# Initialize the database of the identity server
run_command('docker-compose run --rm stack is-db init')

# Steps required only for Enterprise deployments
if enterprise_deployment:
    # Initialize the database of the Application Server (storage integration)
    run_command('docker-compose run --rm stack storage-db init')
    # Create a tenant (must have at least one) - this will use tenancy.default-id from the configuration file
    run_command('docker-compose run --rm stack is-db create-tenant')

# Create an admin user
run_command('docker-compose run --rm stack is-db create-admin-user '\
            f'--id admin --password {secret[KEY_ADMIN_PASS]} --email {secret[KEY_ADMIN_EMAIL]}',
            'docker-compose run --rm stack is-db create-admin-user [CREDENTIALS REDACTED]')

# Register the CLI as an OAuth client
run_command('docker-compose run --rm stack is-db create-oauth-client '\
            '--id cli --name "Command Line Interface" --owner admin --no-secret '\
            f'--redirect-uri "local-callback" --redirect-uri "code"{oauth_all_tenants}')

# Register the Console as an OAuth client
run_command('docker-compose run --rm stack is-db create-oauth-client '\
            '--id console --name "Console" --owner admin '\
            f'--secret "{stack_config_yaml["console"]["oauth"]["client-secret"]}" '\
            f'--redirect-uri "/console/oauth/callback" --logout-redirect-uri "/console"{oauth_all_tenants}')

# Register the Device Claiming Server as an OAuth client (if Enterprise deployment)
if enterprise_deployment:
    run_command('docker-compose run --rm stack is-db create-oauth-client '\
                '--id device-claiming --name "Device Claiming Server" --owner admin '\
                f'--secret "{stack_config_yaml["dcs"]["oauth"]["client-secret"]}" '\
                f'--redirect-uri "/claim/oauth/callback" --logout-redirect-uri "/claim"{oauth_all_tenants}')

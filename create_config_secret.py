# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Creates or updates The Things Stack configuration secret in Secrets Manager.
This recursively bundles all files in the tts-config directory into the
secret. If using BYO certificates, these should be placed into the tts-config
directory prior to creating the secret. The gdk-config.json file should be
updated with the desired AWS region prior to running this script.

Example execution:
python3 create_config_secret.py mypassword user@example.com
"""

import argparse
import glob
from libs.secret import Secret
from libs.gdk_config import GdkConfig

DIRECTORY_CONFIG = 'tts-config/'

def escape(in_str):
    """ Escapes a string to make it suitable for storage in JSON """
    return in_str.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')

parser = argparse.ArgumentParser(description='Create (or update) a secret to '\
                                                'hold The Things Stack configuration securely')
parser.add_argument('adminPassword', help='Password of the "admin" user of The Things Stack')
parser.add_argument('adminEmail', help='Email address of the "admin" user of The Things Stack')
args = parser.parse_args()

secret_string = '{"admin-password":"' + args.adminPassword +\
                '","admin-email":"' + args.adminEmail

filenames = glob.glob(DIRECTORY_CONFIG + '/**/*.*', recursive=True)

print('Files to add to secret: {}'.format(filenames))

for filename in filenames:
    with open(filename, encoding="utf-8") as file:
        file_str = file.read()
        secret_string += '","{}":"'.format(filename.replace(DIRECTORY_CONFIG, '')) + escape(file_str)

secret_string += '"}'

gdk_config = GdkConfig()

secret = Secret(gdk_config.region())
secret_response = secret.put(secret_string)

print('\nBEFORE DEPLOYING COMPONENT:')
print('Add secretsmanager:GetSecretValue for {} to the Greengrass device role'.format(secret_response['ARN']))

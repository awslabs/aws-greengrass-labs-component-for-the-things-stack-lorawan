# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
API for The Things Stack configuration secret in Secrets Manager.
"""

import boto3

class Secret():
    """ API for The Things Stack configuration secret in Secrets Manager. """

    SECRET_NAME = 'greengrass-tts-lorawan'
    SECRET_DESCRIPTION = 'Secure configuration for The Things Stack component on Greengrass'

    def __init__(self, region):
        self.secretsmanager_client = boto3.client('secretsmanager', region_name=region)

    def get(self):
        """ Gets a secret from Secrets Manager """
        try:
            print('Getting The Things Stack secret {}'.format(self.SECRET_NAME))
            response = self.secretsmanager_client.get_secret_value(SecretId=self.SECRET_NAME)
        except Exception as e:
            print('Failed to get secret\nException: {}'.format(e))
            raise e

        return response

    def put(self, secret_string):
        """ Creates or updates The Things Stack secret in Secrets Manager """
        if self.exists():
            try:
                print('Updating The Things Stack secret {}'.format(self.SECRET_NAME))
                self.secretsmanager_client.update_secret(SecretId=self.SECRET_NAME,
                                                         SecretString=secret_string,
                                                         Description=self.SECRET_DESCRIPTION)
            except Exception as e:
                print('Failed to update The Things Stack secret\nException: {}'.format(e))
                raise e
            print('Successfully updated The Things Stack secret')
        else:
            try:
                print('Creating The Things Stack secret {}'.format(self.SECRET_NAME))
                self.secretsmanager_client.create_secret(Name=self.SECRET_NAME,
                                                         SecretString=secret_string,
                                                         Description=self.SECRET_DESCRIPTION)
            except Exception as e:
                print('Failed to create The Things Stack secret\nException: {}'.format(e))
                raise e
            print('Successfully created The Things Stack secret')

    def exists(self):
        """ Determines whether The Things Stack secret already exists in Secrets Manager """
        response = self.secretsmanager_client.list_secrets()
        if response is not None:
            for secret in response['SecretList']:
                if secret['Name'] == self.SECRET_NAME:
                    return True

        return False

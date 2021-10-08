# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Deploys a component version to the Greengrass core device target. This should be
called after create_component_version.py.

Example execution:
python3 deploy_component_version.py 1.0.0 ap-southeast-1 MyCoreDeviceThingName
"""

import argparse
import sys
import time
import boto3
from libs.secret import Secret

ACCOUNT = boto3.client('sts').get_caller_identity().get('Account')
COMPONENT_NAME = 'aws.greengrass.labs.TheThingsStackLoRaWAN'
COMPONENT_CLI = 'aws.greengrass.Cli'
COMPONENT_DOCKER_APPLICATION_MANAGER = 'aws.greengrass.DockerApplicationManager'
COMPONENT_SECRET_MANAGER = 'aws.greengrass.SecretManager'

def get_core_version():
    """ Gets the version of the Greengrass core (nucleus) """
    try:
        response = greengrassv2_client.get_core_device(coreDeviceThingName=args.coreDeviceThingName)
    except Exception as e:
        print('Failed to get core device\nException: {}'.format(e))
        sys.exit(1)

    return response['coreVersion']

def get_newest_component_version(component_name):
    """ Gets the newest version of a component """
    component_arn = 'arn:aws:greengrass:{}:aws:components:{}'.format(args.region, component_name)

    try:
        response = greengrassv2_client.list_component_versions(arn=component_arn)
    except Exception as e:
        print('Failed to get component versions for {}\nException: {}'.format(component_name, e))
        sys.exit(1)

    return response['componentVersions'][0]['componentVersion']

def create_deployment(cli_ver, dam_ver, sm_ver):
    """ Creates a deployment of The Things Stack LoRaWAN component to the given Greengrass core device """
    thing_arn = 'arn:aws:iot:{}:{}:thing/{}'.format(args.region, ACCOUNT, args.coreDeviceThingName)

    try:
        response = greengrassv2_client.create_deployment(
            targetArn=thing_arn,
            deploymentName='Deployment for {}'.format(args.coreDeviceThingName),
            components={
                COMPONENT_NAME: {
                    'componentVersion': args.version
                },
                COMPONENT_CLI: {
                    'componentVersion': cli_ver
                },
                COMPONENT_DOCKER_APPLICATION_MANAGER: {
                    'componentVersion': dam_ver
                },
                COMPONENT_SECRET_MANAGER: {
                    'componentVersion': sm_ver,
                    'configurationUpdate': {
                        'merge': '{"cloudSecrets":[{"arn":"' + secret_value['ARN'] + '"}]}'
                    }
                }
            }
        )
    except Exception as e:
        print('Failed to create deployment\nException: {}'.format(e))
        sys.exit(1)

    return response['deploymentId']

def wait_for_deployment_to_finish(deploy_id):
    """ Waits for the deployment to complete """
    deployment_status = 'ACTIVE'
    snapshot = time.time()

    while deployment_status == 'ACTIVE' and (time.time() - snapshot) < 120:
        try:
            response = greengrassv2_client.get_deployment(deploymentId=deploy_id)
            deployment_status = response['deploymentStatus']
        except Exception as e:
            print('Failed to get deployment\nException: {}'.format(e))
            sys.exit(1)

    if deployment_status == 'COMPLETED':
        print('Deployment completed successfully in {:.1f} seconds'.format(time.time() - snapshot))
    elif deployment_status == 'ACTIVE':
        print('Deployment timed out')
        sys.exit(1)
    else:
        print('Deployment error: {}'.format(deployment_status))
        sys.exit(1)


parser = argparse.ArgumentParser(description='Deploy a version of the {} component'.format(COMPONENT_NAME))
parser.add_argument('version', help='Version of the component to be created (Example: 1.0.0)')
parser.add_argument('region', help='AWS region (Example: us-east-1)')
parser.add_argument('coreDeviceThingName', help='Greengrass core device to deploy to')
args = parser.parse_args()

greengrassv2_client = boto3.client('greengrassv2', region_name=args.region)

secret = Secret(args.region)
secret_value = secret.get()

print('Deploying version {} to {}'.format(args.version, args.coreDeviceThingName))

# We deploy a CLI version that matches the core version.
# We deploy latest Docker Application Manager and latest Secret Manager.
cli_version = get_core_version()
dam_version = get_newest_component_version(COMPONENT_DOCKER_APPLICATION_MANAGER)
sm_version = get_newest_component_version(COMPONENT_SECRET_MANAGER)

print('Deploying with:\n{} {}\n{} {}\n{} {}'.format(COMPONENT_CLI, cli_version,
                                                    COMPONENT_DOCKER_APPLICATION_MANAGER, dam_version,
                                                    COMPONENT_SECRET_MANAGER, sm_version))

deployment_id = create_deployment(cli_version, dam_version, sm_version)
print('Deployment {} successfully created. Waiting for completion ...'.format(deployment_id))
wait_for_deployment_to_finish(deployment_id)

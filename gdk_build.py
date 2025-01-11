# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Custom build script for GDK component build operation. This script is not designed to
be executed directly. It is designed to be used by GDK.

Prior to running "gdk component build", the user should:
1) Configure TLS certificates: https://www.thethingsindustries.com/docs/getting-started/installation/certificates/
2) If BYO/generating certificate files, then add them to the tts-config directory (or generate with create_certs.sh)
3) Configure the LoRaWAN stack (https://www.thethingsindustries.com/docs/getting-started/installation/configuration/)
   (or generate a minimal configuration with create_config_minimal.py)
4) If using an Enterprise license file, add it to the tts-config directory
5) Set the desired AWS region in ggk-config.json.
6) Create or update The Things Stack secret by running create_config_secret.py

Example execution:
gdk component build
"""

import json
import shutil
import yaml
from libs.secret import Secret
from libs.gdk_config import GdkConfig

DIRECTORY_ARTIFACTS = 'artifacts/'
DIRECTORY_BUILD = 'greengrass-build/artifacts/'
FILE_RECIPE_TEMPLATE = 'recipe.yaml'
FILE_RECIPE = 'greengrass-build/recipes/recipe.yaml'
FILE_ZIP_BASE = 'tts'
FILE_ZIP_EXT = 'zip'
FILE_DOCKER_COMPOSE = 'docker-compose.yml'


def create_recipe():
    """ Creates the component recipe, filling in the Docker images and Secret ARN """
    print(f'Creating recipe {FILE_RECIPE}')

    secret_json = json.loads(secret_value['SecretString'])

    docker_compose_yaml = yaml.safe_load(secret_json[FILE_DOCKER_COMPOSE])

    with open(FILE_RECIPE_TEMPLATE, encoding="utf-8") as recipe_template_file:
        recipe_str = recipe_template_file.read()

    recipe_str = recipe_str.replace('COMPONENT_NAME', gdk_config.name())
    if gdk_config.version() != 'NEXT_PATCH':
        recipe_str = recipe_str.replace('COMPONENT_VERSION', gdk_config.version())

    recipe_str = recipe_str.replace('$SECRET_ARN', secret_value['ARN'])
    recipe_str = recipe_str.replace('$DOCKER_IMAGE_TTS', docker_compose_yaml['services']['stack']['image'])

    if 'postgres' in docker_compose_yaml['services']:
        recipe_str = recipe_str.replace('$DOCKER_IMAGE_DB', docker_compose_yaml['services']['postgres']['image'])
    else:
        print(f'PostgreSQL is not included in {FILE_DOCKER_COMPOSE}')

    if 'redis' in docker_compose_yaml['services']:
        recipe_str = recipe_str.replace('$DOCKER_IMAGE_REDIS', docker_compose_yaml['services']['redis']['image'])
    else:
        print(f'Redis is not included in {FILE_DOCKER_COMPOSE}')

    recipe_yaml = yaml.safe_load(recipe_str)

    for index, artifact in reversed(list(enumerate(recipe_yaml['Manifests'][0]['Artifacts']))):
        if '$DOCKER_IMAGE_' in artifact['Uri']:
            print(f'Excluding template artifact {str(recipe_yaml["Manifests"][0]["Artifacts"][index])}')
            del recipe_yaml['Manifests'][0]['Artifacts'][index]

    recipe_str = yaml.dump(recipe_yaml, indent=2, sort_keys=False)

    with open(FILE_RECIPE, 'w', encoding="utf-8") as recipe_file:
        recipe_file.write(recipe_str)

    print('Created recipe')

def create_artifacts():
    """ Creates the artifacts archive as a ZIP file """
    file_name = DIRECTORY_BUILD + gdk_config.name() + '/' + gdk_config.version() + '/' + FILE_ZIP_BASE
    print(f'Creating artifacts archive {file_name}')
    shutil.make_archive(file_name, FILE_ZIP_EXT, DIRECTORY_ARTIFACTS)
    print('Created artifacts archive')


gdk_config = GdkConfig()

secret = Secret(gdk_config.region())
secret_value = secret.get()

create_recipe()
create_artifacts()

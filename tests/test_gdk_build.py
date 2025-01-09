# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the gdk_build.py script
"""
import runpy
import yaml

NAME = 'FooBar'
VERSION = 'rubbish'
REGION = 'neverland'

DIRECTORY_ARTIFACTS = 'artifacts/'
DIRECTORY_BUILD = 'greengrass-build/artifacts/'
FILE_RECIPE_TEMPLATE = 'recipe.yaml'
FILE_RECIPE = 'greengrass-build/recipes/recipe.yaml'
FILE_DOCKER_COMPOSE = 'docker-compose.yml'
FILE_ZIP_BASE = 'tts'
FILE_ZIP_EXT = 'zip'

SECRET_ARN = 'rhubarb'
NAME_COCKROACH = 'cockroach'
NAME_POSTGRES = 'postgres'
IMAGE_COCKROACH = 'cockroachdb/cockroach:latest'
IMAGE_POSTGRES = 'postgres:latest'
IMAGE_REDIS = 'redis:latest'
IMAGE_STACK = 'thethingsnetwork/lorawan-stack:latest'

OMIT = 'omit'

def recipe(version, secret_arn, image_tts, image_db, image_redis):
    """ Create a recipe string fragment """
    recipe_str =\
    f"""
    {{
    "ComponentName": "{NAME}",
    "ComponentVersion": "{version}",
    "ComponentConfiguration": {{
        "DefaultConfiguration": {{
        "secretArn": "{secret_arn}"
        }}
    }},
    "Manifests": [
        {{
        "Artifacts": [
            {{
            "Uri": "docker:{image_tts}"
            }},
            {{
            "Uri": "docker:{image_db}"
            }},
            {{
            "Uri": "docker:{image_redis}"
            }}
        ]
        }}
    ]
    }}
    """

    recipe_json = yaml.safe_load(recipe_str)

    if image_redis is OMIT:
        del recipe_json['Manifests'][0]['Artifacts'][2]
    if image_db is OMIT:
        del recipe_json['Manifests'][0]['Artifacts'][1]

    recipe_str = yaml.dump(recipe_json, indent=2, sort_keys=False)

    return recipe_str


def docker_compose(database, database_image, redis_image):
    """ Create a Docker compose fragment """
    docker_compose_str =\
    f"""
    services:
        {database}:
            image: {database_image}
        {'redis' if redis_image is not OMIT else OMIT}:
            image: {redis_image}
        stack:
            image: {IMAGE_STACK}
    """

    return docker_compose_str.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')


def check_gdk_build(mocker, db_name, db_image, redis_image=IMAGE_REDIS, version=VERSION):
    """ Confirm that the GDK build correctly assembles the recipe and the archive """
    gdk_config_class = mocker.patch('libs.gdk_config.GdkConfig')
    gdk_config = gdk_config_class.return_value
    gdk_config.name.return_value = NAME
    gdk_config.version.return_value = version
    secret_class = mocker.patch('libs.secret.Secret')
    secret = secret_class.return_value
    secret_string = '{"' + FILE_DOCKER_COMPOSE + '":"' + docker_compose(db_name, db_image, redis_image) + '"}'
    secret.get.return_value = {'SecretString':secret_string, 'ARN': SECRET_ARN}
    recipe_template_str = recipe(version, '$SECRET_ARN', '$DOCKER_IMAGE_TTS',\
                                 '$DOCKER_IMAGE_DB', '$DOCKER_IMAGE_REDIS')
    file = mocker.patch('builtins.open', mocker.mock_open(read_data=recipe_template_str))
    make_archive = mocker.patch('shutil.make_archive')
    runpy.run_module('gdk_build')

    file.assert_any_call(FILE_RECIPE_TEMPLATE, encoding="utf-8")
    file.assert_any_call(FILE_RECIPE, 'w', encoding="utf-8")
    recipe_str = recipe(version, SECRET_ARN, IMAGE_STACK, db_image, redis_image)
    file().write.assert_called_once_with(recipe_str)
    archive_name = DIRECTORY_BUILD + NAME + '/' + version + '/' + FILE_ZIP_BASE
    make_archive.assert_called_once_with(archive_name, FILE_ZIP_EXT, DIRECTORY_ARTIFACTS)
    gdk_config_class.assert_called_once()
    assert gdk_config.name.call_count == 2
    assert gdk_config.version.call_count ==(2 if version == 'NEXT_PATCH' else 3)
    gdk_config.region.assert_called_once()
    secret_class.assert_called_once()
    secret.get.assert_called_once()

def test_cockroach_and_redis(mocker):
    """ Recipe assembled with Coackroach and Redis both included """
    check_gdk_build(mocker, NAME_COCKROACH, IMAGE_COCKROACH)

def test_postgres_and_redis(mocker):
    """ Recipe assembled with Postgres and Redis both included """
    check_gdk_build(mocker, NAME_POSTGRES, IMAGE_POSTGRES)

def test_cockroach_only(mocker):
    """ Recipe assembled with Coackroach but Redis omitted """
    check_gdk_build(mocker, NAME_COCKROACH, IMAGE_COCKROACH, redis_image=OMIT)

def test_postgres_only(mocker):
    """ Recipe assembled with Postgres but Redis omitted """
    check_gdk_build(mocker, NAME_POSTGRES, IMAGE_POSTGRES, redis_image=OMIT)

def test_redis_only(mocker):
    """ Recipe assembled with Redis included, but databases omitted """
    check_gdk_build(mocker, OMIT, OMIT)

def test_all_omitted(mocker):
    """ Recipe assembled with databases and Redis omitted """
    check_gdk_build(mocker, OMIT, OMIT, redis_image=OMIT)

def test_next_patch(mocker):
    """ Recipe assembled with NEXT_PATCH version """
    check_gdk_build(mocker, NAME_POSTGRES, IMAGE_COCKROACH, version='NEXT_PATCH')

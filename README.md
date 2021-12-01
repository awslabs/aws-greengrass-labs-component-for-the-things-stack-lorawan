# AWS IoT Greengrass V2 Community Component - The Things Stack LoRaWAN 

[The Things Stack](https://www.thethingsindustries.com/docs/) is an [open-source LoRaWAN stack](https://github.com/TheThingsNetwork/lorawan-stack). Users can deploy the stack as [Open Source](https://hub.docker.com/r/thethingsnetwork/lorawan-stack) (free) or [Enterprise](https://hub.docker.com/r/thethingsindustries/lorawan-stack) (requires a [license](https://accounts.thethingsindustries.com/fee-calculator/)) from images available on Docker Hub.


This repository facilitates packaging The Things Stack into an AWS IoT Greengrass V2 component named **aws.greengrass.labs.TheThingsStackLoRaWAN**. This component enables customer use cases that require a private LoRaWAN Network Server (LNS) at the edge. For Enterprise deployments, ingestion into AWS IoT Core can then be achieved by deploying [The Things Stack AWS IoT default integration](https://www.thethingsindustries.com/docs/integrations/aws-iot/default/) into your AWS account. 


The Things Stack is also offered as [an AWS Marketplace AMI](https://aws.amazon.com/marketplace/pp/prodview-okhh3ofzhqj56). This Greengrass component is a logical equivalent, but pitching at the edge.

# Table of Contents
* [Architecture](#architecture)
* [Repository Contents](#repository-contents)
* [Requirements and Prerequisites](#requirements-and-prerequisites)
  * [Greengrass Core Device](#greengrass-core-device)
    * [Platform](#platform)
    * [Edge Runtime](#edge-runtime)
    * [Docker Requirements](#docker-requirements)
    * [Python Requirements](#python-requirements)
  * [Greengrass Cloud Services](#greengrass-cloud-services)
    * [Core Device Role](#core-device-role)
  * [Developer Machine](#developer-machine)
    * [AWS CLI](#aws-cli)
    * [cfssl](#cfssl)
    * [Python](#python)
    * [GDK CLI](#gdk-cli)
    * [Bash](#bash)
* [Getting Started](#getting-started)
  * [Quickstart](#quickstart)
  * [Slowstart](#slowstart)
    * [Manual Deployment](#manual-deployment)
    * [Example Execution](#example-execution)
    * [CI/CD Pipeline](#cicd-pipeline)
    * [Automated Testing](#automated-testing)
* [The Things Stack Configuration Tips](#the-things-stack-configuration-tips)
  * [Defaults](#defaults)
  * [Enterprise versus Open Source](#enterprise-versus-open-source)
  * [Production Deployments](#production-deployments)
  * [Image Architecture](#image-architecture)
  * [Pub/Sub Integration](#pubsub-integration)
* [Development](#development)
  * [Static Analysis](#static-analysis)
  * [Unit Tests](#unit-tests)

# Architecture

An overview of the system architecture is presented below.

![ggv2-tts-architecture](images/ggv2-tts-architecture.png)

The **aws.greengrass.labs.TheThingsStackLoRaWAN** component is a thin wrapper around a conventional The Things Stack deployment. The Things Stack is composed of multiple Docker containers, using Docker Compose. Subject to configuration, there may be a Redis container and either a PostreSQL or CockroachDB container, in addition to The Things Stack container.

The Things Stack is delivered as Docker images on Docker Hub. This component downloads Docker images from Docker Hub with the help of the [Docker application manager](https://docs.aws.amazon.com/greengrass/v2/developerguide/docker-application-manager-component.html) managed component.

The Things Stack configuration includes a considerable amount of sensitive information. Accordingly, the configuration is stored as a secret in [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/). This component gets its configuration from Secrets Manager with the help of the [Secret manager](https://docs.aws.amazon.com/greengrass/v2/developerguide/secret-manager-component.html) managed component. 

For Enterprise deployments, ingestion into AWS IoT Core can be best achieved by deploying [The Things Stack AWS IoT default integration](https://www.thethingsindustries.com/docs/integrations/aws-iot/default/) into your AWS account. 

The Things Stack offers [an API](https://www.thethingsindustries.com/docs/getting-started/api/) and various [integrations](https://www.thethingsindustries.com/docs/integrations/) that can be used for remote ingestion or control, or can be used by other Greengrass components to achieve local data processing and actions. The [Pub/Sub integration](https://www.thethingsindustries.com/docs/integrations/pubsub/) is a good option for achieving ingestion into AWS IoT Core from the Open Source edition of The Things Stack.

# Repository Contents

| Item                          | Description                                                                                           |
| ----------------------------- | ----------------------------------------------------------------------------------------------------- |
| /artifacts                    | Greengrass V2 component artifacts that run on the Greengrass edge runtime.                            |
| /cicd                         | CDK Typescript app for a CodePipeline CI/CD pipeline.                                                 |
| /images                       | Images for README files.                                                                              |
| /libs                         | Python libraries shared by Python scripts.                                                            |
| /robot                        | Robot Framework integration tests.                                                                    |
| /tests                        | Pytest unit tests.
| /tts-config                   | The Things Stack configuration files.                                                                 |
| create_certs.sh               | Creates self-signed TLS certificates for a given domain name or IP address.                           |
| create_config_minimal.py      | Creates a minimal configuration needed to deploy the component for a given domain name or IP address. |
| create_config_secret.py       | Creates or updates The Things Stack configuration secret in Secrets Manager.                          |
| deploy_component_version.py   | Deploys a component version to the Greengrass core device target.                                     |
| gdk_build.py                  | Custom build script for the Greengrass Development Kit (GDK) - Command Line Interface.                |
| gdk-config.json               | Configuration for the Greengrass Development Kit (GDK) - Command Line Interface.                      |
| quickstart.sh                 | Creates and deploys a component with default configuration for a given domain name or IP address.     |
| recipe.json                   | Greengrass V2 component recipe template.                                                              |

# Requirements and Prerequisites

## Greengrass Core Device

### Platform

This component requires that the Greengrass device be running a Linux operating system. It [supports all architectures supported by Greengrass itself](https://docs.aws.amazon.com/greengrass/v2/developerguide/setting-up.html#greengrass-v2-supported-platforms).

### Edge Runtime

The [Greengrass edge runtime needs to be deployed](https://docs.aws.amazon.com/greengrass/v2/developerguide/getting-started.html) to a suitable machine, virtual machine or EC2 instance. Please see The Things Stack stated [prerequisites](https://www.thethingsindustries.com/docs/getting-started/installation/) for guidance on the resources required. For a small number of devices and gateways, the processing and memory requirements are small.

The Greengrass machine or instance should not be running any process that uses any [ports that may be needed by The Things Stack](https://www.thethingsindustries.com/docs/reference/networking/). The specific ports used depends on your particular configuration of The Things Stack. The configuration generated by **quickstart.sh** requires ports 443, 1700, 6379, 8881, 8882, 8883, 8884, 8885, 8887, 26256 and 26257 to be available.

### Docker Requirements

The Things Stack is [generally composed as an application with multiple Docker containers](https://www.thethingsindustries.com/docs/getting-started/installation/configuration/), using Docker Compose. Images are obtained from Docker Hub.

Therefore your core device must [meet the requirements to run Docker containers using Docker Compose and Docker Hub](https://docs.aws.amazon.com/greengrass/v2/developerguide/run-docker-container.html).

Not all releases of these third-party container images support all Greengrass architectures. Care must be taken to select appropriate images and releases to suit your target architecture.

### Python Requirements

This component requires both **python3** and **pip3** to be installed on the core device.

## Greengrass Cloud Services

### Core Device Role

Assuming the bucket name in **gdk-config.json** is left unchanged, this component downloads artifacts from an S3 bucket named **greengrass-tts-lorawan-REGION-ACCOUNT**. Therefore your Greengrass core device role must allow the **s3:GetObject** permission for this bucket. For more information: https://docs.aws.amazon.com/greengrass/v2/developerguide/device-service-role.html#device-service-role-access-s3-bucket

Additionally, this component downloads sensitive The Things Stack configuration from Secrets Manager. Therefore your Greengrass core device role must also allow the **secretsmanager:GetSecretValue** permission for the **greengrass-tts-lorawan-ID** secret. 

Policy template to add to your device role (substituting correct values for ACCOUNT, REGION and ID):

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::greengrass-tts-lorawan-REGION-ACCOUNT/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:greengrass-tts-lorawan-ID"
    }
  ]
}
```

## Developer Machine

### AWS CLI

It may be necessary to [upgrade your AWS CLI](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-cli.html) if you wish to use any **greengrassv2** commands, as these are relatively recent additions to the CLI.

### cfssl

If you wish to generate your own self-signed TLS certificates for your domain, or use **quickstart.sh**, then [cfssl](https://github.com/cloudflare/cfssl) is required. Example installation on an Ubuntu or Debian machine:

```
sudo apt update
sudo apt install -y golang-cfssl
```

Or using Homebrew (Mac or Linux):

```
brew install cfssl
```

Alternatively consider installing from [released binaries](https://github.com/cloudflare/cfssl/releases) available in the [cfssl GitHub repository](https://github.com/cloudflare/cfssl). Windows installation executables are available.

### Python

Most of the scripts in this repository are Python scripts. They are Python 3 scripts and hence **python3** and **pip3** are required.

Package dependencies can be resolved as follows:

```
pip3 install -r requirements.txt
pip3 install -r robot/requirements.txt
```

Please consider to use a [virtual environment](https://docs.python.org/3/library/venv.html).

### GDK CLI

This component makes use of the [Greengrass Development Kit (GDK) - Command Line Interface (CLI)](https://github.com/aws-greengrass/aws-greengrass-gdk-cli). This can be installed as follows:

```
pip3 install git+https://github.com/aws-greengrass/aws-greengrass-gdk-cli.git
```

### Bash

The **quickstart.sh** and **create_certs.sh** scripts are Bash scripts. If using a Windows machine, you will need a Bash environment.

# Getting Started

Here we define two ways to get started: Quickstart or Slowstart.

All scripts are compatible with Linux, Mac or Windows operating systems, provided a Bash environment is available.

## Quickstart

The **quickstart.sh** bash script is supplied to help you get going fast. For experimentation in non-production settings.

Before running the script, users must:

1. Deploy Greengrass V2 to an x86-compatible Linux machine, virtual machine or EC2 instance. The default The Things Stack configuration settings will pull **amd64** images, hence the x86-compatibility requirement. 
2. Initialize the Greengrass core device to satisfy the [the requirements to run Docker containers using Docker Compose and Docker Hub](https://docs.aws.amazon.com/greengrass/v2/developerguide/run-docker-container.html).
3. Install **cfssl** on the developer machine.
4. Set the AWS region in **gdk-config.json**.

The Quickstart script will:

1. Install required Python packages.
2. Create self-signed certificates for a given domain name or IP address.
3. Create a minimal The Things Stack configuration for the given domain name or IP address.
4. Upload the secure configuration to a configuration secret in Secrets Manager.
5. Use GDK to build the component.
6. Use GDK to publish a new component version to Greengrass cloud services and upload artifacts to an S3 bucket.
7. Prompt you to add permissions for the configuration secret and artifacts bucket to the Greengrass core device role. 
8. Deploy the new component version to the Greengrass core (creating The Things Stack admin user in the process).
9. Run Robot Framework integration tests to confirm The Things Stack is running under Greengrass.

The script accepts 4 arguments:

1. Domain name or IP address (this can be an EC2 default domain name).
2. The password of The Things Stack admin user that will be created.
3. The email of The Things Stack admin user that will be created.
4. Greengrass Core device name.

Example execution:

```
bash quickstart.sh example.com mypassword user@example.com GGTheThingsStackLoRaWAN
```
## Slowstart

For any serious use of the component, Quickstart shall not be appropriate.

### Manual Deployment
If not using Quickstart, you must perform the following steps:

1. Deploy the Greengrass runtime to your machine, virtual machine or EC2 instance. This should be a Linux machine, but can be of any architecture. 
2. Configure the LoRaWAN stack as per https://www.thethingsindustries.com/docs/getting-started/installation/configuration/. Take care to select Docker images with the correct architecture. 
3. Configure certificates as per https://www.thethingsindustries.com/docs/getting-started/installation/certificates/.
4. If BYO/generating custom TLS certificates (rather than using Lets Encrypt), then add them to the **/tts-config** directory.
5. If using an Enterprise license file, add it to the **/tts-config** directory.
6. Set the AWS region in **gdk-config.json**.
7. Run **create_config_secret.py** to create the configuration secret in Secrets Manager.
8. Run **gdk component build** to build the component.
9. Run **gdk component publish** to create a component version in Greengrass cloud service, and upload artifacts to S3.
10. Add permissions for the configuration secret and artifacts bucket to the Greengrass core device role. 
11. Run **deploy_component_version.py** to deploy the new component version to your Greengrass device.

For iterative configuration changes, repeat steps 2, 7, 8, 9 and 11.


### Example Execution

Example of steps 7, 8, 9 and 11:

```
python3 create_config_secret.py mypassword user@example.com
gdk component build
gdk component publish
python3 deploy_component_version.py 1.0.0 MyCoreDeviceThingName
```

This example:

1. Creates a Secrets Manager secret in your account in the region specified in **gdk-config.json**.
2. Sets the admin user for The Things Stack to have password **mypassword** and email **user@example.com**.
3. Builds the component and publishes it to your account in the region specified in **gdk-config.json**. 
4. Deploys the new component version to Greengrass core device **MyCoreDeviceThingName**.

### CI/CD Pipeline

This repository offers a CodePipeline [CI/CD pipeline](cicd/README.md) as a CDK application. This can be optionally deployed to the same account as the Greengrass core.

This CI/CD pipeline automates steps 7, 8 and 10. Following deployment, it performs automated smoke tests to ensure that The Things Stack has started correctly. With the pipeline deployed, users can make iterative configuration changes, update the configuration secret using **create_config_secret.py**, and then trigger the CI/CD pipeline to handle the rest.

### Automated Testing

This repository includes an [automated test suite](robot/README.md) built on top of [Robot Framework](https://robotframework.org/). This can be run on demand from the command-line but it is also included as part of the CI/CD pipeline.

# The Things Stack Configuration Tips

Configuration of the LoRaWAN stack is mainly an exercise in editing **tts-config/docker-compose.yaml** and **tts-config/config/stack/ttn-lw-stack-docker.yml**. Please consult [The Things Stack configuration documentation](https://www.thethingsindustries.com/docs/getting-started/installation/configuration/) for details.

## Defaults

The **tts-config/docker-compose.yaml** and **tts-config/config/stack/ttn-lw-stack-docker.yml** files in this repository are The
Things Stack Enterprise example configuration files, with the following divergence:

- All Enterprise configuration elements are commented out so that it defaults to Open Source edition.
- Acme Let's Encrypt TLS certificates are disabled and custom TLS certificates are enabled.
- All non-TLS ports and endpoints are disabled.

This is to facilitate minimal effort in deploying this component to a server that only has an IP address, a local network DNS name
or an EC2 default domain name. 

## Enterprise versus Open Source

As compared to Open Source, an Enterprise license adds:

- [Device Claim Server](https://www.thethingsindustries.com/docs/devices/device-claiming/)
- Multi-tenant support
- [Storage Integration](https://www.thethingsindustries.com/docs/integrations/storage/)
- [AWS IoT Default Integration](https://www.thethingsindustries.com/docs/integrations/cloud-integrations/aws-iot/default/) support
- Support plan

## Production Deployments

Per The Things Stack recommendations, production deployments should reference specific Docker image tags (not just **latest**) and consideration should also be given to using external managed instances of the databases.

## Image Architecture

CockroachDB is not available for Arm architecture. You must use PostgreSQL instead.

The Things Stack images tagged **latest** on Docker Hub are not available for Arm architecture. Only formal releases are.

## Pub/Sub Integration

The [Pub/Sub integration](https://www.thethingsindustries.com/docs/integrations/pubsub/) can be used to achieve ingestion into AWS IoT Core. This is particularly useful for the Open Source edition of the stack since the [The Things Stack AWS IoT default integration](https://www.thethingsindustries.com/docs/integrations/aws-iot/default/) is only available for Enterprise deployments. In configuring the Pub/Sub integration, the ***Server URL*** should define the AWS IoT Core endpoint as follows:

```
mqtts://ENDPOINTID-ats.iot.ap-REGION.amazonaws.com:8883
```

# Development

## Static Analysis

Static analysis is performed using [Pylint](https://pylint.org/). Example execution:

```
pylint artifacts libs tests *.py
```

## Unit Tests

Unit tests are performed using [pytest](https://pytest.org/) and [moto](https://github.com/spulec/moto).

Example execution:

```
pytest --cov=artifacts --cov=.
```

Producing an HTML coverage report into the **htmlcov** directory:

```
pytest --cov=artifacts --cov=. --cov-report=html
```

Producing a coverage report for just the on-device artifacts (100% coverage):

```
pytest --cov=artifacts
```

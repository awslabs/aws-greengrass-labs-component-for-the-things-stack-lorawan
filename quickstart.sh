#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# This script is designed for quickstart. It creates and deploys a component with default configuration
# for a given domain name or IP address. 
#
# Before running the script, users must deploy Greengrass V2 to an x86-compatible Linux machine or 
# instance (can be EC2). The default The Things Stack configuration settings shall pull amd64 images, 
# hence the x86-compatibility requirement. Users must also install cfssl on their developer machine. 
#
# This script will:
# 1) Install required Python packages.
# 2) Create self-signed certificates for a given domain name or IP address.
# 3) Create a minimal The Things Stack configuration for the given domain name or IP address.
# 4) Upload the secure configuration to Secrets Manager.
# 5) Create a new component version.
# 6) Deploy the new component version to the Greengrass core.
# 7) Run Robot Framework integration tests to confirm The Things Stack is running under Greengrass.
#
# Example execution:
# bash quickstart.sh example.com ap-southeast-1 mypassword user@example.com 1.0.0 GGTheThingsStackLoRaWAN

# Fail if we don't get the correct number of arguments
if [ "$#" -ne 6 ]; then
    echo "Usage: bash quickstart.sh domain region adminPassword adminEmail componentVersion GGCoreDeviceName"
    exit 1
fi

# Exit when any command fails
set -e

banner() {
    echo -e "\n---------- $1 ----------"
}

# Install requirements
banner "Install required packages"
pip3 install -r requirements.txt
pip3 install -r robot/requirements.txt

# Create self-signed certificates for the given domain name or IP address
banner "Create certificates"
bash create_certs.sh $1

# Generate the minimal required The Things Stack configuration for the given domain name or IP address
banner "Create minimal The Things Stack configuration" 
python3 create_config_minimal.py $1

# Create The Things Stack configuration secret in Secrets Manager to hold the configuration securely
banner "Create or update The Things Stack configuration secret" 
python3 create_config_secret.py $2 $3 $4

# Create a new component version
banner "Create a Greengrass component version"
python3 create_component_version.py $5 $2

# Don't let them proceed until they've added the S3 bucket and secret permissions to the Greengrass device role
done=0
while [ $done -eq 0 ]; do
    echo "Have you added the bucket and secret permissions to the Greengrass device role? ('Press 'y' for yes or 'x' to exit)"
    read -rsn1 keypress

    if [ "$keypress" = "x" ]; then
        echo "Deployment not performed"
        exit 1
    elif [ "$keypress" = "y" ]; then
        done=1
    fi
done

# Deploy the new component version
banner "Deploy the Greengrass component version" 
python3 deploy_component_version.py $5 $2 $6

# Run the Robot Framework integration tests
banner "Run integration tests" 
cd robot
robot --pythonpath libs --variable DOMAIN_NAME:$1 --variable ADMIN_PASSWORD:$3 --xunit results.xml --removekeywords NAME:Login suites

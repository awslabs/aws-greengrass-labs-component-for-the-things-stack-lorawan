#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Generates self-signed certificates for a given domain name or IP address. This is intended
# for generation of non-production certificates only. Deposits the generated certificates
# into the tts-config directory, ready for creation of the configuration secret.
#
# cfssl is a prerequisite.
#
# Example execution:
# bash create_certs.sh example.com

# Fail if no domain name or IP address supplied
if [ -z "$1" ]; then
    echo "No domain name or IP address supplied\nUsage: bash create_certs.sh example.com"
    exit 1
fi

# Fail gracefully if cfssl is not installed
if ! command -v cfssl &> /dev/null
then
    echo "cfssl is not installed!"
    echo "Ubuntu/Debian: sudo apt install golang-cfssl"
    echo "Mac: brew install cfssl"
    echo "Windows: Download installer from https://github.com/cloudflare/cfssl/releases"
    exit 1
fi

echo "Creating self-signed certificates for $1"

# Use default names
NAMES="\"names\": [{\"C\": \"NL\", \"ST\": \"Noord-Holland\", \"L\": \"Amsterdam\", \"O\": \"The Things Demo\"}]"

# Create the JSON files needed for certificate generation
CA_JSON=ca.json
CERT_JSON=cert.json
echo "Generating $CA_JSON"
echo "{$NAMES}" >> $CA_JSON
echo "Generating $CERT_JSON for host $1"
echo "{\"hosts\": [\"$1\"],$NAMES}" >> $CERT_JSON

# Generate ca.pem and then cert.pem and key.pem
echo "Generating CA"
cfssl genkey -initca $CA_JSON | cfssljson -bare ca
echo "Generating Certificate and Key"
cfssl gencert -ca ca.pem -ca-key ca-key.pem $CERT_JSON | cfssljson -bare cert
mv cert-key.pem key.pem

# Clean-up
echo "Removing $CA_JSON"
rm $CA_JSON
echo "Removing $CERT_JSON"
rm $CERT_JSON
echo "Removing CSRs"
rm *.csr
echo "Removing CA private key"
rm ca-key.pem

# Deploy
echo "Moving certificates and key to tts-config"
mv *.pem tts-config/.

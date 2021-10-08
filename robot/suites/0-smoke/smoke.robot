# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

*** Settings ***
Documentation   Smoke Tests
Library         RequestsLibrary
Suite Setup     Establish Session

*** Test Cases ***
Server Is Responsive
    ${response} =   Get On Session  session     https://${DOMAIN_NAME}
    Status Should Be    200     ${response}

Admin User Good Password Succeeds
    ${response} =   Login   ${ADMIN_PASSWORD}   204

Admin User Bad Password Fails
    ${response} =   Login   rubbish     400

*** Keywords ***
Establish Session
    Create Session  session     https://${DOMAIN_NAME}   verify=${False}     disable_warnings=1

Login
    [Arguments]     ${password}     ${status}
    ${data} =      Create Dictionary    user_id=admin   password=${password}
    ${headers} =   Create Dictionary    Content-Type=application/x-www-form-urlencoded
    ${response} =  Post On Session  session     /oauth/api/auth/login    data=${data}   headers=${headers}  expected_status=${status}
    Status Should Be    ${status}   ${response}

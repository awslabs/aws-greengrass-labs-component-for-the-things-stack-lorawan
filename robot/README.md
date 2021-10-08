# AWS Greengrass The Things Stack LoRaWAN Automated Testing

The automated test suite uses [Robot Framework](https://robotframework.org/) as a test harness.

## Installation

Besides Robot Framework itself, the Robot Framework [Requests Library](https://github.com/MarketSquare/robotframework-requests) is required.

```
pip3 install robotframework
pip3 install robotframework-requests
```
## User Guide

[Robot Framework User Guide](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html)

## Test Suite Execution

Substitute correct values for DOMAIN_NAME and ADMIN_PASSWORD.

```
robot --pythonpath libs --variable DOMAIN_NAME:example.com --variable ADMIN_PASSWORD:mypassword --xunit results.xml --removekeywords NAME:Login suites
```

## Output

Test progress and high level outcomes are indicated on standard out.

The __log.html__ file is a detailed time-stamped log. This is saved as an artifact of the test stage of the pipeline.

The __results.xml__ file is a JUnit-compatible output file that is suitable for ingestion by most CI/CD tools. It is used in the CodePipeline pipeline test stage to produce a test report.


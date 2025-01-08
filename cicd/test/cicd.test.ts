// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import * as Cicd from '../lib/cicd-stack';

test('Good Stack', () => {
    const app = new cdk.App({
      context: {
        ConnectionId: 'alpha',
        OwnerName: 'beta',
        RepositoryName: 'delta',
        BranchName: 'gamma',
        GreengrassCoreName: 'epsilon'
      }
    });

    const stack = new Cicd.CicdStack(app, 'MyTestStack');
    const template = Template.fromStack(stack)

    template.hasResourceProperties('AWS::CodePipeline::Pipeline', { Name: 'gg-ttsl-cicd-pipeline' });
    template.resourceCountIs('AWS::CodeBuild::Project', 3);
    template.hasResourceProperties('AWS::CodeBuild::Project', { Name: 'gg-ttsl-cicd-build' });
    template.hasResourceProperties('AWS::CodeBuild::Project', { Name: 'gg-ttsl-cicd-deploy' });
    template.hasResourceProperties('AWS::CodeBuild::Project', { Name: 'gg-ttsl-cicd-test' });
    template.resourceCountIs('AWS::S3::Bucket', 1);
    template.resourceCountIs('AWS::CodeBuild::ReportGroup', 2);
    template.hasResourceProperties('AWS::SNS::Topic', { TopicName: 'gg-ttsl-cicd-notification' });
    template.resourceCountIs('AWS::Events::Rule', 1);
});

test('Missing Context Variables', () => {
  const app = new cdk.App();
  expect(() => {
    new Cicd.CicdStack(app, 'MyTestStack');
  }).toThrow();
});
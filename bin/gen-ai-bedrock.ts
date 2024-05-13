#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { GenAiBedrockStack } from "../lib/gen-ai-bedrock-stack";

const app = new cdk.App();
new GenAiBedrockStack(app, "BedrockStack", {
  description: "Bedrock stack for Gen AI",
  env: { region: "us-east-1" },
});

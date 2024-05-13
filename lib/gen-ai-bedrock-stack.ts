import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { Effect, PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Bucket, BucketEncryption, EventType } from "aws-cdk-lib/aws-s3";
import { S3EventSourceV2 } from "aws-cdk-lib/aws-lambda-event-sources";

export class GenAiBedrockStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const bedrockLayer = new PythonLayerVersion(this, "BedrockLayer", {
      entry: "src/layers/bedrock",
      compatibleRuntimes: [Runtime.PYTHON_3_11],
    });

    const invokeBedrock = new PythonFunction(this, "ReplyToComplaintFunction", {
      functionName: "bedrock-reply-to-complaint",
      entry: "src/lambdas/reply_to_complaint",
      runtime: Runtime.PYTHON_3_11,
      handler: "handler",
      timeout: cdk.Duration.seconds(30),
      layers: [bedrockLayer],
    });

    this.allowInvokeModel(invokeBedrock);

    const bucket = new Bucket(this, "ResultBucket", {
      bucketName: `${this.account}-gen-ai-bedrock-lab`,
      encryption: BucketEncryption.S3_MANAGED,
    });

    const summariseText = new PythonFunction(this, "SummariseTextFunction", {
      functionName: "bedrock-summarise-text",
      entry: "src/lambdas/summarise_text",
      runtime: Runtime.PYTHON_3_11,
      handler: "handler",
      timeout: cdk.Duration.seconds(90),
      layers: [bedrockLayer],
    });

    this.allowInvokeModel(summariseText);
    this.addS3Trigger(summariseText, bucket, "input/summarise");
    bucket.grantReadWrite(summariseText);

    const convertToAudio = new PythonFunction(this, "ConvertToAudioFunction", {
      functionName: "convert-text-to-audio",
      entry: "src/lambdas/convert_to_audio",
      runtime: Runtime.PYTHON_3_11,
      handler: "handler",
      timeout: cdk.Duration.seconds(30),
    });

    this.allowPolly(convertToAudio);
    this.addS3Trigger(convertToAudio, bucket, "output/summary");
    bucket.grantReadWrite(convertToAudio);
  }

  private addS3Trigger(
    pyFunction: PythonFunction,
    bucket: Bucket,
    prefix: string,
  ) {
    pyFunction.addEventSource(
      new S3EventSourceV2(bucket, {
        events: [EventType.OBJECT_CREATED],
        filters: [{ prefix: prefix }],
      }),
    );
  }

  private allowInvokeModel(pyFunction: PythonFunction) {
    pyFunction.addToRolePolicy(
      new PolicyStatement({
        effect: Effect.ALLOW,
        actions: ["bedrock:InvokeModel"],
        resources: ["*"],
      }),
    );
  }

  private allowPolly(pyFunction: PythonFunction) {
    pyFunction.addToRolePolicy(
      new PolicyStatement({
        effect: Effect.ALLOW,
        actions: ["polly:SynthesizeSpeech"],
        resources: ["*"],
      }),
    );
  }
}

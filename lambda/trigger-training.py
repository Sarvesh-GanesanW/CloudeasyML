import boto3
import json
import os
from datetime import datetime

eks_client = boto3.client("eks")
k8s_client = None

EKS_CLUSTER_NAME = os.environ.get("EKS_CLUSTER_NAME", "ml-cluster")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
IMAGE_TAG = os.environ.get("IMAGE_TAG", "latest")


def lambda_handler(event, context):
    try:
        jobId = f"lambda-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        fredApiKey = event.get("fredApiKey", os.environ.get("FRED_API_KEY", ""))
        targetColumn = event.get("targetColumn", "CSUSHPISA")
        useAutogluon = event.get("useAutogluon", False)

        accountId = context.invoked_function_arn.split(":")[4]

        jobManifest = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": f"housing-crisis-training-{jobId}",
                "namespace": "ml-jobs",
                "labels": {
                    "app": "housing-crisis",
                    "component": "training",
                    "triggered-by": "lambda",
                },
            },
            "spec": {
                "ttlSecondsAfterFinished": 86400,
                "backoffLimit": 2,
                "template": {
                    "spec": {
                        "restartPolicy": "OnFailure",
                        "nodeSelector": {
                            "node.kubernetes.io/instance-type": "g5.2xlarge"
                        },
                        "containers": [
                            {
                                "name": "training",
                                "image": f"{accountId}.dkr.ecr.{AWS_REGION}.amazonaws.com/housing-crisis-ml:{IMAGE_TAG}",
                                "command": [
                                    "conda",
                                    "run",
                                    "--no-capture-output",
                                    "-n",
                                    "housing_ml_env",
                                    "/entrypoint.sh",
                                ],
                                "args": [
                                    "train",
                                    "--fred-api-key",
                                    fredApiKey,
                                    "--target",
                                    targetColumn,
                                ]
                                + (["--use-autogluon"] if useAutogluon else []),
                                "env": [
                                    {"name": "CUDA_VISIBLE_DEVICES", "value": "0"},
                                    {"name": "PYTHONUNBUFFERED", "value": "1"},
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": "8",
                                        "memory": "32Gi",
                                        "nvidia.com/gpu": "1",
                                    },
                                    "limits": {
                                        "cpu": "16",
                                        "memory": "64Gi",
                                        "nvidia.com/gpu": "1",
                                    },
                                },
                            }
                        ],
                    }
                },
            },
        }

        from kubernetes import client, config

        config.load_incluster_config()
        batch_v1 = client.BatchV1Api()

        response = batch_v1.create_namespaced_job(namespace="ml-jobs", body=jobManifest)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "jobId": jobId,
                    "jobName": f"housing-crisis-training-{jobId}",
                    "status": "submitted",
                    "timestamp": datetime.now().isoformat(),
                }
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": str(e), "timestamp": datetime.now().isoformat()}
            ),
        }

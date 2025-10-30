import boto3
import json
import os
import requests
from datetime import datetime

ssm_client = boto3.client("ssm")


def getInferenceEndpoint():
    try:
        response = ssm_client.get_parameter(
            Name="/housing-crisis/inference-endpoint", WithDecryption=False
        )
        return response["Parameter"]["Value"]
    except:
        return os.environ.get(
            "INFERENCE_ENDPOINT",
            "http://housing-crisis-inference.ml-inference.svc.cluster.local",
        )


def lambda_handler(event, context):
    try:
        endpoint = getInferenceEndpoint()

        predictionRequest = {
            "data": event.get("data", []),
            "horizon": event.get("horizon", 12),
            "includeUncertainty": event.get("includeUncertainty", False),
            "crisisDetection": event.get("crisisDetection", True),
        }

        response = requests.post(
            f"{endpoint}/predict", json=predictionRequest, timeout=60
        )

        if response.status_code == 200:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(response.json()),
            }
        else:
            return {
                "statusCode": response.status_code,
                "body": json.dumps(
                    {"error": "Inference service error", "details": response.text}
                ),
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": str(e), "timestamp": datetime.now().isoformat()}
            ),
        }

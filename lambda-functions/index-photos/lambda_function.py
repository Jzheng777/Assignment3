import json
import os
from datetime import datetime
from urllib.parse import unquote_plus

import boto3
import urllib3

s3 = boto3.client("s3")
rekognition = boto3.client("rekognition")
http = urllib3.PoolManager()

OS_ENDPOINT = os.environ["OS_ENDPOINT"]
OS_HEADERS = urllib3.make_headers(basic_auth=f"{os.environ['OS_USER']}:{os.environ['OS_PASS']}")
OS_HEADERS["Content-Type"] = "application/json"


def lambda_handler(event, context):
    # This checks which photo was uploaded
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])

    # We create the labels based on Rekognition
    labels = []
    response = rekognition.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    for label in response["Labels"]:
        labels.append(label["Name"].lower())

    # Custom labels from the upload metadata
    metadata = s3.head_object(Bucket=bucket, Key=key)["Metadata"]
    if "customlabels" in metadata:
        for custom in metadata["customlabels"].split(","):
            labels.append(custom.strip().lower())

    # We create the doc in the way the assignment details and then send it to OpenSearch
    doc = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "labels": labels,
    }
    r = http.request("POST", f"{OS_ENDPOINT}/photos/_doc", body=json.dumps(doc), headers=OS_HEADERS)
    print("Labels:", labels, "OpenSearch:", r.status)
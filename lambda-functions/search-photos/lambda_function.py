import json
import os
import uuid

import boto3
import urllib3

lex = boto3.client("lexv2-runtime")
http = urllib3.PoolManager()

OS_ENDPOINT = os.environ["OS_ENDPOINT"]
OS_HEADERS = urllib3.make_headers(basic_auth=f"{os.environ['OS_USER']}:{os.environ['OS_PASS']}")
OS_HEADERS["Content-Type"] = "application/json"


def lambda_handler(event, context):
    q = (event.get("queryStringParameters") or {}).get("q", "")
    if not q:
        return {"statusCode": 200, "headers": {"Access-Control-Allow-Origin": "*"}, "body": json.dumps({"results": []})}

    # We ask Lex for the keywords
    lex_response = lex.recognize_text(botId=os.environ["BOT_ID"], botAliasId="TSTALIASID",
                                      localeId="en_US", sessionId=str(uuid.uuid4()), text=q)
    slots = lex_response["sessionState"]["intent"].get("slots") or {}

    # Collect the plural and singular forms of the keywords
    terms = []
    for slot in slots.values():
        if slot:
            word = slot["value"]["interpretedValue"].lower()
            terms.append(word)
            if word.endswith("s"):
                terms.append(word[:-1])
    # If Lex doesn't find a keyword, use words in the search itself as a fallback
    if not terms:
        filler = ["show", "me", "photos", "photo", "pictures", "of", "with", "and", "in", "them", "find", "the", "a"]
        for word in q.lower().split():
            if word not in filler:
                terms.append(word)

    # Then search OpenSearch for photos with any of those labels
    results = []
    if terms:
        query = {"size": 50, "query": {"match": {"labels": " ".join(terms)}}}
        r = http.request("POST", f"{OS_ENDPOINT}/photos/_search", body=json.dumps(query), headers=OS_HEADERS)
        for hit in json.loads(r.data)["hits"]["hits"]:
            photo = hit["_source"]
            results.append({
                "url": f"https://{photo['bucket']}.s3.amazonaws.com/{photo['objectKey']}",
                "labels": photo["labels"],
            })

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Api-Key,x-amz-meta-customLabels",
            "Access-Control-Allow-Methods": "GET,PUT,OPTIONS",
        },
        "body": json.dumps({"results": results}),
    }
import pymongo
import certifi
import os
import json
import bson.json_util as bson
import logging


default_log_args = {
    "level": logging.DEBUG if os.environ.get("DEBUG", False) else logging.INFO,
    "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    "datefmt": "%d-%b-%y %H:%M",
    "force": True,
}
logging.basicConfig(**default_log_args)
log = logging.getLogger("Run-Lambda")

PAGE_SIZE = 25

ca = certifi.where()
client = pymongo.MongoClient(
    f"{os.environ.get('MONGO_URI')}/?authMechanism=MONGODB-AWS&authSource=$external",
    tlsCAFile=ca,
)


def list_communities(event, context):
    query_params = event.get('queryStringParameters', {})
    page = int(query_params.get('page'))
    if not page:
        page = 1

    host = event.get('host')
    path = event.get('path')

    # log.info("this is running")
    db = client['eac-ratings-dev']
    community_collection = db.community
    community_list = []
    for community_bson in community_collection.find(
            batch_size=PAGE_SIZE + 1,
            sort=[("_-id", pymongo.ASCENDING)],
            skip=(page-1) * PAGE_SIZE):
        community_list.append(json.loads(bson.dumps(community_bson)))

    return {
        "isBase64Encoded": True,
        'statusCode': 200,
        'headers': None,
        'multiValueHeaders': None,
        'body': json.dumps({
            'next': f'{host}{path}?page={page + 1}' if len(community_list) > PAGE_SIZE else None,
            'previous': f'{host}{path}?page={page - 1}' if page > 1 else None,
            'results': community_list[:PAGE_SIZE]
        })
    }



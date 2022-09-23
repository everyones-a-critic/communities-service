import pymongo
import certifi
import os
import json
import bson.json_util as bson
from bson.objectid import ObjectId
import logging
import datetime


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


# GET
# /communities
def list_communities(event, context):
    page = 1
    user_id = None
    search_string = None

    query_params = event.get('queryStringParameters')
    return_params = ""
    if query_params is not None:
        page_param = query_params.get('page')
        if page_param:
            page = int(page_param)
            del query_params['page']

        is_member = query_params.get('isMember')
        if is_member is not None and is_member.lower() in ['true', '1', 'yes']:
            user_id = event['requestContext']['authorizer']['claims']['cognito:username']

        search_string = query_params.get('searchString')

        for param, arg in query_params.items():
            return_params += f"&{param}={arg}"

    path = event.get('path')

    # log.info("this is running")
    db = client['prod']
    community_collection = db.community
    community_member_collection = db.community_member

    if search_string:
        search_pipeline = [{"$search": {
            "text": {
                "path": "name",
                "query": search_string,
                "fuzzy": {}
            }
        }}]

        cursor = community_collection.aggregate(search_pipeline)

    else:
        query_filter = {}
        if user_id:
            community_ids = []
            for member_object in community_member_collection.find({'user_id': user_id}):
                community_ids.append(ObjectId(member_object['community_id']))

            query_filter = {'_id': {'$in': list(community_ids)}}

        cursor = community_collection.find(
            filter=query_filter,
            batch_size=PAGE_SIZE + 1,
            sort=[("_-id", pymongo.ASCENDING)],
            skip=(page-1) * PAGE_SIZE
        )

    community_list = []
    for community_bson in cursor:
        community_list.append(json.loads(bson.dumps(community_bson)))

    return {
        "isBase64Encoded": True,
        'statusCode': 200,
        'headers': None,
        'multiValueHeaders': None,
        'body': json.dumps({
            'next': f'{path}?page={page + 1}{return_params}' if len(community_list) > PAGE_SIZE else None,
            'previous': f'{path}?page={page - 1}{return_params}' if page > 1 else None,
            'results': community_list[:PAGE_SIZE]
        })
    }


# POST
# /communities/{community_id}/members
def join_community(event, context):
    user_id = event['requestContext']['authorizer']['claims']['cognito:username']
    community_id = event['pathParameters']['community_id']

    db = client['eac-ratings-dev']
    community_member = db.community_member
    try:
        community_member.insert_one({
            "community_id": community_id,
            "user_id": user_id,
            "created_date": datetime.datetime.utcnow()
        })
    except pymongo.errors.DuplicateKeyError:
        return {
            "isBase64Encoded": True,
            'statusCode': 409,
            'headers': None,
            'multiValueHeaders': None,
            'body': json.dumps({"message": "You are already a member of that community"})
        }
    else:
        return {
            "isBase64Encoded": True,
            'statusCode': 201,
            'headers': None,
            'multiValueHeaders': None,
            'body': json.dumps({})
        }


# DELETE
# /communities/{community_id}/members
def leave_community(event, context):
    user_id = event['requestContext']['authorizer']['claims']['cognito:username']
    community_id = event['pathParameters']['community_id']

    db = client['eac-ratings-dev']
    community_member = db.community_member

    community_member.delete_one({
        "community_id": community_id,
        user_id: "user_id",
    })

    return {
        "isBase64Encoded": True,
        'statusCode': 200,
        'headers': None,
        'multiValueHeaders': None,
        'body': json.dumps({})
    }


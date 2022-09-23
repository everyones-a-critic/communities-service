import pymongo
import certifi
import os
import json
import bson.json_util as bson
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
    query_params = event.get('queryStringParameters')
    if query_params is None:
        page = 1
    else:
        page = int(query_params.get('page', '1'))

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
            'next': f'{path}?page={page + 1}' if len(community_list) > PAGE_SIZE else None,
            'previous': f'{path}?page={page - 1}' if page > 1 else None,
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
            user_id: "user_id",
            "created_date": datetime.datetime.utcnow()
        })
    except pymongo.errors.DuplicateKeyError:
        return {
            "isBase64Encoded": True,
            'statusCode': 409,
            'headers': None,
            'multiValueHeaders': None,
            'body': {}
        }
    else:
        return {
            "isBase64Encoded": True,
            'statusCode': 201,
            'headers': None,
            'multiValueHeaders': None,
            'body': {}
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
        'body': {}
    }

# {
# 	'resource': '/communities/{community_id}/enrollment',
# 	'path': '/communities/632ccc0a4a531cf8d1db6cdd/enrollment',
# 	'httpMethod': 'POST',
# 	'headers': {
# 		'Accept': '*/*',
# 		'Accept-Encoding': 'gzip, deflate, br',
# 		'Authorization': 'eyJraWQiOiJYYVduT0g2Y0RQbkVTZktpRUdMU29wK3E5V0d3UCs5R3kwTXZMK2owdFwvQT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJiZGJlZjY0ZS05MGRhLTRjOWYtYjQ5Ny0zYTI2ZThjZTEwNzMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLXdlc3QtMS5hbWF6b25hd3MuY29tXC91cy13ZXN0LTFfUjZGSlRRdTFLIiwiY29nbml0bzp1c2VybmFtZSI6ImJkYmVmNjRlLTkwZGEtNGM5Zi1iNDk3LTNhMjZlOGNlMTA3MyIsIm9yaWdpbl9qdGkiOiIxYjg3YWI5ZC04NzUwLTQxNjgtOTBhYS04NDQ0ZDY2NTU0ZjIiLCJhdWQiOiIycGVwNDdyM3FxdmwwNXViODNqdGszcXVrcCIsImV2ZW50X2lkIjoiNGMxYzRkZGEtYTUzYy00ZWI2LTkxODgtMWRlMzIxYTM4NzhmIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE2NjM3MDE5NzYsImV4cCI6MTY2Mzg4NjgwNiwiaWF0IjoxNjYzODgzMjA3LCJqdGkiOiJhYjJiOWJlMi1mYjdiLTQyZjctODI1OS1lOWVlODAyMWYwZmIiLCJlbWFpbCI6IjI0LmRhbmllbC5sb25nQGdtYWlsLmNvbSJ9.T09kKwCDXfFP67OIqTU8mqNxA0kNB4ZrIbIWrcmGPaztPMAjx8rUf8DLkX5_0QMsUrpKXmt-FVc_UnmiiXgF25pimk3i6ClDfUn2TDoXoZA3FVk_ylccMIS4QGKpsxWrsDiEx2xznyAizvtjbHwRxqJlRjRk0c0zHCB0gpgy1OhnbsyffLVKbG8WS_0PdK2xF80NRK49k-9VegVZg3hAuACrIg2Tl4bNm4CwDgL1O826CHzd92HreOr8BRgp0WOTTAotyZ9T5NKa74QuQc7Fjg1wPAyO-qUNR7Smpyf5gWT0D_fii6iE1AkpYJ0zJXRSboRW7e3N3j9oSwaxI8F04g',
# 		'Cache-Control': 'no-cache',
# 		'Host': 'api.everyonesacriticapp.com',
# 		'Postman-Token': '1b340c20-3af3-4308-b1fc-5513dc1459e2',
# 		'User-Agent': 'PostmanRuntime/7.29.2',
# 		'X-Amzn-Trace-Id': 'Root=1-632cddf3-7777baac7019d6430303d158',
# 		'X-Forwarded-For': '65.205.72.122',
# 		'X-Forwarded-Port': '443',
# 		'X-Forwarded-Proto': 'https'
# 	},
# 	'multiValueHeaders': {
# 		'Accept': ['*/*'],
# 		'Accept-Encoding': ['gzip, deflate, br'],
# 		'Authorization': ['eyJraWQiOiJYYVduT0g2Y0RQbkVTZktpRUdMU29wK3E5V0d3UCs5R3kwTXZMK2owdFwvQT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJiZGJlZjY0ZS05MGRhLTRjOWYtYjQ5Ny0zYTI2ZThjZTEwNzMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLXdlc3QtMS5hbWF6b25hd3MuY29tXC91cy13ZXN0LTFfUjZGSlRRdTFLIiwiY29nbml0bzp1c2VybmFtZSI6ImJkYmVmNjRlLTkwZGEtNGM5Zi1iNDk3LTNhMjZlOGNlMTA3MyIsIm9yaWdpbl9qdGkiOiIxYjg3YWI5ZC04NzUwLTQxNjgtOTBhYS04NDQ0ZDY2NTU0ZjIiLCJhdWQiOiIycGVwNDdyM3FxdmwwNXViODNqdGszcXVrcCIsImV2ZW50X2lkIjoiNGMxYzRkZGEtYTUzYy00ZWI2LTkxODgtMWRlMzIxYTM4NzhmIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE2NjM3MDE5NzYsImV4cCI6MTY2Mzg4NjgwNiwiaWF0IjoxNjYzODgzMjA3LCJqdGkiOiJhYjJiOWJlMi1mYjdiLTQyZjctODI1OS1lOWVlODAyMWYwZmIiLCJlbWFpbCI6IjI0LmRhbmllbC5sb25nQGdtYWlsLmNvbSJ9.T09kKwCDXfFP67OIqTU8mqNxA0kNB4ZrIbIWrcmGPaztPMAjx8rUf8DLkX5_0QMsUrpKXmt-FVc_UnmiiXgF25pimk3i6ClDfUn2TDoXoZA3FVk_ylccMIS4QGKpsxWrsDiEx2xznyAizvtjbHwRxqJlRjRk0c0zHCB0gpgy1OhnbsyffLVKbG8WS_0PdK2xF80NRK49k-9VegVZg3hAuACrIg2Tl4bNm4CwDgL1O826CHzd92HreOr8BRgp0WOTTAotyZ9T5NKa74QuQc7Fjg1wPAyO-qUNR7Smpyf5gWT0D_fii6iE1AkpYJ0zJXRSboRW7e3N3j9oSwaxI8F04g'],
# 		'Cache-Control': ['no-cache'],
# 		'Host': ['api.everyonesacriticapp.com'],
# 		'Postman-Token': ['1b340c20-3af3-4308-b1fc-5513dc1459e2'],
# 		'User-Agent': ['PostmanRuntime/7.29.2'],
# 		'X-Amzn-Trace-Id': ['Root=1-632cddf3-7777baac7019d6430303d158'],
# 		'X-Forwarded-For': ['65.205.72.122'],
# 		'X-Forwarded-Port': ['443'],
# 		'X-Forwarded-Proto': ['https']
# 	},
# 	'queryStringParameters': None,
# 	'multiValueQueryStringParameters': None,
# 	'pathParameters': {
# 		'community_id': '632ccc0a4a531cf8d1db6cdd'
# 	},
# 	'stageVariables': None,
# 	'requestContext': {
# 		'resourceId': '8bpwk8',
# 		'authorizer': {
# 			'claims': {
# 				'sub': 'bdbef64e-90da-4c9f-b497-3a26e8ce1073',
# 				'email_verified': 'true',
# 				'iss': 'https://cognito-idp.us-west-1.amazonaws.com/us-west-1_R6FJTQu1K',
# 				'cognito:username': 'bdbef64e-90da-4c9f-b497-3a26e8ce1073',
# 				'origin_jti': '1b87ab9d-8750-4168-90aa-8444d66554f2',
# 				'aud': '2pep47r3qqvl05ub83jtk3qukp',
# 				'event_id': '4c1c4dda-a53c-4eb6-9188-1de321a3878f',
# 				'token_use': 'id',
# 				'auth_time': '1663701976',
# 				'exp': 'Thu Sep 22 22:46:46 UTC 2022',
# 				'iat': 'Thu Sep 22 21:46:47 UTC 2022',
# 				'jti': 'ab2b9be2-fb7b-42f7-8259-e9ee8021f0fb',
# 				'email': '24.daniel.long@gmail.com'
# 			}
# 		},
# 		'resourcePath': '/communities/{community_id}/enrollment',
# 		'httpMethod': 'POST',
# 		'extendedRequestId': 'Y4eeBEhpSK4FR2w=',
# 		'requestTime': '22/Sep/2022:22:13:07 +0000',
# 		'path': '/communities/632ccc0a4a531cf8d1db6cdd/enrollment',
# 		'accountId': '081924037451',
# 		'protocol': 'HTTP/1.1',
# 		'stage': 'prod',
# 		'domainPrefix': 'api',
# 		'requestTimeEpoch': 1663884787180,
# 		'requestId': '3d06b717-e659-4680-9b08-92c0a26eb967',
# 		'identity': {
# 			'cognitoIdentityPoolId': None,
# 			'accountId': None,
# 			'cognitoIdentityId': None,
# 			'caller': None,
# 			'sourceIp': '65.205.72.122',
# 			'principalOrgId': None,
# 			'accessKey': None,
# 			'cognitoAuthenticationType': None,
# 			'cognitoAuthenticationProvider': None,
# 			'userArn': None,
# 			'userAgent': 'PostmanRuntime/7.29.2',
# 			'user': None
# 		},
# 		'domainName': 'api.everyonesacriticapp.com',
# 		'apiId': 'hvsddp1gol'
# 	},
# 	'body': None,

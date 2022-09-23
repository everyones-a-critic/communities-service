import unittest
from unittest.mock import patch
import json
from mocks import MongoCollections, CommunityMember


class TestJoinCommunity(unittest.TestCase):
    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_success(self, clientMock, databaseClassMock):
        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_member_mock=CommunityMember())

        import services
        response = services.join_community({
            'requestContext': {'authorizer': {'claims': {'cognito:username': 'joe'}}},
            'pathParameters': {'community_id': 123},
        }, {})

        self.assertTrue(response['isBase64Encoded'])
        self.assertEqual(response['statusCode'], 201)
        self.assertIsNone(response['headers'])
        self.assertIsNone(response['multiValueHeaders'])
        self.assertEqual(response['body'], json.dumps({}))

    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_already_exists(self, clientMock, databaseClassMock):
        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_member_mock=CommunityMember(already_exists=True))

        import services
        response = services.join_community({
            'requestContext': {'authorizer': {'claims': {'cognito:username': 'joe'}}},
            'pathParameters': {'community_id': 123},
        }, {})

        self.assertTrue(response['isBase64Encoded'])
        self.assertEqual(response['statusCode'], 409)
        self.assertIsNone(response['headers'])
        self.assertIsNone(response['multiValueHeaders'])
        self.assertEqual(response['body'], json.dumps({"message": "You are already a member of that community"}))


if __name__ == '__main__':
    unittest.main()

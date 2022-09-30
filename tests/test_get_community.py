import unittest
from unittest.mock import patch
import json
from mocks import MongoCollections, Community


class TestGetCommunity(unittest.TestCase):
    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_success(self, clientMock, databaseClassMock):
        community_list = [
            {'name': 'Coffee', 'icon': 'coffee'}
        ]
        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_mock=Community(community_list))

        import services
        response = services.get_community({
            'requestContext': {'authorizer': {'claims': {'cognito:username': 'joe'}}},
            'pathParameters': {'community_id': 123},
        }, {})

        self.assertTrue(response['isBase64Encoded'])
        self.assertEqual(response['statusCode'], 200)
        self.assertIsNone(response['headers'])
        self.assertIsNone(response['multiValueHeaders'])
        self.assertEqual(response['body'], json.dumps({'name': 'Coffee', 'icon': 'coffee'}))

    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_not_found(self, clientMock, databaseClassMock):
        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_mock=Community())

        import services
        response = services.get_community({
            'requestContext': {'authorizer': {'claims': {'cognito:username': 'joe'}}},
            'pathParameters': {'community_id': 123},
        }, {})

        self.assertTrue(response['isBase64Encoded'])
        self.assertEqual(response['statusCode'], 404)
        self.assertIsNone(response['headers'])
        self.assertIsNone(response['multiValueHeaders'])
        self.assertEqual(response['body'], json.dumps({"message": "Not found"}))


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch
import json
from mocks import MongoCollections


class TestJoinCommunity(unittest.TestCase):
    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_success(self, clientMock, databaseClassMock):
        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections()

        import services
        response = services.join_community({
            'requestContext': {'authorizer': {'claims': {'cognito:username': 'joe'}}},
            'pathParameters': {'community_id': 123},
        }, {})

        self.assertTrue(response['isBase64Encoded'])
        self.assertEqual(response['statusCode'], 201)
        self.assertIsNone(response['headers'])
        self.assertIsNone(response['multiValueHeaders'])
        self.assertEqual(response['body'], {})

    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_already_exists(self, clientMock, databaseClassMock):
        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(already_exists=True)

        import services
        response = services.join_community({
            'requestContext': {'authorizer': {'claims': {'cognito:username': 'joe'}}},
            'pathParameters': {'community_id': 123},
        }, {})

        self.assertTrue(response['isBase64Encoded'])
        self.assertEqual(response['statusCode'], 409)
        self.assertIsNone(response['headers'])
        self.assertIsNone(response['multiValueHeaders'])
        self.assertEqual(response['body'], {})


if __name__ == '__main__':
    unittest.main()

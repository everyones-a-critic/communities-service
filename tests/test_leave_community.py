import unittest
from unittest.mock import patch
import json
from mocks import MongoCollections, CommunityMember


class TestJoinCommunity(unittest.TestCase):
    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_delete(self, clientMock, databaseClassMock):
        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_member_mock=CommunityMember())

        import services
        response = services.leave_community({
            'requestContext': {'authorizer': {'claims': {'cognito:username': 'joe'}}},
            'pathParameters': {'community_id': 123},
        }, {})

        self.assertTrue(response['isBase64Encoded'])
        self.assertEqual(response['statusCode'], 200)
        self.assertIsNone(response['headers'])
        self.assertIsNone(response['multiValueHeaders'])
        self.assertEqual(response['body'], "{}")


if __name__ == '__main__':
    unittest.main()

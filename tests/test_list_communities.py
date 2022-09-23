import unittest
from unittest.mock import patch
import json
from unittest.mock import MagicMock
from bson.objectid import ObjectId

from mocks import MongoCollections, Community, CommunityMember


class TestListCommunities(unittest.TestCase):
    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_returned_data(self, clientMock, databaseClassMock):
        community_list = [
            {'name': 'Coffee', 'icon': 'coffee'},
            {'name': 'Whiskey', 'icon': 'whiskey-glass'}
        ]

        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_mock=Community(community_list))

        import services
        communities = services.list_communities({'path': '/communities'}, {})
        self.assertTrue(communities['isBase64Encoded'])
        self.assertEqual(communities['statusCode'], 200)
        self.assertIsNone(communities['headers'])
        self.assertIsNone(communities['multiValueHeaders'])
        body_json = json.loads(communities['body'])
        self.assertIsNone(body_json['next'])
        self.assertIsNone(body_json['previous'])
        self.assertEqual(community_list, body_json['results'])

    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_pages_first_page(self, clientMock, databaseClassMock):
        community_list = []
        for i in range(1, 27):
            community_list.append({'name': str(i), 'some_value': i})

        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_mock=Community(community_list))

        import services
        communities = services.list_communities({
            'path': '/communities'
        }, {})

        body_json = json.loads(communities['body'])
        self.assertEqual(body_json['next'], '/communities?page=2')
        self.assertIsNone(body_json['previous'])

    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_pages_middle_page(self, clientMock, databaseClassMock):
        community_list = []
        for i in range(1, 27):
            community_list.append({'name': str(i), 'some_value': i})

        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_mock=Community(community_list))

        import services
        communities = services.list_communities({
            'path': '/communities', 'queryStringParameters': {'page': '2'}
        }, {})

        body_json = json.loads(communities['body'])
        self.assertEqual(body_json['next'], '/communities?page=3')
        self.assertEqual(body_json['previous'], '/communities?page=1')

    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_pages_final_page(self, clientMock, databaseClassMock):
        community_list = []
        for i in range(1, 10):
            community_list.append({'name': str(i), 'some_value': i})

        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_mock=Community(community_list))

        import services
        communities = services.list_communities({
            'path': '/communities', 'queryStringParameters': {'page': '3'}
        }, {})

        body_json = json.loads(communities['body'])
        self.assertIsNone(body_json['next'])
        self.assertEqual(body_json['previous'], '/communities?page=2')
        self.assertEqual(community_list[0:25], body_json['results'])

    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_is_member_filter_return_values(self, clientMock, databaseClassMock):
        community_list = []
        for i in range(1, 27):
            community_list.append({'name': str(i), 'some_value': i})

        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(
            community_mock=Community(community_list),
            community_member_mock=CommunityMember()
        )

        import services
        communities = services.list_communities({
            'path': '/communities', 'queryStringParameters': {'isMember': 'true'},
            'requestContext': {'authorizer': {'claims': {'cognito:username': 'joe'}}},
        }, {})

        body_json = json.loads(communities['body'])
        self.assertEqual(body_json['next'], '/communities?page=2&isMember=true')
        self.assertIsNone(body_json['previous'])
        self.assertEqual(community_list[0:25], body_json['results'])

    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_is_member_filter_mongo_call(self, clientMock, databaseClassMock):
        community_list = []
        for i in range(1, 27):
            community_list.append({'name': str(i), 'some_value': i})

        clientMock.return_value = None
        mock = Community([])
        mock.find = MagicMock()
        databaseClassMock.return_value = MongoCollections(
            community_mock=mock,
            community_member_mock=CommunityMember()
        )

        import services
        services.list_communities({
            'path': '/communities', 'queryStringParameters': {'isMember': 'true'},
            'requestContext': {'authorizer': {'claims': {'cognito:username': 'joe'}}},
        }, {})

        mock.find.assert_called_with(
            filter={'_id': {'$in': [
                ObjectId('632ccc0a4a531cf8d1db6cdd'),
                ObjectId('632ccc0a4a531cf8d1db6cdf'),
                ObjectId('632ccc0a4a531cf8d1db6ce0')]}
            },
            batch_size=26,
            sort=[('_-id', 1)],
            skip=0
        )


if __name__ == '__main__':
    unittest.main()

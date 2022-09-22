import unittest
from unittest.mock import patch
import json


# Mock Objects
class Community:
    def __init__(self, records):
        self.records = records

    def find(self, *args, **kwargs):
        return self.records


class MongoCollections:
    def __init__(self, records):
        self.community = Community(records)


class TestListCommunities(unittest.TestCase):
    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_returned_data(self, clientMock, databaseClassMock):
        community_list = [
            {'name': 'Coffee', 'icon': 'coffee'},
            {'name': 'Whiskey', 'icon': 'whiskey-glass'}
        ]

        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_list)

        import services
        communities = services.list_communities({'host': 'api.everyonesacriticapp.com', 'path': '/communities'}, {})
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
        databaseClassMock.return_value = MongoCollections(community_list)

        import services
        communities = services.list_communities({
            'host': 'api.everyonesacriticapp.com', 'path': '/communities'
        }, {})

        body_json = json.loads(communities['body'])
        self.assertEqual(body_json['next'], 'api.everyonesacriticapp.com/communities?page=2')
        self.assertIsNone(body_json['previous'])

    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_pages_middle_page(self, clientMock, databaseClassMock):
        community_list = []
        for i in range(1, 27):
            community_list.append({'name': str(i), 'some_value': i})

        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_list)

        import services
        communities = services.list_communities({
            'host': 'api.everyonesacriticapp.com', 'path': '/communities', 'queryStringParameters': {'page': '2'}
        }, {})

        body_json = json.loads(communities['body'])
        self.assertEqual(body_json['next'], 'api.everyonesacriticapp.com/communities?page=3')
        self.assertEqual(body_json['previous'], 'api.everyonesacriticapp.com/communities?page=1')

    @patch('pymongo.database.Database')
    @patch('pymongo.MongoClient.__init__')
    def test_pages_final_page(self, clientMock, databaseClassMock):
        community_list = []
        for i in range(1, 10):
            community_list.append({'name': str(i), 'some_value': i})

        clientMock.return_value = None
        databaseClassMock.return_value = MongoCollections(community_list)

        import services
        communities = services.list_communities({
            'host': 'api.everyonesacriticapp.com', 'path': '/communities', 'queryStringParameters': {'page': '3'}
        }, {})

        body_json = json.loads(communities['body'])
        self.assertIsNone(body_json['next'], )
        self.assertEqual(body_json['previous'], 'api.everyonesacriticapp.com/communities?page=2')
        self.assertEqual(community_list[0:25], body_json['results'])


if __name__ == '__main__':
    unittest.main()

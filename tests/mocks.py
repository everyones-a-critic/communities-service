import pymongo
from unittest.mock import MagicMock


class Community:
    def __init__(self, records=[]):
        self.records = records

    def find(self, *args, **kwargs):
        return self.records

    def find_one(self, *args, **kwargs):
        if self.records:
            return self.records[0]

    def aggregate(self, *args, **kwargs):
        return self.records


class CommunityMember:
    def __init__(self, already_exists=False):
        self.already_exists = already_exists

    def insert_one(self, *args, **kwargs):
        if self.already_exists:
            raise pymongo.errors.DuplicateKeyError("Unique constraint violated")
        else:
            return {}

    @staticmethod
    def find(*args, **kwargs):
        return [
            {'community_id': '632ccc0a4a531cf8d1db6cdd'},
            {'community_id': '632ccc0a4a531cf8d1db6cdf'},
            {'community_id': '632ccc0a4a531cf8d1db6ce0'}
        ]

    @staticmethod
    def delete_one(*args, **kwargs):
        return {}


class MongoCollections:
    def __init__(self, community_mock=None, community_member_mock=None):
        self.community = community_mock or MagicMock()
        self.community_member = community_member_mock or MagicMock()
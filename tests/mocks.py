import pymongo


class Community:
    def __init__(self, records):
        self.records = records

    def find(self, *args, **kwargs):
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
    def delete_one(*args, **kwargs):
        return {}


class MongoCollections:
    def __init__(self, records=None, already_exists=False):
        self.community = Community(records)
        self.community_member = CommunityMember(already_exists)
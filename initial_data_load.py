import pymongo
import certifi
import os


def load_data():
    ca = certifi.where()
    client = pymongo.MongoClient(
        f"mongodb+srv://cli_user:{os.environ.get('MONGO_PASSWORD')}@{os.environ.get('MONGO_URL_SNIP')}.mongodb.net/?retryWrites=true&w=majority",
        tlsCAFile=ca
    )

    communities_to_insert = [
        {"name": "Coffee", "plural_name": "Coffees"},
        {"name": "Whiskey", "plural_name": "Whiskeys"},
        {"name": "Restaurant", "plural_name": "Restaurants"},
        {"name": "Tequila", "plural_name": "Tequilas"},
        {"name": "Coffee Shop", "plural_name": "Coffee Shops"},
        {"name": "Movie", "plural_name": "Movies"},
        {"name": "Beer", "plural_name": "Beers"},
    ]

    db = client['eac-ratings-dev']
    community_coll = db.community
    community_coll.drop()

    result = community_coll.insert_many(communities_to_insert)
    print(result.inserted_ids)

    client.close()


if __name__ == "__main__":
    load_data()

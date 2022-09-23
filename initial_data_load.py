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
        {"display_name": "Coffee", "name": "Coffee", "plural_name": "Coffees", "icon": "coffee", "primary_color": "413121",  "secondary_color": "FFFFFF"},
        {"display_name": "Whiskey", "name": "Whiskey", "plural_name": "Whiskeys", "background_color": "413121", "icon": "whiskey-glass", "primary_color": "121B26",  "secondary_color": "BEA480"},
        {"display_name": "Restaurants", "name": "Restaurant", "plural_name": "Restaurants", "icon": "utensils", "primary_color": "BF0704",  "secondary_color": "FFFFFF"},
        {"display_name": "Coffee Shops", "name": "Coffee Shop", "plural_name": "Coffee Shops", "icon": "coffee", "primary_color": "FFFAE7",  "secondary_color": "604A3F"},
        {"display_name": "Golf Courses", "name": "Golf Course", "plural_name": "Golf Courses", "icon": "golf-ball", "primary_color": "004D43",  "secondary_color": "FFFCDF"},
        {"display_name": "Movies", "name": "Movie", "plural_name": "Movies", "icon": "clapperboard", "primary_color": "4808B0", "secondary_color": "FFFFFF"},
        {"display_name": "Beer", "name": "Beer", "plural_name": "Beers", "icon": "wheat-alt", "primary_color": "20353C", "secondary_color": "BDA571"},
    ]

    db = client['eac-ratings-dev']
    community_coll = db.community
    community_coll.create_index("name")
    community_coll.drop()
    result = community_coll.insert_many(communities_to_insert)

    community_member = db.community_member
    community_member.create_index([("user_id", pymongo.ASCENDING), ("community_id", pymongo.ASCENDING)], unique=True)

    client.close()


if __name__ == "__main__":
    load_data()

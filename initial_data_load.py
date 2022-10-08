import pymongo
import certifi
import os
import datetime


def load_data():
    ca = certifi.where()
    client = pymongo.MongoClient(
        f"mongodb+srv://cli_user:{os.environ.get('MONGO_PASSWORD')}@{os.environ.get('MONGO_URL_SNIP')}.mongodb.net/?retryWrites=true&w=majority",
        tlsCAFile=ca
    )

    communities_to_insert = [
        {
            "display_name": "Coffee", "name": "Coffee", "plural_name": "Coffees",
            "icon": "coffee", "primary_color": "413121", "secondary_color": "FFFFFF",
            "primary_fields": [
                {"name": "categories"},
                {"name": "price", "formatting": "currency"},
            ],
            "secondary_fields": [
                {"name": "location", "label": "Region", "type": "currency"},
                {"name": "tasting_notes", "label": "Tasting Notes"},
                {"name": "process", "label": "Process"},
                {"name": "variety", "label": "Variety"},
                {"name": "roast", "label": "Roast Level", "type": "scale-5"},
            ],
        },
        {
            "display_name": "Whiskey", "name": "Whiskey", "plural_name": "Whiskeys",
            "icon": "whiskey-glass", "primary_color": "121B26",  "secondary_color": "BEA480",
            "primary_fields": [
                {"name": "categories"},
                {"name": "price", "formatting": "currency"},
            ],
            "secondary_fields": [],
        },
        # {"display_name": "Restaurants", "name": "Restaurant", "plural_name": "Restaurants", "icon": "utensils", "primary_color": "BF0704",  "secondary_color": "FFFFFF"},
        # {"display_name": "Coffee Shops", "name": "Coffee Shop", "plural_name": "Coffee Shops", "icon": "coffee", "primary_color": "FFFAE7",  "secondary_color": "604A3F"},
        # {"display_name": "Golf Courses", "name": "Golf Course", "plural_name": "Golf Courses", "icon": "golf-ball", "primary_color": "004D43",  "secondary_color": "FFFCDF"},
        # {"display_name": "Movies", "name": "Movie", "plural_name": "Movies", "icon": "clapperboard", "primary_color": "4808B0", "secondary_color": "FFFFFF"},
        # {"display_name": "Beer", "name": "Beer", "plural_name": "Beers", "icon": "wheat-alt", "primary_color": "20353C", "secondary_color": "BDA571"},
        # {"display_name": "Cheese", "name": "Cheese", "plural_name": "Cheeses", "icon": "cheese", "primary_color": "C21319", "secondary_color": "F4C13A"},
    ]

    db = client[os.environ.get('MONGO_CLUSTER_NAME')]
    community_coll = db.community
    community_coll.create_index([('name', pymongo.TEXT)])
    existing_communities = {}
    for community in community_coll.find():
        existing_communities[community['name']] = community

    for community in communities_to_insert:
        print(community['name'], end=": ")
        if community['name'] not in existing_communities:
            community_coll.insert_one(community)
            print("inserted")
        else:
            existing_community = existing_communities[community['name']]
            comparison_community = existing_community.copy()
            del comparison_community['_id']
            del comparison_community['created_by_id']
            del comparison_community['created_date']
            del comparison_community['modified_by_id']
            del comparison_community['modified_date']
            if community == comparison_community:
                print("no updates needed")
            else:
                unsetValues = {}
                for key in comparison_community:
                    if key not in community:
                        unsetValues[key] = ""

                setValues = {
                    "modified_by_id": 'bdbef64e-90da-4c9f-b497-3a26e8ce1073',
                    "modified_date": datetime.datetime.utcnow(),
                }

                for key, value in community.items():
                    if value != comparison_community.get(key):
                        setValues[key] = value

                community_coll.find_one_and_update(
                    {"_id": existing_community['_id']}, {
                        "$set": setValues,
                        "$unset": unsetValues,
                    },
                    upsert=True
                )
                print("updated")

    community_member = db.community_member
    community_member.create_index([("user_id", pymongo.ASCENDING), ("community_id", pymongo.ASCENDING)], unique=True)

    client.close()


if __name__ == "__main__":
    load_data()

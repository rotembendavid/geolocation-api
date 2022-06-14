from pymongo import MongoClient
from exceptions import MongoDbEx
from geo_distance import GeoDistance
from pymongo.errors import ConnectionFailure

client = MongoClient()
db = client.get_database("Sinamedia")
geoloc = db.get_collection("geoloc")
popular_search = db.get_collection("most_popular_search")


def is_connected():
    try:
        client.admin.command('ismaster')
        return True
    except ConnectionFailure as ex:
        return False


def get_distance(key: tuple):
    try:
        geo_distance_dict = geoloc.find_one({'key': key})
        if geo_distance_dict:
            geo_distance_dict.pop("_id")
            return GeoDistance(**geo_distance_dict)
        else:
            return None
    except Exception as ex:
        raise MongoDbEx(ex)


def update_searches_count(key, number_of_searches):
    result = geoloc.update_one({"key": key}, {"$set": {'number_of_searches': number_of_searches}})


def validate_max_searches(geo_distance_obj: GeoDistance):
    popular_search_dict = popular_search.find_one()
    if popular_search_dict:
        if popular_search_dict["hits"] < geo_distance_obj.number_of_searches:
            popular_search.update_one({"_id": popular_search_dict["_id"]},
                                      {"$set": {"hits": geo_distance_obj.number_of_searches,
                                                "cities": geo_distance_obj.key}})
    elif popular_search_dict is None:
        popular_search.insert_one({"cities": geo_distance_obj.key, "hits": geo_distance_obj.number_of_searches})


def add_cities_distance(geo_distance_obj: GeoDistance):
    geo_distance_dict = geo_distance_obj.__dict__
    result = geoloc.insert_one(geo_distance_dict)
    return result


def get_most_popular_search():
    return popular_search.find_one()



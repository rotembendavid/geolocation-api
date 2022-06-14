import googlemaps
from exceptions import LocationApiEx

gmaps = googlemaps.Client(key='AIzaSyA_DZAYPDTjgvrPKNU4UQwgpQLu8qOLRio')


def get_distance(city_a: str, city_b: str):
    try:
        distance = gmaps.distance_matrix(city_a, city_b)['rows'][0]['elements'][0]['distance']['text']
        return distance.split()[0]
    except Exception as ex:
        raise LocationApiEx(ex)

import uvicorn
import mongo_db
import exceptions
import location_api
from fastapi import FastAPI
from fastapi import HTTPException
from geo_distance import GeoDistance
from request_body import RequestBody

app = FastAPI()


@app.get("/hello")
async def root():
    return {}


@app.get("/distance")
async def get_item(sourceCity: str, destinationCity:str):
    try:
        result = None
        key = generate_cities_key(sourceCity, destinationCity)
        is_connected = mongo_db.is_connected()

        if is_connected:
            result = mongo_db.get_distance(key)

        if result:
            result.number_of_searches += 1
            mongo_db.update_searches_count(result.key, result.number_of_searches)
        else:
            # new distance to calculate
            distance = location_api.get_distance(key[0], key[1])
            result = GeoDistance(key, distance, 1)
            if is_connected:
                mongo_db.add_cities_distance(result)
        if is_connected:
            mongo_db.validate_max_searches(result)

        return {"distance": result.distance}

    except exceptions.MongoDbEx as ex:
        raise HTTPException(status_code=500, detail=f"Database error: {ex.__doc__}")
    except exceptions.LocationApiEx as ex:
        raise HTTPException(status_code=500, detail=f"Location API error: {ex.__doc__}")
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Unhandled error: {ex.__doc__}")


@app.get("/health")
async def check_db_connection():
    is_connected = mongo_db.is_connected()
    if is_connected:
        return {}
    else:
        raise HTTPException(status_code=500, detail="Not connected to database")


@app.get("/popularsearch")
async def get_most_popular_search():
    result = mongo_db.get_most_popular_search()
    if result is None:
        return "No searches were found"
    return {"source": result["cities"][0], "destination":  result["cities"][1], "hits": result["hits"]}


@app.post("/distance", status_code=201)
async def add_distance(body: RequestBody):
    try:
        distance = body.distance
        key, result = check_if_distance_exists_in_db(body.source, body.destination)
        if result is None:
            mongo_db.add_cities_distance(GeoDistance(key, distance, 0))
            hits = 0
        else:
            hits = result.number_of_searches

        return {"source": body.source, "destination": body.destination, "hits": hits}

    except exceptions.MongoDbEx as ex:
        raise HTTPException(status_code=500, detail=f"Database error: {ex.__doc__}")
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Unhandled error: {ex.__doc__}")


def check_if_distance_exists_in_db(source_city, destination_city):
    try:
        key = generate_cities_key(source_city, destination_city)
        geo_distance_obj = mongo_db.get_distance(key)
        return key, geo_distance_obj

    except exceptions.MongoDbEx as ex:
        raise ex(detail=f"Database error: {ex.__doc__}")
    except Exception as ex:
        raise ex


def generate_cities_key(source_city, destination_city):
    source_city = source_city.lower()
    destination_city = destination_city.lower()
    key = tuple(sorted([source_city, destination_city]))
    return key


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
    
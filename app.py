from flask import Flask, jsonify, render_template_string, request
from decouple import config
from py2neo import Graph, Node, Relationship
import time
from pymongo import MongoClient
import json
import os
import random
import markdown

app = Flask(__name__)

ville_choisie = "Quebec City"

# MONGODB
database_name = config('MONGODB_DBNAME')
collection_name = config('MONGODB_COLLECTION')
mongo_uri = config('MONGODB_URL')

client = MongoClient(mongo_uri)
db = client[database_name]
restaurants_collection = db[collection_name]

# NEO4J
USERNAME, PASSWORD = config('NEO4J_CREDENTIALS').split('/')
INTERNAL_URL = config('NEO4J_URL')


def connect_to_neo4j():
    max_retries = 10
    retries = 0
    while retries < max_retries:
        try:
            database = Graph(INTERNAL_URL, auth=(
                USERNAME, PASSWORD), secure=False)
            return database
        except Exception as e:
            print(
                f"Failed to connect to Neo4j. Retrying ({retries}/{max_retries})...")
            retries += 1
            time.sleep(5)  # Adjust the delay as needed

    raise Exception("Failed to connect to Neo4j after multiple retries.")


database = connect_to_neo4j()


@app.route('/extracted_data', methods=['GET'])
def get_extracted_data():
    document_count = restaurants_collection.count_documents({})

    number_of_roads = database.run("MATCH p=()-[r:TO]->() RETURN COUNT(p)")
    nbsegments = list(number_of_roads)[0][0]

    return jsonify({"nbRestaurants": document_count, "nbSegments": nbsegments})


@app.route('/transformed_data', methods=['GET'])
def get_transformed_data():
    unique_types = restaurants_collection.distinct("categories.title")
    type_counts = {}
    for unique_type in unique_types:
        count = restaurants_collection.count_documents(
            {"categories.title": unique_type})
        type_counts[unique_type] = count

    length_of_roads = database.run(
        "MATCH (a)-[to:TO]->(b) WHERE id(a) < id(b) RETURN SUM(DISTINCT to.length) AS totalLength;")
    longueur = list(length_of_roads)[0][0]

    return jsonify({"restaurants": type_counts, "longueurCyclable": longueur})


@app.route('/heartbeat', methods=['GET'])
def get_heartbeat():
    return jsonify({"villeChoisie": ville_choisie})


@app.route("/readme", methods=['GET'])
def get_readme():
    # Charger le contenu du fichier README.md
    readme_path = os.path.join(os.getcwd(), 'README.md')
    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()
    # Convertir le contenu Markdown en HTML
    html_content = markdown.markdown(readme_content)

    # Renvoyer le contenu HTML dans la réponse
    return render_template_string(html_content)


@app.route("/type", methods=['GET'])
def get_type():
    list_valid_types = list(database.run(
        "MATCH (r:Restaurant) RETURN DISTINCT r.type AS restaurantType"))
    unique_types = [item for sublist in list_valid_types for item in sublist]

    return jsonify(unique_types)


@app.route('/starting_point', methods=['POST'])
def get_starting_point():
    try:
        data = request.get_json()

        required_keys = ['length', 'type']
        if set(data.keys()) != set(required_keys):
            raise ValueError(f"Invalid keys. Required keys: {required_keys}")

        list_valid_types = list(database.run(
            "MATCH (r:Restaurant) RETURN DISTINCT r.type AS restaurantType"))
        unique_types = [
            item for sublist in list_valid_types for item in sublist]
        length = data['length']

        # Vérifier que length est un entier positif
        if not isinstance(length, int) or length <= 0:
            raise ValueError("Length must be a positive integer.")

        types = data.get('type', [])  # Liste des types de restaurants

        # Vérifier que tous les types sont présents dans unique_types
        if not set(types).issubset(set(unique_types)):
            invalid_types = set(types) - set(unique_types)
            raise ValueError(
                f"Invalid types: {invalid_types}. All types must be in {unique_types}.")

        # Calculer la tolérance de longueur
        tolerance = length * 0.10  # 10% de tolérance sur la longueur
        min_length = length - tolerance
        max_length = length + tolerance

        # Construire la requête pour trouver des points à une distance spécifique
        query = """
        MATCH (p:Point)-[:NEAR]->(r:Restaurant)
        WHERE r.type IN $types
        WITH p, r
        MATCH (p2:Point)
        WHERE p <> p2
        WITH p, r, p2, point.distance(point({latitude: p.latitude, longitude: p.longitude}), 
                                point({latitude: p2.latitude , longitude:p2.longitude})) AS dist
        WHERE dist >= $min_length AND dist <= $max_length
        RETURN p AS startingPoint, collect(r) AS nearbyRestaurants, dist
        """
        parameters = {'min_length': min_length,
                      'max_length': max_length, 'types': types}

        # Exécution de la requête Neo4j
        result = database.run(query, parameters)

        # Collect all records into a list
        records = list(result)

        # Check if records is empty
        if not records:
            raise ValueError("No matching records found.")

        record = random.choice(records)
        starting_point_node = record['startingPoint']
        starting_point = {
            "type": "Point",
            "coordinates": [
                starting_point_node['latitude'],
                starting_point_node['longitude']
            ]
        }

        return jsonify({"startingPoint": starting_point})

    except ValueError as ve:
        error_message = f"Validation error: {str(ve)}"
        return jsonify({"error": error_message}), 400

    except KeyError as e:
        error_message = f"Missing key in JSON data: {str(e)}"
        return jsonify({"error": error_message}), 400

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500


@app.route('/parcours', methods=['POST'])
def create_parcours():
    try:
        data = request.get_json()
        starting_point = data['startingPoint']['coordinates']
        length = data['length']
        types = data.get('type', [])  # Liste des types de restaurants
        number_of_stops = data.get('numberOfStops', 0) - 1

        required_keys = ['startingPoint', 'length', 'numberOfStops', 'type']
        if set(data.keys()) != set(required_keys):
            raise ValueError(f"Invalid keys. Required keys: {required_keys}")

        # Vérifier que length est un entier positif
        if not isinstance(length, int) or length <= 0:
            raise ValueError("Length must be a positive integer.")

        # Vérifier que numberOfStops est un entier positif
        if not isinstance(number_of_stops, int) or number_of_stops < 0:
            raise ValueError("number_of_stops must be a positive integer.")

        # Vérifier que tous les types sont présents dans unique_types
        list_valid_types = list(database.run(
            "MATCH (r:Restaurant) RETURN DISTINCT r.type AS restaurantType"))
        unique_types = [
            item for sublist in list_valid_types for item in sublist]
        if not set(types).issubset(set(unique_types)):
            invalid_types = set(types) - set(unique_types)
            raise ValueError(
                f"Invalid types: {invalid_types}. All types must be in {unique_types}.")

        # Vérification du type de startingPoint
        if data['startingPoint']['type'] != "Point":
            raise ValueError(
                "Invalid value for 'startingPoint.type'. It should be 'Point'.")

        # Vérification des coordinates de startingPoint
        if not isinstance(data['startingPoint']['coordinates'], list) or len(data['startingPoint']['coordinates']) != 2:
            raise ValueError(
                "Invalid value for 'startingPoint.coordinates'. It should be a list with two float values.")
        for coordinate in data['startingPoint']['coordinates']:
            if not isinstance(coordinate, float):
                raise ValueError(
                    "Invalid value in 'startingPoint.coordinates'. All values should be of type float.")

        # Calculer la tolérance de longueur
        tolerance = length * 0.10  # 10% de tolérance sur la longueur
        min_length = length - tolerance
        max_length = length + tolerance

        # Initialiser le parcours
        parcours_features = []

        # Trouver le point de depart
        query = """
        MATCH (p:Point)-[:NEAR]->(r:Restaurant)
        WHERE p.latitude = $lat AND p.longitude = $lon AND r.type IN $types
        RETURN r AS restaurant,r.latitude AS latitude, r.longitude AS longitude, r.id AS id, id(p) AS fromPointId, r.type AS type LIMIT 1
        """
        parameters = {
            'lat': starting_point[0],
            'lon': starting_point[1],
            'types': types
        }

        parcours = {
            "type": "FeatureCollection",
            "features": parcours_features
        }

        result = database.run(query, parameters)
        restaurant_id = None
        from_point_id = None
        latitude = None
        longitude = None
        type = None
        if result:
            for record in result:
                # Traiter chaque enregistrement ici
                restaurant_id = record['id']
                from_point_id = record['fromPointId']
                latitude = record['latitude']
                longitude = record['longitude']
                type = record['type']
            restaurant_name = findRestaurantNameInMongodb(restaurant_id)
            restaurant_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "properties": {
                    "name": restaurant_name,
                    "type": type

                }
            }
            parcours_features.append(restaurant_feature)

        total_distance = 0
        idList = []
        id = restaurant_id

        idList.append(id)
        idList.append(from_point_id)
        while not (min_length <= total_distance <= max_length):
            res = None
           # if number_of_stops > 0:
            res = pathFromPoint(id)
            if res:
                # Déclaration des variables à l'extérieur de la boucle
                other_restaurant_id = None
                nearby_point_id = None
                connected_point_id = None
                resto_id = None
                resto_latitude = None
                resto_longitude = None
                resto_type = None
                resto_name = None
                restaurant_feature = None
                length = 0
                dist = 0
                nearby_point_longitude = 0
                nearby_point_latitude = 0
                connected_point_longitude = 0
                connected_point_latitude = 0
                for res_record in res:
                    # Extraction des données de chaque enregistrement dans 'res'
                    nearby_point_id = res_record['nearbyPointId']
                    nearby_point_longitude = res_record['nearbyPoint_longitude']
                    nearby_point_latitude = res_record['nearbyPoint_latitude']
                    connected_point_id = res_record['connectedPointId']
                    connected_point_longitude = res_record['connectedPoint_longitude']
                    connected_point_latitude = res_record['connectedPoint_latitude']
                    resto_type = res_record['typeResto']
                    resto_id = res_record['idResto']
                    resto_longitude = res_record['resto_longitude']
                    resto_latitude = res_record['resto_latitude']
                    other_restaurant_id = res_record['otherRestaurantId']
                    length = res_record['length']
                    dist = res_record['dist']
                    id = resto_id


                number_of_stops -= 1
                idList.append(other_restaurant_id)
                idList.append(connected_point_id)
                idList.append(nearby_point_id)
                if length is not None and dist is not None:
                    total_distance = total_distance + length + dist

                resto_name = findRestaurantNameInMongodb(resto_id)
                restaurant_feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [resto_longitude, resto_latitude]
                    },
                    "properties": {
                        "name": resto_name,
                        "type": resto_type

                    }
                }

                parcours_features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiLineString",
                        "coordinates": [[nearby_point_latitude, nearby_point_longitude],
                                        [connected_point_latitude, connected_point_longitude,]]
                    },
                    "properties": {
                        "length": length,
                    }
                })
                parcours_features.append(restaurant_feature)

        return jsonify(parcours)

    except ValueError as ve:
        error_message = f"Validation error: {str(ve)}"
        return jsonify({"error": error_message}), 400

    except KeyError as e:
        error_message = f"Missing key in JSON data: {str(e)}"
        return jsonify({"error": error_message}), 400

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return jsonify({"error": error_message}), 500


def findRestaurantNameInMongodb(restaurantId):
    restaurant = restaurants_collection.find_one({"id": restaurantId})
    return restaurant['name']


def pathFromPoint(restoId):
    query = """
    MATCH (refRestaurant:Restaurant {id: $restoId})
    MATCH (nearbyPoint:Point)-[:NEAR]->(otherRestaurant:Restaurant)
    OPTIONAL MATCH (nearbyPoint)-[toRelation:TO]-(connectedPoint:Point)
    WITH refRestaurant, nearbyPoint, otherRestaurant, connectedPoint, toRelation,
         point.distance(point({latitude: refRestaurant.latitude, longitude: refRestaurant.longitude}), 
                  point({latitude: nearbyPoint.longitude , longitude: nearbyPoint.latitude })) AS dist
    WHERE dist <= 500
    RETURN  
    id(nearbyPoint) AS nearbyPointId,nearbyPoint.longitude AS nearbyPoint_longitude,nearbyPoint.latitude AS nearbyPoint_latitude,
    id(connectedPoint) AS connectedPointId,connectedPoint.longitude AS connectedPoint_longitude, connectedPoint.latitude AS connectedPoint_latitude,
    otherRestaurant.type AS typeResto,  otherRestaurant.id AS idResto, otherRestaurant.longitude AS resto_longitude,
    otherRestaurant.latitude AS resto_latitude, id(otherRestaurant) AS otherRestaurantId,  toRelation.length AS length, dist
    ORDER BY dist
    LIMIT 1
    """
    return database.run(query, {'restoId': restoId})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

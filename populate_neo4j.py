from py2neo import Graph, Node, Relationship
import json
from src.toolsneo4j import validate_neo_connection, is_database_empty
from decouple import config

USERNAME, PASSWORD=config('NEO4J_CREDENTIALS').split('/')
INTERNAL_URL= config('NEO4J_URL')

print("Waiting for servers connections")


validate_neo_connection(url=INTERNAL_URL, username=USERNAME, password=PASSWORD)
    
database = Graph(INTERNAL_URL, auth=(USERNAME, PASSWORD), secure=False)
database_is_empty = is_database_empty(database)
    
if database_is_empty:
    print("Database is empty, populating Neo4j database")
    output_file = "src/roads.geojson"
    try:
        with open(output_file, "r") as geojson_file:
            data = json.load(geojson_file)
    except FileNotFoundError:
        print("The "+output_file+" file does not exist.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    else:
        print("Populating Neo4j database...")

        for feature in data["features"]:
            properties = feature["properties"]
            coordinates = feature["geometry"]["coordinates"]

            # Extract the start point (first coordinate) and the arrival point (last coordinate)
            start_point = coordinates[0]
            arrival_point = coordinates[-1]

            # Create a node for the road with its properties
            road_node = Node("Road", NOM_TOPOGRAPHIE=properties["NOM_TOPOGRAPHIE"], SENS_UNIQUE=properties["SENS_UNIQUE"], LONGUEUR=properties["LONGUEUR"])
            database.create(road_node)

            # Create nodes for the start point and arrival point
            start_lat, start_lon = start_point
            arrival_lat, arrival_lon = arrival_point
            start_point_node = Node("Point", latitude=start_lat, longitude=start_lon)
            arrival_point_node = Node("Point", latitude=arrival_lat, longitude=arrival_lon)

            # Create relationships between the road and the start and arrival points
            start_relationship = Relationship(road_node, "START_POINT", start_point_node)
            arrival_relationship = Relationship(road_node, "ARRIVAL_POINT", arrival_point_node)

            database.create(start_point_node)
            database.create(arrival_point_node)
            database.create(start_relationship)
            database.create(arrival_relationship)

        print("Data import completed.")




#TEMPS TOTAL: 13 minutes 32 secondes
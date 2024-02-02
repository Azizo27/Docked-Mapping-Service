# We wait for services Neo4J to start
import time

import py2neo
from py2neo import Graph
    
    
def validate_neo_connection(url, username, password):
    try:
        print("Trying connection to neo")
        print("the url is: " + url)
        print("the username is: " + username)
        print("the password is: " + password)
        Graph(url, auth=(username, password), secure=False)
        print("Successfully connected Neo4J")
    except py2neo.errors.ConnectionUnavailable:
        print("Connection to neo failed, will retry in 10 sec")
        time.sleep(10)
        validate_neo_connection(url=url, username=username, password=password)


def is_database_empty(database):
    """
    Validate if the database is empty
    """
    number_of_data_elements_in_db = database.run("MATCH (n) RETURN n")
    return len(list(number_of_data_elements_in_db)) == 0



#Function used to fetch the geojson file from the web
'''
import requests
import json

def fetch_geojson(output_file):
    url = (
        "https://www.donneesquebec.ca/recherche/dataset/8dba5a63-49b2-"
        "4d20-8333-f99df764ce10/resource/57064f57-122c-4e45-894e-a4dcf3"
        "9ce6fa/download/vdq-reseaucyclable.geojson"
    )
    response = requests.get(url)

    if response.status_code == 200:
        geojson_data = response.json()

        with open(output_file, 'w') as file:
            json.dump(geojson_data, file)

        return True
    else:
        print(f"Failed to fetch GeoJSON data from {url}")
        return False
'''


#Fonction Pour Ajout Incremental des données
'''
import json

def compare_and_update(json_file1, json_file2):
    # Load the JSON data from the files
    with open(json_file1, 'r') as file1:
        data1 = json.load(file1)

    with open(json_file2, 'r') as file2:
        data2 = json.load(file2)

    # Compare and update data1 based on differences with data2
    update_json(data1, data2)

    # Write the updated data back to the first JSON file
    with open(json_file1, 'w') as file1:
        json.dump(data1, file1, indent=2)

def update_json(data1, data2, path=None):
    # Recursively compare and update the dictionaries
    for key, value in data2.items():
        if path:
            current_path = f"{path}.{key}"
        else:
            current_path = key

        if isinstance(value, dict):
            # If the value is a dictionary, recursively update
            update_json(data1[key], value, current_path)
        else:
            # If the values are different, update the first JSON
            if data1[key] != value:
                print(f"Updating {current_path}: {data1[key]} -> {value}")
                data1[key] = value

# Example usage
compare_and_update('file1.json', 'file2.json')

'''
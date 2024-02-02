from pymongo import MongoClient

def format_business_data(business):
    formatted_data = {
        "id": business["id"],
        "name": business["name"],
        "image_url": business.get("image_url", None),
        "url": business["url"],
        "review_count": business["review_count"],
        "categories": business["categories"],
        "rating": business["rating"],
        "coordinates": business["coordinates"],
        "location": {
            "display_address": business["location"]["display_address"]
        },
        "display_phone": business["display_phone"],
        "distance": business["distance"]
    }
    return formatted_data






#Code utilisé pour extraire les données de l'API Yelp
'''
import requests
import json

from src.tools import format_business_data

# Define API Key, Search Type, and header
MY_API_KEY = 'ngn8dQO9_GkBEyB2-fQTFLha1K9mfCSHy9qfp-4EPvO7DxJbDdBLvV7Yd87DxjOb8TfuICTI_7I4SST77ReiGjEZNTp1xvJk8_CyWIAQUccOk4P2tnGP9AKN1m4OZXYx'
MY_API_KEY = '8CvOCX2tCJRa3hZQf7lWI4-qo7VswnHfinCRovPkQJZIr9eKH34u1NCdD3qZ5vhBlkSX2jD9j0d9nkMqfIz1CwBiiKpZcYqv2MCZ52qi36l9Ghb848PIoq86_XJJZXYx'
BUSINESS_PATH = 'https://api.yelp.com/v3/businesses/search'
HEADERS = {'Authorization': 'bearer %s' % MY_API_KEY}

# Define the Parameters of the search
limit = 50  # Nombre maximum d'entreprises par page
offset = 0  # Index de départ
unique_ids = set()  # Initialiser l'ensemble pour stocker les ID uniques
formatted_businesses = []



while True:
    PARAMETERS = {'location': 'Québec',
                  'limit': limit,
                  'offset': offset,
                  'categories': 'restaurants'}

    # Make a Request to the API, and return results
    response = requests.get(url=BUSINESS_PATH, params=PARAMETERS, headers=HEADERS)

    # Convert response to a JSON String
    business_data = response.json()
    businesses = business_data.get("businesses", [])

    for business in businesses:
        formatted_business = format_business_data(business)
        formatted_businesses.append(formatted_business)

        business_id = business["id"]
        unique_ids.add(business_id)

    # Vérifier s'il y a plus de pages
    if len(businesses) < limit:
        break

    # Incrémenter l'offset pour la prochaine page
    offset += limit

# Enregistrer les données formatées dans un fichier JSON
with open("restaurants.json", "w", encoding="utf-8") as json_file:
    json.dump(formatted_businesses, json_file, ensure_ascii=False, indent=4)
    print("Les données ont été enregistrées dans restaurants.json.")

'''
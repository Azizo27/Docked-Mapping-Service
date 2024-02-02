import json
from pymongo import MongoClient
from decouple import config




# Replace these with your MongoDB connection details
database_name = config('MONGODB_DBNAME')
collection_name = config('MONGODB_COLLECTION')
mongo_uri = config('MONGODB_URL')


client = MongoClient(mongo_uri)
db = client[database_name]
restaurants_collection = db[collection_name]

if restaurants_collection.count_documents({}) == 0:
    print(f"The collection '{collection_name}' in database '{database_name}' is empty.")
    with open("/app/restaurants.json", "r") as file:
        data = json.load(file)
    
    batch_size = 1000
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        restaurants_collection.insert_many(batch)

    print("Data population complete. Total documents inserted:", len(data))
else:
    print(f"The collection '{collection_name}' in database '{database_name}' is not empty.")


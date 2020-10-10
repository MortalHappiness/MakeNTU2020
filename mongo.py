import os
import json

from dotenv import load_dotenv
from pymongo import MongoClient

# ========================================

if os.getenv("FLASK_ENV") != "production":
    load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST", None)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", None)

if MONGO_HOST is None or MONGO_DB_NAME is None:
    print('Please specify MONGO_HOST and MONGO_DB_NAME ' +
          'as environment variables.')
    exit()

# ========================================

client = MongoClient(MONGO_HOST)

# Reset database
client.drop_database(MONGO_DB_NAME)
db = client[MONGO_DB_NAME]

# ========================================

with open("./data/stores.json") as fin:
    stores = json.load(fin)
    for store in stores:
        store["current_people"] = 0
    db.stores.insert_many(stores)

from pymongo import MongoClient, ASCENDING

# Connection URI format: mongodb://<username>:<password>@<host>:<port>
client = MongoClient("mongodb://root:rootpassword@mongodb:27017/")

db = client["sensor_data_db"]
collection = db["sensor_readings"]

# Create indexes
collection.create_index([("type", ASCENDING)])
collection.create_index([("building", ASCENDING)])
collection.create_index([("timestamp", ASCENDING)])
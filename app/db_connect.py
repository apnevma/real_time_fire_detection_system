from pymongo import MongoClient, ASCENDING

# Connection URI format: mongodb://<username>:<password>@<host>:<port>
client = MongoClient("mongodb://root:rootpassword@mongodb:27017/")

db = client["sensor_data_db"]

sensor_readings_collection = db["sensor_readings"]
events_collection = db["events"]
alerts_collection = db["alerts"]

# Create indexes
sensor_readings_collection.create_index([("type", ASCENDING)])
sensor_readings_collection.create_index([("building", ASCENDING)])
sensor_readings_collection.create_index([("timestamp", ASCENDING)])

events_collection.create_index([("type", ASCENDING)])
events_collection.create_index([("building", ASCENDING)])
events_collection.create_index([("start_time", ASCENDING)])

alerts_collection.create_index([("type", ASCENDING)])
alerts_collection.create_index([("detected_at", ASCENDING)])
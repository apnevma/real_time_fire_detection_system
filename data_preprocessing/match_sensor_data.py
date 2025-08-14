from pymongo import MongoClient
import pandas as pd
from datetime import datetime

client = MongoClient("mongodb://root:rootpassword@localhost:27017/")
db = client["sensor_data_db"]
collection = db["sensor_readings"]

# Fetch all documents
docs = list(collection.find())
print(f"Total documents: {len(docs)}")

# Convert to DataFrame
df = pd.DataFrame(docs)

# Keep only needed columns
df = df[["building", "floor", "type", "timestamp", "temperature", "humidity", "soundLevel"]]
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["time_bin"] = df["timestamp"].dt.floor("2min")  # bin timestamps into 2-minute intervals

# Map sensor reading values into a 'value' column
def extract_value(row):
    if row["type"] == "Temperature":
        return row["temperature"]
    elif row["type"] == "Humidity":
        return row["humidity"]
    elif row["type"] == "Acoustic":
        return row["soundLevel"]
    else:
        return None

df["value"] = df.apply(extract_value, axis=1)

# Drop the now-unnecessary value columns
df = df[["building", "floor", "time_bin", "type", "value"]]

# Pivot the table so each row has temperature, humidity, and soundLevel
pivoted = df.pivot_table(index=["building", "floor", "time_bin"], columns="type", values="value").reset_index()

# Rename columns for consistency
pivoted = pivoted.rename(columns={
    "Temperature": "temperature",
    "Humidity": "humidity",
    "Acoustic": "soundLevel"
})

# Final clean dataframe
final_df = pivoted[["temperature", "humidity", "soundLevel"]].dropna()
final_df.columns.name = None

print(final_df.head(10))
print(f"\nTotal rows in final_df: {len(final_df)}")

final_df.to_csv("data_preprocessing/matched_sensor_data.csv")

from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb://root:rootpassword@localhost:27017/")
db = client["sensor_data_db"]
collection = db["sensor_readings"]

# Load all sensor readings
docs = list(collection.find())
print(f"Total documents: {len(docs)}")

# Convert to DataFrame
df = pd.DataFrame(docs)

# Keep only useful columns
df = df[["building", "floor", "type", "event", "timestamp", "temperature", "humidity", "soundLevel"]]
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Split into 3 DataFrames
temperature_df = df[df["type"] == "Temperature"].copy()
humidity_df = df[df["type"] == "Humidity"].copy()
sound_df = df[df["type"] == "Acoustic"].copy()

# Extract values into unified 'value' column
temperature_df["value"] = temperature_df["temperature"]
humidity_df["value"] = humidity_df["humidity"]
sound_df["value"] = sound_df["soundLevel"]

# Keep only needed columns
temperature_df = temperature_df[["building", "floor", "timestamp", "event", "value"]].sort_values("timestamp")
humidity_df = humidity_df[["building", "floor", "timestamp", "event", "value"]].sort_values("timestamp")
sound_df = sound_df[["building", "floor", "timestamp", "event", "value"]].sort_values("timestamp")

# Function tp determine final event: fire if any sensor says fire, else normal
def resolve_event(row):
    if row.get("event_temp") == "fire" or row.get("event_humid") == "fire" or row.get("event_sound") == "fire":
        return "fire"
    else:
        return "normal"

# Prepare for merge_asof by sorting and grouping
merged_list = []

# Process each (building, floor) combo separately
locations = temperature_df[["building", "floor"]].drop_duplicates()

for _, loc in locations.iterrows():
    building = loc["building"]
    floor = loc["floor"]

    t_df = temperature_df[(temperature_df["building"] == building) & (temperature_df["floor"] == floor)].copy()
    h_df = humidity_df[(humidity_df["building"] == building) & (humidity_df["floor"] == floor)].copy()
    s_df = sound_df[(sound_df["building"] == building) & (sound_df["floor"] == floor)].copy()

    # Merge temperature with nearest humidity (within +-5 minutes)
    th_merged = pd.merge_asof(
        t_df, h_df,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta("3min"),
        suffixes=("_temp", "_humid")
    )

    # Merge result with nearest acoustic reading (within +-5 minutes)
    full_merged = pd.merge_asof(
        th_merged, s_df,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta("3min")
    )

    # Rename for clarity
    full_merged = full_merged.rename(columns={
        "value_temp": "temperature",
        "value_humid": "humidity",
        "value": "soundLevel",
        "event_temp": "event_temp",
        "event_humid": "event_humid",
        "event": "event_sound"  
    })

    # Drop rows with any missing sensor readings
    full_merged = full_merged.dropna(subset=["temperature", "humidity", "soundLevel"])

    # Resolve event
    full_merged["event"] = full_merged.apply(resolve_event, axis=1)

    # Keep only the final cleaned data
    merged_list.append(full_merged[["temperature", "humidity", "soundLevel", "event"]])

# Final DataFrame
df = pd.concat(merged_list, ignore_index=True)

print(df.head())
print(df["event"].value_counts())
print(f"Total rows in final_df: {len(df)}")

df.to_csv("data_preprocessing/matched_sensor_data.csv")

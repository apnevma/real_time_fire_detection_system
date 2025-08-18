import random
import uuid
import requests
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import json

athens_tz = ZoneInfo("Europe/Athens") #Athens timezone

# Configuration for humidity reading
sensor_config = {
    "Humidity": {
        "distribution": "normal",
        "mean": 60.0,
        "std": 10.0,
        "min": 30.0,
        "max": 90.0,
        "daily_deviation": 3  # Small fluctuations within the same day
    }
}

STATE_FILE = "state/last_humidity.json"
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

# Try to load the persisted last_humidity_data
try:
    with open(STATE_FILE, "r") as f:
        last_humidity_data = json.load(f)        
        # Convert keys back to tuples since JSON keys must be strings
        last_humidity_data = {
            eval(k): v for k, v in last_humidity_data.items()
        }
    # key = (building, floor), value = (humidity, date_string)
    print("Last humidity data loaded:")
    print(last_humidity_data)
except FileNotFoundError:
    last_humidity_data = {}
    print("last_humidity.json file not found!")

def generate_sensor_data(building: str, floor: int):
    # check for fire
    fire_mode = check_fire_mode(building, floor)

    # Assign fixed sensor vendor to each building
    building_vendors = {
        'A': ("HydroSense", "support@hydrosense.com"),
        'B': ("AquaMetrics", "contact@aquametrics.org"),
        'C': ("Kolumpame Gr", "info@kolympame.gr")
    }
    vendorName, vendorEmail = building_vendors[building]

    key = (building, floor)
    now = datetime.now(tz=athens_tz)
    today_str = now.date().isoformat()
    config = sensor_config["Humidity"]

    # Humidity generation logic
    if fire_mode:
        humidity = round(random.uniform(10, 30), 1)
        event = "fire"
        print("Fire mode active! Sending low humidity readings.")
    else:
        event = "normal"
        if key not in last_humidity_data or last_humidity_data[key][1] != today_str:
            # First time or new day → use full normal distribution
            humidity = random.gauss(config["mean"], config["std"])
        else:
            # Same day → small fluctuation from last value
            prev_humidity = last_humidity_data[key][0]
            humidity = prev_humidity + random.gauss(0, config["daily_deviation"])
            print("Small flunctuation! :)")
        # Clamp and round
        humidity = round(max(config["min"], min(config["max"], humidity)), 1)

        # Update last value
        last_humidity_data[key] = (humidity, today_str)

        # Save updated  value
        try:
            # Convert keys to strings for JSON
            serializable_data = {
                str(k): v for k, v in last_humidity_data.items()
            }
            with open(STATE_FILE, "w") as f:
                json.dump(serializable_data, f)
            print("Updated last value!")
        except Exception as e:
            print(f"Failed to persist humidity state: {e}")

    # Return structured sensor reading
    return {
        "sensorId": str(uuid.uuid4()),
        "type": "Humidity",
        "event": event,
        "vendorName": vendorName,
        "vendorEmail": vendorEmail,
        "description": "Simulated humidity sensor",
        "building": building,
        "floor": floor,
        "temperature": None,
        "humidity": humidity,
        "soundLevel": None,
        "timestamp": datetime.now(tz=athens_tz).isoformat()
    }

def wait_for_api(max_retries=30, delay=2):
    for _ in range(max_retries):
        try:
            response = requests.get("http://sensor-api:8000/docs")
            if response.status_code == 200:
                print("FastAPI is up! Starting data simulation.")
                return
        except Exception as e:
            print("Waiting for sensor-api to be ready...")
        time.sleep(delay)
    raise Exception("sensor-api service did not become available in time.")

def check_fire_mode(building, floor):
    try:
        response = requests.get(f"http://sensor-api:8000/fire-status/{building}/{floor}")
        if response.status_code == 200:
            return response.json().get("fire") == True
    except Exception as e:
        print(f"Error checking fire mode: {e}")
    return False  # Default to normal

def simulate_posting():
    wait_for_api()
    while True:
        # Scenario: 3 buildings (A–C), 4 floors each
        for building in ['A', 'B', 'C']:    # Buildings A, B, C
            for floor in range(1, 5):  # Floors 1 to 4
                humidity_data = generate_sensor_data(building, floor)
                try:
                    response = requests.post("http://sensor-api:8000/sensor-data/", json=humidity_data)
                    print(f"Sent data: {humidity_data}")
                    print(f"Response: {response.status_code}, {response.json()}")
                except Exception as e:
                    print(f"Error posting data: {e}")
        time.sleep(600)  # Post every 10 minutes

if __name__ == "__main__":
    simulate_posting()
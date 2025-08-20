import random
import uuid
import requests
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import json

athens_tz = ZoneInfo("Europe/Athens") #Athens timezone

# Configuration for temperature reading
sensor_config = {
    "Temperature": {
        "min": 16.0,
        "max": 30.0,
        "mean": 22.5,
        "std": 2.0,  # For daily initial value
        "daily_deviation": 0.4  # Small fluctuations within the same day
    }
}

STATE_FILE = "state/last_temperature.json"
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

# Try to load the persisted last_temperature_data
try:
    with open(STATE_FILE, "r") as f:
        last_temperature_data = json.load(f)
        # Convert keys back to tuples since JSON keys must be strings
        last_temperature_data = {
            eval(k): v for k, v in last_temperature_data.items()
        }
    print("Last temperature data loaded:")
    print(last_temperature_data)
except FileNotFoundError:
    last_temperature_data = {}
    print("last_temperature.json file not found!")

def generate_sensor_data(building: str, floor: int):
    # check for fire
    fire_mode = check_fire_mode(building, floor)

    # Assign fixed sensor vendor to each building
    building_vendors = {
        'A': ("ACME Corp", "support@acmecorp.com"),
        'B': ("ThermoSense", "contact@thermosense.org"),
        'C': ("ExoumeSkasei Gr", "service@exoumeskasei.gr")
    }
    vendorName, vendorEmail = building_vendors[building]

    key = (building, floor)
    now = datetime.now(tz=athens_tz)
    today_str = now.date().isoformat()
    config = sensor_config["Temperature"]

    # Temperature generation logic
    if fire_mode:
        temperature = round(random.uniform(55, 80), 1)
        #event = "fire"
        print("Fire mode active! Sending high temperature.")
    else:
        #event = "normal"
        if key not in last_temperature_data or last_temperature_data[key][1] != today_str:
            # First time or new day → use full normal distribution
            temperature = random.gauss(config["mean"], config["std"])
            print("Big flunctuation! :(")
        else:
            # Same day → small fluctuation from last value
            prev_temperature = last_temperature_data[key][0]
            temperature = prev_temperature + random.gauss(0, config["daily_deviation"])
            print("Small flunctuation! :)")
        # Clamp and round
        temperature = round(max(config["min"], min(config["max"], temperature)), 1)

        # Update last value
        last_temperature_data[key] = (temperature, today_str)

        # Save updated  value
        try:
            # Convert keys to strings for JSON
            serializable_data = {
                str(k): v for k, v in last_temperature_data.items()
            }
            with open(STATE_FILE, "w") as f:
                json.dump(serializable_data, f)
            print("Updated last value!")
        except Exception as e:
            print(f"Failed to persist temperature state: {e}")

    # Return structured sensor reading
    return {
        "sensorId": str(uuid.uuid4()),
        "type": "Temperature",
        #"event": event,
        "vendorName": vendorName,
        "vendorEmail": vendorEmail,
        "description": "Simulated temperature sensor",
        "building": building,
        "floor": floor,
        "temperature": temperature,
        "humidity": None,
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
            print("Waiting for temp-api to be ready...")
        time.sleep(delay)
    raise Exception("temp-api service did not become available in time.")

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
                data = generate_sensor_data(building, floor)
                try:
                    response = requests.post("http://sensor-api:8000/sensor-data/", json=data)
                    print(f"Sent data: {data}")
                    print(f"Response: {response.status_code}, {response.json()}")
                except Exception as e:
                    print(f"Error posting data: {e}")
        time.sleep(300)  # Post every 5 minutes

if __name__ == "__main__":
    simulate_posting()
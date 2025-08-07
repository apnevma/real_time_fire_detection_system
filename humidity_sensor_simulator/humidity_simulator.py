import random
import uuid
import requests
import time
from datetime import datetime
from zoneinfo import ZoneInfo

athens_tz = ZoneInfo("Europe/Athens") #Athens timezone

# Configuration for humidity reading
sensor_config = {
    "Humidity": {
        "distribution": "normal",
        "mean": 60.0,
        "std": 10.0,
        "min": 30.0,
        "max": 90.0
    }
}

def generate_sensor_data(building: str, floor: int):
    # Assign fixed sensor vendor to each building
    building_vendors = {
        'A': ("HydroSense", "support@hydrosense.com"),
        'B': ("AquaMetrics", "contact@aquametrics.org"),
        'C': ("Kolumpame Gr", "info@kolympame.gr")
    }
    vendorName, vendorEmail = building_vendors[building]

    # Humidity generation logic: Gaussian distribution
    config = sensor_config["Humidity"]
    if config["distribution"] == "normal":
        humidity = random.gauss(config["mean"], config["std"])
        humidity = max(config["min"], min(config["max"], humidity))  # Clamp to [min, max]
    else:
        humidity = random.uniform(config["min"], config["max"])
    humidity = round(humidity, 1)

    # Return structured sensor reading
    return {
        "sensorId": str(uuid.uuid4()),
        "type": "Humidity",
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
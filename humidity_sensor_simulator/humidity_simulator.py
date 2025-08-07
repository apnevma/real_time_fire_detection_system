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

def generate_sensor_data():
    vendors = [
        ("HydroSense", "support@hydrosense.com"),
        ("AquaMetrics", "contact@aquametrics.org"),
        ("HumidityPro", "service@humiditypro.com"),
        ("Kolumpame Gr", "info@kolympame.gr")
    ]

    vendorName, vendorEmail = random.choice(vendors)

    # Scenario: 3 buildings (A–C), 4 floors each
    building = random.choice(['A', 'B', 'C'])
    floor = random.randint(1, 4)

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
        humidity_data = generate_sensor_data()
        try:
            respone = requests.post("http://sensor-api:8000/sensor-data/", json=humidity_data)
            print(f"Response: {respone.status_code}, {respone.json()}")
        except Exception as e:
            print(f"Error posting humidity data: {e}")
        time.sleep(10)

if __name__ == "__main__":
    simulate_posting()
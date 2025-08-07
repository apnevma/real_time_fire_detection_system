import random
import uuid
import requests
import time
from datetime import datetime
from zoneinfo import ZoneInfo

athens_tz = ZoneInfo("Europe/Athens") #Athens timezone

# Configuration for temperature reading
sensor_config = {
    "Temperature": {
        "min": 16.0,
        "max": 30.0,
        "mean": 22.5,
        "std": 2.0,
        "distribution": "normal"
    }
}

def generate_sensor_data():
    vendors = [
        ("ACME Corp", "support@acmecorp.com"),
        ("CoolTech Inc", "info@cooltech.com"),
        ("ThermoSense", "contact@thermosense.org"),
        ("ExoumeSkasei Gr", "service@exoumeskasei.gr")
    ]

    vendorName, vendorEmail = random.choice(vendors)

    # Scenario: 3 buildings (A–C), 4 floors each
    building = random.choice(['A', 'B', 'C'])
    floor = random.randint(1, 4)

    # Temperature generation logic: Gaussian distribution
    config = sensor_config["Temperature"]
    if config["distribution"] == "normal":
        temperature = random.gauss(config["mean"], config["std"])
        temperature = max(config["min"], min(config["max"], temperature))  # Clamp to [min, max]
    else:
        temperature = random.uniform(config["min"], config["max"])
    temperature = round(temperature, 1)

    # Return structured sensor reading
    return {
        "sensorId": str(uuid.uuid4()),
        "type": "Temperature",
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

def simulate_posting():
    wait_for_api()
    while True:
        data = generate_sensor_data()
        try:
            response = requests.post("http://sensor-api:8000/sensor-data/", json=data)
            print(f"Sent data: {data}")
            print(f"Response: {response.status_code}, {response.json()}")
        except Exception as e:
            print(f"Error posting data: {e}")
        time.sleep(600)  # Post every 10 minutes

if __name__ == "__main__":
    simulate_posting()
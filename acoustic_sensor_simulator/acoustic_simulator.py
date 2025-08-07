import random
import uuid
import requests
import time
from datetime import datetime
from zoneinfo import ZoneInfo

athens_tz = ZoneInfo("Europe/Athens") #Athens timezone

sensor_config = {
    "Acoustic": {
        "min": 30.0,       # Quiet room (e.g., whisper)
        "max": 90.0,      # Very loud (e.g., factory, heavy traffic)
        "mean": 55.0,      # Normal environment (e.g., conversation level)
        "std": 10.0,       # Natural variation
        "distribution": "normal"
    }
}

def generate_sensor_data():
    vendors = [
        ("SoundWave Systems", "support@soundwave.com"),
        ("EchoTrack Inc", "info@echotrack.io"),
        ("AcoustiCore", "service@acousticore.net"),
        ("Koufathikame Gr", "info@koufathikame.gr")
    ]

    vendorName, vendorEmail = random.choice(vendors)

    # Scenario: 3 buildings (A–C), 50 rooms each
    building = random.choice(['A', 'B', 'C'])
    room = random.randint(1, 50)

    # Sound Level generation logic: Gaussian distribution
    config = sensor_config["Acoustic"]
    if config["distribution"] == "normal":
        soundLevel = random.gauss(config["mean"], config["std"])
        soundLevel = max(config["min"], min(config["max"], soundLevel))  # Clamp to [min, max]
    else:
        soundLevel = random.uniform(config["min"], config["max"])
    soundLevel = round(soundLevel, 1)

    # Return structured sensor reading
    return {
        "sensorId": str(uuid.uuid4()),
        "type": "Acoustic",
        "vendorName": vendorName,
        "vendorEmail": vendorEmail,
        "description": "Simulated acoustic sensor",
        "building": building,
        "room": room,
        "temperature": None,
        "humidity": None,
        "soundLevel": soundLevel,
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
        acoustic_data = generate_sensor_data()
        try:
            respone = requests.post("http://sensor-api:8000/sensor-data/", json=acoustic_data)
            print(f"Response: {respone.status_code}, {respone.json()}")
        except Exception as e:
            print(f"Error posting acoustic data: {e}")
        time.sleep(10)

if __name__ == "__main__":
    simulate_posting()
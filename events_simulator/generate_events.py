import requests
import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# Timezone setup
athens_tz = ZoneInfo("Europe/Athens")

# Config
event_types_probabilities = {
    "fire": 0.05,  # 5% chance
}
max_duration_seconds = 3600  # 1 hour
min_duration_seconds = 300  # 5 minutes
    
def check_fire_status(building, floor):
    try:
        response = requests.get(f"http://sensor-api:8000/fire-status/{building}/{floor}")
        if response.status_code == 200:
            return response.json().get("fire") == True
    except Exception as e:
        print(f"Failed to check active events for {building} Floor {floor}: {e}")
    return False  # Default to normal

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

def generate_random_event(building, floor, event_types_probabilities, min_duration_seconds, max_duration_seconds):
    now = datetime.now(tz=athens_tz)

    if check_fire_status(building, floor):
        print(f"Skipping {building} Floor {floor} (active fire exists)")
        return
    
    for event_type, prob in event_types_probabilities.items():
        if random.random() < prob:
            duration = random.randint(min_duration_seconds, max_duration_seconds)
            event = {
                "type": event_type,
                "building": building,
                "floor": floor,
                "start_time": now.isoformat(),
                "duration": duration
            }
            return event
        else:
            print(f"No {event_type} event for {building} Floor {floor} this round.")
    
    return None  # In case no event is selected

def simulate_posting():
    wait_for_api()
    while True:
        # Scenario: 3 buildings (A–C), 4 floors each
        for building in ['A', 'B', 'C']:    # Buildings A, B, C
            for floor in range(1, 5):  # Floors 1 to 4
                event = generate_random_event(building, floor, event_types_probabilities, min_duration_seconds, max_duration_seconds)
                if event:
                    try:
                        response = requests.post("http://sensor-api:8000/events/", json=event)
                        print(f"Sent data: {event}")
                        print(f"Response: {response.status_code}, {response.json()}")
                    except Exception as e:
                        print(f"Failed to post event: {e}")
        time.sleep(600)  # Post every 10 minutes

if __name__ == "__main__":
    simulate_posting()

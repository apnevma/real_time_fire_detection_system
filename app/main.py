from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import pytz
import json
import os
from db_connect import collection, events_collection, alerts_collection
from zoneinfo import ZoneInfo
import joblib

# Timezone setup
athens_tz = ZoneInfo("Europe/Athens")

app = FastAPI()

# file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))      # folder for HTML files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR,"static")), name="static")     # allows serving to css/js

FILE_PATH = os.path.join(BASE_DIR, "sensor_data.json")      # sensor_data.json file path
rf_model_path = os.path.join("ML", "models", "rf_model.pkl")

# Load ML Models
rf_model = joblib.load(rf_model_path)

# Pydantic models
class SensorData(BaseModel):
    sensorId: str
    type: str
    vendorName: str
    vendorEmail: EmailStr
    description: Optional[str]
    building: str
    floor: int
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soundLevel: Optional[float] = None

class Event(BaseModel):
    type: str
    building: str
    floor: int
    start_time: str 
    duration: int       # In seconds

@app.post("/sensor-data/")
async def receive_sensor_data(data: SensorData):
    sensor_dict = data.model_dump()

    # Save timestamp to local timezone, instead of UTC
    local_tz = pytz.timezone("Europe/Athens")  
    now = datetime.now(local_tz).isoformat()
    sensor_dict["timestamp"] = now

    # Save to MongoDB
    try:
        result = collection.insert_one(sensor_dict)
    except Exception as e:
        print(f"File Write Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save data to file")
    
    # Attempt Fire Detection
    try:
        # Look for 3 recent readings (temperature, humidity, soundLevel)
        window_start = datetime.now(local_tz) - timedelta(minutes=1)
        query = {
            "building": data.building,
            "floor": data.floor,
            "timestamp": {"$gte": window_start.isoformat()}
        }
        recent = list(collection.find(query))

        # Group by sensor type
        latest = {d["type"]: d for d in recent}

        if {"Temperature", "Humidity", "Acoustic"}.issubset(latest):
            # Extract feature vector
            temp = latest["Temperature"]["temperature"]
            hum = latest["Humidity"]["humidity"]
            sound = latest["Acoustic"]["soundLevel"]

            features = [[temp, hum, sound]]

            # Make prediction
            prediction = rf_model.predict(features)[0]  
            predicted_label = "fire" if prediction == 1 else "normal"       # 1 = fire, 0 = normal

            print(f"Prediction for {data.building}-{data.floor}: {predicted_label.upper()}")

            # Save Fire predictions to alerts collection
            if prediction == 1:
                alerts_collection.insert_one({
                    "building": data.building,
                    "floor": data.floor,
                    "detected_at": now,
                    "type": "fire",
                    "source": "model_prediction",
                    "sensor_data": {
                        "temperature": temp,
                        "humidity": hum,
                        "soundLevel": sound
                    }
                })

            return {
                "message": "Data saved and prediction made",
                "prediction": predicted_label,
                "id": str(result.inserted_id)
            }
        
    except Exception as e:
        print(f"Prediction Error: {e}")
    
    return {
        "message": "Data saved (prediction skipped or not enough data)",
        "id": str(result.inserted_id)
    }
    

@app.post("/events")
async def receive_event(event: Event):
    event_dict = event.model_dump()
    try:
        events_collection.insert_one(event_dict)
        return {"message": "Event stored successfully"}
    except Exception as e:
        print("Failed to save event!")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sensor-data/")
async def query_sensor_data(
    type: Optional[str] = Query(None, description="Temperature, Humidity or Acoustic"),
    building: Optional[str] = Query(None, description="A, B or C"),
    floor: Optional[int] = Query(None, description="1 - 4"),
    start_time: Optional[str] = Query(None, description="Start datetime (e.g., 2025-08-06 or 2025-08-06T14:00:00)"),
    end_time: Optional[str] = Query(None, description="End datetime (exclusive, e.g., 2025-08-07 or 2025-08-06T18:00:00)"),
    page: int = 1,
    page_size: int = 10
):
    query = {}

    # Add filters
    if type:
        query["type"] = type
    if building:
        query["building"] = building
    if floor:
        query["floor"] = floor
    if start_time or end_time:
        time_filter = {}
        try:
            if start_time:
                start_dt = datetime.fromisoformat(start_time)
                time_filter["$gte"] = start_dt.isoformat()

            if end_time:
                end_dt = datetime.fromisoformat(end_time)
                time_filter["$lt"] = end_dt.isoformat()

            query["timestamp"] = time_filter

        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")

    try:
        skip = (page - 1) * page_size
        results = list(collection.find(query).skip(skip).limit(page_size))
        
        # Convert ObjectId to string
        for r in results:
            r["_id"] = str(r["_id"])
        
        return {
            "page": page,
            "page_size": page_size,
            "results": results
        }

    except Exception as e:
        print(f"Query Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to query sensor data")
    

@app.get("/sensors/stats/{sensor_type}")
def get_sensor_stats(sensor_type: str):
    valid_sensor_types = {
        "Temperature": "temperature",
        "Humidity": "humidity",
        "Acoustic": "soundLevel"
    }

    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=400, detail="Invalid sensor type. Must be Temperature, Humidity or Acoustic.")
    
    sensor_field = valid_sensor_types[sensor_type]

    # Get readings from MongoDB
    readings = list(collection.find({"type":sensor_type}))

    if not readings:
        raise HTTPException(status_code=404, detail=f"No data found for sensor type: {sensor_type}")
    
    # Extract values 
    values = [reading[sensor_field] for reading in readings if isinstance(reading[sensor_field], (int, float))]

    if not values:
        raise HTTPException(status_code=404, detail=f"No numeric values found for {sensor_type}")
    
    values.sort()

    stats = {
        "sensorType": sensor_type,
        "min": values[0],
        "max": values[-1],
        "range": values[-1] - values[0],
        "mean": round(sum(values) / len(values)),
        "top10_max": sorted(values, reverse=True)[:10],
        "top10_min": values[:10]
    }

    return JSONResponse(content=stats)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("visualize.html", {"request": request})

# Returns currently active events for a given building and floor.
@app.get("/events/active")
def get_active_events(building: str = Query(...), floor: int = Query(...)):
    now = datetime.now(tz=athens_tz)

    # Find events whose time range includes `now`
    events = events_collection.find({
        "building": building,
        "floor": floor,
        "start_time": {"$lte": now.isoformat()}
    })

    active_events = []
    for event in events:
        try:
            start_time = datetime.fromisoformat(event["start_time"])
            end_time = start_time + timedelta(seconds=event["duration"])
            if now <= end_time:
                event["_id"] = str(event["_id"])
                active_events.append(event)
        except Exception as e:
            print(f"Error parsing event time: {e}")

    return JSONResponse(content=active_events)

@app.get("/fire-status/{building}/{floor}")
def get_fire_status(building: str, floor: int):
    try:
        now = datetime.now(tz=athens_tz)

        # Find all fire events for the location
        fire_events = events_collection.find({
            "type": "fire",
            "building": building,
            "floor": int(floor)
        })

        for event in fire_events:
            # Check if still active (based on duration)
            start = datetime.fromisoformat(event["start_time"])
            end = start + timedelta(seconds=event["duration"])
            if start <= now <= end:
                return {"fire": True}

        return {"fire": False}

    except Exception as e:
        print(f"Error fetching fire status: {e}")
        raise HTTPException(status_code=500, detail="Error checking fire status")

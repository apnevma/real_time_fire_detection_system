from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import os
import math
from db_connect import sensor_readings_collection, events_collection, alerts_collection
from zoneinfo import ZoneInfo
import joblib
from keras.models import load_model

app = FastAPI()

# Timezone setup
local_tz = ZoneInfo("Europe/Athens")

# Setup for sensor data visualization
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))      # Set directory for HTML templates
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR,"static")), name="static")     # Serve static assets (CSS, JS)

# ML model paths
rf_model_path = os.path.join("ML", "models", "rf_model.pkl")
nn_model_path = os.path.join("ML", "models", "nn_model.keras")
scaler_path = os.path.join("ML", "models", "scaler.pkl")
# Load ML models
rf_model = joblib.load(rf_model_path)
nn_model = load_model(nn_model_path)
scaler = joblib.load(scaler_path)

active_connections = []

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
    now = datetime.now(local_tz).isoformat()
    sensor_dict["timestamp"] = now

    # Save to MongoDB
    try:
        result = sensor_readings_collection.insert_one(sensor_dict)
    except Exception as e:
        print(f"File Write Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save data to file")
    
    # Attempt Fire Detection
    try:
        model_name = "nn_model"
        await live_fire_detection(result, data, now, model_name)
    except Exception as e:
        print(f"Prediction Error: {e}")
    
    return {
        "message": "Data saved",
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
        results = list(sensor_readings_collection.find(query).skip(skip).limit(page_size))
        total_results = sensor_readings_collection.count_documents(query)
        
        # Convert ObjectId to string
        for r in results:
            r["_id"] = str(r["_id"])
        
        return {
            "page": page,
            "page_size": page_size,
            "total_results": total_results,
            "total_pages": math.ceil(total_results / page_size),
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
    readings = list(sensor_readings_collection.find({"type":sensor_type}))

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


# Returns currently active events
@app.get("/events/active")
def get_active_events(page: int = 1, page_size: int = 10):
    now = datetime.now(tz=local_tz)

    # Find events whose time range includes `now`
    events = events_collection.find({"start_time": {"$lte": now.isoformat()}})
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

    if len(active_events) == 0:
        return "There are no active events currently  :)"
    
    # Apply pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated_results = active_events[start:end]
        
    return {
        "page": page,
        "page_size": page_size,
        "total_results": len(active_events),
        "total_pages": math.ceil(len(active_events) / page_size),
        "results": paginated_results
        }
    

@app.get("/fire-status/{building}/{floor}")
def get_fire_status(building: str, floor: int):
    try:
        now = datetime.now(tz=local_tz)

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


@app.websocket("/ws/alerts")
async def alert_websocket(websocket: WebSocket):
    print("WebSocket endpoint hit! :)")
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await asyncio.sleep(10)  # keep connection alive
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("WebSocket client disconnected.")


async def notify_clients(alert: dict):
    for conn in active_connections:
        try:
            await conn.send_json(alert)
            print("Alert sent to websocket:", alert)
        except Exception as e:
            print(f"WebSocket send error: {e}")


# Predict fire status    
async def live_fire_detection(result, data: SensorData, now, model_name:str = "nn_model"):
        # Look for 3 recent readings (temperature, humidity, soundLevel)
        window_start = datetime.now(local_tz) - timedelta(minutes=1)
        query = {
            "building": data.building,
            "floor": data.floor,
            "timestamp": {"$gte": window_start.isoformat()}
        }
        recent = list(sensor_readings_collection.find(query))

        # Group by sensor type
        latest = {d["type"]: d for d in recent}

        if {"Temperature", "Humidity", "Acoustic"}.issubset(latest):
            # Extract feature vector
            temp = latest["Temperature"]["temperature"]
            hum = latest["Humidity"]["humidity"]
            sound = latest["Acoustic"]["soundLevel"]

            features = [[temp, hum, sound]]

            # Make prediction with chosen model
            if model_name == "nn_model":
                scaled_features = scaler.transform(features)        # Scale input (only for NN)
                prediction = (nn_model.predict(scaled_features)[0] > 0.5).astype("int32")
            else:
                prediction = rf_model.predict(features)[0]
            
            predicted_label = "fire" if prediction == 1 else "normal"       # 1 = fire, 0 = normal

            print(f"Prediction for {data.building}-{data.floor}: {predicted_label.upper()}")

            # Look for an existing fire alert without an ended_at timestamp
            existing_alert = alerts_collection.find_one({
                "building": data.building,
                "floor": data.floor,
                "type": "fire",
                "ended_at": {"$exists": False}
                })
            # Save Fire predictions to alerts collection
            if prediction == 1:
                if not existing_alert:
                    alert = {
                        "building": data.building,
                        "floor": data.floor,
                        "detected_at": now,
                        "type": "fire",
                        "source": model_name,
                        "sensor_data": {
                            "temperature": temp,
                            "humidity": hum,
                            "soundLevel": sound
                        }
                    }
                    alerts_collection.insert_one(alert)
                    print("New fire alert inserted!")
                    alert["_id"] = str(result.inserted_id)
                    await notify_clients(alert)
                else:
                    print("Fire already ongoing — no new alert inserted.")

            elif prediction == 0:
                if existing_alert:
                    # Fire has ended — update alert with ended_at timestamp
                    alerts_collection.update_one(
                        {"_id": existing_alert["_id"]},
                        {"$set": {"ended_at": now}}
                    )
                    print("Fire alert closed with ended_at.")
                else:
                    print("No ongoing fire alert to close.")

            return {
                "message": "Prediction made",
                "prediction": predicted_label,
                "id": str(result.inserted_id)
            }

# Sensor System

This project simulates a multi-sensor system using Docker containers. Each sensor (temperature, humidity, acoustic) runs in its own container and sends data to a central API, which stores it in a MongoDB database.

## Features

- Sensor simulators (Temperature, Humidity, Acoustic)
- Central FastAPI server for data collection
- MongoDB for data storage
- Mongo Express UI
- Docker Compose setup
- Persistent state tracking for realistic fluctuations
- Interactive dashboard for visualization


## Sensor Data Simulation

This project simulates three types of sensors: temperature, humidity, and acoustic. For each sensor type, a reading is generated every 10 minutes for all floors of all buildings in the simulated environment.

    There are 3 buildings: A, B, and C

    Each building has 4 floors

    That gives 12 unique locations per sensor type

As a result, 36 sensor readings (12 per sensor type) are created and sent to the database every 10 minutes.

Each reading includes metadata such as sensor type, vendor info, building and floor location, timestamp, and the simulated value. The values are generated using a normal distribution within realistic min/max ranges defined per sensor.


## Realistic Sensor Fluctuations (Temperature & Humidity)

To make simulation more realistic:

- Each (building, floor) combination retains its latest temperature and humidity reading in a state file (`state/last_temperature.json` or `state/last_humidity.json`).
- If a new reading is on the same day, it’s generated with a small fluctuation based on the previous value.
- If it’s a new day, the reading resets using a full normal distribution.

This behavior ensures that readings over the same day change gradually, imitating real-world sensor behavior and avoiding unrealistic spikes.

## Event Simulation (Fire Mode)

The system includes a probabilistic event simulator that currently generates fire events. Each location (building + floor) has a small chance (default 5%) of entering a fire state.

- Active fire events are stored in a MongoDB events collection.
- When a location is under an active fire event, all three sensor simulators (temperature, humidity, and acoustic) adjust their behavior to generate abnormal readings.

## Data Visualization Dashboard

A web dashboard is available to interactively view sensor readings over time.

### Dashboard features:
- Built with FastAPI and Jinja2 templates
- Powered by Chart.js
- Allows you to filter by:
  - Sensor type (Temperature, Humidity, Acoustic)
  - Building (A, B, C)
  - Floor (1–4)
- Shows time-series line chart of sensor values
- Allows multiple location (building, floor) data plotting within the same chart

### Access:
- Navigate to `http://localhost:8000`  
- Select the filters and press "Load Data" to view the chart

## Machine Learning for Fire Detection

A basic machine learning pipeline has been added to detect fire events based on sensor data.

### Data Preprocessing
- Sensor readings from different simulators are matched by building, floor, and approximate timestamp to form a combined dataset.
- The resulting dataset includes: temperature, humidity, soundLevel, and the event label ("normal" or "fire").
- This is saved to ML/matched_sensor_data.csv.

### Models Trained

#### 1. Random Forest Classifier
- Trained on the preprocessed dataset
- Handles class imbalance using class_weight="balanced"
- Evaluated using accuracy, confusion matrix, and feature importance

#### 2. Neural Network
- A simple feedforward model with:
  - Two hidden layers (16 and 8 neurons)
  - ReLU activations and sigmoid output
- Uses binary cross-entropy loss
- Features normalized using StandardScaler
- Evaluated on 20% test set with validation split during training

Both models achieved high accuracy on the current dataset, showing that the simulated features are highly predictive of fire events.

## Getting Started

### Prerequisites
- Make sure you have Docker and Docker Compose installed and running on your machine.

### Steps
1. Clone the repo
2. Run `docker compose -f docker-compose-mongodb.yml -p mongodb up --build -d`
3. Monitor sensor data in Mongo Express or query the API

## Endpoints

- `POST /sensor-data/`: Send sensor reading
- `POST /events/`: Send event to database
- `GET /sensor-data/`: Query sensor data by sensor_type, location or timestamp
- `GET /sensors/stats/{sensor_type}`: Get sensor statistics (min, max, mean, top10_min, top10_max)
- `GET /events/active`: Retrive currently active fire events (used by simulators to determine fire mode)

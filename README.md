# Sensor System

This project simulates a multi-sensor system using Docker containers. Each sensor (temperature, humidity, acoustic) runs in its own container and sends data to a central API, which stores it in a MongoDB database.

## Features

- Sensor simulators (Temperature, Humidity, Acoustic)
- Central FastAPI server for data collection
- MongoDB for data storage
- Mongo Express UI
- Docker Compose setup

## Getting Started

1. Clone the repo
2. Run `docker compose -f docker-compose-mongodb.yml -p mongodb up --build -d`
3. Monitor sensor data in Mongo Express or query the API

## Endpoints

- `POST /sensor-data/`: Send sensor reading
- `GET /sensor-data/`: Query sensor data by sensor_type, location or timestamp
- `GET /sensors/stats/{sensor_type}`: Get sensor statistics (min, max, mean, top10_min, top10_max)

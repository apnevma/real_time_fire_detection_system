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
2. Run `docker-compose -f docker-compose-mongodb.yml up --build`
3. Monitor sensor data in Mongo Express or query the API

## Endpoints

- `POST /sensor-data/`: Send sensor reading
- `GET /sensor-data/`: View all readings
- `GET /sensors/stats/{sensor_type}`: Get min, max, avg

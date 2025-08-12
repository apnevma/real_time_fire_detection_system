import pytest
import os
import json
from datetime import datetime, date
from humidity_sensor_simulator import humidity_simulator

def test_generate_sensor_data_first_call(tmp_path, monkeypatch):
    # Use a temporary directory for state file
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    fake_state_file = state_dir / "last_humidity.json"

    # Patch the STATE_FILE path used in the module
    monkeypatch.setattr(humidity_simulator, "STATE_FILE", str(fake_state_file))
    monkeypatch.setattr(humidity_simulator, "last_humidity_data", {})

    # Run function
    data = humidity_simulator.generate_sensor_data("A", 1)

    # Assert structure
    assert data["sensorId"]
    assert data["type"] == "Humidity"
    assert data["building"] == "A"
    assert data["floor"] == 1
    assert humidity_simulator.sensor_config["Humidity"]["min"] <= data["humidity"] <= humidity_simulator.sensor_config["Humidity"]["max"]

    # Check that state file was created and contains the expected data
    with open(fake_state_file, "r") as f:
        saved = json.load(f)
        assert str(("A", 1)) in saved

def test_generate_sensor_data_with_existing_state(tmp_path, monkeypatch):
    # Use a temporary directory for state file
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    fake_state_file = state_dir / "last_humidity.json"

    # Patch the path and reset the internal cache
    monkeypatch.setattr(humidity_simulator, "STATE_FILE", str(fake_state_file))
    monkeypatch.setattr(humidity_simulator, "last_humidity_data", {})

    # Initial state: simulate previous reading for A-1
    initial_humidity = 60
    now = datetime.now(humidity_simulator.athens_tz)
    today_str = now.date().isoformat()
    fake_state = {
        str(("A", 1)) : [initial_humidity, today_str]
    }
    with open(fake_state_file, "w") as f:
        json.dump(fake_state, f)

    # Run function
    data = humidity_simulator.generate_sensor_data("A", 1)
    
    new_humidity = data["humidity"]
    # Apply same rounding as in your simulator
    new_humidity = round(new_humidity, 1)
    min_humidity = humidity_simulator.sensor_config["Humidity"]["min"]
    max_humidity = humidity_simulator.sensor_config["Humidity"]["max"]
    daily_deviation = humidity_simulator.sensor_config["Humidity"]["daily_deviation"]

    assert data["building"] == "A"
    assert data["floor"] == 1

    assert abs(new_humidity - initial_humidity) <= 3 * daily_deviation, "Humidity fluctuation should stay within 3×std deviation"
    assert min_humidity <= new_humidity <= max_humidity, "Humidity should be within defined range"

    # Check that state file was updated
    with open(fake_state_file, "r") as f:
        saved = json.load(f)
        
        key = str(("A", 1))
        assert key in saved

        # Extract saved humidity and date
        saved_humidity, saved_date = saved[key]

        # Convert back to float (JSON may store numbers as float, but you used str())
        saved_humidity = float(saved_humidity)
        saved_humidity = round(saved_humidity, 1)

        # Check that humidity and date are correct
        assert abs(saved_humidity - new_humidity) < 0.0001, "Saved humidity should match generated humidity"
        assert saved_date == today_str, "Saved date should be today's date"
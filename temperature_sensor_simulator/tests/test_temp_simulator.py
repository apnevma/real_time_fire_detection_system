import pytest
import os
import json
from datetime import datetime, date
from temperature_sensor_simulator import temp_simulator

def test_generate_sensor_data_first_call(tmp_path, monkeypatch):
    # Use a temporary directory for state file
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    fake_state_file = state_dir / "last_temperature.json"

    # Patch the STATE_FILE path used in the module
    monkeypatch.setattr(temp_simulator, "STATE_FILE", str(fake_state_file))
    monkeypatch.setattr(temp_simulator, "last_temperature_data", {})

    # Run function
    data = temp_simulator.generate_sensor_data("A", 1)

    # Assert structure
    assert data["sensorId"]
    assert data["type"] == "Temperature"
    assert data["building"] == "A"
    assert data["floor"] == 1
    assert temp_simulator.sensor_config["Temperature"]["min"] <= data["temperature"] <= temp_simulator.sensor_config["Temperature"]["max"]

    # Check that state file was created and contains the expected data
    with open(fake_state_file, "r") as f:
        saved = json.load(f)
        assert str(("A", 1)) in saved

def test_generate_sensor_data_with_existing_state(tmp_path, monkeypatch):
    # Use a temporary directory for state file
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    fake_state_file = state_dir / "last_temperature.json"

    # Patch the path and reset the internal cache
    monkeypatch.setattr(temp_simulator, "STATE_FILE", str(fake_state_file))
    monkeypatch.setattr(temp_simulator, "last_temperature_data", {})

    # Initial state: simulate previous reading for A-1
    initial_temp = 22.5
    now = datetime.now(temp_simulator.athens_tz)
    today_str = now.date().isoformat()
    fake_state = {
        str(("A", 1)) : [initial_temp, today_str]
    }
    with open(fake_state_file, "w") as f:
        json.dump(fake_state, f)

    # Run function
    data = temp_simulator.generate_sensor_data("A", 1)
    
    new_temp = data["temperature"]
    min_temp = temp_simulator.sensor_config["Temperature"]["min"]
    max_temp = temp_simulator.sensor_config["Temperature"]["max"]
    daily_deviation = temp_simulator.sensor_config["Temperature"]["daily_deviation"]

    assert data["building"] == "A"
    assert data["floor"] == 1

    assert abs(new_temp - initial_temp) <= 3 * daily_deviation, "Temperature fluctuation should stay within 3×std deviation"
    assert min_temp <= new_temp <= max_temp, "Temperature should be within defined range"

    # Check that state file was updated
    with open(fake_state_file, "r") as f:
        saved = json.load(f)
        
        key = str(("A", 1))
        assert key in saved

        # Extract saved temperature and date
        saved_temp, saved_date = saved[key]

        # Convert back to float (JSON may store numbers as float, but you used str())
        saved_temp = float(saved_temp)

        # Check that temperature and date are correct
        assert abs(saved_temp - new_temp) < 0.0001, "Saved temperature should match generated temperature"
        assert saved_date == today_str, "Saved date should be today's date"
import pytest
import os
import json
from datetime import datetime
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

"""Compatibility checks backed by anonymized firmware response samples."""

import json
from pathlib import Path

from custom_components.unifi_mobility.binary_sensor import BINARY_SENSORS
from custom_components.unifi_mobility.sensor import SENSORS

FIXTURES = Path(__file__).parent / "fixtures"


def test_umr_industrial_eu_1_17_11_sample() -> None:
    sample = json.loads(
        (FIXTURES / "umr_industrial_eu_1_17_11.json").read_text(encoding="utf-8")
    )
    data = sample["responses"]
    sensor_values = {item.key: item.value_fn(data) for item in SENSORS}
    binary_values = {item.key: item.value_fn(data) for item in BINARY_SENSORS}

    assert sample["model"] == "UMR-Industrial-EU"
    assert sensor_values["firmware"] == sample["firmware"]
    assert sensor_values["operator"] == "Example Mobile"
    assert sensor_values["data_usage"] == 250000000
    assert sensor_values["data_remaining"] == 750000000
    assert sensor_values["data_usage_percent"] == 25.0
    assert sensor_values["network_type"] == "LTE"
    assert binary_values == {
        "connectivity": True,
        "sim_present": True,
        "pin_locked": False,
        "activated": True,
        "poe_passthrough": True,
    }

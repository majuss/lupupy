"""Synthetic modern/legacy battery data; no private inventory is imported."""

import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import RLock
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from lupupy import Lupusec, newDevice
from lupupy.battery import (
    battery_low_value,
    battery_state_from_snapshot,
)
from requests import HTTPError, Timeout


@pytest.fixture
def row():
    return {
        "sid": "RF:00000001",
        "name": "Detector A",
        "type": 11,
        "area": 1,
        "zone": 1,
        "status": "",
        "cond": "",
        "cond_ok": "1",
        "battery": "",
        "battery_ok": "1",
    }


def panel_for(rows, model=2):
    panel = Lupusec.__new__(Lupusec)
    panel.model = model
    panel.api_sensors = "deviceListGet" if model == 2 else "sensorListGet"
    panel.api_device_id = "sid" if model == 2 else "no"
    panel._cacheSensors, panel._cacheStampS = None, 0
    panel._sensor_lock = RLock()
    panel._battery_snapshot_at = None
    response = Mock(text=json.dumps({"senrows": rows}))
    panel._request_get = Mock(return_value=response)
    return panel, response


@pytest.mark.parametrize(
    "fields,expected",
    [
        ({"battery_ok": "1"}, False),
        ({"battery_ok": 1}, False),
        ({"battery_ok": "0"}, True),
        ({"battery_ok": 0}, True),
        ({"battery_ok": "0", "battery": ""}, True),
        ({"battery_ok": "0", "battery": "{WEB_MSG_LOW_BATTERY}"}, True),
        ({"battery_ok": "1", "battery": "{WEB_MSG_LOW_BATTERY}"}, None),
        ({"battery": "{WEB_MSG_LOW_BATTERY}"}, True),
        ({"battery": ""}, None),
        ({}, None),
        ({"battery_ok": None}, None),
        ({"battery_ok": "2"}, None),
        ({"battery_ok": True}, None),
        ({"battery": "80%"}, None),
        ({"faults": {"low_battery": "1"}}, True),
        ({"faults": {"low_battery": "0"}}, False),
        ({"faults": {"low_battery": True}}, True),
        ({"faults": {"low_battery": False}}, False),
        ({"faults": {}}, None),
        ({"faults": None}, None),
        ({"faults": {"low_battery": "invalid"}}, None),
        ({"battery_ok": "1", "faults": {"low_battery": "1"}}, None),
        ({"battery_ok": "0", "faults": {"low_battery": "0"}}, None),
        ({"battery_ok": "0", "faults": {"low_battery": "1"}}, True),
        ({"battery_ok": "1", "faults": {"low_battery": "0"}}, False),
    ],
)
def test_explicit_modern_and_legacy_battery_sources(fields, expected):
    assert battery_low_value(fields) is expected


@pytest.mark.parametrize(
    "change",
    [
        {"cond_ok": "0"},
        {"cond_ok": None},
        {"cond": "{WEB_MSG_OOO}"},
        {"faults": {"no_response": 1}},
        {"faults": {"out_of_order": 1}},
        {"faults": {"no_response": "bad"}},
    ],
)
def test_unreliable_or_offline_device_is_unavailable(row, change):
    row.update(change)
    assert battery_state_from_snapshot(row) is None


def test_legacy_connectivity_can_establish_reliable_state():
    data = {"faults": {"low_battery": 1, "no_response": 0, "out_of_order": False}}
    assert battery_state_from_snapshot(data) is True
    data["faults"]["low_battery"] = 0
    assert battery_state_from_snapshot(data) is False


def test_no_connectivity_information_is_not_assumed_healthy():
    assert battery_low_value({"faults": {"low_battery": 0}}) is False
    assert battery_state_from_snapshot({"faults": {"low_battery": 0}}) is None


def test_offline_then_online(row):
    row.update(cond="{WEB_MSG_OOO}", cond_ok="0")
    assert battery_state_from_snapshot(row) is None
    row.update(cond="", cond_ok="1")
    assert battery_state_from_snapshot(row) is False


@pytest.mark.parametrize("device_type", [4, 5, 11, 37, 46, "Fensterkontakt"])
def test_flags_are_not_tied_to_smoke_type(row, device_type):
    row.update(type=device_type, battery_ok="0", battery="{WEB_MSG_LOW_BATTERY}")
    assert battery_state_from_snapshot(row) is True


def test_warm_sensor_cache_causes_no_additional_request(row):
    panel, _ = panel_for([row])
    sensors = panel.get_sensors()
    first = panel.get_battery_snapshot()
    second = panel.get_battery_snapshot()
    assert panel._request_get.call_count == 1
    assert first == second
    assert first.updated_at == panel._battery_snapshot_at
    assert sensors[0]["status"] == "Geschlossen"
    assert "cond" not in sensors[0]


def test_battery_only_consumer_fetches_once_when_needed(row):
    panel, _ = panel_for([row])
    assert panel.get_battery_snapshot().states == {"RF:00000001": False}
    panel._request_get.assert_called_once_with("deviceListGet")


def test_cache_reuse_does_not_forge_freshness(row):
    panel, _ = panel_for([row])
    first = panel.get_battery_snapshot()
    with patch("lupupy.time.monotonic", return_value=first.updated_at + 100):
        second = panel.get_battery_snapshot()
    assert second.updated_at == first.updated_at


def test_concurrent_battery_and_regular_reads_share_one_request(row):
    panel, _ = panel_for([row])
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(panel.get_battery_snapshot),
            executor.submit(panel.get_sensors),
            executor.submit(panel.get_battery_snapshot),
            executor.submit(panel.get_sensors),
        ]
        for f in futures:
            f.result(timeout=3)
    assert panel._request_get.call_count == 1


@pytest.mark.parametrize("failure", ["timeout", "http", "json", "shape"])
def test_failure_does_not_advance_freshness_or_cache_deadline(row, failure):
    panel, response = panel_for([row])
    first = panel.get_battery_snapshot()
    panel._cacheStampS = 0
    if failure == "timeout":
        panel._request_get.side_effect = Timeout()
        error = Timeout
    elif failure == "http":
        response.raise_for_status.side_effect = HTTPError()
        error = HTTPError
    else:
        response.text = "invalid" if failure == "json" else "{}"
        error = ValueError
    with pytest.raises(error):
        panel.get_battery_snapshot()
    assert panel._battery_snapshot_at == first.updated_at
    assert panel._cacheStampS == 0


def test_duplicate_ids_are_rejected(row):
    panel, _ = panel_for([row, dict(row)])
    with pytest.raises(ValueError, match="ambiguous"):
        panel.get_battery_snapshot()


@pytest.mark.parametrize("bad_row", [None, {}, {"sid": "RF:00000001"}, {"cond": ""}])
def test_malformed_rows_fail_closed_without_cache_refresh(bad_row):
    panel, _ = panel_for([bad_row])
    with pytest.raises(ValueError):
        panel.get_battery_snapshot()
    assert panel._battery_snapshot_at is None
    assert panel._cacheSensors is None


def test_absent_device_is_not_carried_forward(row):
    panel, response = panel_for([row])
    panel.get_battery_snapshot()
    panel._cacheStampS = 0
    response.text = '{"senrows":[]}'
    assert panel.get_battery_snapshot().states == {}


def test_restart_and_old_events_use_only_current_snapshot(row):
    panel, response = panel_for([row])
    response.text = json.dumps(
        {
            "senrows": [row],
            "rptrows": [{"cid_event": "384", "new_event": "{WEB_MSG_TRIGGER}"}],
        }
    )
    panel.get_history_xt2 = Mock(
        side_effect=AssertionError("history must not define battery state")
    )
    assert panel.get_battery_snapshot().states["RF:00000001"] is False
    panel.get_history_xt2.assert_not_called()


def test_synthetic_restore_does_not_clear_current_low(row):
    row.update(battery_ok="0", battery="{WEB_MSG_LOW_BATTERY}")
    panel, response = panel_for([row])
    response.text = json.dumps(
        {
            "senrows": [row],
            "rptrows": [
                {
                    "cid_event": "384",
                    "new_event": "{WEB_MSG_RESTORE}",
                    "message": "{RPT_CID_384R}",
                }
            ],
        }
    )
    assert panel.get_battery_snapshot().states["RF:00000001"] is True


def test_low_to_normal_is_read_from_new_snapshot(row):
    row.update(battery_ok="0", battery="{WEB_MSG_LOW_BATTERY}")
    panel, response = panel_for([row])
    assert panel.get_battery_snapshot().states["RF:00000001"] is True
    row.update(battery_ok="1", battery="")
    panel._cacheStampS = 0
    response.text = json.dumps({"senrows": [row]})
    assert panel.get_battery_snapshot().states["RF:00000001"] is False


def test_device_property_supports_legacy_and_does_not_require_faults(row):
    row["device_id"] = row["sid"]
    device = newDevice(deepcopy(row), SimpleNamespace(model=2))
    assert device.battery_low is False
    device.update(dict(row, battery_ok="0", battery="{WEB_MSG_LOW_BATTERY}"))
    assert device.battery_low is True
    device.update(dict(row, battery_ok=0, battery=""))
    assert device.battery_low is True
    device.update(dict(row, battery_ok="1", battery=""))
    assert device.battery_low is False


def test_contact_update_copies_empty_and_numeric_battery_fields(row):
    row.update(type=4, device_id=row["sid"])
    device = newDevice(deepcopy(row), SimpleNamespace(model=2))
    device.update(dict(row, battery_ok=0, battery="{WEB_MSG_LOW_BATTERY}", status=1))
    assert device.battery_low is True and device.is_on is True
    device.update(dict(row, battery_ok=1, battery="", status="Geschlossen"))
    assert device.battery_low is False and device.is_on is False


def test_missing_fields_clear_old_battery_property(row):
    row.update(device_id=row["sid"])
    device = newDevice(deepcopy(row), SimpleNamespace(model=2))
    device.update({"status": "Geschlossen"})
    assert device.battery_low is None and not device.has_battery_information


def test_self_update_does_not_erase_fields(row):
    row.update(device_id=row["sid"])
    device = newDevice(row, SimpleNamespace(model=2))
    device.update(row)
    assert device.battery_low is False


def test_legacy_sensor_api_uses_same_cache():
    row = {
        "no": "synthetic_1",
        "name": "Legacy A",
        "type": "Fensterkontakt",
        "cond": "",
        "faults": {"low_battery": "1", "no_response": "0", "out_of_order": "0"},
    }
    panel, response = panel_for([row], model=1)
    # Wire YAML/header parsing is unchanged; this is a synthetic normalized response.
    panel.clean_json = Mock(return_value={"senrows": [row]})
    assert panel.get_battery_snapshot().states == {"synthetic_1": True}
    panel.get_sensors()
    panel._request_get.assert_called_once_with("sensorListGet")

"""Tests that the domain layer works on top of the api layer."""

from unittest.mock import patch

import pytest

import lupupy.constants as CONST
from lupupy import Lupusec
from lupupy.api.data_models import LupusecAlarmMode, LupusecModelType
from lupupy.devices.alarm import LupusecAlarm
from lupupy.devices.binary_sensor import LupusecBinarySensor


class FakeApi:
    """A panel that answers from memory instead of over the network."""

    model = LupusecModelType.XT2_3_4

    def __init__(self):
        self.mode_set = None
        self.sensors = [
            {
                "device_id": "RF:00000001",
                "name": "Front Door",
                "type": CONST.TYPE_CONTACT_XT,
                "status": CONST.STATUS_CLOSED,
            }
        ]

    def get_panel(self):
        return {
            "device_id": CONST.ALARM_DEVICE_ID,
            "type": CONST.ALARM_TYPE,
            "name": CONST.ALARM_NAME,
            "mode": CONST.MODE_DISARMED,
        }

    def get_sensors(self):
        return self.sensors

    def get_power_switches(self):
        return []

    def set_mode(self, mode):
        self.mode_set = mode
        return {"result": 1}


@pytest.fixture(name="system")
def fixture_system():
    """Build a Lupusec system backed by the fake panel."""
    api = FakeApi()
    with patch("lupupy.lupusec.LupusecApi", return_value=api):
        system = Lupusec("user", "password", "panel.lan")
    system.api = api
    return system


def test_devices_are_built(system):
    devices = system.get_devices()

    assert len(devices) == 2
    assert any(isinstance(device, LupusecBinarySensor) for device in devices)
    assert any(isinstance(device, LupusecAlarm) for device in devices)


def test_get_alarm(system):
    assert isinstance(system.get_alarm(), LupusecAlarm)


def test_devices_can_be_filtered_by_type(system):
    devices = system.get_devices(generic_type=[CONST.TYPE_CONTACT_XT])

    assert len(devices) == 1
    assert devices[0].name == "Front Door"


def test_the_model_is_exposed(system):
    """Home Assistant reads the model straight off the system."""
    assert system.model is LupusecModelType.XT2_3_4


def test_set_mode_is_delegated_to_the_api(system):
    system.set_mode(LupusecAlarmMode.Home)

    assert system.api.mode_set is LupusecAlarmMode.Home


def test_the_alarm_can_be_armed(system):
    alarm = system.get_alarm()

    assert alarm.set_home(system.api) is True
    assert system.api.mode_set is LupusecAlarmMode.Home


def test_a_device_refreshes_against_the_api(system):
    device = system.get_devices(generic_type=[CONST.TYPE_CONTACT_XT])[0]
    system.api.sensors[0]["status"] = CONST.STATUS_OPEN

    device.refresh(system.api)

    assert device.status == CONST.STATUS_OPEN


def test_refreshing_through_the_system(system):
    """get_device(refresh=True) used to call refresh() without the api."""
    assert system.get_device("RF:00000001", refresh=True) is not None


def test_history_is_delegated_to_the_api(system, monkeypatch):
    """The command line calls get_history() on the system."""
    monkeypatch.setattr(system.api, "get_history", lambda: ["row"], raising=False)

    assert system.get_history() == ["row"]

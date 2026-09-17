"""Init for Lupusec module."""

import logging
from pathlib import Path

import lupupy.constants as CONST
from lupupy.api.data_models import LupusecAlarmMode, LupusecModelType
from lupupy.api.lupusec_api import LupusecApi
from lupupy.devices import LupusecDevice
from lupupy.devices.alarm import LupusecAlarm
from lupupy.devices.binary_sensor import LupusecBinarySensor
from lupupy.devices.switch import LupusecSwitch

_LOGGER = logging.getLogger(__name__)

home = str(Path.home())


class Lupusec:
    """Class to represent the Lupusec alarm system."""

    def __init__(
        self, username: str, password: str, ip_address: str, get_devices: bool = False
    ):
        """Set up the Lupusec alarm system."""
        self.api = LupusecApi(username, password, ip_address)
        self._devices = None
        self._panel = self.api.get_panel()

        if get_devices:
            self._devices = self.get_devices()
        else:
            self._devices = None

    def get_devices(
        self, refresh: bool = False, generic_type: list[str] = None
    ) -> list:
        """Get all devices from Lupusec."""
        _LOGGER.info("Updating all devices...")

        if refresh or self._devices is None:
            if self._devices is None:
                self._devices = {}

            self._update_devices()
            self._handle_panel()
            self._handle_power_switches()

        if generic_type:
            return [
                device
                for device in self._devices.values()
                if device.type in generic_type
            ]

        return list(self._devices.values())

    def get_device(self, device_id: str, refresh: bool = False) -> LupusecDevice:
        """Get a single device."""
        if self._devices is None:
            self.get_devices()
            refresh = False

        device = self._devices.get(device_id)

        if device and refresh:
            device.refresh(self.api)

        return device

    def get_alarm(self, area: str = "1", refresh: bool = False) -> LupusecAlarm:
        """Shortcut method to get the alarm device."""
        if self._devices is None:
            self.get_devices()
            refresh = False

        return self.get_device(CONST.ALARM_DEVICE_ID, refresh)

    @property
    def model(self) -> LupusecModelType:
        """Model type of the connected panel."""
        return self.api.model

    def set_mode(self, mode: LupusecAlarmMode) -> dict:
        """Set the mode of the alarm."""
        return self.api.set_mode(mode)

    def get_history(self) -> list:
        """Get the event history of the panel."""
        return self.api.get_history()

    def _newDevice(self, deviceJson: dict) -> None | LupusecDevice:
        """Create new device object for the given type."""
        type_tag = deviceJson.get("type")

        if not type_tag:
            _LOGGER.info("Device has no type")

        if (
            type_tag in CONST.TYPE_OPENING
            or type_tag in CONST.TYPE_SENSOR
            or type_tag in CONST.TYPE_SIREN
            or type_tag in CONST.TYPE_KEYPAD
        ):
            return LupusecBinarySensor(deviceJson)
        elif type_tag in CONST.TYPE_SWITCH:
            return LupusecSwitch(deviceJson)
        else:
            _LOGGER.info("Device is not known")
        return None

    def _update_devices(self) -> None:
        """Update devices from the API."""
        responseObject = self.api.get_sensors()

        for deviceJson in responseObject:
            device = self._devices.get(deviceJson["name"])
            if device:
                device.update(deviceJson)
            else:
                device = self._newDevice(deviceJson)
                if not device:
                    _LOGGER.info("Device is unknown")
                    continue
                self._devices[device.device_id] = device

    def _handle_panel(self) -> None:
        """Handle the Lupusec panel as an armable device."""
        panelJson = self.api.get_panel()
        _LOGGER.debug("Get the panel in get_devices: %s", panelJson)

        self._panel.update(panelJson)

        alarmDevice = self._devices.get("0")
        if alarmDevice:
            alarmDevice.update(panelJson)
        else:
            alarmDevice = LupusecAlarm(panelJson)
            self._devices["0"] = alarmDevice

    def _handle_power_switches(self) -> None:
        """Handle power switches based on the model type."""
        if self.api.model == LupusecModelType.XT1:
            switches = self.api.get_power_switches()
            _LOGGER.debug("Get active the power switches in get_devices: %s", switches)

            for deviceJson in switches:
                device = self._devices.get(deviceJson["name"])
                if device:
                    device.update(deviceJson)
                else:
                    device = self._newDevice(deviceJson)
                    if not device:
                        _LOGGER.info("Device is unknown")
                        continue
                    self._devices[device.device_id] = device
        elif self.api.model == LupusecModelType.XT2_3_4:
            _LOGGER.debug("Power switches for XT2 not implemented")

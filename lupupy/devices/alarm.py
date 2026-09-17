"""Lupusec alarm device."""

import logging

from typing import TYPE_CHECKING

from lupupy.api.data_models import LupusecAlarmMode
from lupupy.devices.switch import LupusecDevice, LupusecSwitch

if TYPE_CHECKING:
    from lupupy.api.lupusec_api import LupusecApi

_LOGGER = logging.getLogger(__name__)


class LupusecAlarm(LupusecSwitch):
    """Class to represent the Lupusec alarm as a device."""

    def __init__(self, json_obj: dict, area: str = "1"):
        """Set up Lupusec alarm device."""
        LupusecSwitch.__init__(self, json_obj)
        self._area = area

    def set_mode(self, mode: LupusecAlarmMode, api: "LupusecApi") -> bool:
        """Set Lupusec alarm mode."""
        _LOGGER.debug("State change called from alarm device")
        if not mode:
            _LOGGER.info("No mode supplied")
        response_object = api.set_mode(mode)
        if response_object["result"] != 1 and response_object["result"] != "1":
            _LOGGER.warning("Mode setting unsuccessful")

        self._json_state["mode"] = mode
        _LOGGER.info("Mode set to: %s", mode)
        return True

    def set_home(self, api: "LupusecApi") -> bool:
        """Arm Lupusec to home mode."""
        return self.set_mode(LupusecAlarmMode.Home, api)

    def set_away(self, api: "LupusecApi") -> bool:
        """Arm Lupusec to armed mode."""
        return self.set_mode(LupusecAlarmMode.Armed, api)

    def set_standby(self, api: "LupusecApi") -> bool:
        """Arm Lupusec to stay mode."""
        return self.set_mode(LupusecAlarmMode.Disarmed, api)

    def refresh(self, api: "LupusecApi") -> bool:
        """Refresh the alarm device."""
        response_object = LupusecDevice.refresh(self, api)
        return response_object

    def switch_on(self, api: "LupusecApi") -> bool:
        """Arm Abode to default mode."""
        return self.set_mode(LupusecAlarmMode.Armed, api)

    def switch_off(self, api: "LupusecApi") -> bool:
        """Arm Abode to home mode."""
        return self.set_standby(api)

    @property
    def is_on(self) -> bool:
        """Is alarm armed."""
        return self.mode in (LupusecAlarmMode.Home, LupusecAlarmMode.Armed)

    @property
    def is_standby(self) -> bool:
        """Is alarm in standby mode."""
        return self.mode == LupusecAlarmMode.Disarmed

    @property
    def is_home(self) -> bool:
        """Is alarm in home mode."""
        return self.mode == LupusecAlarmMode.Home

    @property
    def is_away(self) -> bool:
        """Is alarm in away mode."""
        return self.mode == LupusecAlarmMode.Armed

    @property
    def is_alarm_triggered(self) -> bool:
        """Is alarm in alarm triggered mode."""
        return self.mode == LupusecAlarmMode.AlarmTriggered

    @property
    def mode(self) -> LupusecAlarmMode:
        """Get alarm mode."""
        mode_value = self.get_value("mode")
        try:
            return LupusecAlarmMode(mode_value)
        except ValueError:
            _LOGGER.error("Unknown mode: %s", mode_value)
        return LupusecAlarmMode.Unknown

    @property
    def status(self) -> str:
        """To match existing property."""
        return self.mode.value

    @property
    def battery(self) -> bool:
        """Return true if base station on battery backup."""
        return int(self._json_state.get("battery", "0")) == 1

    @property
    def is_cellular(self) -> bool:
        """Return true if base station on cellular backup."""
        return int(self._json_state.get("is_cellular", "0")) == 1

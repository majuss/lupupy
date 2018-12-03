"""Lupusec alarm device."""
import json
import logging

from lupupy.devices.switch import LupusecDevice, LupusecSwitch
import lupupy.constants as CONST

_LOGGER = logging.getLogger(__name__)


def create_alarm(panel_json, lupusec, area='1'):
    """Create a new alarm device from a panel response."""
    return LupusecAlarm(panel_json, lupusec, area)


class LupusecAlarm(LupusecSwitch):
    """Class to represent the Lupusec alarm as a device."""

    def __init__(self, json_obj, lupusec, area='1'):
        """Set up Lupusec alarm device."""
        LupusecSwitch.__init__(self, json_obj, lupusec)
        self._area = area

    def set_mode(self, mode):
        """Set Lupusec alarm mode."""
        _LOGGER.debug('State change called from alarm device')
        if not mode:
            _LOGGER.info('No mode supplied')
        elif mode not in CONST.ALL_MODES:
            _LOGGER.warning('Invalid mode')
        response_object = self._lupusec.set_mode(CONST.MODE_TRANSLATION[mode])
        if response_object['result'] != 1:
            _LOGGER.warning('Mode setting unsuccessful')

        self._json_state['mode'] = mode
        _LOGGER.info('Mode set to: %s', mode)
        return True

    def set_home(self):
        """Arm Lupusec to home mode."""
        return self.set_mode(CONST.MODE_HOME)

    def set_away(self):
        """Arm Lupusec to armed mode."""
        return self.set_mode(CONST.MODE_AWAY)

    def set_standby(self):
        """Arm Lupusec to stay mode."""
        return self.set_mode(CONST.MODE_DISARMED)

    def refresh(self):
        """Refresh the alarm device."""
        response_object = LupusecDevice.refresh(self)
        return response_object

    def switch_on(self):
        """Arm Abode to default mode."""
        return self.set_mode(CONST.DEFAULT_MODE)

    def switch_off(self):
        """Arm Abode to home mode."""
        return self.set_standby()

    @property
    def is_on(self):
        """Is alarm armed."""
        return self.mode in (CONST.MODE_HOME, CONST.MODE_AWAY)

    @property
    def is_standby(self):
        """Is alarm in standby mode."""
        return self.mode == CONST.MODE_DISARMED

    @property
    def is_home(self):
        """Is alarm in home mode."""
        return self.mode == CONST.MODE_HOME

    @property
    def is_away(self):
        """Is alarm in away mode."""
        return self.mode == CONST.MODE_AWAY

    @property
    def is_alarm_triggered(self):
        """Is alarm in alarm triggered mode."""
        return self.mode == CONST.STATE_ALARM_TRIGGERED

    @property
    def mode(self):
        """Get alarm mode."""
        mode = self.get_value('mode')
        return mode

    @property
    def status(self):
        """To match existing property."""
        return self.mode

    @property
    def battery(self):
        """Return true if base station on battery backup."""
        return int(self._json_state.get('battery', '0')) == 1

    @property
    def is_cellular(self):
        """Return true if base station on cellular backup."""
        return int(self._json_state.get('is_cellular', '0')) == 1

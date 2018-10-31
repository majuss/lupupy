"""Init file for devices directory."""
import json
import logging

import lupupy.constants as CONST

class LupusecDevice(object):
    """Class to represent each Lupusec device."""

    def __init__(self, json_obj, lupusec):
        """Set up Lupusec device."""
        self._json_state = json_obj
        self._device_id = json_obj.get('device_id')
        self._name = json_obj.get('name')
        self._type = json_obj.get('type')

        if self._type in CONST.TYPE_TRANSLATION:
            self._generic_type = CONST.TYPE_TRANSLATION[self._type]
        else:
            self._generic_type = 'generic_type_unknown'

        self._status = json_obj.get('status')
        self._lupusec = lupusec

        if not self._name:
            self._name = self.type + ' ' + self.device_id

    def get_value(self, name):
        """Get a value from the json object.
        """

        return self._json_state.get(name)

    def refresh(self):
        """Refresh a device"""
        # new_device = {}
        if self.type in CONST.BINARY_SENSOR_TYPES:
            response = self._lupusec.get_sensors()
            for device in response:
                if device['device_id'] == self._device_id:
                    self.update(device)

            return device

        elif self.type == CONST.ALARM_TYPE:
            response = self._lupusec.get_panel()
            self.update(response)
            return response
        
        elif self.type == CONST.TYPE_POWER_SWITCH:
            response = self._lupusec.get_power_switches()
            for pss in response:
                if pss['device_id'] == self._device_id:
                    self.update(pss)
            return pss

    def set_status(self, status):
        """Set status of power switch."""
        # self._apipost

    def update(self, json_state):
        """Update the json data from a dictionary.

        Only updates if it already exists in the device.
        """
        if self._type in CONST.BINARY_SENSOR_TYPES:
            self._json_state['status'] = json_state['status']
        else:
            self._json_state.update(
                {k: json_state[k] for k in json_state if self._json_state.get(k)})

    @property
    def status(self):
        """Shortcut to get the generic status of a device."""
        return self.get_value('status')

    @property
    def level(self):
        """Shortcut to get the generic level of a device."""
        return self.get_value('level')

    @property
    def battery_low(self):
        """Is battery level low."""
        return int(self.get_value('faults').get('low_battery', '0')) == 1

    @property
    def no_response(self):
        """Is the device responding."""
        return int(self.get_value('faults').get('no_response', '0')) == 1

    @property
    def out_of_order(self):
        """Is the device out of order."""
        return int(self.get_value('faults').get('out_of_order', '0')) == 1

    @property
    def tampered(self):
        """Has the device been tampered with."""
        # 'tempered' - Typo in API?
        return int(self.get_value('faults').get('tempered', '0')) == 1

    @property
    def name(self):
        """Get the name of this device."""
        return self._name

    @property
    def type(self):
        """Get the type of this device."""
        return self._type

    @property
    def generic_type(self):
        """Get the generic type of this device."""
        return self._generic_type

    @property
    def device_id(self):
        """Get the device id."""
        return self._device_id

    @property
    def desc(self):
        """Get a short description of the device."""
        return '{0} (ID: {1}) - {2} - {3}'.format(
            self.name, self.device_id, self.type, self.status)

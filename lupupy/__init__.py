import string
import requests
import demjson
import pickle
import os
import time
import logging
from pathlib import Path

import lupupy.devices.alarm as ALARM
import lupupy.constants as CONST
from lupupy.devices.binary_sensor import LupusecBinarySensor
from lupupy.devices.switch import LupusecSwitch
from lupupy.exceptions import LupusecException

_LOGGER = logging.getLogger(__name__)
home = str(Path.home())

class Lupusec():
    """Interface to Lupusec Webservices."""

    def __init__(self, username, password, ip_address, model="xt1", get_devices=False):
        """LupsecAPI constructor requires IP and credentials to the
         Lupusec Webinterface.
        """
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.api_url = "http://{}/action/".format(ip_address)
        self.model = model
        self.headers = None

        if model == 'xt1':
            self.mode_translation = {'Disarm': 2, 'Home': 1, 'Arm': 0}
            self.key_mode = 'mode_st'
            self.key_sensors = 'sensorListGet'
            self.key_device_id = 'no'
            self._request_post('login')
        elif model == 'xt3':
            self.mode_translation = {'Disarm': 0, 'Arm': 1, 'Home': 2}
            self.key_mode = 'mode_a1'  # Could also be mode_a2 for area 2. TODO: Needs to be made configurable
            self.key_sensors = 'deviceListGet'
            self.key_device_id = 'sid'

            # On XT3, we need to get a token that will be sent which each request
            token_response = self._request_get('tokenGet')  # Example response: {"result" : 1, "message" : "..."}
            token = self.clean_json(token_response.text)['message']
            self.headers = {"X-Token": token}
            # TODO: add method to refresh token when it expires
        else:
            raise Exception("Unsupported model")

        self._mode = None
        self._devices = None

        try:
            self._history_cache = pickle.load(open(home + "/" + CONST.HISTORY_CACHE_NAME, "rb"))
        except (OSError, IOError) as e:
            self._history_cache = []
            pickle.dump(self._history_cache, open(home + "/" + CONST.HISTORY_CACHE_NAME, "wb"))

        self._panel = self.get_panel()
        self._cacheSensors = None
        self._cacheStampS = time.time()
        self._cachePss = None
        self._cacheStampP = time.time()

        if get_devices or self._devices is None:
            self.get_devices()

    def _request_get(self, action):
        response = self.session.get(self.api_url + action, timeout=15, headers=self.headers)
        _LOGGER.debug('Action and statuscode of apiGET command: %s, %s',
                      action, response.status_code)
        return response

    def _request_post(self, action, params={}):
        return self.session.post(self.api_url + action, data=params, headers=self.headers)

    def clean_json(self, textdata):
        _LOGGER.debug('Input for clean json' + textdata)
        textdata = textdata.replace("\t", "")
        i = textdata.index('\n')
        if self.model == 'xt1':
            textdata = textdata[i+1:-2]
        textdata = demjson.decode(textdata)
        return textdata

    def get_power_switches(self):
        stampNow = time.time()
        length = len(self._devices)
        if self._cachePss is None or stampNow - self._cacheStampP > 2.0:
            self._cacheStamp_p = stampNow
            response = self._request_get('pssStatusGet')
            response = self.clean_json(response.text)['forms']
            powerSwitches = []
            counter = 1
            for pss in response:
                powerSwitch = {}
                if response[pss]['ready'] == 1:
                    powerSwitch['status'] = response[pss]['pssonoff']
                    powerSwitch['device_id'] = counter + length
                    powerSwitch['type'] = CONST.TYPE_POWER_SWITCH
                    powerSwitch['name'] = response[pss]['name']
                    powerSwitches.append(powerSwitch)
                else:
                    _LOGGER.debug('Pss skipped, not active')
                counter += 1
            self._cachePss = powerSwitches

        return self._cachePss

    def get_sensors(self):
        stamp_now = time.time()
        if self._cacheSensors is None or stamp_now - self._cacheStampS > 2.0:
            self._cacheStampS = stamp_now
            response = self._request_get(self.key_sensors)
            response = self.clean_json(response.text)['senrows']
            sensors = []
            for device in response:
                device['status'] = device['cond']
                device['device_id'] = device[self.key_device_id]
                device.pop('cond')
                device.pop(self.key_device_id)
                if not device['status']:
                    device['status'] = 'Geschlossen'
                else:
                    device['status'] = None
                sensors.append(device)
            self._cacheSensors = sensors

        return self._cacheSensors

    def get_panel(self):  # we are trimming the json from Lupusec heavily, since its bullcrap
        response = self._request_get('panelCondGet')
        if response.status_code != 200:
            print(response.text)
            raise Exception('Unable to get panel')
        panel = self.clean_json(response.text)['updates']
        panel['mode'] = panel[self.key_mode]
        panel.pop(self.key_mode)

        # XT3 uses different namings for the modes. "Translate" them to the ones used everywhere else in this module.
        # TODO: This needs a cleaner solution
        if self.model == 'xt3':
            panel['mode'] = CONST.XT3_MODES_TO_TEXT[panel['mode']]

        panel['device_id'] = CONST.ALARM_DEVICE_ID
        panel['type'] = CONST.ALARM_TYPE
        panel['name'] = CONST.ALARM_NAME

        history = self.get_history()

        # TODO: add compatibility for XT3
        if self.model == 'xt1':
            for histrow in history:
                if histrow not in self._history_cache:
                    if CONST.MODE_ALARM_TRIGGERED in histrow[CONST.HISTORY_ALARM_COLUMN]:
                        panel['mode'] = CONST.STATE_ALARM_TRIGGERED
                    self._history_cache.append(histrow)
                    pickle.dump(self._history_cache, open(home + "/" + CONST.HISTORY_CACHE_NAME, "wb"))

        return panel

    def get_history(self):
        response = self._request_get(CONST.HISTORY_REQUEST)
        return self.clean_json(response.text)[CONST.HISTORY_HEADER]

    def refresh(self):
        """Do a full refresh of all devices and automations."""
        self.get_devices(refresh=True)

    def get_devices(self, refresh=False, generic_type=None):
        """Get all devices from Lupusec."""
        _LOGGER.info("Updating all devices...")
        if refresh or self._devices is None:
            if self._devices is None:
                self._devices = {}

            responseObject = self.get_sensors()
            if (responseObject and
                    not isinstance(responseObject, (tuple, list))):
                responseObject = responseObject

            for deviceJson in responseObject:
                # Attempt to reuse an existing device
                device = self._devices.get(deviceJson['name'])

                # No existing device, create a new one
                if device:
                    device.update(deviceJson)
                else:
                    device = newDevice(deviceJson, self)

                    if not device:
                        _LOGGER.info('Device is unknown')
                        continue

                    self._devices[device.device_id] = device

            # We will be treating the Lupusec panel itself as an armable device.
            panelJson = self.get_panel()
            _LOGGER.debug("Get the panel in get_devices: %s", panelJson)

            self._panel.update(panelJson)

            alarmDevice = self._devices.get('0')

            if alarmDevice:
                alarmDevice.update(panelJson)
            else:
                alarmDevice = ALARM.create_alarm(panelJson, self)
                self._devices['0'] = alarmDevice

            # Now we will handle the power switches (only for XT1, as switches are already in the feed with the sensors)
            if self.model == 'xt1':
                switches = self.get_power_switches()
                _LOGGER.debug(
                    'Get active the power switches in get_devices: %s', switches)

                for deviceJson in switches:
                    # Attempt to reuse an existing device
                    device = self._devices.get(deviceJson['name'])

                    # No existing device, create a new one
                    if device:
                        device.update(deviceJson)
                    else:
                        device = newDevice(deviceJson, self)
                        if not device:
                            _LOGGER.info('Device is unknown')
                            continue
                        self._devices[device.device_id] = device

        if generic_type:
            devices = []
            for device in self._devices.values():
                if (device.type is not None and
                        device.type in generic_type[0]):
                    devices.append(device)
            return devices

        return list(self._devices.values())

    def get_device(self, device_id, refresh=False):
        """Get a single device."""
        if self._devices is None:
            self.get_devices()
            refresh = False

        device = self._devices.get(device_id)

        if device and refresh:
            device.refresh()

        return device

    def get_alarm(self, area='1', refresh=False):
        """Shortcut method to get the alarm device."""
        if self._devices is None:
            self.get_devices()
            refresh = False

        return self.get_device(CONST.ALARM_DEVICE_ID, refresh)

    def set_mode(self, mode):
        if self.model == 'xt1':
            params = {
                'mode': mode,
            }
        elif self.model == 'xt3':
            params = {
                'mode': mode,
                'area': 1  # TODO: Needs to be made configurable
            }
        r = self._request_post(
            "panelCondPost",
            params
        )
        responseJson = self.clean_json(r.text)
        return responseJson


def newDevice(deviceJson, lupusec):
    """Create new device object for the given type."""
    type_tag = deviceJson.get('type')

    if not type_tag:
        _LOGGER.info('Device has no type')

    if type_tag in CONST.TYPE_OPENING:
        return LupusecBinarySensor(deviceJson, lupusec)
    elif type_tag in CONST.TYPE_SENSOR:
        return LupusecBinarySensor(deviceJson, lupusec)
    elif type_tag in CONST.TYPE_SWITCH:
        return LupusecSwitch(deviceJson, lupusec)
    else:
        _LOGGER.info('Device is not known')
    return None

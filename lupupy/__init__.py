import string
import requests
import demjson
import time
import logging

import lupupy.devices.alarm as ALARM
import lupupy.constants as CONST
from lupupy.devices.binary_sensor import LupusecBinarySensor
from lupupy.devices.switch import LupusecSwitch

_LOGGER = logging.getLogger(__name__)

class Lupusec():
    """Interface to Lupusec Webservices."""

    def __init__(self, username, password, ip_address, get_devices=False):
        """LupsecAPI constructor requires IP and credentials to the
         Lupusec Webinterface.
        """
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.api_url = "http://{}/action/".format(ip_address)
        self._apipost('login')

        self._mode = None
        self._devices = None
        self._panel = self.getPanel()
        self._cache_sensors = None
        self._cache_stamp_s = None
        self._cache_pss = None
        self._cache_stamp_p = None

        if get_devices or self._devices == None:
            self.get_devices()

    def _apiget(self, action):
        response = self.session.get(self.api_url + action, timeout=15)
        _LOGGER.debug('Action and statuscode of apiGET command: %s, %s', action, response.status_code)
        return response

    def _apipost(self, action, params={}):
        return self.session.post(self.api_url + action, data=params)

    def cleanJson(self, textdata):
        _LOGGER.debug('Input for clean json' + textdata)
        textdata = textdata.replace("\t", "")
        i = textdata.index('\n')
        textdata = textdata[i+1:-2]
        textdata = demjson.decode(textdata)
        return textdata
    
    def getPowerswitches(self):
        stamp_now = time.time()
        length = len(self._devices)
        if self._cache_pss is None or stamp_now - self._cache_stamp_p > 2.0:
            self._cache_stamp_p = stamp_now
            response = self._apiget('pssStatusGet')
            response = self.cleanJson(response.text)['forms']
            power_switches = []
            counter = 1
            for pss in response:
                power_switch = {}
                if response[pss]['ready'] == 1:
                    power_switch['status'] = response[pss]['pssonoff']
                    power_switch['device_id'] = counter + length
                    power_switch['type'] = CONST.TYPE_POWER_SWITCH
                    power_switch['name'] = response[pss]['name']
                    power_switches.append(power_switch)
                else:
                    _LOGGER.debug('Pss skipped, not active')
                counter += 1
            self._cache_pss = power_switches
        
        return self._cache_pss
    
    def getSensors(self):
        stamp_now = time.time()
        if self._cache_sensors is None or stamp_now - self._cache_stamp_s > 2.0:
            self._cache_stamp_s = stamp_now
            response = self._apiget('sensorListGet')
            response = self.cleanJson(response.text)['senrows']
            sensors = []
            for device in response:
                device['status'] = device['cond']
                device['device_id'] = device['no']
                device.pop('cond')
                device.pop('no')
                if not device['status']:
                    device['status'] == 'Geschlossen'
                sensors.append(device)
            self._cache_sensors = sensors
            
        return self._cache_sensors

    def getPanel(self): #we are trimming the json from Lupusec heavily, since its bullcrap
        response = self._apiget('panelCondGet')
        if response.status_code != 200:
            print(response.text)
            raise Exception('Unable to get panel')
        panel = self.cleanJson(response.text)['updates']
        panel['mode'] = panel['mode_st']
        panel.pop('mode_st')
        panel['device_id'] = CONST.ALARM_DEVICE_ID
        panel['type'] = CONST.ALARM_TYPE
        panel['name'] = CONST.ALARM_NAME

        return panel

    def getHistory(self):
        response = self._apiget('historyGet')
        return self.cleanJson(response.text)

    def refresh(self):
        """Do a full refresh of all devices and automations."""
        self.get_devices(refresh=True)

    def get_devices(self, refresh=False, generic_type=None):
        """Get all devices from Lupusec."""
        _LOGGER.info("Updating all devices...")
        if refresh or self._devices is None:
            if self._devices is None:
                self._devices = {}

            response_object = self.getSensors()
            if (response_object and
                    not isinstance(response_object, (tuple, list))):
                response_object = response_object

            for device_json in response_object:
                # Attempt to reuse an existing device
                device = self._devices.get(device_json['name'])

                # No existing device, create a new one
                if device:
                    device.update(device_json)
                else:
                    device = new_device(device_json, self)

                    if not device:
                        _LOGGER.info('Device is unknown')
                        continue

                    self._devices[device.device_id] = device

            # We will be treating the Lupusec panel itself as an armable device.
            panel_json = self.getPanel()
            _LOGGER.debug("Get the panel in getDevices: %s", panel_json)

            self._panel.update(panel_json)

            alarm_device = self._devices.get('0')

            if alarm_device:
                alarm_device.update(panel_json)
            else:
                alarm_device = ALARM.create_alarm(panel_json, self)
                self._devices['0'] = alarm_device

            #Now we will handle the power switches
            switches = self.getPowerswitches()
            _LOGGER.debug('Get active the power switches in getDevices: %s', switches)

            for device_json in switches:
                # Attempt to reuse an existing device
                device = self._devices.get(device_json['name'])

                # No existing device, create a new one
                if device:
                    device.update(device_json)
                else:
                    device = new_device(device_json, self)
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
    
    def setMode(self, mode):
        r = self._apipost(
            "panelCondPost",
            {
                'mode': mode,
            }
        )
        response_json = self.cleanJson(r.text)
        return response_json

def new_device(device_json, lupusec):
    """Create new device object for the given type."""
    type_tag = device_json.get('type')

    if not type_tag:
        _LOGGER.info('Device has no type')

    if type_tag in CONST.TYPE_OPENING:
        return LupusecBinarySensor(device_json, lupusec)
    elif type_tag in CONST.TYPE_SENSOR:
        return LupusecBinarySensor(device_json, lupusec)
    elif type_tag in CONST.ALL_SWITCHES:
        return LupusecSwitch(device_json, lupusec)
    else:
        _LOGGER.info('Device is not known')
    return None
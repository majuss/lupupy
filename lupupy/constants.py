#Used in setup.py
# -*- coding: utf-8 -*-
VERSION = '0.0.20'
PROJECT_PACKAGE_NAME = 'lupupy'
PROJECT_LICENSE = 'MIT'
PROJECT_URL = 'http://www.github.com/majuss/lupupy'
PROJECT_DESCRIPTION = 'A python cli for Lupusec alarm panels.'
PROJECT_LONG_DESCRIPTION = ('lupupy is a python3 interface for'
                            ' the Lupus Electronics alarm panel.'
                            ' Its intented to get used in various'
                            ' smart home services to get a full'
                            ' integration of all you devices.')
PROJECT_AUTHOR = 'Majuss'

MODE_AWAY = 'Arm'
MODE_HOME = 'Home'
MODE_DISARMED = 'Disarm'
MODE_ALARM_TRIGGERED = 'Einbruch'
ALL_MODES = [MODE_DISARMED, MODE_HOME, MODE_AWAY]

XT3_MODES_TO_TEXT = {
    '{AREA_MODE_0}': 'Disarm',
    '{AREA_MODE_1}': 'Arm',
    '{AREA_MODE_2}': 'Home',
    '{AREA_MODE_3}': 'Home',
    '{AREA_MODE_4}': 'Home'
}

STATE_ALARM_DISARMED = 'disarmed'
STATE_ALARM_ARMED_HOME = 'armed_home'
STATE_ALARM_ARMED_AWAY = 'armed_away'
STATE_ALARM_TRIGGERED = 'alarm_triggered'
MODE_TRANSLATION_GENERIC = {'Disarm' : 'disarmed', 'Home' : 'armed_home', 'Arm' : 'armed_away'}
DEFAULT_MODE = MODE_AWAY

HISTORY_REQUEST = 'historyGet'
HISTORY_ALARM_COLUMN = 'a'
HISTORY_HEADER = 'hisrows'
HISTORY_CACHE_NAME = '.lupusec_history_cache'

STATUS_ON_INT = 0
STATUS_ON = 'on'
STATUS_OFF_INT = 1
STATUS_OFF = 'off'
STATUS_OFFLINE = 'offline'
STATUS_CLOSED = 'Geschlossen'
STATUS_CLOSED_INT = 0
STATUS_OPEN = 'Offen'
STATUS_OPEN_INT = 1

ALARM_NAME = 'Lupusec Alarm'
ALARM_DEVICE_ID = '0'
ALARM_TYPE = 'Alarm'

# GENERIC Lupusec DEVICE TYPES
TYPE_WINDOW = "Fensterkontakt"
TYPE_DOOR = "Türkontakt"
TYPE_CONTACT_XT3 = 4
TYPE_WATER_XT3 = 5
# TYPE_MOTION_SENSOR_XT3 = 9
TYPE_SMOKE_XT3 = 11
TYPE_POWER_SWITCH_1_XT3 = 24
TYPE_POWER_SWITCH_2_XT3 = 25
TYPE_POWER_SWITCH = 'Steckdose'
TYPE_SWITCH = [TYPE_POWER_SWITCH, TYPE_POWER_SWITCH_1_XT3, TYPE_POWER_SWITCH_2_XT3]
TYPE_OPENING = [TYPE_DOOR, TYPE_WINDOW, TYPE_CONTACT_XT3]
BINARY_SENSOR_TYPES = TYPE_OPENING
TYPE_SENSOR = ['Rauchmelder', 'Wassermelder', TYPE_WATER_XT3, TYPE_SMOKE_XT3]
TYPE_TRANSLATION = {
    'Fensterkontakt': 'window',
    'Türkontakt': 'door',
    TYPE_CONTACT_XT3: 'Fenster-/Türkontakt',
    TYPE_WATER_XT3: 'Wassermelder',
    TYPE_SMOKE_XT3: 'Rauchmelder',
}

"""Lupusec API module."""

import json
import logging
import pickle
import time
import unicodedata
from pathlib import Path

import requests
import yaml

import lupupy.constants as CONST
from lupupy.api.data_models import LupusecAlarmMode, LupusecModelType

_LOGGER = logging.getLogger(__name__)
home = str(Path.home())


API_ACTION_TOKEN_GET = "tokenGet"
API_ACTION_PSS_STATUS_GET = "pssStatusGet"
API_ACTION_PANEL_COND_GET = "panelCondGet"
API_ACTION_PANEL_COND_POST = "panelCondPost"
API_ACTION_LOGIN = "login"


class LupusecApi:
    """Interface to Lupusec Webservices."""

    def __init__(self, username: str, password: str, ip_address: str):
        """LupsecAPI constructor requires IP and credentials to the Lupusec Webinterface."""
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.api_url = f"http://{ip_address}/action/"
        self.headers = None
        self.model = self._get_model(ip_address)
        self._fail_counter = 0

        if self.model == LupusecModelType.XT1:
            resp = self.session.get(self.api_url + CONST.DEVICES_API_XT1)
            if resp.status_code == 200:
                _LOGGER.debug("XT1 found, setting it up")
                self.api_mode = "mode_st"
                self.api_sensors = CONST.DEVICES_API_XT1
                self.api_device_id = "no"
                self._request_post(API_ACTION_LOGIN)
            else:
                _LOGGER.debug("Unknown error while finding out which model is used")
                return
        elif self.model == LupusecModelType.XT2_3_4:
            _LOGGER.debug("XT2 or higher found, setting up")
            self.api_mode = "mode_a1"
            self.api_sensors = CONST.DEVICES_API_XT2
            self.api_device_id = "sid"
            self._token_ts = time.time()
            response = self._request_get(API_ACTION_TOKEN_GET)
            self.headers = {"X-Token": json.loads(response.text)["message"]}
        else:
            _LOGGER.error("Unable to setup Lupusec panel, model not supported.")

        try:
            self._history_cache = pickle.load(
                open(home + "/" + CONST.HISTORY_CACHE_NAME, "rb")
            )
        except FileNotFoundError as e:
            _LOGGER.debug(e)
            self._history_cache = []
            pickle.dump(
                self._history_cache, open(home + "/" + CONST.HISTORY_CACHE_NAME, "wb")
            )

        self._cacheSensors = None
        self._cacheStampS = time.time()
        self._cachePss = None
        self._cacheStampP = time.time()

    def get_power_switches(self) -> dict:
        """Get all power switches from Lupusec."""
        stampNow = time.time()
        length = len(self._devices)
        if self._cachePss is None or stampNow - self._cacheStampP > 2.0:
            self._cacheStamp_p = stampNow
            response = self._request_get(API_ACTION_PSS_STATUS_GET)
            response = self.clean_json(response.text)["forms"]
            powerSwitches = []
            counter = 1
            for pss in response:
                powerSwitch = {}
                if response[pss]["ready"] == 1:
                    powerSwitch["status"] = response[pss]["pssonoff"]
                    powerSwitch["device_id"] = counter + length
                    powerSwitch["type"] = CONST.TYPE_POWER_SWITCH
                    powerSwitch["name"] = response[pss]["name"]
                    powerSwitches.append(powerSwitch)
                else:
                    _LOGGER.debug("Pss skipped, not active")
                counter += 1
            self._cachePss = powerSwitches

        return self._cachePss

    def get_sensors(self) -> dict:
        """Get all sensors from Lupusec."""
        stamp_now = time.time()
        if self._cacheSensors is None or stamp_now - self._cacheStampS > 2.0:
            self._cacheStampS = stamp_now
            response = self._request_get(self.api_sensors)
            response = self.clean_json(response.text)["senrows"]
            sensors = []
            for device in response:
                if self.model == LupusecModelType.XT1:
                    device["status"] = device["cond"]
                elif "openClose" in device:
                    device["status"] = device["openClose"]
                    device.pop("openClose")
                device["device_id"] = device[self.api_device_id]
                device.pop("cond")
                device.pop(self.api_device_id)
                if (
                    device["status"] == "{WEB_MSG_DC_OPEN}"
                    or device["status"] == CONST.STATUS_OPEN
                ):
                    device["status"] = 1
                if (
                    device["status"] == "{WEB_MSG_DC_CLOSE}"
                    or device["status"] == "0"
                    or device["status"] == ""
                ):
                    device["status"] = "Geschlossen"
                sensors.append(device)
            self._cacheSensors = sensors

        return self._cacheSensors

    def get_panel(
        self,
    ) -> dict:
        """Get the panel status from Lupusec."""
        # we are trimming the json from Lupusec heavily, since its bullcrap
        response = self._request_get(API_ACTION_PANEL_COND_GET)
        if response.status_code != 200:
            self._fail_counter += 1
            if (
                response.status_code == 401
                and self.model == LupusecModelType.XT2_3_4
                and self._fail_counter < 5
            ):
                response = self._request_get("tokenGet")
                self.headers = {"X-Token": json.loads(response.text)["message"]}
                self.get_panel()
            else:
                raise Exception(
                    "Unable to get panel "
                    + str(response.status_code)
                    + " Failed tries: "
                    + self._fail_counter
                )
        panel = self.clean_json(response.text)["updates"]
        panel["mode"] = panel[self.api_mode]
        panel.pop(self.api_mode)

        if self.model == LupusecModelType.XT2_3_4:
            panel["mode"] = CONST.XT2_MODES_TO_TEXT[panel["mode"]]
        panel["device_id"] = CONST.ALARM_DEVICE_ID
        panel["type"] = CONST.ALARM_TYPE
        panel["name"] = CONST.ALARM_NAME

        if self.model == LupusecModelType.XT1:
            history = self.get_history_xt1()
            for histrow in history:
                if histrow not in self._history_cache:
                    if (
                        CONST.MODE_ALARM_TRIGGERED
                        in histrow[CONST.HISTORY_ALARM_COLUMN]
                    ):
                        panel["mode"] = CONST.STATE_ALARM_TRIGGERED
                    self._history_cache.append(histrow)
                    pickle.dump(
                        self._history_cache,
                        open(home + "/" + CONST.HISTORY_CACHE_NAME, "wb"),
                    )
        elif self.model == LupusecModelType.XT2_3_4:
            history = self.get_history_xt2()
            for histrow in history:
                if histrow not in self._history_cache:
                    if (
                        histrow[CONST.HISTORY_ALARM_COLUMN_XT2]
                        == CONST.MODE_ALARM_TRIGGERED_XT2
                    ):
                        panel["mode"] = CONST.STATE_ALARM_TRIGGERED
                    self._history_cache.append(histrow)
                    pickle.dump(
                        self._history_cache,
                        open(home + "/" + CONST.HISTORY_CACHE_NAME, "wb"),
                    )
        return panel

    def get_history(self) -> list:
        """Get the history from Lupusec."""
        history = []
        if self.model == LupusecModelType.XT1:
            history = self.get_history_xt1()
        elif self.model == LupusecModelType.XT2_3_4:
            history = self.get_history_xt2()
        return history

    def get_history_xt1(self) -> list:
        """Get the history for XT1."""
        response = self._request_get(CONST.HISTORY_REQUEST_XT1)
        return self.clean_json(response.text)[CONST.HISTORY_HEADER]

    def get_history_xt2(self) -> list:
        """Get the history for XT2."""
        response = self._request_get(CONST.HISTORY_REQUEST_XT2)
        return self.clean_json(response.text)[CONST.HISTORY_HEADER_XT2]

    def set_mode(self, mode: LupusecAlarmMode) -> dict:
        """Set the mode of the alarm."""

        mode_value = self.get_alarm_mode_value(mode)

        if mode_value == -1:
            _LOGGER.error("Mode not found")
            return

        """Set the mode of the alarm."""
        if self.model == LupusecModelType.XT1:
            params = {
                "mode": mode_value,
            }
        elif self.model == LupusecModelType.XT2_3_4:
            params = {"mode": mode_value, "area": 1}

        response = self._request_post(API_ACTION_PANEL_COND_POST, params)
        responseJson = self.clean_json(response.text)
        return responseJson

    def get_alarm_mode_value(self, mode: LupusecAlarmMode) -> int:
        """Get the value of the alarm mode based on the model type."""
        if self.model == LupusecModelType.XT1:
            if mode == LupusecAlarmMode.Disarmed:
                return 2
            elif mode == LupusecAlarmMode.Armed:
                return 0
            elif mode == LupusecAlarmMode.Home:
                return 1
        elif self.model == LupusecModelType.XT2_3_4:
            if mode == LupusecAlarmMode.Disarmed:
                return 0
            elif mode == LupusecAlarmMode.Armed:
                return 1
            elif mode == LupusecAlarmMode.Home:
                return 2
        return -1  # Default case if mode is not found

    def remove_control_characters(self, s: str) -> str:
        """Remove control characters from string."""
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

    def clean_json(self, textdata: str) -> str:
        """Clean up the json response from Lupusec."""

        _LOGGER.debug("Input for clean json" + textdata)  # noqa: G003
        if self.model == LupusecModelType.XT1:
            textdata = textdata.replace("\t", "")
            i = textdata.index("\n")
            textdata = textdata[i + 1 : -2]
            try:
                textdata = yaml.load(textdata, Loader=yaml.BaseLoader)
            except Exception as e:
                _LOGGER.warning(
                    "Lupupy couldn't parse provided response: %s, %s", e, textdata
                )
            return textdata
        else:
            try:
                return json.loads(self.remove_control_characters(textdata))
            except json.decoder.JSONDecodeError as e:
                _LOGGER.error("Failed to parse JSON from " + str(textdata))  # noqa: G003
                _LOGGER.error(e)

    def _get_model(self, ip_address: str) -> LupusecModelType:
        response = requests.get(f"http://{ip_address}/images/model.gif")
        if response.status_code == 200:
            return LupusecModelType.XT1
        else:
            return LupusecModelType.XT2_3_4

    def _request_get(self, action: str) -> requests.Response:
        if self.model == LupusecModelType.XT2_3_4:
            ts = time.time()
            if ts - self._token_ts > 60:
                self._token_ts = ts
                response = self._request_get(API_ACTION_TOKEN_GET)
                self.headers = {"X-Token": json.loads(response.text)["message"]}
        response = self.session.get(
            self.api_url + action, timeout=15, headers=self.headers
        )
        _LOGGER.debug(
            "Action and statuscode of apiGET command: %s, %s",
            action,
            response.status_code,
        )
        return response

    def _request_post(self, action: str, params: dict = {}) -> requests.Response:
        if self.model == LupusecModelType.XT2_3_4:
            ts = time.time()
            if ts - self._token_ts > 60:
                self._token_ts = ts
                response = self._request_get(API_ACTION_TOKEN_GET)
                self.headers = {"X-Token": json.loads(response.text)["message"]}
        return self.session.post(
            self.api_url + action, data=params, headers=self.headers
        )

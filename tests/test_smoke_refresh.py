"""Exercise the released refresh API without panel access or alarm assumptions."""

from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from requests import Timeout

import lupupy.constants as CONST
from lupupy.devices.binary_sensor import LupusecBinarySensor


class SmokeRefreshTests(unittest.TestCase):
    def setUp(self):
        self.network = patch(
            "socket.socket.connect",
            side_effect=AssertionError("Network access forbidden in offline tests"),
        )
        self.network.start()
        self.addCleanup(self.network.stop)
        # A normalized idle deviceListGet row. Synthetic identity, no alarm data.
        self.idle = {
            "device_id": "RF:00000001",
            "name": "Smoke A",
            "type": 11,
            "area": 1,
            "zone": 1,
            "status": CONST.STATUS_CLOSED,
            "alarm_status": "",
            "cond_ok": "1",
            "battery_ok": "1",
        }
        self.panel = SimpleNamespace(get_sensors=Mock(return_value=[self.idle]))
        self.device = LupusecBinarySensor(deepcopy(self.idle), self.panel)

    def test_smoke_refresh_reads_sensors_once(self):
        self.device.refresh()
        self.panel.get_sensors.assert_called_once_with()

    def test_smoke_refresh_returns_matching_row(self):
        expected = dict(self.idle)
        other = dict(self.idle, device_id="RF:00000002", zone=2)
        self.panel.get_sensors.return_value = [expected, other]
        self.assertIs(self.device.refresh(), expected)

    def test_smoke_refresh_updates_existing_normalized_status(self):
        # Both values already mean off in lupupy. This tests copying, not an
        # assumed physical smoke-alarm representation.
        self.panel.get_sensors.return_value = [dict(self.idle, status=CONST.STATUS_OFF)]
        self.device.refresh()
        self.assertEqual(self.device.status, CONST.STATUS_OFF)
        self.assertIs(self.device.is_on, False)

    def test_subsequent_refresh_uses_new_response(self):
        self.panel.get_sensors.side_effect = [
            [dict(self.idle, status=CONST.STATUS_OFF)],
            [dict(self.idle)],
        ]
        self.device.refresh()
        self.device.refresh()
        self.assertEqual(self.panel.get_sensors.call_count, 2)
        self.assertEqual(self.device.status, CONST.STATUS_CLOSED)

    def test_different_rf_id_never_updates_this_device(self):
        self.panel.get_sensors.return_value = [
            dict(self.idle, device_id="RF:00000002", status=CONST.STATUS_OFF)
        ]
        self.assertIsNone(self.device.refresh())
        self.assertEqual(self.device.status, CONST.STATUS_CLOSED)

    def test_same_name_does_not_override_rf_identity(self):
        self.panel.get_sensors.return_value = [
            dict(self.idle, device_id="RF:00000002", status=CONST.STATUS_OFF),
            dict(self.idle, name="Renamed"),
        ]
        result = self.device.refresh()
        self.assertEqual(result["device_id"], self.idle["device_id"])
        self.assertEqual(self.device.status, CONST.STATUS_CLOSED)

    def test_empty_inventory_preserves_previous_status(self):
        self.panel.get_sensors.return_value = []
        self.assertIsNone(self.device.refresh())
        self.assertEqual(self.device.status, CONST.STATUS_CLOSED)

    def test_read_failure_propagates_and_preserves_previous_status(self):
        self.panel.get_sensors.side_effect = Timeout("synthetic transport failure")
        with self.assertRaises(Timeout):
            self.device.refresh()
        self.assertEqual(self.device.status, CONST.STATUS_CLOSED)

    def test_idle_status_remains_off(self):
        self.device.refresh()
        self.assertIs(self.device.is_on, False)

    def test_offline_condition_is_not_reinterpreted_as_smoke(self):
        self.panel.get_sensors.return_value = [dict(self.idle, cond_ok="0")]
        self.device.refresh()
        self.assertIs(self.device.is_on, False)

    def test_unverified_alarm_attribute_gets_no_new_semantics(self):
        self.panel.get_sensors.return_value = [
            dict(self.idle, alarm_status="UNVERIFIED_VALUE")
        ]
        self.device.refresh()
        self.assertIs(self.device.is_on, False)

    def test_binary_status_interpretation_remains_unchanged(self):
        for status in [
            CONST.STATUS_CLOSED,
            CONST.STATUS_OFF,
            CONST.STATUS_OFFLINE,
            0,
            1,
        ]:
            with self.subTest(status=status):
                self.device._json_state["status"] = status
                expected = status not in (
                    CONST.STATUS_OFF,
                    CONST.STATUS_OFFLINE,
                    CONST.STATUS_CLOSED,
                    CONST.STATUS_CLOSED_INT,
                    CONST.STATUS_OPEN_WEB,
                    CONST.STATUS_CLOSED_WEB,
                    CONST.STATUS_OPEN,
                )
                self.assertIs(self.device.is_on, expected)

    def test_contact_refresh_still_updates_status(self):
        row = dict(self.idle, type=CONST.TYPE_CONTACT_XT)
        contact = LupusecBinarySensor(row, self.panel)
        self.panel.get_sensors.return_value = [dict(row, status=1)]
        contact.refresh()
        self.assertIs(contact.is_on, True)

    def test_other_sensor_types_are_outside_this_fix(self):
        for device_type in [CONST.TYPE_WATER_XT, 58, 67, CONST.TYPE_SMOKE]:
            with self.subTest(device_type=device_type):
                panel = SimpleNamespace(get_sensors=Mock())
                device = LupusecBinarySensor(dict(self.idle, type=device_type), panel)
                self.assertIsNone(device.refresh())
                panel.get_sensors.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""Integration test against a real panel.

This test arms and disarms a real alarm system. It is deselected by default
and only runs when it is asked for explicitly:

    LUPUS_HARDWARE_TEST=1 pytest -m hardware

Read the warnings in the README before running it. Every mode change is
reported to whatever monitoring service the panel is configured to notify.
"""

import os
import time

import pytest

import lupupy.constants as CONST
from lupupy import Lupusec
from lupupy.__main__ import load_env_file
from lupupy.api.data_models import LupusecAlarmMode

SETTLE_TIMEOUT = 90
POLL_INTERVAL = 2

pytestmark = pytest.mark.hardware


def panel_mode(system):
    """Read the mode from the panel itself.

    set_mode() writes the new mode into the device optimistically, so asking
    the device would confirm nothing. This goes to the panel every time.
    """
    return LupusecAlarmMode(system.api.get_panel()["mode"])


def wait_for_mode(system, expected, timeout=SETTLE_TIMEOUT):
    """Wait until the panel itself reports the expected mode.

    Arming applies an exit delay that is configurable per installation, so
    the test waits for the state instead of guessing how long it takes.
    """
    deadline = time.monotonic() + timeout
    while True:
        mode = panel_mode(system)
        if mode is expected:
            return mode
        if time.monotonic() >= deadline:
            pytest.fail(
                f"Panel stayed in {mode} instead of reaching {expected} "
                f"within {timeout} seconds"
            )
        time.sleep(POLL_INTERVAL)


def open_contacts(system):
    """Return contacts that would trigger an alarm when arming.

    Bypassed zones are excluded, the panel ignores them while armed.
    """
    return [
        device
        for device in system.get_devices()
        if device.type in CONST.TYPE_OPENING
        and str(device.get_value("status_ex")) == "1"
        and str(device.get_value("bypass")) != "1"
    ]


CREDENTIALS = ("LUPUS_USER", "LUPUS_PASSWORD", "LUPUS_IP")
ENABLE_FLAG = "LUPUS_HARDWARE_TEST"


def hardware_tests_enabled():
    """Whether the opt-in for running against real hardware is set.

    The env file is read first, so the flag can live next to the credentials
    in .env instead of being retyped on every invocation.
    """
    load_env_file()
    return os.environ.get(ENABLE_FLAG) == "1"


def missing_credentials():
    """Names of the credentials that are still missing."""
    load_env_file()
    return [name for name in CREDENTIALS if not os.environ.get(name)]


@pytest.fixture(name="system")
def fixture_system():
    """Connect to the panel and make sure it is safe to test against."""
    if not hardware_tests_enabled():
        pytest.skip(
            f"set {ENABLE_FLAG}=1, in the environment or in .env, to run "
            "against real hardware; this arms and disarms the alarm"
        )

    missing = missing_credentials()
    if missing:
        pytest.skip(
            f"missing credentials: {', '.join(missing)} "
            "(set them, or put them in .env / LUPUS_ENV_FILE)"
        )

    system = Lupusec(
        username=os.environ["LUPUS_USER"],
        password=os.environ["LUPUS_PASSWORD"],
        ip_address=os.environ["LUPUS_IP"],
    )

    starting_mode = system.get_alarm(refresh=True).mode
    if starting_mode is not LupusecAlarmMode.Disarmed:
        pytest.skip(f"panel is {starting_mode}, expected it to be disarmed")

    blocking = open_contacts(system)
    if blocking:
        names = ", ".join(device.name.strip() for device in blocking)
        pytest.skip(f"open contacts would set off the siren: {names}")

    try:
        yield system
    finally:
        # Never leave the panel armed, whatever happened above.
        system.get_alarm().set_standby(system.api)


def test_home_mode_round_trip(system):
    """Disarmed -> home -> disarmed, reading the state at every step."""
    assert panel_mode(system) is LupusecAlarmMode.Disarmed
    assert system.get_alarm(refresh=True).is_standby

    system.get_alarm().set_home(system.api)
    wait_for_mode(system, LupusecAlarmMode.Home)
    assert system.get_alarm(refresh=True).is_home

    system.get_alarm().set_standby(system.api)
    wait_for_mode(system, LupusecAlarmMode.Disarmed)
    assert system.get_alarm(refresh=True).is_standby


def test_away_mode_round_trip(system):
    """Disarmed -> armed -> disarmed.

    Arming activates every motion detector, so nobody must move in a covered
    room while this runs.
    """
    assert panel_mode(system) is LupusecAlarmMode.Disarmed

    system.get_alarm().set_away(system.api)
    wait_for_mode(system, LupusecAlarmMode.Armed)
    assert system.get_alarm(refresh=True).is_away

    system.get_alarm().set_standby(system.api)
    wait_for_mode(system, LupusecAlarmMode.Disarmed)
    assert system.get_alarm(refresh=True).is_standby

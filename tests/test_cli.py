"""Tests for the command line utility."""

import argparse
from unittest.mock import patch

import pytest

from lupupy.__main__ import call


@pytest.fixture(autouse=True)
def without_an_env_file(tmp_path, monkeypatch):
    """Keep a real .env in the working directory out of these tests."""
    monkeypatch.setenv("LUPUS_ENV_FILE", str(tmp_path / "absent.env"))


def arguments(**overrides):
    """Build the argument namespace the parser would produce."""
    args = dict(
        username=None, password=None, ip_address=None, env_file=None, version=False,
        arm=False, disarm=False, home=False, history=False, status=False,
        devices=False, debug=False, quiet=False,
    )
    args.update(overrides)
    return argparse.Namespace(**args)


def test_credentials_can_come_from_the_environment(monkeypatch):
    """Passing them as arguments exposes them in the process list."""
    monkeypatch.setenv("LUPUS_USER", "user")
    monkeypatch.setenv("LUPUS_PASSWORD", "secret")
    monkeypatch.setenv("LUPUS_IP", "panel.lan")

    with patch("lupupy.__main__.Lupusec") as lupusec:
        call(arguments(status=True))

    lupusec.assert_called_once_with(
        ip_address="panel.lan", username="user", password="secret"
    )


def test_missing_credentials_stop_with_a_readable_message(monkeypatch):
    for name in ("LUPUS_USER", "LUPUS_PASSWORD", "LUPUS_IP"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(SystemExit, match="Please supply a username"):
        call(arguments(status=True))

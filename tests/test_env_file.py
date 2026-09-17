"""Tests for reading credentials from an env file."""

import os

import pytest

from lupupy.__main__ import load_env_file


@pytest.fixture(name="env_file")
def fixture_env_file(tmp_path, monkeypatch):
    """Write an env file and make it the one the loader picks up."""

    def write(content, mode=0o600):
        path = tmp_path / ".env"
        path.write_text(content, encoding="utf-8")
        path.chmod(mode)
        monkeypatch.setenv("LUPUS_ENV_FILE", str(path))
        return path

    return write


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in ("LUPUS_USER", "LUPUS_PASSWORD", "LUPUS_IP"):
        monkeypatch.delenv(name, raising=False)


def test_values_are_read(env_file):
    env_file("LUPUS_USER=admin\nLUPUS_PASSWORD=secret\nLUPUS_IP=192.168.1.10\n")

    load_env_file()

    assert os.environ["LUPUS_USER"] == "admin"
    assert os.environ["LUPUS_PASSWORD"] == "secret"
    assert os.environ["LUPUS_IP"] == "192.168.1.10"


def test_the_environment_wins(env_file, monkeypatch):
    """An explicit export must not be overridden by the file."""
    monkeypatch.setenv("LUPUS_USER", "from-environment")
    env_file("LUPUS_USER=from-file\n")

    load_env_file()

    assert os.environ["LUPUS_USER"] == "from-environment"


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("LUPUS_USER=admin", "admin"),
        ('LUPUS_USER="admin"', "admin"),
        ("LUPUS_USER='admin'", "admin"),
        ("export LUPUS_USER=admin", "admin"),
        ("  LUPUS_USER = admin  ", "admin"),
    ],
    ids=["plain", "double_quoted", "single_quoted", "exported", "padded"],
)
def test_accepted_spellings(env_file, line, expected):
    env_file(line + "\n")

    load_env_file()

    assert os.environ["LUPUS_USER"] == expected


def test_comments_and_noise_are_skipped(env_file):
    env_file("# a comment\n\nnot-an-assignment\nLUPUS_USER=admin\n")

    load_env_file()

    assert os.environ["LUPUS_USER"] == "admin"


def test_a_missing_file_is_not_an_error(monkeypatch, tmp_path):
    monkeypatch.setenv("LUPUS_ENV_FILE", str(tmp_path / "nothing-here"))

    load_env_file()

    assert "LUPUS_USER" not in os.environ


def test_an_explicit_path_wins(tmp_path, monkeypatch):
    elsewhere = tmp_path / "other.env"
    elsewhere.write_text("LUPUS_USER=explicit\n", encoding="utf-8")
    monkeypatch.setenv("LUPUS_ENV_FILE", str(tmp_path / "ignored.env"))

    load_env_file(str(elsewhere))

    assert os.environ["LUPUS_USER"] == "explicit"


def test_loose_permissions_are_warned_about(env_file, caplog):
    env_file("LUPUS_USER=admin\n", mode=0o644)

    load_env_file()

    assert "readable by others" in caplog.text


def test_the_hardware_test_reads_the_env_file(env_file):
    """The integration test resolves credentials the same way the CLI does."""
    from tests.test_hardware import missing_credentials

    env_file("LUPUS_USER=admin\nLUPUS_PASSWORD=secret\nLUPUS_IP=192.168.1.10\n")

    assert missing_credentials() == []


def test_missing_entries_are_named(env_file):
    from tests.test_hardware import missing_credentials

    env_file("LUPUS_USER=admin\n")

    assert missing_credentials() == ["LUPUS_PASSWORD", "LUPUS_IP"]


def test_the_hardware_opt_in_can_live_in_the_env_file(env_file, monkeypatch):
    """The flag is read after the file, so it need not be retyped."""
    from tests.test_hardware import hardware_tests_enabled

    monkeypatch.delenv("LUPUS_HARDWARE_TEST", raising=False)
    env_file("LUPUS_HARDWARE_TEST=1\n")

    assert hardware_tests_enabled() is True


def test_without_the_flag_hardware_tests_stay_off(env_file, monkeypatch):
    from tests.test_hardware import hardware_tests_enabled

    monkeypatch.delenv("LUPUS_HARDWARE_TEST", raising=False)
    env_file("LUPUS_USER=admin\n")

    assert hardware_tests_enabled() is False

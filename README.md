# Lupupy

A python3 library to communicate with the Lupus Electronics alarm control panel.

## Disclaimer:

Published under the MIT license - See LICENSE file for more details.

"Lupusec" is a trademark owned by Lupusec Electronics, see www.lupus-electronics.de for more information. I am in no way affiliated with Lupus Electronics.

This library is based on the work of MisterWil See: https://github.com/MisterWil/abodepy. By "based" I mean that I copied huge portions of code and customized it to work with Lupusec.

## Installation

You can install the library with pip:
```
pip install Lupupy
```

## Usage

You can integrate the library into your own project, or simply use it in the command line.
```
lupupy -u USERNAME -p PASSWORD -i IP_ADDRESS --devices
```
This will retrieve a simple list of all devices.

Arguments are visible to every process on the machine, so credentials can also
be supplied through the environment, or through an env file:

```
cp .env.example .env
chmod 600 .env          # it holds your panel password
$EDITOR .env

lupupy --devices
```

`.env` is read from the current directory. Use `--env-file PATH` or the
`LUPUS_ENV_FILE` variable to point somewhere else. Values already set in the
environment are never overridden by the file, and `.env` is ignored by git.

## Testing against a real panel

There are no integration tests, because every panel is configured differently.
The command line utility is the way to check a change against real hardware.

Read-only commands, safe to run at any time:

```
lupupy --status         # the mode the panel is in
lupupy --devices        # every device the panel reports
lupupy --history        # the event log
lupupy --devices --debug  # with the raw requests and responses
```

Commands that change the state of the alarm system:

```
lupupy --arm            # arm
lupupy --home           # arm in home mode
lupupy --disarm         # disarm
```

Arming a panel with an open contact sets off the siren, so check `--status` and
`--devices` first. A typical session while working on the library:

```
pip install -e .
lupupy --status                  # before
lupupy --devices | grep -i door
lupupy --disarm
lupupy --status                  # after
```

Please mention the panel model and firmware you verified against when opening a
pull request. `lupupy --devices --debug` prints both.

### The integration test

`tests/test_hardware.py` walks a real panel through its modes and reads the
state back at every step: disarmed, home, disarmed. It is deselected by
default and needs two things to run:

```
cp .env.example .env && chmod 600 .env   # panel, credentials and the opt-in
pytest -m hardware
```

`.env.example` carries `LUPUS_HARDWARE_TEST` commented out. Uncommenting it is
the opt-in, and the marker keeps these tests out of an ordinary `pytest` run
either way.

The test reads `.env` the same way the command line does, so `--env-file`'s
counterpart works here as well:

```
LUPUS_HARDWARE_TEST=1 LUPUS_ENV_FILE=~/my-panel.env pytest -m hardware
```

It arms a real alarm system, so read this first:

- **The panel must be disarmed** when the test starts, and it is always put
  back to disarmed afterwards, including when a step fails.
- **Open contacts abort the run.** The test skips rather than arm a panel
  that would immediately sound the siren. Bypassed zones are ignored, as the
  panel ignores them too.
- **Every mode change is reported** through whatever the panel is configured
  to notify, including a monitoring service over Contact ID. Those are real
  events on somebody's screen.
- **Arming in away mode activates the motion detectors.** Anybody moving in a
  covered room sets off the siren while the panel is armed, so pick a quiet
  moment.

The test waits for the panel to reach each mode instead of sleeping for a
fixed time, because entry and exit delays are configurable per installation.

---

### Shortcomings

The library currently only works with the XT1 alarm panel and since version 0.1.1 at least with the XT2. Others may work but aren't tested yet. The json responses of other panel will differ and most likely not work. Most of the advanced devices are not yet supported, I don't have the hardware to reverse engineer these devices. If someone need a further integration please open an issue and we will find a way.

### Currently supported features:
- Status of binary sensors like door and window sensors
- Setting the mode of the alarm control panel
- Get the history for further parsing
- Status of power switches

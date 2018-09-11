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

---

### Shortcomings

The library currently only works with the XT1 alarm panel. The json responses of other panel will differ and most likely not work. Most of the advanced devices are not yet supported, I don't have the hardware to reverse engineer these devices. If someone need a further integration please open an issue and we will find a way.

### Currently supported features:
- Status of binary sensors like door and window sensors
- Setting the mode of the alarm control panel
- Get the history for further parsing
- Status of power switches
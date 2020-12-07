# usb-test

`cm119_gpio.py` is for manipulating the I/O pins on the CM119. `board_test.py` contains
some user-friendly CLI-based test routines for working the GPIO pins.

## Install
First, install the `hidapi` for your system, then install the packages in `requirements.txt`

```
pip install -r requirements.txt
```

For more help, see https://pypi.org/project/hid/ or https://github.com/apmorton/pyhidapi

This was developed on Python 3.8 so use a modern Python 3.

## Run

```
python board_test.py --help
```

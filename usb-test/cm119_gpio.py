"""
USB HID interface to CM119 GPIO pins

Tristan Honscheid KD8YHB
6 Dec 2020
"""

import hid

# This should be compatible with the CM108, too --Use PID 0x000C
CM119_USB_VID = 0x0D8C
CM119_USB_PID = 0x013A

#
# HID Input Report (4 bytes)
#
# - Byte 0
#    0000.0000
#    |||| |||+------ VOLUP pressed (0), released (1)
#    |||| ||+------- VOLDN pressed (0), released (1)
#    |||| |+-------- Playback/Mute button* pressed (1), no activity (0)
#    |||| +--------- Record/Mute button* pressed (1), no activity (0)
#    ||++----------- Generic register written by Host MCU (not used)
#    ++------------- 00. Byte 1 caries general purpose input (what we use)
#                    01. Bytes 0-3 are generic HID registers
#                    10. Values written to Bytes 0-3 are also mapped to
#                        MCU_CTRL and EEPROM registers. (see datasheet page 17)
#                    11. Reserved
#    * This input not connected on board.
# - Byte 1 - GPIO input register
#    0000.0000
#    |       +------ GPIO1 input (1=high, 0=low)
#    |               ...
#    +-------------- GPIO8
# - Byte 2 - Generic register writen by host MCU (not used)
# - Byte 3 - Generic register writen by host MCU (not used)
#

#
# HID Output Report (1 byte report number + 4 bytes payload)
#
# - Byte 0 - Report number. Has value of 0x00
# - Byte 1 - Mode, buzzer, and SPDIF
#    0000.0000
#    |||| ++++------ SPDIF status channel (not used)
#    |||+----------- SPDIF valid bit (not used)
#    ||+------------ Buzzer control (1=on, 0=off)
#    ++------------- 00. Report carries GPIO commands. (what we use)
#                    01. Bytes 1-4 are generic HID registers
#                    10. Bytes 1-4 are mapped to MCU_CRTL and EEPROM
#                       registers (see datasheet page 18)
#                    11. Reserved
# - Byte 2 - GPIO output drivers
#    0000.0000
#    |       +------ GPIO1 output (1=high, 0=low)
#    |               ...
#    +-------------- GPIO8
# - Byte 3 - GPIO data direction register
#    0000.0000
#    |       +------ GPIO1 dir (1=output, 0=input) Input is default
#    |               ...
#    +-------------- GPIO8
# - Byte 4 - SPDIF category byte (not used)
#


class CM119_IO(hid.Device):
    """
    Manages a CM119's GPIO via USB HID
    """

    def __init__(self, vid=CM119_USB_VID, pid=CM119_USB_PID):
        """ Open the device. """
        # Maintain a record of our HID output report so we can modify individual pins. Array
        # holds Report Number (0x00), followed by 4 report bytes
        self.output_report = bytearray(5)

        # Init superclass
        super().__init__(vid, pid)

    def set_dir(self, pin_modes: dict):
        """
        Configure the GPIO in the device.
        :param: pin_modes A dictionary of the form {1: "I", 2: "O"}, etc. Pins not included
                do not change state. GPIOs are numbered 1-8.
        """
        # Configure inputs/outputs
        for key, val in pin_modes.items():
            if not (1 <= key <= 8):
                raise ValueError(f"Illegal GPIO number: {key}")
            if val == "O":
                # If output, set bit
                self.output_report[3] |= 1 << (key - 1)
            else:
                # If input, clear bit
                self.output_report[3] &= ~(1 << (key - 1))

        self.write(bytes(self.output_report))

    def set_output(self, gpio_num: int, state: bool):
        """
        Sets a GPIO output
        :param: gpio_num    The GPIO pin number to adjust (range 1-8)
        :param: state       True for on/high, False for off/low
        """
        if not (1 <= gpio_num <= 8):
            raise ValueError(f"Illegal GPIO number: {gpio_num}")
        if state:
            # Set output
            self.output_report[2] |= 1 << (gpio_num - 1)
        else:
            # Clear output
            self.output_report[2] &= ~(1 << (gpio_num - 1))

        self.write(bytes(self.output_report))

    def read_inputs(self):
        """
        Waits for an HID interrupt w/ an Input Report.
        """
        input_report = self.read(4)
        assert (
            input_report[0] & 0xC0 == 0x00
        )  # Make sure this a GPIO input report (bits 7:6 clear)

        # Quantar Interface board doesn't use Mute/Playback or Mute/Record buttons, but those could be
        # easily added. See input report description at top of file.
        pin_states = {
            "VOLDN": bool(input_report[0] & 0x02),
            "VOLUP": bool(input_report[0] & 0x01),
            "GPIO1": bool(input_report[1] & 0x01),
            "GPIO2": bool(input_report[1] & 0x02),
            "GPIO3": bool(input_report[1] & 0x04),
            "GPIO4": bool(input_report[1] & 0x08),
            "GPIO5": bool(input_report[1] & 0x10),
            "GPIO6": bool(input_report[1] & 0x20),
            "GPIO7": bool(input_report[1] & 0x40),
            "GPIO8": bool(input_report[1] & 0x80),
        }

        return pin_states

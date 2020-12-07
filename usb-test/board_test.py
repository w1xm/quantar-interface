"""
CLI test routines for CM119 GPIO pins

Tristan Honscheid KD8YHB
6 Dec 2020
"""

import click
import time

from cm119_gpio import CM119_IO, CM119_USB_VID, CM119_USB_PID


@click.group()
@click.option("--vid", default=hex(CM119_USB_VID), help="USB Vendor ID as hex string (opt.)")
@click.option("--pid", default=hex(CM119_USB_PID), help="USB Product ID as hex string (opt.)")
@click.pass_context
def testcli(ctx, vid, pid):
    # Save VID/PID in context dict
    ctx.ensure_object(dict)
    ctx.obj["vid"] = int(vid, base=16)
    ctx.obj["pid"] = int(pid, base=16)


@testcli.command()
@click.pass_context
def hidtest(ctx):
    """ Opens the HID device and prints product, serial, and mfg info. Doesn't do any GPIO manipulation. """
    d = CM119_IO(ctx.obj["vid"], ctx.obj["pid"])

    click.echo(f"Device manufacturer: {d.manufacturer}")
    click.echo(f"Product: {d.product}")
    click.echo(f"Serial: {d.serial}")
    click.echo(click.style("Success!", fg="green", bold=True))

    d.close()


@testcli.command()
@click.option("--pin", help="Pin to blink (1-8)", required=True, type=int)
@click.option("--delay", default=0.5, help="Time to wait in float seconds")
@click.pass_context
def output_blink(ctx, pin, delay):
    """ Blinks the specified output pin. Ctrl-C to stop. """
    if pin not in (1, 2, 3, 4):
        # For safety don't allow pins wired for input functions to be driven as outputs.
        click.echo(
            click.style(
                "This pin is not used as an output on the Quantar Interface board. HW damage may occur",
                fg="red",
            )
        )
        return

    d = CM119_IO(ctx.obj["vid"], ctx.obj["pid"])
    d.set_dir({pin: "O"})

    try:
        while True:
            d.set_output(pin, True)
            time.sleep(delay)
            d.set_output(pin, False)
            time.sleep(delay)
    except KeyboardInterrupt:
        pass

    click.echo("Closing device")
    d.close()


@testcli.command()
@click.pass_context
def input_mon(ctx):
    """ Monitors all pins for changes. Expects ANSI terminal color. """
    click.echo("Ctrl-\\ to quit")

    d = CM119_IO(ctx.obj["vid"], ctx.obj["pid"])
    d.set_dir({pin: "I" for pin in range(1, 9)})  # All GPIOs as inputs

    def pin_formatter(pin_name, state):
        """Helper function for adding ansi color indicators to pin status.
        Blue = low, White w/ Green BG = high"""
        if state:
            return click.style(f" {pin_name} ", bg="green", fg="white", bold=True)
        else:
            return click.style(f" {pin_name} ", fg="blue")

    click.echo("Pin states:")
    while True:
        pin_states = d.read_inputs()
        click.echo(
            "\r"
            + " ".join(
                [pin_formatter(pin, state) for pin, state in pin_states.items()]
            ),
            nl=False,
        )

    click.echo("Closing device")
    d.close()


if __name__ == "__main__":
    testcli()

# Oscilloscope module

These notes assume that you have already built the circuit and flashed the Arduino with `dmcomm.ino`. So long as everything is in good working order, the Arduino IDE serial monitor is sufficient. However, the `dmscope.py` program gives some additional visual information which can help to investigate problems.

It requires Python 3, Pygame and pyserial (see below).

The command-line arguments are as follows:

* The name of the serial port (see below). Or the path to a text file containing results data in the same format (see `test.txt`).
* If the path provided is a serial port and not a file, a second argument is required with the dmcomm code, the same as would be used for a serial command (see `codes.txt` in the folder above).
* If the path provided is a serial port and not a file, a third optional argument specifies the debug command to send, e.g. `DA-1A`. See the main README for details. `D1` is the default, for backwards compatibility.

If the serial connection was successful, a Pygame window will open, and after a few seconds will start displaying results. Controls are as follows:

* Press the left/right arrow keys to navigate the history of traces captured
* Press space to print the full data for the current trace to the console
* Press P to pause data collection and R to resume it
* Press Q or escape, or click the close button to exit.

The line of text at the top of the Pygame window shows where you are in the history, and the short description of the result.

The second line shows the operating parameters reported on the `p:` row (see the main README for details).

With older versions of the `dmcomm` sketch, the second line instead shows a frequency plot of the voltages detected - the most common voltages should be in the green areas, with nothing in the red. The orange area is probably OK, depending on the USB voltage.

The main section is the trace, of signal level against time, split across multiple rows. Each pixel horizontally on the image represents 200 microseconds. There are also some coloured dots to mark events:

* Cyan: non-bit stages of receiving
* Magenta: receiving failed
* Green: non-bit stages of sending
* White: detected the falling edge of bit 0; about to send bit 0
* Yellow: detected the falling edge of bit 1; about to send bit 1
* Red: unknown event

## Windows

Install Python, making sure to tick the box "Add Python to PATH".

Install the libraries using Command Prompt or PowerShell:

```
pip install --user pyserial
pip install --user pygame
```

Connect your Arduino. The serial port is likely to be named COM3 or any other number. You can check in the control panel for devices to see which number it is.

Open Command Prompt or PowerShell in the folder containing `dmscope.py`, and run it for example:

* `python dmscope.py COM3 V1-FC03-FD02`
* `python dmscope.py COM4 "V2-FC03-F^30^3" DA-1A` (the code needs to be quoted because `^` is a special character in Command Prompt)
* `python dmscope.py test.txt`

## Linux

Install pyserial: `pip install --user pyserial`

Installing Pygame this way has a lot of non-Python dependencies, so using the system package manager is easier if the package exists. On Fedora: `dnf install python3-pygame`

Joining the `dialout` user group is recommended, to avoid the need for root.

Connect your Arduino. The serial port is likely to be named `/dev/ttyACM0` or `/dev/ttyUSB0` (or a higher number if other serial devices are present).

Examples:
* `./dmscope.py /dev/ttyACM0 V1-FC03-FD02`
* `./dmscope.py /dev/ttyUSB0 V2-FC03-F^30^3 DA-1A`
* `./dmscope.py test.txt`


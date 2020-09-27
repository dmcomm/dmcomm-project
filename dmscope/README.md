# Oscilloscope module

These notes assume that you have already built the circuit and flashed the Arduino with `dmcomm.ino`. So long as everything is in good working order, the Arduino IDE serial monitor is sufficient. However, the `dmscope.py` program gives some additional visual information which can help to investigate problems.

It requires Python 3, Pygame and pyserial (see below).

It takes two command-line arguments:

* The name of the serial port (see below)
* The dmcomm code, the same as would be used for a serial command (see `codes.txt` in the folder above).

If the serial connection was successful, a Pygame window will open, and after a few seconds will start displaying results. Controls are as follows. (There may be an issue on some computers with presses of the arrow keys registering twice: if this occurs, then counter-intuitively, it can be prevented by pressing the key for longer.)

* Press the left/right arrow keys to navigate the history of traces captured
* Press space to print the full data for the current trace to the console
* Press P to pause data collection and R to resume it
* Press escape or click the close button to exit.

The line of text at the top of the Pygame window shows where you are in the history, and the short description of the result.

The next section is a frequency plot of the voltages detected - the most common voltages should be in the green areas, with nothing in the red. The orange area is probably OK, depending on the USB voltage.

The main section is the digital trace, of signal level against time, split across multiple rows. Each pixel horizontally on the image represents 200 microseconds. There are also some coloured dots to mark events:

* Cyan: non-bit stages of receiving
* Magenta: receiving failed
* Green: non-bit stages of sending
* White: finished receiving bit 0; about to send bit 0 (this is inconsistent and may be changed soon)
* Yellow: finished receiving bit 1; about to send bit 1 (ditto)
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

`python dmscope.py COM3 V1-FC03-FD02`

## Linux

Install pyserial: `pip install --user pyserial`

Installing Pygame this way has a lot of non-Python dependencies, so using the system package manager is easier if the package exists. On Fedora: `dnf install python3-pygame`

Joining the `dialout` user group is recommended, to avoid the need for root.

Connect your Arduino. The serial port is likely to be named `/dev/ttyACM0` or `/dev/ttyUSB0` (or a higher number if other serial devices are present).

Example: `./dmscope.py /dev/ttyUSB0 V1-FC03-FD02`


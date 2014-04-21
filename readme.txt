
Project using Arduino to communicate with Digimon toys

by BladeSabre, bladethecoder@gmail.com

Licences:
C and Python code: BSD (see code headers)
Documentation, diagrams and photos: CC-BY-SA ( https://creativecommons.org/licenses/by-sa/4.0/ )

This project is provided with absolutely no warranty! The author is not responsible for any damage to your property that may result from following these instructions.



CIRCUIT

The circuit is designed to drop the voltage below 3V for the connection to the toy. Check this before using it! Also, be sure the polarity is correct. Mistakes here are the most likely to break something.

The connection to the toy has 2 lines, signal and GND. On 2-prong devices, the prong nearest the screen is for the signal ("Ain" on the circuit diagram) and the back prong is GND. On 3-prong devices, the central prong is for the signal and the outer two prongs are GND. 

The diode should be the common type which drops about 0.6V at small currents. It creates a virtual power rail at about 2.7V. The capacitors stabilise the voltage, and the 100k resistor to ground also helps with this by ensuring there is always a small current through the diode.

The 74HC125 tristate buffer is wired to drive high or low through the 1K resistor, and to give a weak pull-up through 100K when output is not enabled. The 10K resistors on the inputs of the tristate buffer allow these inputs to be driven safely by the 5V Arduino outputs while the buffer's power supply is 2.7V. Unused inputs should not be left floating: safest to tie them to the buffer's Vcc, as this disables the unused outputs.

The circuit works fine on breadboard. Diagrams for a stripboard "shield" are also provided.

In the breadboard photo, the jumper wires from the Arduino in the top left go 3.3V (red), GND (black), out (orange), notOE (grey), Ain (green). The connector for the toy was clipped onto the two gold hoops at the far right; it could equally well be plugged into the breadboard over there if it had suitable wires.

The project was tested on Arduino Uno, but will probably work on any similar ones.



SERIAL INTERFACE (CODES)

D0 - disable debug
D1 - enable debug

If the first character of a code is 'V', use V-Pet / 2-prong timings. If the first character is 'X', use PenX / 3-prong timings.

If the second character is '0', listen for input only (don't send anything). If it is '1', send first (automatically repeating every few seconds). If it is '2', listen for input and reply. For '1' or '2', take turns sending 16 bits at a time.

The 16-bit message groups are written as 4 hex digits separated by dashes.

Examples of giving a Str-Max to a PenX:

X1-0459-7009
Use PenX timings. Send 0x0459; wait a short time for a response; if we got one, send 0x7009; wait a short time for a response.

X2-0459-7009
Use PenX timings. Wait for an initial message; if we got one, send 0x0459; wait a short time for a response; if we got one, send 0x7009; wait a short time for a response (which generally won't happen).



SERIAL INTERFACE (RESULTS)

r:XXXX - received the 16 bits XXXX
s:XXXX - sent the 16 bits XXXX
t - timed out while waiting for a message (this is normal)
t:-1 etc - timed out while receiving a message

c:XXXX XXXX... - the frequency map of the voltages detected (only with debug enabled)
d:XX XX XX... - the digital trace and events (only with debug enabled)

There are also some descriptive messages about what it is doing. It will echo back commands it receives so you can see if they were delivered and processed as expected.



OSCILLOSCOPE MODULE

So long as everything is in good working order, the Arduino serial monitor is sufficient (and is probably easier to use). However, the dmscope.py program gives some useful visual information.

It requires Pygame and pySerial. Edit the name of the serial port near the top of the file to match your system. It takes one command-line argument, which is the code, the same as for a serial command.

Use the left/right arrow keys to navigate the history of traces captured. Press space to print the full data for the current trace to the console.

The line of text at the top of the Pygame window shows where you are in the history, and the short description of the result.

The next section is a frequency plot of the voltages detected - the most common voltages should be in the green areas, with nothing in the red.

The main section is the digital trace, of signal level against time, split across multiple rows. There are also some coloured dots to mark events.


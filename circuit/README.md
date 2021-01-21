
# Circuit

This project is provided with absolutely no warranty! The author is not responsible for any damage to your property that may result from following these instructions.

The circuit is designed to drop the voltage below 3V for the connection to the toy. Check this before using it! Also, be sure the polarity is correct. Mistakes here are the most likely to break something.

The connection to the toy has 2 lines, signal and GND. On 2-prong devices, the prong nearest the screen is for the signal ("Ain" on the circuit diagram) and the back prong is GND. On 3-prong devices, the central prong is for the signal and the outer two prongs are GND.

The diode should be the common type which drops about 0.6V at small currents. It creates a virtual power rail at about 2.7V. The capacitors stabilise the voltage, and the 100k resistor to ground also helps with this by ensuring there is always a small current through the diode.

The 74HC125 tristate buffer is wired to drive high or low through the 1K resistor, and to give a weak pull-up through 100K when output is not enabled. The 10K resistors on the inputs of the tristate buffer allow these inputs to be driven safely by the 5V Arduino outputs while the buffer's power supply is 2.7V. Unused inputs should not be left floating: safest to tie them to the buffer's Vcc, as this disables the unused outputs.

The circuit works fine on breadboard. Diagrams for a stripboard "shield" are also provided.

In the breadboard photo, the jumper wires from the Arduino in the top left go 3.3V (red), GND (black), out (orange), notOE (grey), Ain (green). The connector for the toy was clipped onto the two gold hoops at the far right; it could equally well be plugged into the breadboard over there if it had suitable wires.

The project was tested on Arduino Uno, but will probably work on any similar ones.


# Circuit

*This project is provided with absolutely no warranty! The author is not responsible for any damage to your property that may result from following these instructions.*

The connection to the toy has 2 lines, signal and GND. On 2-prong devices, the prong nearest the screen is for the signal ("Ain" on the circuit diagram) and the back prong is GND. On 3-prong devices, the central prong is for the signal and the outer two prongs are GND.

Any suitable circuit should drop the voltage below 3V for the connection to the toy. Check this before using it! Also, be sure the polarity is correct. Mistakes here are the most likely to break something. If the circuit is wired correctly, the voltage test in the sketch can provide information about the voltages at the output. However, using a separate voltmeter is recommended.

This project was originally designed for Arduino Uno, but the (smaller and cheaper) CH340 Nano has since become popular.

## A-Com

It is possible to achieve results almost as good as a D-Com with just two resistors. As such, the D-Com design is largely obsolete. See https://dmcomm.github.io/guide/nano/ .

## D-Com

The original idea uses a 74HC125 tristate buffer, wired to drive high or low through a 1K resistor, and to give a weak pull-up through 100K when output is not enabled. This resembles the behaviour of the toys.

The diode should be the common type which drops about 0.6V at small currents. It creates a virtual power rail at about 2.7V. The capacitors stabilise the voltage, and the 100K resistor to ground also helps with this by ensuring there is always a small current through the diode.

Voltage dividers on the inputs of the tristate buffer allow these inputs to be driven safely by the 5V Arduino outputs while the buffer's power supply is 2.7V. Unused inputs should not be left floating: safest to tie them to the buffer's Vcc, as this disables the unused outputs.

The circuit works fine on breadboard. Diagrams for a stripboard Uno shield are also provided, but clearly a different layout is needed for the Nano.

## D-Com issue

The original design lacked the 10K pull-downs on the tristate buffer's inputs. Some 74HC125 chips are built to handle this, including NXP and Philips brands. However, some other brands leak current to Vcc, resulting in a higher voltage at the output. Fortunately, the capacitors largely keep the voltage down when the Arduino is signalling, so most of the overvoltage at the toy comes through the 100K pull-up. Also, the diode protects the Arduino's 3.3V pin. Codes for the Xros Mini drive the line high for longer periods, so these are more likely to be harmful.

To confirm whether a D-Com has the issue, check the voltage at the output, using either a voltmeter or the voltage test in the sketch, as above. It should be below 3V.

To fix a D-Com with the issue, there are three options:

* Add the 10K pull-downs to the inputs of the 74HC125.
* Replace the 74HC125 with one which does not require these pull-downs.
* Worst option but easiest on a PCB: Replace the 100k pull-down on Vcc with 4K7, to sink the excess current from Vcc.


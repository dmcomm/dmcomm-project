
# DMComm

Project using Arduino to communicate with Digimon toys, by BladeSabre, bladethecoder@gmail.com

Licences:
* C code: GPLv3+ (see file dmcomm/COPYING)
* Python code: BSD (see code headers)
* Documentation, diagrams and photos: CC-BY-SA ( https://creativecommons.org/licenses/by-sa/4.0/ )

*This project is provided with absolutely no warranty! The author is not responsible for any damage to your property that may result from following these instructions.*

## Overview

On the hardware side, some circuitry is needed to interface the Arduino with the toys. See the `circuit` folder for details.

The core of the project is the `dmcomm` Arduino sketch. This accepts instructions via the serial interface, communicates with the toys, and responds via serial with the results.

Software is needed to send commands and do something with the results. This could be the Arduino IDE serial monitor. Alternatively, the `dmscope` script provided here displays the debug information. Other software is available with more advanced functions, including the [Alpha](https://www.alphahub.site/) project and the [ACom Wiki](https://play.google.com/store/apps/details?id=com.mintmaker.acomwiki) Android app.

## Serial interface (commands)

The commands listed here are shown in upper-case, but they are case-insensitive.

### Communication codes

These contain the instructions for how to communicate with the toys.

If the first character of a code is 'V', use V-Pet / 2-prong timings. If the first character is 'X', use PenX / 3-prong timings. If the first character is 'Y', use Xros Mini timings. *(Note the warning in the circuit README about Xros Mini codes on a D-Com.)*

If the second character is '0', listen for input only (don't send anything). If it is '1', send first (automatically repeating every few seconds). If it is '2', listen for input and reply. For '1' or '2', take turns sending 16 bits at a time.

The 16-bit message groups are written as 4 hex digits separated by dashes. Placing the '@' character before a single digit in the final group gives a check digit, such that all the digits sent sum to the digit specified (mod 16). In type 2 codes, placing the '^' character before a digit gives the XOR of that digit and the corresponding digit being replied to.

* `X1-0459-7009` : Give a Str-Max to a PenX. Use PenX timings. Send 0x0459; wait a short time for a response; if we got one, send 0x7009; wait a short time for a response.
* `X2-0459-7009` : Give a Str-Max to a PenX. Use PenX timings. Wait for an initial message; if we got one, send 0x0459; wait a short time for a response; if we got one, send 0x7009; wait a short time for a response (which generally won't happen).
* `Y2-1017-0057-0007-@C^1^F7` : Do a Xros Mini battle with Shoutmon at minimum power with all single shots. Use Xros Mini timings. Wait for a message and respond 4 times, as above. In the second and third digits of the final response, 3 bits are copied from the message just received, and 5 bits are copied and inverted. The first digit in the final response is a check digit such that the sum of the 16 digits sent is 0xC (mod 16).

### Debug mode

* `D0` : disable debug mode
* `D1` : enable debug mode

The debug mode includes extra information in the results, mainly for use by `dmscope`.

### Voltage test

Ensure there is no toy connected to the output, and send "T". The sketch will run some tests and respond with information about the voltages.

## Serial interface (results)

* `r:XXXX` : received the 16 bits XXXX
* `s:XXXX` : sent the 16 bits XXXX
* `t` : timed out while waiting for a message (this is normal)
* `t:-1` etc : timed out while receiving a message
* `c:XXXX XXXX...` : the frequency map of the voltages detected (only with debug enabled)
* `d:XX XX XX...` : the digital trace and events (only with debug enabled)

There are also some descriptive messages about what it is doing. It will echo back commands it receives so you can see if they were delivered and processed as expected.


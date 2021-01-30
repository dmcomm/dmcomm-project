
# DMComm

Project using Arduino to communicate with Digimon toys, by BladeSabre ( bladethecoder@gmail.com ). License: MIT.

## Overview

On the hardware side, some circuitry is needed to interface the Arduino with the toys. See the `circuit` folder for details.

The core of the project is the `dmcomm` Arduino sketch. This accepts instructions via the serial interface, communicates with the toys, and responds via serial with the results.

Software is needed to send commands and do something with the results. This could be the Arduino IDE serial monitor. Alternatively, the `dmscope` script provided here displays the debug information. Other software is available with more advanced functions, including the [Alpha](https://www.alphahub.site/) project and the [ACom Wiki](https://play.google.com/store/apps/details?id=com.mintmaker.acomwiki) Android app.

## Serial interface commands

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
* `DD` : enable digital debug mode (`D1` still works too)
* `DA` : enable analog debug mode
* `DA-1A` etc: enable analog debug mode with trigger (see below)

The debug mode includes extra information in the results, mainly for use by `dmscope`.

For capturing analog data, the RAM may be limited. The trigger waits until the start of the specified packet, so can be used to capture analog data from later in the interaction. (It can also be used in digital mode, but will not normally be needed.) Packets are numbered 1A,1B,2A,2B...9A,9B,AA,AB.

### Voltage test

Ensure there is no toy connected to the output, and send "T". The sketch will run some tests and respond with information about the voltages.

## Serial interface results

* `r:XXXX` : received the 16 bits XXXX
* `s:XXXX` : sent the 16 bits XXXX
* `t` : timed out while waiting for a message (this is normal)
* `t:-1` etc : timed out while receiving a message
* `p:timing=...` : some of the operating parameters (only with debug enabled)
* `d:XX XX XX...` : the digital trace and events (only with digital debug enabled)
* `a:XX XX XX...` : the analog trace and events (only with analog debug enabled)

There are also some descriptive messages about what it is doing. It will echo back commands it receives so you can see if they were delivered and processed as expected.

**The rest of this document explains the debug protocol. Most people can stop reading here!**

### p-line (p for "parameters")

* `timing` is V/X/Y according to the code specified.
* `threshold` is the analog threshold on a 6-bit scale from 0-3.3V. If voltage >= threshold then it's logic high.
* `trigger` is the specified trigger packet.

### c-line (c for "counts")

On older versions of the sketch, `c:XXXX XXXX...XXXX` contained a frequency map of the voltages, with 16 4-digit hex values representing the sample counts from dividing the ADC result into 16 buckets. Supposing the power supply is exactly 5V, the left number is the number of samples measured between 0V-0.31V, the second number between 0.31V-0.62V ... the rightmost number between 4.69V-5V. This was replaced by the analog debug mode.

### Trace and events

The line starts with `d:` for digital or `a:` for analog. The remainder is the contents of the log buffer, written as 2-digit hex values separated by spaces. Samples are taken every 200 microseconds. A multi-byte duration could get cut off at the end of the buffer, but this does not really matter in practice.

Bytes starting 0b11 represent events:

* `log_opp_enter_wait = 0xC0` : when it enters the listening stage
* `log_opp_init_pulldown = 0xC1` : when it detects the opponent's initial pulldown
* `log_opp_start_bit_high = 0xC2` : when it detects the opponent going into the start bit
* `log_opp_start_bit_low = 0xC3` : when it detects the low part of the start bit
* `log_opp_bits_begin_high = 0xC4` : when it detects the start of the first bit
* `log_opp_got_bit_0 = 0xC5` : when it detects the falling edge of bit 0 (previously, this marked the following rising edge)
* `log_opp_got_bit_1 = 0xC6` : when it detects the falling edge of bit 1 (previously, this marked the following rising edge)
* `log_opp_exit_ok = 0xC8` : when it has received a complete packet
* `log_opp_exit_fail = 0xC9` : when it bails out of receiving a packet
* `log_self_enter_delay = 0xE0` : when it enters the sending stage
* `log_self_init_pulldown = 0xE1` : when it starts the initial pulldown
* `log_self_start_bit_high = 0xE2` : when it goes into the start bit
* `log_self_start_bit_low = 0xE3`: when it goes into the low part of the start bit
* `log_self_send_bit_0 = 0xE5` : when it starts sending bit 0
* `log_self_send_bit_1 = 0xE6` : when it starts sending bit 1
* `log_self_release = 0xE7` : when it completes the sending stage

Bytes starting 0xF represent missed samples. The least significant 4 bits indicate the number of samples missed, with 0 meaning more than 15.

### Digital scope data

Bytes starting 0b00 represent logic low. The other 6 bits are either the number of samples, or the least significant 6 bits of that number in which case the following bytes starting 0b10 contain the remaining bits in groups of 6.

Bytes starting 0b01 represent logic high. The other 6 bits are either the number of samples, or the least significant 6 bits of that number in which case the following bytes starting 0b10 contain the remaining bits in groups of 6.

### Analog scope data

Bytes starting 0b00 represent a voltage level. The other 6 bits indicate the voltage on a 6-bit scale from 0-3.3V. If one of these bytes appears by itself, this voltage level is present for one sample.

Bytes starting 0b10 represent extension of the previous voltage level. They contain the number of additional samples, in groups of 6 bits, least significant first. (Note that this number does not include the original sample, so is 1 less than the total duration.)


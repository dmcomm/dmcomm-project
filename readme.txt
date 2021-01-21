
Project using Arduino to communicate with Digimon toys

by BladeSabre, bladethecoder@gmail.com

Licences:
C code: GPLv3+ (see file dmcomm/COPYING)
Python code: BSD (see code headers)
Documentation, diagrams and photos: CC-BY-SA ( https://creativecommons.org/licenses/by-sa/4.0/ )

This project is provided with absolutely no warranty! The author is not responsible for any damage to your property that may result from following these instructions.



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


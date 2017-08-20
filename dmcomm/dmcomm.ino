/*
  Copyright (c) 2014, BladeSabre

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are
  met:
   
  * Redistributions of source code must retain the above copyright notice,
    this list of conditions and the following disclaimer.
  * Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.
   
  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
  TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
  PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
  OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/


//pin assignments

const byte led_pin = 13;
const byte dm_pin_out = A2;
const byte dm_pin_notOE = A1;
const byte dm_pin_Ain = A3;
const byte probe_pin = 2;


//analog conversion parameters

const int sensor_threshold = 0x180; //should be multiple of (1 << sensor_shift)
//want sensor_levels << sensor_shift == 1024 (for ADC)
const byte sensor_levels = 16;
const byte sensor_shift = 6;


//durations, in microseconds unless otherwise specified

const unsigned int tick_length = 200;
const unsigned long listen_timeout = 3000000;

const unsigned int gofirst_repeat_ms = 5000;
const unsigned int serial_timeout_ms = 6000;
const unsigned int inactive_delay_ms = 1000;
const unsigned int ended_capture_ms = 500;


//buffer sizes

const byte serial_buffer_size = 80;
const byte send_buffer_size = 12;
const int log_length = 1200;


//bytes for log protocol

const byte log_prefix_low   = 0b00000000;
const byte log_prefix_high  = 0b01000000;
const byte log_prefix_again = 0b10000000;
const byte log_prefix_other = 0b11000000;
const byte log_max_count    = 0b00111111;
const byte log_count_bits   = 6;

const byte log_opp_enter_wait = 0xC0;
const byte log_opp_init_pulldown = 0xC1;
const byte log_opp_start_bit_high = 0xC2;
const byte log_opp_start_bit_low = 0xC3;
const byte log_opp_bits_begin_high = 0xC4;
const byte log_opp_got_bit_0 = 0xC5;
const byte log_opp_got_bit_1 = 0xC6;
const byte log_opp_exit_ok = 0xC8;
const byte log_opp_exit_fail = 0xC9;

const byte log_self_enter_delay = 0xE0;
const byte log_self_init_pulldown = 0xE1;
const byte log_self_start_bit_high = 0xE2;
const byte log_self_start_bit_low = 0xE3;
const byte log_self_send_bit_0 = 0xE5;
const byte log_self_send_bit_1 = 0xE6;
const byte log_self_release = 0xE7;


//globals

byte logBuf[log_length];
int logIndex;
boolean prevSensorLevel;
long ticksSame;
unsigned int sensorCounts[sensor_levels];

struct dm_times_t {
    unsigned long pre_high, pre_low;
    unsigned long start_high, start_low, bit1_high, bit1_low, bit0_high, bit0_low, send_recovery;
    unsigned long bit1_high_min;
    unsigned long timeout_reply, timeout_bits, timeout_bit;
} dm_times;


//configure durations depending on whether we are using X timings or not
void initDmTimes(boolean is_x) {
    dm_times.pre_high = 3000;
    dm_times.pre_low = 59000;
    dm_times.timeout_reply = 100000;
    dm_times.timeout_bits = 200000; 
    dm_times.timeout_bit = 5000;
    if (is_x) {
        dm_times.start_high = 2125;
        dm_times.start_low = 1625;
        dm_times.bit1_high = 3167;
        dm_times.bit1_low = 1708; 
        dm_times.bit0_high = 1083;
        dm_times.bit0_low = 3792;
        dm_times.send_recovery = 300;
        dm_times.bit1_high_min = 2125;
    } else {
        dm_times.start_high = 2083;
        dm_times.start_low = 917;
        dm_times.bit1_high = 2667; 
        dm_times.bit1_low = 1667; 
        dm_times.bit0_high = 1000; 
        dm_times.bit0_low = 3167;
        dm_times.send_recovery = 300;
        dm_times.bit1_high_min = 1833;
    }
}

void ledOn() {
    digitalWrite(led_pin, HIGH);
}

void ledOff() {
    digitalWrite(led_pin, LOW);
}

void busDriveLow() {
    digitalWrite(dm_pin_out, LOW);
    digitalWrite(dm_pin_notOE, LOW);
}

void busDriveHigh() {
    digitalWrite(dm_pin_out, HIGH);
    digitalWrite(dm_pin_notOE, LOW);
}

void busRelease() {
    digitalWrite(dm_pin_notOE, HIGH);
}

//add specified byte to the log
void addLogByte(byte b) {
    if (logIndex < log_length) {
        logBuf[logIndex] = b;
        logIndex ++;
    }
}

//add current logic level and time to the log (may be multiple bytes)
//and initialize next timing
void addLogTime() {
    byte log_prefix = (prevSensorLevel == LOW) ? log_prefix_low : log_prefix_high;
    addLogByte((ticksSame & log_max_count) | log_prefix);
    ticksSame >>= log_count_bits;
    while (ticksSame > 0) {
        addLogByte((ticksSame & log_max_count) | log_prefix_again);
        ticksSame >>= log_count_bits;
    }
}

//add specified byte to the log, making sure current timing information is logged first
void addLogEvent(byte b) {
    addLogTime();
    addLogByte(b);
}

//read analog input and do logging, clocked by tick_length;
//return current logic level measured
boolean doTick() {
    static unsigned long prev_micros = 0;
    static int ticks = 0;
    
    unsigned int sensorValue;
    int sensorCat;
    boolean sensorLevel;
    
    sensorValue = analogRead(dm_pin_Ain);
    
    if (micros() - prev_micros > 2*tick_length) {
        delayMicroseconds(tick_length);
        prev_micros = micros(); //resync the clock
    } else {
        while(micros() - prev_micros < tick_length);
        prev_micros += tick_length;
    }
    ticks ++;
    
    if (ticks % 2 == 0) {
        digitalWrite(probe_pin, LOW);
    } else {
        digitalWrite(probe_pin, HIGH);
    }
    
    if (sensorValue >= sensor_threshold) {
        sensorLevel = HIGH;
    } else {
        sensorLevel = LOW;
    }
    sensorCat = (sensorValue >> sensor_shift) % sensor_levels;
    sensorCounts[sensorCat] += 1;
    
    if (ticksSame != 0 && sensorLevel != prevSensorLevel) {
        addLogTime();
    } else {
        ticksSame ++;
    }
    prevSensorLevel = sensorLevel;
    return sensorLevel;
}

//initialize logging for a new run
void startLog() {
    int i;
    for (i = 0; i < sensor_levels; i ++) {
        sensorCounts[i] = 0;
    }
    logIndex = 0;
    ticksSame = 0;
}

//delay by specified number of microseconds (with resolution of tick_length)
//while logging each tick
void delayByTicks(unsigned long delay_micros) {
    unsigned long delay_ticks = delay_micros / tick_length;
    unsigned long i;
    for (i = 0; i < delay_ticks; i ++) {
        doTick();
    }
}

void setup() {     
    Serial.begin(9600);  

    ledOn();
    busRelease();

    pinMode(led_pin, OUTPUT);
    pinMode(probe_pin, OUTPUT);
    pinMode(dm_pin_out, OUTPUT);
    pinMode(dm_pin_notOE, OUTPUT);
    pinMode(dm_pin_Ain, INPUT);
    
    initDmTimes(false);
}


//receiving

//wait until measured input equals level, or timeout microseconds;
//return time taken in microseconds
unsigned long busWaitTime(boolean level, unsigned long timeout) {
    unsigned long timeStart = micros();
    unsigned long time;
    boolean sensorLevel;
    do {
        sensorLevel = doTick();
        time = micros() - timeStart;
    } while (sensorLevel != level && time <= timeout);
    return time;
}

//wait until measured input equals level, or timeout microseconds;
//return true if timeout was reached, false otherwise
boolean busWait(boolean level, unsigned long timeout) {
    unsigned long time = busWaitTime(level, timeout);
    return (time > timeout);
}

//receive one bit, and rotate into bits from the left;
//return false on success, true on error
boolean rcvBit(unsigned int * bits) {
    unsigned long time;
    unsigned long timeout = dm_times.timeout_bit;
    boolean bit0 = false;
    time = busWaitTime(LOW, timeout);
    if (time > timeout) {
        return true;
    }
    if (time > dm_times.bit1_high_min) {
        bit0 = true;
    }
    if (busWait(HIGH, timeout)) {
        return true;
    }
    (*bits) >>= 1;
    if (bit0) {
        addLogEvent(log_opp_got_bit_1);
        (*bits) |= 0x8000;
    } else {
        addLogEvent(log_opp_got_bit_0);
    }
    return false;
}

//receive a 16-bit packet,
//with specified timeout in microseconds,
//reporting results on serial and storing into bits parameter;
//return 0 on success, non-zero error code on failure
int rcvPacketGet(unsigned int * bits, unsigned long timeout1) {
    char i;
    if (timeout1 == 0) {
        timeout1 = dm_times.timeout_reply;
    }
    addLogEvent(log_opp_enter_wait);
    if (busWait(LOW, timeout1)) {
        addLogEvent(log_opp_exit_fail);
        Serial.write("t ");
        return -4;
    }
    addLogEvent(log_opp_init_pulldown);
    if (busWait(HIGH, dm_times.timeout_bits)) {
        addLogEvent(log_opp_exit_fail);
        Serial.write("t:-3 ");
        return -3;
    }
    addLogEvent(log_opp_start_bit_high);
    if (busWait(LOW, dm_times.timeout_bit)) {
        addLogEvent(log_opp_exit_fail);
        Serial.write("t:-2 ");
        return -2;
    }
    addLogEvent(log_opp_start_bit_low);
    if (busWait(HIGH, dm_times.timeout_bit)) {
        addLogEvent(log_opp_exit_fail);
        Serial.write("t:-1 ");
        return -1;
    }
    addLogEvent(log_opp_bits_begin_high);
    for (i = 0; i < 16; i ++) {
        if (rcvBit(bits)) {
            Serial.write("t:");
            Serial.print(i, DEC);
            Serial.write(':');
            serialPrintHex((*bits) >> (16-i), 4);
            Serial.write(' ');
            addLogEvent(log_opp_exit_fail);
            return i+1;
        }
    }
    Serial.write("r:");
    serialPrintHex(*bits, 4);
    Serial.write(' ');
    addLogEvent(log_opp_exit_ok);
    return 0;
}

//receive a 16-bit packet,
//with specified timeout in microseconds,
//reporting results on serial but discarding the data;
//return 0 on success, non-zero error code on failure
int rcvPacket(unsigned long timeout1) {
    unsigned int bits;
    int result;
    result = rcvPacketGet(&bits, timeout1);
    return result;
}


//sending

//send one bit
void sendBit(unsigned int bit) {
    addLogEvent(bit ? log_self_send_bit_1 : log_self_send_bit_0);
    delayByTicks(bit ? dm_times.bit1_high : dm_times.bit0_high);
    busDriveLow();
    delayByTicks(bit ? dm_times.bit1_low : dm_times.bit0_low);
    busDriveHigh();
}

//send a 16-bit packet
void sendPacket(unsigned int bits) {
    byte i;
    Serial.write("s:");
    serialPrintHex(bits, 4);
    Serial.write(' ');
    addLogEvent(log_self_enter_delay);
    delayByTicks(dm_times.pre_high);
    
    addLogEvent(log_self_init_pulldown);
    busDriveLow();
    delayByTicks(dm_times.pre_low);
    
    addLogEvent(log_self_start_bit_high);
    busDriveHigh();
    delayByTicks(dm_times.start_high);
    
    addLogEvent(log_self_start_bit_low);
    busDriveLow();
    delayByTicks(dm_times.start_low);
    
    busDriveHigh();
    for (i = 0; i < 16; i ++) {
        sendBit(bits & 1);
        bits >>= 1;
    }
    delayByTicks(dm_times.send_recovery);
    
    addLogEvent(log_self_release);
    busRelease();
}


//high-level communication functions

//just listen for sequences of incoming messages,
//e.g. if only the first packet is wanted, or listening to 2 toys
void commListen(boolean X) {
    int result;
    initDmTimes(X);
    result = rcvPacket(listen_timeout);
    ledOff();
    while (result == 0 || result >= 13) {
        result = rcvPacket(0);
    }
    delayByTicks((long)ended_capture_ms * 1000);
    ledOn();
    Serial.println();
    return;
}

//interact with the toy on the other end of the connection
void commBasic(boolean X, boolean goFirst, byte length, unsigned int * toSend) {
    byte i;
    initDmTimes(X);
    if (goFirst) {
        delay(gofirst_repeat_ms);
        //delayByTicks((long)gofirst_repeat_ms * 1000);
    } else {
        if (rcvPacket(listen_timeout)) {
            Serial.println();
            return;
        }
    }
    ledOff();
    for (i = 0; i < length; i ++) {
        sendPacket(toSend[i]);
        if (rcvPacket(0)) {
            break;
        }
    }
    delayByTicks((long)ended_capture_ms * 1000);
    ledOn();
    Serial.println();
}



//serial processing

//convert buffer to upper case in-place
void upperCase(byte length, char * buffer) {
    byte i;
    for (i = 0; i < length; i ++) {
        if (buffer[i] >= 'a' && buffer[i] <= 'z') {
            buffer[i] -= 'a';
            buffer[i] += 'A';
        }
    }
}

//return integer value of hex digit character, or -1 if not a hex digit
char hex2val(char hexdigit) {
    char value;
    if (hexdigit >= '0' && hexdigit <= '9') {
        value = hexdigit - 0x30;
    } else if (hexdigit >= 'a' && hexdigit <= 'f') {
        value = hexdigit - 0x57;
    } else if (hexdigit >= 'A' && hexdigit <= 'F') {
        value = hexdigit - 0x37;
    } else {
        value = -1;
    }
    return value;
}

//return integer value of 4 hex digit string, assuming correct input
unsigned int hexQuad2int(byte * str) {
    char i;
    unsigned int result = 0;
    for (i = 0; i < 4; i ++) {
        result <<= 4;
        result += hex2val(str[i]); 
    }
    return result;
}

//print number onto serial as hex, with specified number of digits
//(if too few digits, will take least significant)
void serialPrintHex(unsigned int number, char digits) {
    char digit;
    char pow;
    unsigned int mul = 1;
    for (pow = 1; pow < digits; pow ++) {
        mul *= 16;
    }
    while (mul > 0) {
        digit = (number / mul) % 16;
        Serial.print(digit, HEX);
        mul /= 16;
    }
}

//try to read from serial into buffer;
//return 0 on failure, or positive integer for number of characters read
char serialRead(byte * buffer) {
    unsigned long timeStart;
    unsigned long time;
    int incomingInt;
    byte incomingByte;
    byte i = 0;
    
    if (Serial.available() == 0) {
        return 0;
    }
    timeStart = millis();
    do {
        do {
            incomingInt = Serial.read();
            time = millis() - timeStart;
            if (time > serial_timeout_ms) {
                Serial.println("too late");
                return 0;
            }
        } while (incomingInt == -1);
        incomingByte = incomingInt;
        if (incomingByte != '\r' && incomingByte != '\n') {
            buffer[i] = incomingByte;
            i += 1;
        }
    } while (incomingByte != '\r' && incomingByte != '\n' && i < serial_buffer_size);
    if (incomingByte != '\r' && incomingByte != '\n') {
        Serial.println("too long");
        return 0;
    }
    return i;
}


//main loop
void loop() {
    static boolean active = false;
    static boolean debug = false;
    static boolean X;
    static boolean listenOnly;
    static boolean goFirst;
    static byte numPackets;
    static unsigned int toSend[send_buffer_size];
    static byte buffer[serial_buffer_size];

    int i, j;
    byte bufCursor;
    byte tsCursor;

    //process serial input
    i = serialRead(buffer);
    if (i > 0) {
        Serial.print("got ");
        Serial.print(i, DEC);
        Serial.print(" bytes: ");
        for (j = 0; j < i; j ++) {
            Serial.write(buffer[j]);
        }
        Serial.print(" -> ");
        if ((buffer[0] == 'd' || buffer[0] == 'D') && i >= 2) {
            if (buffer[1] == '0') {
                Serial.println("debug off");
                debug = false;
            } else {
                Serial.println("debug on");
                debug = true;
            }
            return;
        }
        // start changing stuff
        active = true;
        if (buffer[0] == 'x' || buffer[0] == 'X') {
            X = true;
            Serial.print("X");
        } else if (buffer[0] == 'v' || buffer[0] == 'V') {
            X = false;
            Serial.print("V");
        } else {
            active = false;
        }
        if (i < 2 || (i < 5 && buffer[1] != '0')) {
            active = false;
        }
        if (active) {
            if (buffer[1] == '0') {
                listenOnly = true;
                Serial.print("0");
            } else if (buffer[1] == '1') {
                listenOnly = false;
                goFirst = true;
                Serial.print("1");
            } else if (buffer[1] == '2') {
                listenOnly = false;
                goFirst = false;
                Serial.print("2");
            } else {
                active = false;
                Serial.print("?");
            }
            //buffer[2] discarded
        }
        if (i < 7 && !listenOnly) {
            active = false;
        }
        if (active && !listenOnly) {
            numPackets = (i - 2) / 5;
            if (numPackets > send_buffer_size) {
                numPackets = send_buffer_size;
            }
            for (tsCursor = 0; tsCursor < numPackets; tsCursor ++) {
                toSend[tsCursor] = hexQuad2int(buffer + (tsCursor*5) + 3);
                Serial.print("-");
                serialPrintHex(toSend[tsCursor], 4);
            }
        }
        if (!active) {
            Serial.print("N");
        }
        Serial.println();
    }
    
    //do it
    if (active) {
        startLog();
        if (listenOnly) {
            commListen(X);
        } else {
            commBasic(X, goFirst, numPackets, toSend);
        }
        if (debug) {
            Serial.print("c:");
            for (i = 0; i < sensor_levels; i++) {
                serialPrintHex(sensorCounts[i], 4);
                Serial.print(" ");
            }
            Serial.println();
            Serial.print("d:");
            for (i = 0; i < logIndex; i ++) {
                serialPrintHex(logBuf[i], 2);
                Serial.print(" ");
            }
            Serial.println();
        }
    } else {
        delay(inactive_delay_ms);
    }
}


#!/usr/bin/env python3

#  Copyright (c) 2014,2020 BladeSabre
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#   
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#   
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
#  TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#  PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
#  OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


#graphics dimensions

screenWidth = 800
screenHeight = 600

countsY = 30
countsColW = 10
countsRowH = 20

traceY = 70
traceRowH = 12
traceMargin = 6

########################################

import sys, time, serial, pygame, threading, queue


log_prefix_low   = 0b00000000
log_prefix_high  = 0b01000000
log_prefix_again = 0b10000000
log_prefix_mask  = 0b11000000
log_max_count    = 0b00111111
log_count_bits   = 6


def parseHexBuf(s):
    parts = s[2:].split(" ")
    return [int(part, 16) for part in parts]

def renderCounts(c):
    counts = parseHexBuf(c)
    m = max(counts)
    for n in range(16):
        count = counts[n]
        x1 = n * countsColW
        x2 = x1 + countsColW - 1 
        rect = pygame.Rect(x1, countsY, countsColW+1, countsRowH+1)
        if n in [0, 1, 8, 9]:
            col = pygame.Color("dark green")
        elif n in [2, 3, 4, 5, 6, 7]:
            col = pygame.Color("dark blue")
        else:
            col = pygame.Color("dark red")
        pygame.draw.rect(screen, col, rect, 0)
        offsetPos = countsRowH * count // m
        yL = countsY + countsRowH - offsetPos
        pygame.draw.line(screen, pygame.Color("white"), (x1, yL), (x2, yL))
        if n > 0:
            pygame.draw.line(screen, pygame.Color("white"), (x1, yL), (x1, yLprev))
        yLprev = yL

def renderTrace(d, reporting=0):
    counts = []
    prevCount = None
    prevLevel = None
    shift = 0
    for item in parseHexBuf(d):
        prefix = item & log_prefix_mask
        isNewLow = prefix == log_prefix_low
        isNewHigh = prefix == log_prefix_high
        if isNewHigh or isNewLow:
            if prevCount is not None:
                counts.append((prevLevel, prevCount))
            prevCount = item & log_max_count
            shift = 0
            if isNewHigh:
                prevLevel = 1
            else:
                prevLevel = 0
        elif prefix == log_prefix_again:
            shift += log_count_bits
            prevCount |= (item & log_max_count) << shift
        else:
            counts.append((prevLevel, prevCount))
            prevCount = None
            prevLevel = None
            counts.append((item, None))
    if prevLevel is not None:
        counts.append((prevLevel, prevCount))
    
    if reporting > 1:
        print(counts)
    countsCut = [[]]
    x = 0
    row = 0
    for (level, count) in counts:
        if count is None:
            countsCut[row].append((level, count))
        else:
            while x + count > screenWidth:
                chunk = screenWidth - x
                countsCut[row].append((level, chunk))
                count -= chunk
                x = 0
                countsCut.append([])
                row += 1
            countsCut[row].append((level, count))
            x += count
    if reporting > 1:
        print(countsCut)
    
    y = traceY
    prevLevel = None
    for rowCounts in countsCut:
        rect = pygame.Rect(0, y, screenWidth, traceMargin)
        pygame.draw.rect(screen, pygame.Color("dark red"), rect, 0)
        y += traceMargin
        x = 0
        for (level, count) in rowCounts:
            if count is None:
                if (level >= 0xC0 and level <= 0xC4) or level == 0xC8:
                    #misc stages of receive
                    col = pygame.Color("cyan")
                elif level == 0xC9:
                    #receive fail
                    col = pygame.Color("magenta")
                elif (level >= 0xE0 and level <= 0xE3) or level == 0xE7:
                    #misc stages of send
                    col = pygame.Color("green")
                elif level in [0xC5, 0xE5]:
                    #bit 0
                    col = pygame.Color("white")
                elif level in [0xC6, 0xE6]:
                    #bit 1
                    col = pygame.Color("yellow")
                else:
                    #unknown event
                    col = pygame.Color("red")
                pygame.draw.line(screen, col, (x, y-2), (x, y-3))
            else:
                x1 = x
                x2 = x + count
                y1 = y if level else y + traceRowH - 1
                pygame.draw.line(screen, pygame.Color("white"), (x1, y1), (x2, y1))
                if prevLevel is not None and level != prevLevel:
                    y2 = y if prevLevel else y + traceRowH - 1
                    pygame.draw.line(screen, pygame.Color("white"), (x1, y1), (x1, y2))
                prevLevel = level
                x += count
        y += traceRowH
    rect = pygame.Rect(0, y, screenWidth, traceMargin)
    pygame.draw.rect(screen, pygame.Color("dark red"), rect, 0)

def display(cursor, curmax, data, reporting=0):
    (r, c, d) = data
    if reporting:
        print(r)
        print(c)
        print(d)
    
    cstr = str(cursor+1) + "/" + str(curmax+1) + " "
    screen.fill(pygame.Color("black"))
    t = font.render(cstr + r, False, pygame.Color("white"))
    screen.blit(t, (0, 0))
    
    renderCounts(c)
    renderTrace(d, reporting)
    pygame.display.update()

def pygameThread():
    cursor = -1
    results = []
    while True:
        reporting = 0
        curmax = len(results) - 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
                elif event.key == pygame.K_LEFT:
                    cursor -= 1
                    if cursor < 0:
                        cursor = 0
                elif event.key == pygame.K_RIGHT:
                    cursor += 1
                    if cursor > curmax:
                        cursor = curmax
                elif event.key == pygame.K_SPACE:
                    reporting = 1
                if len(results) > 0:
                    display(cursor, curmax, results[cursor], reporting)
        curAtMax = (cursor == curmax)
        new = False
        while not resultQ.empty():
            item = resultQ.get_nowait()
            results.append(item)
            curmax += 1
            new = True
        if new:
            if curAtMax:
                cursor = curmax
            display(cursor, curmax, results[cursor], False)
        
        time.sleep(0.25)

def consoleThread():
    time.sleep(2)
    ser.write("d1\n".encode("ascii"))
    ser.write((code + "\n").encode("ascii"))
    c = None
    r = None
    while 1:
        line = ser.readline().decode("ascii").rstrip()
        if line != "":
            if line.startswith("c:"):
                c = line
            elif line.startswith("d:"):
                d = line
                resultQ.put((r, c, d), True)
            elif line.startswith("r:") or line.startswith("s:") or line == "t":
                r = line
                print(line)
            else:
                print(line)

resultQ = queue.Queue()
test = False

print("\n***dmscope***")
if len(sys.argv) < 2:
    print("required arg: serialPort")
    sys.exit()
serialPort = sys.argv[1]

if serialPort == "testxt1":
    #X1-0459-7009: computer trades Str-Max for PenX's meat
    test = True
    testR = "s:0459 r:0409 s:7009 r:C009"
    testC = "c:08C0 0002 0001 0000 0000 0000 0001 0000 0120 0187 0000 0000 0000 0000 0000 0000"
    testD = "d:40 E0 4F E1 27 84 E2 4A E3 08 E6 4F 07 E5 45 11 E5 45 11 E6 4F 07 E6 4F 07 E5 45 11 E6 4F 07 E5 45 11 E5 45 11 E5 45 11 E6 4F 07 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E5 45 11 40 E7 40 C0 5F 00 C1 2F 84 40 C2 4A 00 C3 07 40 C4 4F 07 40 C6 45 12 40 C5 44 13 40 C5 4F 07 40 C6 45 12 40 C5 44 13 40 C5 44 12 40 C5 45 12 40 C5 44 13 40 C5 44 12 40 C5 4F 08 40 C6 44 13 40 C5 44 12 40 C5 45 12 40 C5 44 13 40 C5 44 10 40 C5 40 C8 40 E0 4F E1 27 84 E2 4A E3 08 E6 4F 07 E5 45 11 E5 45 11 E6 4F 07 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E6 4F 07 E6 4F 07 E6 4F 07 E5 45 11 40 E7 40 C0 42 81 00 C1 2F 84 40 C2 4A 00 C3 07 40 C4 4F 07 40 C6 45 12 40 C5 45 12 40 C5 4F 07 40 C6 45 12 40 C5 44 13 40 C5 44 12 40 C5 45 12 40 C5 45 12 40 C5 44 13 40 C5 44 12 40 C5 45 12 40 C5 44 13 40 C5 44 12 40 C5 4F 08 40 C6 4F 05 40 C6 40 C8"
elif serialPort == "testxt2":
    #X2-0459-7009: computer trades Str-Max for PenX's meat
    test = True
    testR = "r:0409 s:0459 r:C009 s:7009 t"
    testC = "c:08AA 0000 0000 0001 0000 0000 0000 0099 1B28 18B9 0000 0000 0000 0000 0000 0000"
    testD = "d:40 C0 54 80 83 00 C1 27 84 40 C2 49 00 C3 07 40 C4 4F 08 40 C6 44 13 40 C5 44 12 40 C5 4F 08 40 C6 44 12 40 C5 45 12 40 C5 45 12 40 C5 44 13 40 C5 44 12 40 C5 45 12 40 C5 4F 07 40 C6 45 12 40 C5 45 12 40 C5 44 13 40 C5 44 12 40 C5 45 10 40 C5 40 C8 40 E0 4F E1 27 84 E2 4A E3 08 E6 4F 07 E5 45 11 E5 45 11 E6 4F 07 E6 4F 07 E5 45 11 E6 4F 07 E5 45 11 E5 45 11 E5 45 11 E6 4F 07 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E5 45 11 40 E7 40 C0 6A 00 C1 20 84 40 C2 49 00 C3 07 40 C4 4F 08 40 C6 44 13 40 C5 44 12 40 C5 4F 08 40 C6 44 12 40 C5 45 12 40 C5 45 12 40 C5 44 13 40 C5 44 12 40 C5 45 12 40 C5 45 12 40 C5 44 12 40 C5 45 12 40 C5 45 12 40 C5 4F 07 40 C6 4F 05 40 C6 40 C8 40 E0 4F E1 27 84 E2 4A E3 08 E6 4F 07 E5 45 11 E5 45 11 E6 4F 07 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E5 45 11 E6 4F 07 E6 4F 07 E6 4F 07 E5 45 11 40 E7 40 C0 75 87 C9"
else:
    if len(sys.argv) < 3:
        print("required arg: code")
        sys.exit()
    code = sys.argv[2]
    ser = serial.Serial(serialPort, 9600)

pygame.init()
pygame.font.init()
font = pygame.font.Font(None, 30)
screen = pygame.display.set_mode((screenWidth, screenHeight))
pygame.display.set_caption("dmscope")
pygame.event.set_allowed(None)
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])

if test:
    display(0, 0, (testR, testC, testD), 2)
else:
    th = threading.Thread(target=consoleThread)
    th.daemon = True
    th.start()
pygameThread()

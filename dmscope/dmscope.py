#!/usr/bin/env python3

#  Copyright (c) 2014,2020,2021 BladeSabre
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.


#graphics dimensions

screenWidth = 800
screenHeight = 600

countsY = 30
countsColW = 10
countsRowH = 20

traceY = 70
traceRowH_D = 12
traceRowH_A = 32
traceMargin = 6

########################################

import os, sys, time, serial, pygame, threading, queue


log_prefix_low   = 0b00000000
log_prefix_high  = 0b01000000
log_prefix_again = 0b10000000
log_prefix_mask  = 0b11000000
log_max_count    = 0b00111111
log_count_bits   = 6

log_prefix_tick_overrun = 0xF0
log_max_ticks_missed = 0x0F


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
        elif n in [10]:
            col = pygame.Color("orange 4")
        else:
            col = pygame.Color("dark red")
        pygame.draw.rect(screen, col, rect, 0)
        offsetPos = countsRowH * count // m
        yL = countsY + countsRowH - offsetPos
        pygame.draw.line(screen, pygame.Color("white"), (x1, yL), (x2, yL))
        if n > 0:
            pygame.draw.line(screen, pygame.Color("white"), (x1, yL), (x1, yLprev))
        yLprev = yL

def checkMissedTicks(item):
    if item & log_prefix_tick_overrun == log_prefix_tick_overrun:
        ticksMissed = item & log_max_ticks_missed
        if ticksMissed == 0:
            return [(None, 8), (item, None), (None, 8)]
        else:
            return [(None, ticksMissed)]
    else:
        return [(item, None)]

def processDigital(d):
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
            if prevLevel is not None:
                counts.append((prevLevel, prevCount))
            prevCount = None
            prevLevel = None
            counts.extend(checkMissedTicks(item))
    if prevLevel is not None:
        counts.append((prevLevel, prevCount))
    return counts

def processAnalog(d):
    counts = []
    prevCount = None
    prevLevel = None
    shift = 0
    for item in parseHexBuf(d):
        prefix = item & log_prefix_mask
        if prefix == log_prefix_low: #"new value"
            if prevCount is not None:
                counts.append((prevLevel, prevCount + 1))
            prevLevel = item
            prevCount = 0
            shift = 0
        elif prefix == log_prefix_again:
            prevCount |= (item & log_max_count) << shift
            shift += log_count_bits
        else:
            if prevLevel is not None:
                counts.append((prevLevel, prevCount + 1))
            prevCount = None
            prevLevel = None
            counts.extend(checkMissedTicks(item))
    if prevLevel is not None:
        counts.append((prevLevel, prevCount + 1))
    return counts

def renderTrace(d, reporting=0):
    isAnalog = d.startswith("a")
    if isAnalog:
        counts = processAnalog(d)
        traceRowH = traceRowH_A
        maxLevel = 63
    else:
        counts = processDigital(d)
        traceRowH = traceRowH_D
        maxLevel = 1
    def calcYoffset(level):
        return int(traceRowH - (traceRowH - 1) * level / maxLevel - 1)
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
        y += traceMargin
        rect = pygame.Rect(0, y, screenWidth, traceRowH)
        pygame.draw.rect(screen, pygame.Color("dark blue"), rect, 0)
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
                if level is not None:
                    y1 = y + calcYoffset(level)
                    pygame.draw.line(screen, pygame.Color("white"), (x1, y1), (x2, y1))
                if prevLevel is not None and level is not None and level != prevLevel:
                    y2 = y + calcYoffset(prevLevel)
                    pygame.draw.line(screen, pygame.Color("white"), (x1, y1), (x1, y2))
                prevLevel = level
                x += count
        y += traceRowH

def display(cursor, curmax, data, reporting=0):
    (r, c, p, d) = data
    if reporting:
        print(r)
        print(c)
        print(p)
        print(d)
    
    summary = r + "  (" + str(cursor+1) + "/" + str(curmax+1) + " " + state + ")"
    screen.fill(pygame.Color("black"))
    t = font.render(summary, False, pygame.Color("white"))
    screen.blit(t, (0, 0))
    
    if c is not None:
        renderCounts(c)
    elif p is not None:
        #only expecting one of these
        t = font.render(p[2:], False, pygame.Color("white"))
        screen.blit(t, (0, countsY))
    
    if d is not None and len(d) >= 4:
        renderTrace(d, reporting)
    pygame.display.update()

def pygameThread():
    global state
    cursor = -1
    results = []
    while True:
        reporting = 0
        curmax = len(results) - 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    sys.exit()
                elif event.key == pygame.K_LEFT:
                    cursor -= 1
                    if cursor < 0:
                        cursor = curmax
                elif event.key == pygame.K_RIGHT:
                    cursor += 1
                    if cursor > curmax:
                        cursor = 0
                elif event.key == pygame.K_SPACE:
                    reporting = 1
                elif event.key == pygame.K_p and state == "running":
                    state = "paused"
                elif event.key == pygame.K_r and state == "paused":
                    state = "running"
            if len(results) > 0:
                display(cursor, curmax, results[cursor], reporting)
            else:
                display(-1, -1, ("please wait...", None, None, None), 0)
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
        
        pygame.time.wait(25)

def consoleThread():
    if state != "file":
        print("please wait...")
        time.sleep(2)
        ser.write((debugCmd + "\n").encode("ascii"))
        ser.write((code + "\n").encode("ascii"))
    r = None; c = None; p = None; d = None
    while 1:
        line = ser.readline().decode("ascii").rstrip()
        if line != "":
            if line.startswith("r:") or line.startswith("s:") or line.startswith("t:") or line == "t":
                r = line
                print(line)
            elif line.startswith("c:"):
                if r is None:
                    print("got c without r")
                else:
                    c = line
            elif line.startswith("p:"):
                if r is None:
                    print("got p without r")
                else:
                    p = line
            elif line.startswith("d:") or line.startswith("a:"):
                if r is None:
                    print("got d without r")
                else:
                    d = line
                    if state != "paused":
                        resultQ.put((r, c, p, d), True)
                    else:
                        print("ignored")
                    r = None; c = None; p = None; d = None
            else:
                print(line)

resultQ = queue.Queue()

print("\n***dmscope***")
if len(sys.argv) < 2:
    print("required arg: serialPort")
    sys.exit()
filename = sys.argv[1]

if os.path.isfile(filename):
    state = "file"
    ser = open(filename, "rb")
else:
    state = "running"
    if len(sys.argv) < 3:
        print("required arg: code")
        sys.exit()
    code = sys.argv[2]
    if len(sys.argv) >= 4:
        debugCmd = sys.argv[3]
    else:
        debugCmd = "d1"
    ser = serial.Serial(filename, 9600)

pygame.init()
pygame.font.init()
font = pygame.font.Font(None, 30)
screen = pygame.display.set_mode((screenWidth, screenHeight))
pygame.display.set_caption("dmscope")
pygame.event.set_allowed(None)
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])

th = threading.Thread(target=consoleThread)
th.daemon = True
th.start()
pygameThread()

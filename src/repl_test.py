"""
Interactive MIDI test harness for Wokwi.

Run from terminal (Wokwi simulator must be running in VS Code):
  mpremote connect port:rfc2217://localhost:4000 run src/repl_test.py

Commands (no Enter needed):
  c   one CLOCK tick
  C   24 CLOCK ticks = one beat @ 120 BPM
  n   NOTE_ON  ch0 C4 (note 60) vel=100
  N   NOTE_OFF ch0 C4
  s   START transport
  S   STOP transport
  t   CONTINUE transport
  v   toggle verbose CLOCK output
  h   show this help
"""

import sys
import time
from machine import Pin

from event_bus import EventBus
from midi_clock_tracker import MidiClockTracker
from midi_router import MidiRouter
from midi_input import MidiInput
from midi_output import MidiOutput
from uart_writer import MessageFilter, UartWriter
from tempo_to_cc import ValetonTempoHandler
from midi_message import MidiMessage, NOTE_ON, NOTE_OFF, CLOCK, START, STOP, CONTINUE

_verbose_clock = False


# ---------------------------------------------------------------------------
# Mock UART — prints decoded MIDI bytes to the serial terminal
# ---------------------------------------------------------------------------

class _PrintUart:
    def read(self):
        return None  # input injected directly via bus

    def write(self, data):
        data = bytes(data)
        if not data:
            return
        b0 = data[0]

        if b0 == 0xF8:
            if _verbose_clock:
                print("[OUT1] CLOCK")
            return
        if b0 == 0xFA:
            print("[OUT1] START")
        elif b0 == 0xFC:
            print("[OUT1] STOP")
        elif b0 == 0xFB:
            print("[OUT1] CONTINUE")
        elif b0 & 0xF0 == 0x90 and len(data) >= 3:
            print("[OUT1] NOTE_ON  ch{} note={} vel={}".format(b0 & 0xF, data[1], data[2]))
        elif b0 & 0xF0 == 0x80 and len(data) >= 3:
            print("[OUT1] NOTE_OFF ch{} note={} vel={}".format(b0 & 0xF, data[1], data[2]))
        elif b0 & 0xF0 == 0xB0 and len(data) >= 3:
            print("[OUT1] CC       ch{} cc={} val={}".format(b0 & 0xF, data[1], data[2]))
        elif b0 & 0xF0 == 0xC0 and len(data) >= 2:
            print("[OUT1] PC       ch{} prog={}".format(b0 & 0xF, data[1]))
        else:
            print("[OUT1] RAW      {}".format(data.hex()))


# ---------------------------------------------------------------------------
# Build system directly — no config.py or system_builder.py needed
# ---------------------------------------------------------------------------

bus = EventBus()
clock = MidiClockTracker(bus)
router = MidiRouter(bus, clock)

_out_uart = _PrintUart()
_writer = UartWriter(_out_uart, MessageFilter())
_output = MidiOutput("OUT1", bus, _writer, ValetonTempoHandler(channels=[0]))

tempo_led = Pin(15, Pin.OUT)
bus.on("beat", lambda: tempo_led.toggle())
bus.on("tempo_changed", lambda bpm: print("  *** TEMPO {:.1f} BPM".format(bpm)))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

_CLOCK_BPM = 120.0


def _send_clocks(n, bpm=_CLOCK_BPM):
    interval_us = int(60_000_000 / bpm / 24)
    for _ in range(n):
        time.sleep_us(interval_us)
        bus.emit("midi_in", MidiMessage(CLOCK))


def _help():
    print("""
  c   one CLOCK tick
  C   24 CLOCK ticks = one beat @ 120 BPM
  n   NOTE_ON  ch0 C4 vel=100
  N   NOTE_OFF ch0 C4
  s   START
  S   STOP
  t   CONTINUE
  v   toggle verbose CLOCK output (now: {})
  h   this help
""".format("on" if _verbose_clock else "off"))


def _toggle_verbose():
    global _verbose_clock
    _verbose_clock = not _verbose_clock
    print("Verbose CLOCK: {}".format("on" if _verbose_clock else "off"))


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

print("MidiClockWork test harness — type 'h' for help")
print()

while True:
    ch = sys.stdin.read(1)
    if ch == 'c':
        bus.emit("midi_in", MidiMessage(CLOCK))
    elif ch == 'C':
        print("Sending 24 clocks @ 120 BPM...")
        _send_clocks(24)
    elif ch == 'n':
        bus.emit("midi_in", MidiMessage(NOTE_ON,  channel=0, data1=60, data2=100))
    elif ch == 'N':
        bus.emit("midi_in", MidiMessage(NOTE_OFF, channel=0, data1=60, data2=0))
    elif ch == 's':
        bus.emit("midi_in", MidiMessage(START))
        print("START")
    elif ch == 'S':
        bus.emit("midi_in", MidiMessage(STOP))
        print("STOP")
    elif ch == 't':
        bus.emit("midi_in", MidiMessage(CONTINUE))
        print("CONTINUE")
    elif ch == 'v':
        _toggle_verbose()
    elif ch == 'h':
        _help()

from machine import Pin, UART
import time
from event_bus import EventBus

from midi_clock_tracker import MidiClockTracker
from midi_input import MidiInput
from midi_output import MidiOutput

# Hardware
tempo_led = Pin(15, Pin.OUT)
wireless_led = Pin(16, Pin.OUT)
button = Pin(14, Pin.IN, Pin.PULL_UP)

# MIDI hardware
midi_uart_in = UART(0, baudrate=31250, rx=Pin(1))

# Dummy UART for testing output
class DummyUart:
    def write(self, data):
        print("OUT: {}".format([hex(b) for b in data]))

# Event system
bus = EventBus()

# MIDI input and output
midi_in = MidiInput("IN", midi_uart_in, bus)
midi_out = MidiOutput("OUT1", DummyUart(), bus)

# Clock tracker listens to incoming MIDI
clock = MidiClockTracker(bus)

# Wire midi_in events to clock tracker and outputs
def on_midi_in(msg):
    clock.process(msg)
    bus.emit("midi_out", msg)

bus.on("midi_in", on_midi_in)

# Tempo LED blinks on beat
def on_beat():
    tempo_led.toggle()

bus.on("beat", on_beat)

print("MidiClockWork starting...")

while True:
    midi_in.poll()
    time.sleep_ms(1)

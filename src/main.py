from machine import Pin, UART
import time
from event_bus import EventBus
from midi_clock_tracker import MidiClockTracker
from midi_input import MidiInput
from midi_output import MidiOutput
from midi_router import MidiRouter
from tempo_to_cc import ValetonTempoHandler
from uart_writer import MessageFilter, UartWriter

# Hardware
tempo_led = Pin(15, Pin.OUT)
wireless_led = Pin(16, Pin.OUT)
button = Pin(14, Pin.IN, Pin.PULL_UP)

# MIDI hardware
midi_uart_in = UART(0, baudrate=31250, rx=Pin(1))
midi_uart_out1 = UART(1, baudrate=31250, tx=Pin(4))

# Event system
bus = EventBus()

# Components
midi_in = MidiInput("IN", midi_uart_in, bus)
clock = MidiClockTracker(bus)
router = MidiRouter(bus, clock)

# OUT1: pass everything through
midi_out = MidiOutput("OUT1", 
                      bus, 
                      UartWriter(midi_uart_out1, MessageFilter()),
                      ValetonTempoHandler(0))

# Tempo LED blinks on beat
bus.on("beat", lambda: tempo_led.toggle())

print("MidiClockWork starting...")

while True:
    midi_in.poll()
    time.sleep_ms(1)

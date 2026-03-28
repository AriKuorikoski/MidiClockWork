from machine import Pin
import time
from config import Config
from system_builder import SystemBuilder

# Hardware
tempo_led = Pin(15, Pin.OUT)

# Load configuration and build the system
try:
    system = SystemBuilder().build(Config.from_file("config.json"))
except OSError as e:
    print("ERROR: config.json not found -", e)
    raise
except Exception as e:
    print("ERROR: failed to load config -", e)
    raise

# Tempo LED blinks on beat
system.bus.on("beat", lambda: tempo_led.toggle())

print("MidiClockWork starting...")

while True:
    for midi_in in system.inputs:
        midi_in.poll()
    time.sleep_ms(1)

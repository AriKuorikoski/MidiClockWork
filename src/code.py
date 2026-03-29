import board
import digitalio
from config import Config
from system_builder import SystemBuilder

# Hardware — Pico W LED is on board.LED (CYW43 WL_GPIO0)
tempo_led = digitalio.DigitalInOut(board.LED)
tempo_led.direction = digitalio.Direction.OUTPUT

# Load configuration and build the system
try:
    system = SystemBuilder().build(Config.from_file("config.json"))
except OSError as e:
    print("ERROR: config.json not found -", e)
    raise
except Exception as e:
    print("ERROR: failed to load config -", e)
    raise

# Tempo LED toggles on beat
def _toggle_led():
    tempo_led.value = not tempo_led.value

system.bus.on("beat", _toggle_led)

print("MidiClockWork starting...")

while True:
    for midi_in in system.inputs:
        midi_in.poll()

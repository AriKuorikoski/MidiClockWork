# Development Environment Setup

## Prerequisites

- Python 3.13+ (`winget install Python.Python.3.13`)
- GitHub CLI (`winget install GitHub.cli`)
- VS Code with Wokwi extension (for emulator)

## Step 1: Install dependencies

```
python -m pip install pytest mpremote
```

## Step 2: VS Code Python interpreter

If VS Code doesn't discover tests or shows "pytest Discovery Error":

1. `F1` → "Python: Select Interpreter"
2. Select **Python 3.13 (64-bit)** from `~\AppData\Local\Programs\Python\Python313\python.exe`

This ensures VS Code uses the system Python where pytest is installed, rather than another environment manager (e.g. `uv`).

## Step 3: Running tests

From the command line:

```
python -m pytest tests/ -v
```

Or use the **Test Explorer** panel in VS Code (flask icon in the sidebar).

## Step 4: Flash MicroPython on the Pico WH

1. Download the latest stable MicroPython `.uf2` from https://micropython.org/download/RPI_PICO_W/
2. Hold the **BOOTSEL** button on the Pico WH
3. While holding, plug in USB to your PC
4. Release the button — a USB drive called **RPI-RP2** appears
5. Drag and drop the `.uf2` file onto the drive
6. The Pico reboots into MicroPython

## Step 5: Deploy to Pico

Upload all source files from `src/` to the Pico's root filesystem:

```
mpremote fs cp src/main.py :main.py
mpremote fs cp src/event_bus.py :event_bus.py
mpremote fs cp src/midi_message.py :midi_message.py
mpremote fs cp src/midi_input.py :midi_input.py
mpremote fs cp src/midi_output.py :midi_output.py
mpremote fs cp src/midi_clock_tracker.py :midi_clock_tracker.py
```

## Step 6: Wokwi emulator (optional)

The Wokwi emulator can be used to test with simulated hardware (LEDs, buttons).

1. Open the project in VS Code
2. Start simulator: `F1` → "Wokwi: Start Simulator"
3. Upload modules and run:

```
mpremote connect port:rfc2217://localhost:4000 fs cp src/event_bus.py :event_bus.py
mpremote connect port:rfc2217://localhost:4000 fs cp src/midi_message.py :midi_message.py
mpremote connect port:rfc2217://localhost:4000 fs cp src/midi_input.py :midi_input.py
mpremote connect port:rfc2217://localhost:4000 fs cp src/midi_output.py :midi_output.py
mpremote connect port:rfc2217://localhost:4000 fs cp src/midi_clock_tracker.py :midi_clock_tracker.py
mpremote connect port:rfc2217://localhost:4000 run src/main.py
```

Note: The emulator filesystem resets when stopped — files must be re-uploaded each time.

## Project structure

```
MidiClockWork/
├── src/               # Source modules (deployed to Pico root)
│   ├── main.py        # Entry point
│   ├── event_bus.py   # Pub/sub event system
│   ├── midi_message.py       # MIDI message parse/serialize
│   ├── midi_input.py         # UART input, emits to bus
│   ├── midi_output.py        # Bus subscriber, filters, UART output
│   └── midi_clock_tracker.py # BPM calculation, beat/tempo events
├── tests/             # Unit tests (pytest)
├── docs/              # Documentation
├── firmware/          # MicroPython UF2 firmware (gitignored)
├── diagram.json       # Wokwi circuit diagram
└── wokwi.toml         # Wokwi config
```

> **Note on folder structure:** Source modules are kept flat in `src/` for simplicity
> and because MicroPython deploys to a flat filesystem. If the module count grows
> significantly, consider reorganizing into subpackages (e.g. `messages/`, `handlers/`,
> `io/`). MicroPython supports packages via `__init__.py` and searches `/lib` by default.

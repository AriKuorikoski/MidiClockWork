# Development Environment Setup

## Prerequisites

- Python 3.13+ (`winget install Python.Python.3.13`)
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

## Step 5: Wokwi emulator (optional)

The Wokwi emulator can be used to test with simulated hardware (LEDs, buttons).

1. Open the project in VS Code
2. Start simulator: `F1` → "Wokwi: Start Simulator"
3. Upload modules and run:

```
mpremote connect port:rfc2217://localhost:4000 fs cp event_bus.py :event_bus.py
mpremote connect port:rfc2217://localhost:4000 fs cp midi_clock_tracker.py :midi_clock_tracker.py
mpremote connect port:rfc2217://localhost:4000 fs cp midi_output.py :midi_output.py
mpremote connect port:rfc2217://localhost:4000 run main.py
```

Note: The emulator filesystem resets when stopped — files must be re-uploaded each time.

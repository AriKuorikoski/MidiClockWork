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

## Step 6: Interactive test harness (Wokwi)

Upload all modules and launch the interactive MIDI test harness in one command:

```
bash run_test_harness.sh
```

Type `h` in the terminal for the list of commands (`C` sends a beat, `n` sends NOTE_ON, etc.).
The Wokwi simulator must already be running in VS Code before executing this script.

## Step 7: Wokwi emulator (optional, manual upload)

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
├── src/                      # Source modules (deployed to Pico root)
│   ├── main.py               # Entry point
│   ├── config.py             # JSON config loader
│   ├── config.json           # Default device configuration
│   ├── system_builder.py     # Wires all components from config
│   ├── event_bus.py          # Pub/sub event system
│   ├── midi_message.py       # MIDI message parse/serialize
│   ├── midi_input.py         # Transport input, channel filter, emits to bus
│   ├── midi_output.py        # Bus subscriber, delegates to writer + tempo handler
│   ├── midi_router.py        # Routes midi_in → clock tracker + midi_out
│   ├── midi_clock_tracker.py # BPM calculation, beat/tempo/transport events
│   ├── uart_writer.py        # MessageFilter + UartWriter (leaf output layer)
│   ├── tempo_to_cc.py        # ValetonTempoHandler: BPM → CC73+CC74
│   ├── transport_ble.py      # BLE MIDI 1.0 transport (ubluetooth)
│   ├── transport_usb.py      # USB MIDI 1.0 transport (usb module, v1.22+)
│   └── repl_test.py          # Interactive test harness (run via mpremote)
├── tests/                    # Unit + integration tests (pytest, desktop Python)
├── docs/                     # Documentation
├── firmware/                 # MicroPython UF2 firmware (gitignored)
├── diagram.json              # Wokwi circuit diagram
├── wokwi.toml                # Wokwi config (normal mode)
├── wokwi_test.toml           # Wokwi config (test harness mode)
├── run_test_harness.ps1      # Upload + run interactive harness (PowerShell)
└── KNOWN_ISSUES.md           # Known show-stopper bugs
```

---

## Test scenarios

### Scenario A — BLE MIDI in, USB MIDI out (no physical components needed)

Tests the full clock→tempo-CC pipeline using only the Pico WH and its USB cable.
No optocoupler, TRS jacks, or other components required.

**Hardware needed:**
- Raspberry Pi Pico WH
- USB cable (Pico → PC)
- iPhone with a BLE MIDI app (e.g. MIDI Wrench, free on App Store)
- PC with a MIDI monitor app (e.g. MIDI-OX on Windows)

**Config (`src/config.json`):**
```json
{
  "inputs": [
    { "name": "BLE_IN", "type": "ble_midi" }
  ],
  "outputs": [
    {
      "name": "USB_OUT",
      "type": "usb_midi",
      "filter": {},
      "tempo_handler": { "type": "valeton", "channels": [0] }
    }
  ]
}
```

**Steps:**
1. Flash MicroPython firmware to Pico WH (see Step 4 above)
2. Deploy all source files (see Step 5 above)
3. Update `config.json` on the Pico with the config above
4. Connect Pico to PC via USB — it should appear as a USB MIDI device
5. Open MIDI monitor on PC, select the Pico as MIDI input
6. On iPhone, open MIDI Wrench → connect to "MidiClockWork" via Bluetooth
7. In MIDI Wrench, send MIDI clock (start a clock source at any BPM)
8. On PC, observe CC73 + CC74 messages arriving on the MIDI monitor

**Expected output** (example at 120 BPM):
```
CC  ch0  cc=73  val=0    ← MSB (range byte)
CC  ch0  cc=74  val=120  ← LSB (BPM within range)
```

**Note:** The USB transport uses `usb.device.midi` (MicroPython v1.22+) with
`builtin_driver=True` to present a composite USB device (MIDI + serial REPL).
If the REPL stops responding over USB, the composite mode may need adjustment
— connect via Bluetooth serial or reflash to recover.

---

### Scenario B — Full hardware (Boss MS-3 → Valeton GP-50)

The production use case. Requires all components from [bom.md](bom.md).

**Config (`src/config.json`):**
```json
{
  "inputs": [
    {
      "name": "IN",
      "type": "uart",
      "uart": 0,
      "rx_pin": 1,
      "filter": { "include_global": true }
    }
  ],
  "outputs": [
    {
      "name": "OUT1",
      "type": "uart",
      "uart": 1,
      "tx_pin": 4,
      "filter": { "channels": [0] },
      "tempo_handler": { "type": "valeton", "channels": [0] }
    }
  ]
}
```

**Steps:**
1. Build circuit per [schematic.md](schematic.md)
2. Connect Boss MS-3 MIDI OUT → TRS IN jack (via TRS-to-DIN adapter if needed)
3. Connect TRS OUT 1 jack → Valeton GP-50 MIDI IN (via TRS-to-DIN adapter)
4. Power via 9V center-negative supply
5. Play on MS-3 — the tempo LED should blink on each beat
6. On Valeton GP-50, the tempo should track the MS-3 BPM via CC73/CC74

---

> **Note on folder structure:** Source modules are kept flat in `src/` for simplicity
> and because MicroPython deploys to a flat filesystem. If the module count grows
> significantly, consider reorganizing into subpackages (e.g. `messages/`, `handlers/`,
> `io/`). MicroPython supports packages via `__init__.py` and searches `/lib` by default.

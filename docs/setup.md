# Development Environment Setup

## Prerequisites

- Python 3.13+ (`winget install Python.Python.3.13`)
- GitHub CLI (`winget install GitHub.cli`)
- VS Code with Wokwi extension (for emulator)

## Step 1: Install dependencies

```
python -m pip install pytest pyserial
pip install circup
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

## Step 4: Flash CircuitPython on the Pico WH

You have a **Pico WH** (Pico W with headers). You must use the **Pico W** CircuitPython firmware.

A firmware file is included in the `firmware/` folder: `adafruit-circuitpython-raspberry_pi_pico_w-en_GB-10.1.4.uf2`.

> The `firmware/` folder also contains a MicroPython file (`RPI_PICO-*.uf2`). **Do not use it** — this project has been ported to CircuitPython.

1. Hold the **BOOTSEL** button on the Pico WH
2. While holding, plug in the USB data cable to your PC
3. Release the button — a USB drive called **RPI-RP2** appears in Explorer
4. Drag and drop the CircuitPython `.uf2` file onto the drive
5. The drive disappears and reappears as **CIRCUITPY**

**Verify the firmware is working:** The CIRCUITPY drive should appear in Explorer. You can also connect via serial:

```
# Find the REPL serial port
python -c "import serial.tools.list_ports; [print(p.device, p.description) for p in serial.tools.list_ports.comports()]"
```

Connect to the REPL COM port with a serial terminal (PuTTY, VS Code serial monitor, etc.) at any baud rate. Press Enter to get a `>>>` prompt.

**To reflash later:** Hold BOOTSEL while plugging in — the `RPI-RP2` drive reappears and you can drop a new `.uf2` onto it.

## Step 5: Install CircuitPython libraries

The BLE MIDI transport requires Adafruit libraries. Install them using `circup`:

```
circup install adafruit_ble adafruit_ble_midi
```

Or manually download the [Adafruit CircuitPython Bundle](https://circuitpython.org/libraries) and copy `adafruit_ble/` and `adafruit_ble_midi/` to `CIRCUITPY/lib/`.

## Step 6: Deploy to Pico

Copy all source files from `src/` to the CIRCUITPY drive:

```powershell
.\deploy.ps1
```

The script auto-detects the CIRCUITPY drive and copies all files. CircuitPython auto-reloads when files change — no manual reset needed.

To deploy manually, copy all `.py` and `.json` files from `src/` to the root of the CIRCUITPY drive. The entry point is `code.py` (runs automatically on boot).

## Step 7: Interactive test harness (Wokwi)

The Wokwi emulator can be used to test with simulated hardware. Note that BLE and USB MIDI are not available in the emulator.

1. Open the project in VS Code
2. Start simulator: `F1` → "Wokwi: Start Simulator"
3. The test harness (`repl_test.py`) can be loaded for interactive testing

Type `h` in the terminal for the list of commands (`C` sends a beat, `n` sends NOTE_ON, etc.).

## Project structure

```
MidiClockWork/
├── src/                      # Source modules (deployed to CIRCUITPY root)
│   ├── code.py               # Entry point (CircuitPython runs this on boot)
│   ├── boot.py               # USB config (MIDI + dual CDC serial)
│   ├── config.py             # JSON config loader
│   ├── config.json           # Default device configuration
│   ├── system_builder.py     # Wires all components from config
│   ├── event_bus.py          # Pub/sub event system
│   ├── midi_message.py       # MIDI message parse/serialize
│   ├── midi_input.py         # Transport input, channel filter, emits to bus
│   ├── midi_output.py        # Bus subscriber, delegates to writer + tempo handler
│   ├── midi_router.py        # Routes midi_in → clock tracker + midi_out
│   ├── midi_clock_tracker.py # BPM calculation, beat/tempo/transport events
│   ├── uart_writer.py        # MessageFilter + UartWriter + ConsoleWriter
│   ├── tempo_to_cc.py        # ValetonTempoHandler: BPM → CC73+CC74
│   ├── transport_ble.py      # BLE MIDI transport (adafruit_ble_midi)
│   ├── transport_usb.py      # USB MIDI transport (usb_midi)
│   ├── transport_serial.py   # USB CDC serial transport (for PC testing)
│   └── repl_test.py          # Interactive test harness
├── tests/                    # Unit + integration tests (pytest, desktop Python)
├── tools/                    # PC-side utilities
│   └── send_midi_clock.py    # Send MIDI clock over serial to Pico
├── docs/                     # Documentation
├── firmware/                 # CircuitPython UF2 firmware
├── diagram.json              # Wokwi circuit diagram
├── wokwi.toml                # Wokwi config
├── deploy.ps1                # Deploy source to CIRCUITPY drive
└── KNOWN_ISSUES.md           # Known bugs and limitations
```

---

## Debugging with a console output

Any output can be switched to print MIDI messages to the serial console instead of sending them out a physical port. This is useful when you want to verify the pipeline is working before the target device (e.g. Valeton GP-50) is connected.

Add `"writer": "console"` to an output in `config.json`:

```json
{
  "inputs": [
    { "name": "BLE_IN", "type": "ble_midi" }
  ],
  "outputs": [
    {
      "name": "DEBUG",
      "type": "uart",
      "uart": 1,
      "tx_pin": 4,
      "writer": "console",
      "tempo_handler": { "type": "valeton", "channels": [0] }
    }
  ]
}
```

Example output at 120 BPM with the Valeton tempo handler active:

```
CLOCK
CLOCK
...
CC             ch=0 data1=73 data2=0
CC             ch=0 data1=74 data2=120
```

To switch back to real output, remove `"writer": "console"` (it defaults to `"uart"`).

---

## Test scenarios

### Scenario A — BLE MIDI in, USB MIDI out (no physical components needed)

Tests the full clock→tempo-CC pipeline using only the Pico WH and its USB cable.
No optocoupler, TRS jacks, or other components required.

**Hardware needed:**
- Raspberry Pi Pico WH with CircuitPython
- USB cable (Pico → PC)
- iPhone with a BLE MIDI app (e.g. MIDI Wrench, free on App Store)
- PC with a MIDI monitor app (e.g. MIDIView on Windows)

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
1. Flash CircuitPython firmware to Pico WH (see Step 4 above)
2. Install Adafruit BLE libraries (see Step 5 above)
3. Deploy all source files (see Step 6 above)
4. Update `config.json` on the CIRCUITPY drive with the config above
5. Connect Pico to PC via USB — it should appear as a USB MIDI device
6. Open MIDI monitor on PC, select the Pico as MIDI input
7. On iPhone, open MIDI Wrench → connect to "MidiClockWork" via Bluetooth
8. In MIDI Wrench, send MIDI clock (start a clock source at any BPM)
9. On PC, observe CC73 + CC74 messages arriving on the MIDI monitor

**Expected output** (example at 120 BPM):
```
CC  ch0  cc=73  val=0    ← MSB (range byte)
CC  ch0  cc=74  val=120  ← LSB (BPM within range)
```

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

### Scenario C — Serial testing from PC (no phone or MIDI hardware needed)

Uses the PC-side `send_midi_clock.py` tool to send MIDI clock over serial.

**Config (`src/config.json`):**
```json
{
  "inputs": [
    { "name": "SERIAL_IN", "type": "serial" }
  ],
  "outputs": [
    {
      "name": "OUT1",
      "type": "uart",
      "uart": 1,
      "tx_pin": 4,
      "writer": "console",
      "filter": {},
      "tempo_handler": { "type": "valeton", "channels": [0] }
    }
  ]
}
```

**Steps:**
1. Deploy with the config above
2. Identify the data COM port (the Pico shows two COM ports — one is the REPL, the other is the data port)
3. Run: `python tools/send_midi_clock.py COM_DATA 120`
4. Observe CC73 + CC74 messages and beat markers in the output

---

> **Note on folder structure:** Source modules are kept flat in `src/` for simplicity
> and because CircuitPython deploys to a flat filesystem. If the module count grows
> significantly, consider reorganizing into subpackages.

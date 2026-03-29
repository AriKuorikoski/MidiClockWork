# Architecture: MIDI Message Flow

## Overview

MidiClockWork is built around an event bus. Components are decoupled — they communicate by emitting and subscribing to events, not by calling each other directly.

The system is fully declarative: a `config.json` file describes inputs, outputs, filters, and handlers. `SystemBuilder` wires all components at startup. No source code changes are needed to reconfigure routing.

```
 Transports (inputs)               Core pipeline              Transports (outputs)
┌────────────────────┐                                       ┌────────────────────┐
│  UART / BLE / USB  │──> MidiInput ──> [midi_in] ──────────> MidiOutput ──────> │ UART / BLE / USB │
│  (per input)       │    (filter)      EventBus   MidiRouter                     │ (per output)     │
└────────────────────┘                             (routes)  ┌────────────────────┤
                                                      │       │ MidiOutput ──────> │ UART / BLE / USB │
                                                      │       └────────────────────┘
                                            MidiClockTracker
                                            [beat] [tempo_changed] [transport]
```

Expanded view:

```
┌──────────────┐   ┌───────────┐   ┌─────────────┐   ┌─────────────┐
│  Transport   │──>│ MidiInput │──>│  EventBus   │──>│ MidiRouter  │
│  IN (any)    │   │  + filter │   │ "midi_in"   │   │             │
└──────────────┘   └───────────┘   └─────────────┘   └──────┬──────┘
                                                             │
                   ┌─────────────────────────────────────────┤
                   │                                         │
            ┌──────▼──────┐                        ┌────────▼────────┐
            │  EventBus   │                        │ MidiClockTracker│
            │ "midi_out"  │                        └────────┬────────┘
            └──────┬──────┘                                 │
                   │                                EventBus events:
         ┌─────────┴─────────┐                     "beat"
         │                   │                     "tempo_changed"
  ┌──────▼──────┐     ┌──────▼──────┐              "transport"
  │ MidiOutput  │     │ MidiOutput  │
  │  + handler  │     │  + handler  │
  └──────┬──────┘     └──────┬──────┘
         │                   │
  ┌──────▼──────┐     ┌──────▼──────┐
  │ UartWriter  │     │ UartWriter  │
  │  + filter   │     │  + filter   │
  └──────┬──────┘     └──────┬──────┘
         │                   │
  ┌──────▼──────┐     ┌──────▼──────┐
  │ Transport   │     │ Transport   │
  │  OUT (any)  │     │  OUT (any)  │
  └─────────────┘     └─────────────┘
```

---

## Configuration

The system is configured via `src/config.json`. `SystemBuilder` reads this at startup and wires all components.

```json
{
  "inputs": [
    {
      "name": "IN",
      "type": "uart",
      "uart": 0,
      "rx_pin": 1,
      "filter": { "channels": [0], "include_global": true }
    },
    {
      "name": "BLE_IN",
      "type": "ble_midi"
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
    },
    {
      "name": "USB_OUT",
      "type": "usb_midi",
      "filter": {}
    }
  ]
}
```

**Transport types:** `"uart"`, `"ble_midi"`, `"usb_midi"`, `"serial"`. Physical UART requires `uart` and `rx_pin`/`tx_pin`; BLE, USB, and serial do not.

**Input filter** (`filter` on each input):
- `channels` — list of MIDI channels to accept (0–15). Absent = all.
- `include_global` — if true, system real-time messages (CLOCK, START, STOP, CONTINUE) pass regardless of channel filter. Default true.

**Output filter** (`filter` on each output):
- `types` — list of message type strings to accept (`"clock"`, `"cc"`, `"note_on"`, etc.). Absent = all.
- `channels` — list of MIDI channels to accept. Absent = all.
- `cc_numbers` — list of CC numbers to accept. Absent = all.
- All specified criteria must match (AND logic).

**Tempo handler** (`tempo_handler` on each output, or `null`):
- `"type": "valeton"` — converts BPM to CC73 + CC74 for the Valeton GP-50.
- `channels` — list of MIDI channels to send tempo CCs on.

---

## Layers

### 1. Transports (`src/transport_ble.py`, `src/transport_usb.py`, `src/transport_serial.py`, `busio.UART`)

**Purpose:** Abstract hardware I/O behind a two-method interface.

All transports implement the same minimal contract:
- `read()` → `bytes` or `None` — called by `MidiInput.poll()`
- `write(bytes)` → `None` — called by `UartWriter`

| Transport | Module | Notes |
|-----------|--------|-------|
| Hardware UART | `busio.UART` | Physical TRS MIDI via GPIO pins |
| BLE MIDI | `transport_ble.py` | Uses `adafruit_ble_midi` (requires nRF chip; Pico W BLE not yet supported) |
| USB MIDI | `transport_usb.py` | Uses CircuitPython `usb_midi` module (built-in) |
| Serial | `transport_serial.py` | USB CDC data port for PC-side testing |

**BLE MIDI** uses Adafruit's `adafruit_ble_midi` library which handles GATT service registration, BLE MIDI packet framing, advertising, and iOS pairing automatically. Note: requires a board with native BLE support (nRF52840). The Pico W's CYW43 chip is not yet supported by CircuitPython's `_bleio` module.

**USB MIDI** uses CircuitPython's built-in `usb_midi` module which handles all USB MIDI 1.0 protocol framing internally.

**Serial** reads raw MIDI bytes from the USB CDC data port (`usb_cdc.data`), allowing a PC-side script to send MIDI for testing without MIDI hardware.

Nothing above this layer knows which transport is in use.

### 2. MidiInput (`src/midi_input.py`)

**Purpose:** Bridge between transport bytes and the event system.

- Called via `poll()` in the main loop
- Reads bytes from its transport
- Buffers partial messages (bytes can arrive split across multiple polls)
- Handles system real-time messages (clock, start, stop) immediately — they can arrive mid-message per MIDI spec
- Applies the per-input **channel filter** before emitting — messages that don't pass are dropped here, before the bus
- Emits `"midi_in"` on the bus with a parsed `MidiMessage` object

Nothing above this layer knows about raw bytes or transport type.

### 3. EventBus — `"midi_in"` event (`src/event_bus.py`)

**Purpose:** Decouples inputs from all consumers.

Any component can subscribe to `"midi_in"` without `MidiInput` knowing about it. Currently subscribed: `MidiRouter`.

### 4. MidiRouter (`src/midi_router.py`)

**Purpose:** Dispatches incoming messages to the processing pipeline.

- Passes every message to `MidiClockTracker` for timing analysis
- Re-emits every message as `"midi_out"` for outputs to consume

Single point where "what happens to every incoming message" is decided.

### 5. MidiClockTracker (`src/midi_clock_tracker.py`)

**Purpose:** Analyse MIDI clock messages and emit higher-level timing events.

- Counts clock ticks (24 per beat per MIDI spec)
- Measures intervals between ticks to calculate BPM
- Emits:
  - `"beat"` — every 24 clock ticks (one quarter note)
  - `"tempo_changed"` — when calculated BPM changes (smoothed over 10 readings, rounded to integer)
  - `"transport"` — on Start / Stop / Continue with state string

Consumers of these events don't need to know about MIDI clock bytes at all.

### 6. EventBus — `"midi_out"` event

**Purpose:** Decouples the router from the outputs.

All `MidiOutput` instances subscribe to `"midi_out"`. Each independently decides what to do based on its writer's filter. `MidiOutput` also subscribes to `"tempo_changed"` to drive its tempo handler.

### 7. MidiOutput (`src/midi_output.py`)

**Purpose:** Route messages and tempo events to the output transport.

- Subscribes to `"midi_out"` — checks the message against the writer's filter; writes if it matches
- Subscribes to `"tempo_changed"` — if a tempo handler is configured, converts BPM to MIDI messages and routes each through the output filter before writing

Multiple `MidiOutput` instances can exist on the same bus (one per physical or logical output). Each is configured independently.

### 8. ValetonTempoHandler (`src/tempo_to_cc.py`)

**Purpose:** Convert BPM to the two-CC encoding used by the Valeton GP-50.

- `handle(bpm)` returns a list of `MidiMessage` objects (CC73 + CC74 per configured channel)
- BPM range: 40–260. Out-of-range BPM → empty list (no messages sent)
- Can target multiple MIDI channels simultaneously (`channels=[0, 1, 2]`)
- Encoding: BPM ≤ 127 → range 0; 128–255 → range 1; 256–260 → range 2

The base `TempoHandler` class is a null object (returns `[]`). Swap in `ValetonTempoHandler` per-output in config.

### 9. UartWriter + MessageFilter (`src/uart_writer.py`)

**Purpose:** The leaf layer — decides which messages reach a transport and what they look like.

**MessageFilter** declares which messages a writer accepts:
- `types` — set of accepted message types (`{CLOCK}`, `{CC, PC}`, etc.)
- `channels` — set of accepted MIDI channels, or `None` for all
- `cc_numbers` — set of accepted CC numbers, only relevant when CC is in types
- All specified criteria must match (AND logic). All `None` → accepts everything.

**UartWriter** does the actual writing:
- Calls `transport.write(msg.serialize())` for matching messages
- Optional `generate` function: transforms a message into zero or more replacement messages before writing

### 10. MidiMessage (`src/midi_message.py`)

**Purpose:** The data model passed between all layers.

Carries: `type`, `channel`, `data1`, `data2`. Knows how to `serialize()` itself back to bytes for transport transmission. Created by `parse()` from raw bytes in `MidiInput`, consumed through all layers, serialized by `UartWriter`.

---

## Event Reference

| Event | Emitted by | Payload | Subscribed by |
|-------|-----------|---------|---------------|
| `"midi_in"` | `MidiInput` | `MidiMessage` | `MidiRouter` |
| `"midi_out"` | `MidiRouter` | `MidiMessage` | All `MidiOutput` instances |
| `"beat"` | `MidiClockTracker` | none | Tempo LED (`code.py`) |
| `"tempo_changed"` | `MidiClockTracker` | `float` (BPM) | All `MidiOutput` instances |
| `"transport"` | `MidiClockTracker` | `str` (`"start"` / `"stop"` / `"continue"`) | — |

---

## SystemBuilder and dependency injection

`SystemBuilder` wires all components from a `Config` object. It accepts an optional `uart_factory` (for hardware UART creation) and `transport_overrides` (for injecting mock transports in tests):

```python
# Production
system = SystemBuilder().build(Config.from_file("config.json"))

# Tests — inject mock UARTs and mock BLE
system = SystemBuilder(
    uart_factory=mock_factory,
    transport_overrides={"ble_midi": lambda: MockUart()},
).build(config)
```

This single seam means integration tests exercise the real pipeline with no hardware. See `tests/midi_system.py` and `tests/test_integration.py`.

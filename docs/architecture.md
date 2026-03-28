# Architecture: MIDI Message Flow

## Overview

MidiClockWork is built around an event bus. Components are decoupled — they communicate by emitting and subscribing to events, not by calling each other directly.

```
┌─────────────┐     ┌───────────┐     ┌─────────────┐     ┌─────────────┐
│  UART IN    │────>│ MidiInput │────>│  EventBus   │────>│ MidiRouter  │
│ (hardware)  │     │           │     │ "midi_in"   │     │             │
└─────────────┘     └───────────┘     └─────────────┘     └──────┬──────┘
                                                                  │
                                           ┌──────────────────────┤
                                           │                      │
                                    ┌──────▼──────┐     ┌────────▼────────┐
                                    │  EventBus   │     │ MidiClockTracker│
                                    │ "midi_out"  │     │                 │
                                    └──────┬──────┘     └────────┬────────┘
                                           │                      │
                                    ┌──────▼──────┐       EventBus events:
                                    │ MidiOutput  │       "beat"
                                    │             │       "tempo_changed"
                                    └──────┬──────┘       "transport"
                                           │
                          ┌────────────────┼────────────────┐
                          │                │                │
                   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
                   │ UartWriter  │  │ UartWriter  │  │ UartWriter  │
                   │ (all msgs)  │  │ (CC only)   │  │ (clock→CC)  │
                   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
                          │                │                │
                   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
                   │  UART OUT 1 │  │  UART OUT 2 │  │  UART OUT 3 │
                   └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Layers

### 1. MidiInput (`src/midi_input.py`)

**Purpose:** Bridge between raw hardware bytes and the event system.

- Called via `poll()` in the main loop
- Reads bytes from the hardware UART
- Buffers partial messages (bytes can arrive split across multiple polls)
- Handles system real-time messages (clock, start, stop) immediately — they can arrive mid-message per MIDI spec
- Emits `"midi_in"` on the bus with a parsed `MidiMessage` object

Nothing above this layer knows about raw bytes.

### 2. EventBus — `"midi_in"` event (`src/event_bus.py`)

**Purpose:** Decouples input from all consumers.

Any component can subscribe to `"midi_in"` without MidiInput knowing about it. Currently subscribed: `MidiRouter`.

### 3. MidiRouter (`src/midi_router.py`)

**Purpose:** Dispatches incoming messages to the processing pipeline.

- Passes every message to `MidiClockTracker` for timing analysis
- Re-emits every message as `"midi_out"` for outputs to consume

This is the single point where "what happens to every incoming message" is decided.

### 4. MidiClockTracker (`src/midi_clock_tracker.py`)

**Purpose:** Analyse MIDI clock messages and emit higher-level timing events.

- Counts clock ticks (24 per beat)
- Measures intervals between ticks to calculate BPM
- Emits:
  - `"beat"` — every 24 clock ticks (one quarter note)
  - `"tempo_changed"` — when calculated BPM changes (rounded to 1 decimal)
  - `"transport"` — on Start / Stop / Continue with state string

Consumers of these events (e.g. tempo LED, future CC converter) don't need to know about MIDI clock bytes at all.

### 5. EventBus — `"midi_out"` event

**Purpose:** Decouples the router from the outputs.

All `MidiOutput` instances subscribe to `"midi_out"`. They receive every message and each independently decides what to do with it based on their configured writers.

### 6. MidiOutput (`src/midi_output.py`)

**Purpose:** Dispatch incoming messages to its list of `UartWriter` objects.

- Holds a list of writers added via `add_writer()`
- For each incoming `"midi_out"` message, asks each writer whether it matches
- If a writer matches, calls `writer.process(msg)`
- By default (no writers): nothing is forwarded — behavior is opt-in

Multiple `MidiOutput` instances can exist on the same bus (one per physical output port). Each is configured independently.

### 7. UartWriter + MessageFilter (`src/uart_writer.py`)

**Purpose:** The leaf layer — decides which messages reach a physical UART and what they look like.

**MessageFilter** declares which messages a writer accepts:
- `types` — set of accepted message types (`{CLOCK}`, `{CC, PC}`, etc.)
- `channels` — set of accepted MIDI channels (`{0, 1}`, etc.), or None for all
- `cc_numbers` — set of accepted CC numbers (`{7, 11}`), only relevant when CC is in types
- All specified criteria must match (AND logic)
- All criteria None → accepts everything

**UartWriter** does the actual writing:
- If no `generate` function: writes the original message serialized to bytes
- If `generate` is provided: calls `generate(msg)`, writes whatever it returns
  - Returns `None` or `[]` → nothing written (block)
  - Returns `[msg1, msg2]` → writes multiple messages (transform/expand)

**Examples:**

```python
# Pass all messages through
UartWriter(uart, MessageFilter())

# Pass only MIDI clock
UartWriter(uart, MessageFilter(types={CLOCK}))

# Pass CC on channels 0 and 1, volume and expression only
UartWriter(uart, MessageFilter(types={CC}, channels={0, 1}, cc_numbers={7, 11}))

# Convert MIDI clock to a CC message (tempo-to-CC)
UartWriter(uart, MessageFilter(types={CLOCK}), generate=lambda msg: [
    MidiMessage(CC, channel=0, data1=85, data2=tempo_to_cc(bpm))
])

# Block MIDI clock (generate returns empty)
UartWriter(uart, MessageFilter(types={CLOCK}), generate=lambda msg: [])
```

### 8. MidiMessage (`src/midi_message.py`)

**Purpose:** The data model passed between all layers.

Carries: `type`, `channel`, `data1`, `data2`. Knows how to `serialize()` itself back to bytes for UART transmission. Created by `parse()` from raw bytes in `MidiInput`, consumed through all layers, serialized by `UartWriter`.

---

## Event Reference

| Event | Emitted by | Payload | Subscribed by |
|-------|-----------|---------|---------------|
| `"midi_in"` | `MidiInput` | `MidiMessage` | `MidiRouter` |
| `"midi_out"` | `MidiRouter` | `MidiMessage` | `MidiOutput` (all instances) |
| `"beat"` | `MidiClockTracker` | none | Tempo LED, future consumers |
| `"tempo_changed"` | `MidiClockTracker` | `float` (BPM) | Future consumers (e.g. CC converter) |
| `"transport"` | `MidiClockTracker` | `str` ("start"/"stop"/"continue") | Future consumers |

# MidiClockWork Circuit Schematic

## Overview

```
                         +------------------+
  9V Pedal PSU           | Raspberry Pi     |
  (center-neg)           | Pico WH          |
       |                 |                  |
  [Power Circuit] -5V--> VSYS              |
                         |                  |
  TRS IN ──[MIDI IN]──> GP1  (UART0 RX)   |
                         |                  |
                         | GP4  (UART1 TX) ──> [MIDI OUT 1] ── TRS OUT 1
                         | GP8  (PIO TX)   ──> [MIDI OUT 2] ── TRS OUT 2
                         | GP10 (PIO TX)   ──> [MIDI OUT 3] ── TRS OUT 3
                         | GP12 (PIO TX)   ──> [MIDI OUT 4] ── TRS OUT 4
                         |                  |
                         | GP15            ──> [Tempo LED]
                         | GP16            ──> [Wireless LED]
                         |                  |
  Button ──────────────> GP14              |
                         +------------------+
```

## Pin Assignment

| Function    | GPIO | Pin # | Type              |
|-------------|------|-------|-------------------|
| MIDI IN     | GP1  | 2     | Hardware UART0 RX |
| MIDI OUT 1  | GP4  | 6     | Hardware UART1 TX |
| MIDI OUT 2  | GP8  | 11    | PIO UART TX       |
| MIDI OUT 3  | GP10 | 14    | PIO UART TX       |
| MIDI OUT 4  | GP12 | 16    | PIO UART TX       |
| Tempo LED   | GP15 | 20    | Digital output    |
| Wireless LED| GP16 | 21    | Digital output    |
| Button      | GP14 | 19    | Digital input (pull-up) |
| Power (5V)  | VSYS | 39    | Power input       |
| Ground      | GND  | 38    | Ground            |

## Power Circuit (9V → 5V → Pico)

9V center-negative guitar pedal power supply, regulated to 5V for VSYS.

```
  9V Barrel Jack (center-negative)
  ┌──────────────────────────────────────┐
  │                                      │
  │  Barrel (outside) = +9V              │
  │  Center pin       = GND              │
  │                                      │
  └──┬───────────────────────────────┬───┘
     │                               │
     │ +9V                          GND
     │                               │
     ├──┤ D1: 1N5817 Schottky ├──┐   │
     │   (reverse polarity prot.) │   │
     │                            │   │
     │                     +9V protected
     │                            │
     │                     C1: 100uF electrolytic
     │                            │
     │                           GND
     │
     │                     ┌─────────────┐
     │  +9V protected ───> │ LM7805      │
     │                     │ IN      OUT │──> +5V
     │                     │     GND     │
     │                     └──────┬──────┘
     │                            │
     │                           GND
     │
     │                     +5V output:
     │                      ├── C2: 10uF tantalum
     │                      ├── C3: 100nF ceramic
     │                      │
     │                      └──┤ D2: 1N5817 Schottky ├──> Pico VSYS (pin 39)
     │                          (USB backfeed protection)
     │
    GND ─────────────────────────────────────> Pico GND (pin 38)
```

**Notes:**
- D1 protects against reversed polarity (wrong adapter)
- D2 prevents backfeed into the regulator when USB is also connected
- The Pico has its own Schottky from VBUS to VSYS, so USB and external power can coexist

## MIDI IN Circuit

Uses a 6N137 optocoupler for galvanic isolation at 3.3V.

```
  3.5mm TRS Jack (Type A)
  ┌─────────────────────────┐
  │ Tip    = DIN pin 5      │
  │ Ring   = DIN pin 4      │
  │ Sleeve = DIN pin 2      │
  └──┬────────┬────────┬────┘
     │ Tip    │ Ring   │ Sleeve
     │        │        │
     │        │       (floating / chassis ground only)
     │        │
     │        └──── R1: 220R ────┐
     │                           │
     │                    6N137 pin 2 (anode)
     │                           │
     │              D3: 1N4148 ──┤ (cathode to pin 2, protection)
     │                           │
     └──────────────────── 6N137 pin 3 (cathode)

  6N137 wiring:
  ┌────────────────────────────────────┐
  │ Pin 1 (NC)                         │
  │ Pin 2 (anode)    ← from Ring/220R  │
  │ Pin 3 (cathode)  ← from Tip       │
  │ Pin 4 (GND)      → GND            │
  │ Pin 5 (Vo)       → not used       │
  │ Pin 6 (output)   → GP1 (UART0 RX) │
  │                     R2: 10K to 3.3V (pull-up)  │
  │ Pin 7 (Enable)   → 3.3V           │
  │ Pin 8 (Vcc)      → 3.3V           │
  │                     C4: 100nF bypass cap to GND │
  └────────────────────────────────────┘
```

**Notes:**
- The 6N137 has a logic-gate output, ideal for 3.3V
- D3 (1N4148) protects the optocoupler LED from reverse voltage
- 100nF bypass cap on Vcc is essential for stable operation

## MIDI OUT Circuit (x4, identical)

3.3V MIDI output per MMA CA-033 specification. No buffer IC needed.

```
  Pico TX GPIO ──── R_data: 33R ────┐
                                    │
  3.3V ──────────── R_src:  10R ────┤
                                    │
                              3.5mm TRS Jack (Type A)
                              ┌─────────────────────────┐
  R_data (33R) ─────────────> │ Tip    = DIN pin 5      │
  R_src  (10R) ─────────────> │ Ring   = DIN pin 4      │
                              │ Sleeve = DIN pin 2      │
                              └────────────────┬────────┘
                                               │ Sleeve
                                              (floating)
```

Repeated for each output:

| Output     | TX Pin | R_data | R_src |
|------------|--------|--------|-------|
| MIDI OUT 1 | GP4    | 33R    | 10R   |
| MIDI OUT 2 | GP8    | 33R    | 10R   |
| MIDI OUT 3 | GP10   | 33R    | 10R   |
| MIDI OUT 4 | GP12   | 33R    | 10R   |

**Notes:**
- At 3.3V with 33R + 10R + ~220R receiver impedance, loop current is ~5mA (within MIDI spec)
- Pico GPIO can source up to 12mA, so direct drive is safe

## Tempo LED Circuit

```
  GP15 ──── R5: 330R ────┤►├──── GND
                         LED
                      (any color)
```

- At 3.3V: (3.3V - ~2.0V forward drop) / 330R ≈ 4mA
- For brighter output, use 220R (~6mA)

## Wireless Button Circuit

Single momentary push button with multi-function press patterns.
Uses the RP2040's internal pull-up resistor (no external pull-up needed).

```
  3.3V ──(internal pull-up)── GP14 ──┤ Button ├──── GND
```

| Action         | Function                      |
|----------------|-------------------------------|
| Short press    | Toggle Bluetooth pairing mode |
| Long press (3s)| Toggle Bluetooth on/off       |
| Double press   | Toggle WLAN on/off            |

**Default state:** Both Bluetooth and WLAN are **off** at boot.

## Wireless Status LED Circuit

```
  GP16 ──── R6: 330R ────┤►├──── GND
                         LED
                      (any color)
```

LED blink patterns:

| Pattern              | Meaning                |
|----------------------|------------------------|
| Off                  | Wireless off           |
| Slow blink (1Hz)     | Bluetooth on           |
| Fast blink (4Hz)     | Bluetooth pairing mode |
| Solid on             | WLAN connected         |
| Double blink         | WLAN on, not connected |

## TRS Type A Pinout Reference

All jacks use the MIDI TRS Type A standard (MMA/AMEI):

```
  TRS 3.5mm plug (tip view):

       ┌───┐
  Tip ─┤   ├─ Sleeve
       │   │
  Ring ┘   └

  Tip    = MIDI DIN pin 5 (data / current sink)
  Ring   = MIDI DIN pin 4 (source / Vcc)
  Sleeve = MIDI DIN pin 2 (shield)
```

Compatible with standard TRS-to-DIN adapters (Type A).

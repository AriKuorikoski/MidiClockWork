# Bill of Materials

## Microcontroller

| Qty | Component                        | Notes                          |
|-----|----------------------------------|--------------------------------|
| 1   | Raspberry Pi Pico WH             | RP2040 + WiFi, pre-soldered headers |

## Power Circuit

| Qty | Component                        | Value / Part    | Notes                          |
|-----|----------------------------------|-----------------|--------------------------------|
| 1   | DC barrel jack                   | 2.1mm, center-negative | Standard guitar pedal format |
| 1   | Voltage regulator                | LM7805          | 9V → 5V, TO-220 package       |
| 2   | Schottky diode                   | 1N5817          | D1: reverse polarity, D2: backfeed protection |
| 1   | Electrolytic capacitor           | 100uF / 16V     | Input filter (C1)             |
| 1   | Tantalum capacitor               | 10uF / 10V      | Regulator output (C2)        |
| 1   | Ceramic capacitor                | 100nF           | Regulator output (C3)        |

## MIDI IN Circuit

| Qty | Component                        | Value / Part    | Notes                          |
|-----|----------------------------------|-----------------|--------------------------------|
| 1   | Optocoupler                      | 6N137           | Logic-gate output, 3.3V compatible |
| 1   | Signal diode                     | 1N4148          | Reverse voltage protection (D3) |
| 1   | Resistor                         | 220R            | MIDI input current limiting (R1) |
| 1   | Resistor                         | 10K             | Pull-up on 6N137 output (R2) |
| 1   | Ceramic capacitor                | 100nF           | Bypass cap on 6N137 Vcc (C4) |
| 1   | 3.5mm TRS jack                   | Panel mount      | MIDI IN connector             |

## MIDI OUT Circuits (x4)

| Qty | Component                        | Value / Part    | Notes                          |
|-----|----------------------------------|-----------------|--------------------------------|
| 4   | Resistor                         | 33R             | Data line series resistor      |
| 4   | Resistor                         | 10R             | Source line series resistor    |
| 4   | 3.5mm TRS jack                   | Panel mount      | MIDI OUT connectors           |

## Tempo LED

| Qty | Component                        | Value / Part    | Notes                          |
|-----|----------------------------------|-----------------|--------------------------------|
| 1   | LED                              | Any color, 3mm or 5mm | Tempo indicator          |
| 1   | Resistor                         | 330R            | Current limiting (~4mA)       |

## Wireless Button and Status LED

| Qty | Component                        | Value / Part    | Notes                          |
|-----|----------------------------------|-----------------|--------------------------------|
| 1   | Momentary push button            | 6mm tactile     | Multi-function (BT/WLAN control) |
| 1   | LED                              | Any color, 3mm or 5mm | Wireless status indicator |
| 1   | Resistor                         | 330R            | Wireless LED current limiting  |

## Summary

| Category         | Total parts |
|------------------|-------------|
| ICs / Active     | 3 (Pico WH, LM7805, 6N137) |
| Diodes           | 3 (2x 1N5817, 1x 1N4148) |
| Resistors        | 12 (1x 220R, 1x 10K, 4x 33R, 4x 10R, 2x 330R) |
| Capacitors       | 4 (1x 100uF, 1x 10uF, 2x 100nF) |
| Connectors       | 6 (1x barrel jack, 5x TRS jack) |
| LEDs             | 2 (tempo, wireless status) |
| Button           | 1 |
| **Total**        | **31 components** |

## Optional / Recommended

| Qty | Component                        | Notes                          |
|-----|----------------------------------|--------------------------------|
| 1   | Enclosure                        | Hammond 1590B or similar       |
| 1   | PCB or perfboard                 | For permanent assembly         |
| 5   | TRS-to-DIN adapters              | For testing with 5-pin DIN gear |
| -   | Hookup wire                      | 22-24 AWG solid core           |
| -   | Pin headers / sockets            | If socketing the Pico          |

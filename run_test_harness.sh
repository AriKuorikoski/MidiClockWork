#!/usr/bin/env bash
# Upload all source modules to the Wokwi emulator and start the test harness.
# Requires Wokwi simulator already running in VS Code.

PORT="port:rfc2217://localhost:4000"

mpremote connect $PORT \
  cp src/event_bus.py         :event_bus.py         + \
  cp src/midi_message.py      :midi_message.py      + \
  cp src/midi_input.py        :midi_input.py        + \
  cp src/midi_output.py       :midi_output.py       + \
  cp src/midi_clock_tracker.py :midi_clock_tracker.py + \
  cp src/midi_router.py       :midi_router.py       + \
  cp src/uart_writer.py       :uart_writer.py       + \
  cp src/tempo_to_cc.py       :tempo_to_cc.py       + \
  cp src/config.py            :config.py            + \
  cp src/system_builder.py    :system_builder.py    + \
  cp src/config.json          :config.json          + \
  run src/repl_test.py

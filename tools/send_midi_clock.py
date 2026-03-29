"""
PC-side MIDI clock sender — sends MIDI clock bytes over serial to the Pico.

Usage:
    python tools/send_midi_clock.py COM3 120

Arguments:
    port    COM port (e.g. COM3)
    bpm     Beats per minute (default: 120)

MIDI clock sends 24 pulses per quarter note. At 120 BPM that's
24 * 120 / 60 = 48 clock bytes per second.

Press Ctrl+C to stop. Pico console output is displayed in real time.
"""
import serial
import time
import sys
import threading

MIDI_CLOCK = 0xF8
MIDI_START = 0xFA
MIDI_STOP = 0xFC

CLOCKS_PER_BEAT = 24


def reader_thread(ser):
    """Read and display Pico stdout output."""
    while True:
        try:
            data = ser.read(ser.in_waiting or 1)
            if data:
                # Filter out raw MIDI echoes, show only printable text
                text = data.decode('utf-8', errors='ignore')
                if text:
                    print(text, end='', flush=True)
        except Exception:
            break


def main():
    if len(sys.argv) < 2:
        print("Usage: python send_midi_clock.py PORT [BPM]")
        print("  e.g. python send_midi_clock.py COM3 120")
        sys.exit(1)

    port = sys.argv[1]
    bpm = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    interval = 60.0 / (bpm * CLOCKS_PER_BEAT)

    print(f"Connecting to {port} at {bpm} BPM ({1/interval:.1f} clocks/sec)...")
    ser = serial.Serial(port, 115200, timeout=0.1)
    time.sleep(0.5)  # let Pico boot

    # Start reader thread to display Pico output
    t = threading.Thread(target=reader_thread, args=(ser,), daemon=True)
    t.start()

    # Send MIDI Start
    ser.write(bytes([MIDI_START]))
    print(f"\n--- Sending MIDI clock at {bpm} BPM (Ctrl+C to stop) ---\n")

    try:
        clock_count = 0
        while True:
            ser.write(bytes([MIDI_CLOCK]))
            clock_count += 1
            if clock_count % CLOCKS_PER_BEAT == 0:
                beat = clock_count // CLOCKS_PER_BEAT
                print(f"[Beat {beat}]", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        ser.write(bytes([MIDI_STOP]))
        print("\n--- Stopped ---")
        ser.close()


if __name__ == "__main__":
    main()

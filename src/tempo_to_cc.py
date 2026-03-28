from midi_message import MidiMessage, CC

# Valeton GP-50 uses CC73 (MSB) + CC74 (value) for absolute BPM
# CC73=0, CC74=40-127 -> 40-127 BPM
# CC73=1, CC74=0-127  -> 128-255 BPM (value = BPM - 128)
# CC73=2, CC74=0-4    -> 256-260 BPM (value = BPM - 256)
_BPM_MIN = 40
_BPM_MAX = 260
_CC_TEMPO_MSB = 73
_CC_TEMPO_LSB = 74


class TempoHandler:
    def handle(self, _bpm):
        return []


class ValetonTempoHandler(TempoHandler):
    def __init__(self, channels=None):
        self.channels = channels if channels is not None else [0]

    def _bpm_to_cc(self, bpm):
        bpm = int(round(bpm))
        if bpm < _BPM_MIN or bpm > _BPM_MAX:
            return None
        if bpm <= 127:
            return 0, bpm
        elif bpm <= 255:
            return 1, bpm - 128
        else:
            return 2, bpm - 256

    def handle(self, bpm):
        result = self._bpm_to_cc(bpm)
        if result is None:
            return []
        msb, lsb = result
        msgs = []
        for ch in self.channels:
            msgs.append(MidiMessage(CC, ch, _CC_TEMPO_MSB, msb))
            msgs.append(MidiMessage(CC, ch, _CC_TEMPO_LSB, lsb))
        return msgs

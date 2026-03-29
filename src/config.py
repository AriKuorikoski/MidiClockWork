import json

_TRANSPORT_TYPES = {"uart", "ble_midi", "usb_midi", "serial"}
_WRITER_TYPES    = {"uart", "console"}

_TYPE_MAP = {
    "note_on":          0x90,
    "note_off":         0x80,
    "aftertouch":       0xA0,
    "cc":               0xB0,
    "pc":               0xC0,
    "channel_pressure": 0xD0,
    "pitch_bend":       0xE0,
    "clock":            0xF8,
    "start":            0xFA,
    "continue":         0xFB,
    "stop":             0xFC,
}


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, data):
        self.inputs  = [_parse_input(i)  for i in data.get("inputs",  [])]
        self.outputs = [_parse_output(o) for o in data.get("outputs", [])]

    @staticmethod
    def from_file(path):
        with open(path) as f:
            data = json.loads(f.read())
        return Config(data)

    @staticmethod
    def from_string(text):
        return Config(json.loads(text))


def _parse_input(d):
    if "name" not in d:
        raise ConfigError("input missing required field: name")
    transport = d.get("type", "uart")
    if transport not in _TRANSPORT_TYPES:
        raise ConfigError("unknown input transport type: " + transport)
    if transport == "uart":
        for key in ("uart", "rx_pin"):
            if key not in d:
                raise ConfigError("uart input missing required field: " + key)
    return {
        "name":      d["name"],
        "type":      transport,
        "uart":      d.get("uart"),
        "rx_pin":    d.get("rx_pin"),
        "filter":    _parse_input_filter(d.get("filter", {})),
    }


def _parse_output(d):
    if "name" not in d:
        raise ConfigError("output missing required field: name")
    transport = d.get("type", "uart")
    if transport not in _TRANSPORT_TYPES:
        raise ConfigError("unknown output transport type: " + transport)
    if transport == "uart":
        for key in ("uart", "tx_pin"):
            if key not in d:
                raise ConfigError("uart output missing required field: " + key)
    writer = d.get("writer", "uart")
    if writer not in _WRITER_TYPES:
        raise ConfigError("unknown writer type: " + writer)
    return {
        "name":          d["name"],
        "type":          transport,
        "uart":          d.get("uart"),
        "tx_pin":        d.get("tx_pin"),
        "writer":        writer,
        "filter":        _parse_output_filter(d.get("filter", {})),
        "tempo_handler": _parse_tempo_handler(d.get("tempo_handler")),
    }


def _parse_input_filter(d):
    if d is None:
        d = {}
    channels = d.get("channels")
    return {
        "channels":       set(channels) if channels is not None else None,
        "include_global": d.get("include_global", True),
    }


def _parse_output_filter(d):
    if d is None:
        d = {}
    types      = d.get("types")
    channels   = d.get("channels")
    cc_numbers = d.get("cc_numbers")
    return {
        "types":      _parse_types(types) if types is not None else None,
        "channels":   set(channels)   if channels   is not None else None,
        "cc_numbers": set(cc_numbers) if cc_numbers is not None else None,
    }


def _parse_types(type_list):
    result = set()
    for t in type_list:
        if t not in _TYPE_MAP:
            raise ConfigError("unknown message type: " + t)
        result.add(_TYPE_MAP[t])
    return result


def _parse_tempo_handler(d):
    if d is None:
        return None
    handler_type = d.get("type")
    if handler_type != "valeton":
        raise ConfigError("unknown tempo_handler type: " + str(handler_type))
    channels = d.get("channels", [0])
    return {
        "type":     "valeton",
        "channels": list(channels),
    }

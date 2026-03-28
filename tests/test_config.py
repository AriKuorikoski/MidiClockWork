import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from config import Config, ConfigError


# --- Helpers ---

def make_input(extra=None):
    d = {"name": "IN", "uart": 0, "rx_pin": 1}
    if extra:
        d.update(extra)
    return d

def make_output(extra=None):
    d = {"name": "OUT1", "uart": 1, "tx_pin": 4}
    if extra:
        d.update(extra)
    return d

def parse(inputs=None, outputs=None):
    return Config({"inputs": inputs or [], "outputs": outputs or []})


# --- Config structure ---

def test_empty_config():
    cfg = parse()
    assert cfg.inputs == []
    assert cfg.outputs == []

def test_minimal_input():
    cfg = parse(inputs=[make_input()])
    assert len(cfg.inputs) == 1
    assert cfg.inputs[0]["name"] == "IN"
    assert cfg.inputs[0]["uart"] == 0
    assert cfg.inputs[0]["rx_pin"] == 1

def test_minimal_output():
    cfg = parse(outputs=[make_output()])
    assert len(cfg.outputs) == 1
    assert cfg.outputs[0]["name"] == "OUT1"
    assert cfg.outputs[0]["uart"] == 1
    assert cfg.outputs[0]["tx_pin"] == 4


# --- Input filter ---

def test_input_filter_absent_defaults():
    cfg = parse(inputs=[make_input()])
    f = cfg.inputs[0]["filter"]
    assert f["channels"] is None
    assert f["include_global"] is True

def test_input_filter_empty_dict_defaults():
    cfg = parse(inputs=[make_input({"filter": {}})])
    f = cfg.inputs[0]["filter"]
    assert f["channels"] is None
    assert f["include_global"] is True

def test_input_filter_channels():
    cfg = parse(inputs=[make_input({"filter": {"channels": [0, 1]}})])
    assert cfg.inputs[0]["filter"]["channels"] == {0, 1}

def test_input_filter_include_global_false():
    cfg = parse(inputs=[make_input({"filter": {"include_global": False}})])
    assert cfg.inputs[0]["filter"]["include_global"] is False


# --- Output filter ---

def test_output_filter_absent_defaults():
    cfg = parse(outputs=[make_output()])
    f = cfg.outputs[0]["filter"]
    assert f["types"] is None
    assert f["channels"] is None
    assert f["cc_numbers"] is None

def test_output_filter_empty_dict_defaults():
    cfg = parse(outputs=[make_output({"filter": {}})])
    f = cfg.outputs[0]["filter"]
    assert f["types"] is None
    assert f["channels"] is None
    assert f["cc_numbers"] is None

def test_output_filter_types():
    cfg = parse(outputs=[make_output({"filter": {"types": ["clock", "cc"]}})])
    assert cfg.outputs[0]["filter"]["types"] == {0xF8, 0xB0}

def test_output_filter_channels():
    cfg = parse(outputs=[make_output({"filter": {"channels": [0, 2]}})])
    assert cfg.outputs[0]["filter"]["channels"] == {0, 2}

def test_output_filter_cc_numbers():
    cfg = parse(outputs=[make_output({"filter": {"cc_numbers": [7, 11]}})])
    assert cfg.outputs[0]["filter"]["cc_numbers"] == {7, 11}

def test_output_filter_all_types():
    all_types = ["note_on", "note_off", "aftertouch", "cc", "pc",
                 "channel_pressure", "pitch_bend", "clock", "start", "continue", "stop"]
    cfg = parse(outputs=[make_output({"filter": {"types": all_types}})])
    assert len(cfg.outputs[0]["filter"]["types"]) == 11

def test_unknown_type_raises():
    with pytest.raises(ConfigError):
        parse(outputs=[make_output({"filter": {"types": ["banjo"]}})])


# --- Tempo handler ---

def test_tempo_handler_null():
    cfg = parse(outputs=[make_output({"tempo_handler": None})])
    assert cfg.outputs[0]["tempo_handler"] is None

def test_tempo_handler_absent():
    cfg = parse(outputs=[make_output()])
    assert cfg.outputs[0]["tempo_handler"] is None

def test_tempo_handler_valeton_single_channel():
    cfg = parse(outputs=[make_output({"tempo_handler": {"type": "valeton", "channels": [0]}})])
    th = cfg.outputs[0]["tempo_handler"]
    assert th["type"] == "valeton"
    assert th["channels"] == [0]

def test_tempo_handler_valeton_multi_channel():
    cfg = parse(outputs=[make_output({"tempo_handler": {"type": "valeton", "channels": [0, 1, 2]}})])
    assert cfg.outputs[0]["tempo_handler"]["channels"] == [0, 1, 2]

def test_tempo_handler_valeton_default_channel():
    cfg = parse(outputs=[make_output({"tempo_handler": {"type": "valeton"}})])
    assert cfg.outputs[0]["tempo_handler"]["channels"] == [0]

def test_tempo_handler_unknown_type_raises():
    with pytest.raises(ConfigError):
        parse(outputs=[make_output({"tempo_handler": {"type": "unknown"}})])


# --- Missing required fields ---

def test_input_missing_name_raises():
    with pytest.raises(ConfigError):
        parse(inputs=[{"uart": 0, "rx_pin": 1}])

def test_input_missing_uart_raises():
    with pytest.raises(ConfigError):
        parse(inputs=[{"name": "IN", "rx_pin": 1}])

def test_input_missing_rx_pin_raises():
    with pytest.raises(ConfigError):
        parse(inputs=[{"name": "IN", "uart": 0}])

def test_output_missing_name_raises():
    with pytest.raises(ConfigError):
        parse(outputs=[{"uart": 1, "tx_pin": 4}])

def test_output_missing_uart_raises():
    with pytest.raises(ConfigError):
        parse(outputs=[{"name": "OUT1", "tx_pin": 4}])

def test_output_missing_tx_pin_raises():
    with pytest.raises(ConfigError):
        parse(outputs=[{"name": "OUT1", "uart": 1}])


# --- from_string ---

def test_from_string():
    text = '{"inputs": [{"name": "IN", "uart": 0, "rx_pin": 1}], "outputs": []}'
    cfg = Config.from_string(text)
    assert len(cfg.inputs) == 1
    assert cfg.inputs[0]["name"] == "IN"


# --- from_file ---

def test_from_file_missing_raises():
    with pytest.raises(OSError):
        Config.from_file("nonexistent_config_file.json")

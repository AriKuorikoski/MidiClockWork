import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from event_bus import EventBus


def test_subscribe_and_emit():
    bus = EventBus()
    received = []
    bus.on("test", lambda: received.append(True))
    bus.emit("test")
    assert received == [True]


def test_emit_with_args():
    bus = EventBus()
    received = []
    bus.on("tempo", lambda bpm: received.append(bpm))
    bus.emit("tempo", 120.5)
    assert received == [120.5]


def test_multiple_handlers():
    bus = EventBus()
    results = []
    bus.on("event", lambda: results.append("a"))
    bus.on("event", lambda: results.append("b"))
    bus.emit("event")
    assert results == ["a", "b"]


def test_unsubscribe():
    bus = EventBus()
    received = []
    handler = lambda: received.append(True)
    bus.on("test", handler)
    bus.off("test", handler)
    bus.emit("test")
    assert received == []


def test_emit_unknown_event():
    bus = EventBus()
    bus.emit("nonexistent")  # Should not raise

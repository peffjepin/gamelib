from collections import defaultdict

import pytest

from src.gamelib.events import (
    handler,
    Event,
    KeyedEvent,
    MessageBus,
    find_handlers,
    KeyDown,
    Keys,
    ModifierKeys,
)


class TestInternalIntegration:
    def test_normal_event_should_be_called(self):
        container = HandlerContainer()
        mb = MessageBus(find_handlers(container))

        mb.post_event(Event())

        assert 1 == container.calls[Event]

    def test_normal_event_should_not_be_called(self, example_event):
        container = HandlerContainer()
        mb = MessageBus(find_handlers(container))

        mb.post_event(example_event)

        assert 0 == container.calls[Event]

    def test_keyed_event_key_cant_be_none(self):
        container = HandlerContainer()
        mb = MessageBus(find_handlers(container))

        with pytest.raises(ValueError):
            mb.post_event(KeyedEvent())

    def test_keyed_event_should_be_called(self):
        container = HandlerContainer()
        mb = MessageBus(find_handlers(container))

        mb.post_event(KeyedEvent(), key="ABC")

        assert 1 == container.calls[KeyedEvent]

    def test_keyed_event_should_not_be_called(self):
        container = HandlerContainer()
        mb = MessageBus(find_handlers(container))

        mb.post_event(KeyedEvent(), key="CBA")

        assert 0 == container.calls[KeyedEvent]

    def test_key_handler_maps_with_keys(self):
        container = HandlerContainer()
        mb = MessageBus(find_handlers(container))

        mb.post_event(KeyDown(ModifierKeys(False, False, False)), key=Keys.J)

        assert 1 == container.calls[KeyDown]


class HandlerContainer:
    def __init__(self):
        self.calls = defaultdict(int)

    @handler(Event)
    def some_event_handler(self, event: Event):
        self.calls[Event] += 1

    @handler(KeyedEvent.ABC)
    def keyed_event_handler(self, event: KeyedEvent):
        self.calls[KeyedEvent] += 1

    @handler(KeyDown.J)
    def j_down_handler(self, event):
        self.calls[KeyDown] += 1

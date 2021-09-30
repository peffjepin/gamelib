from collections import defaultdict

from src.gamelib import KeyDown, ModifierKeys, Keys
from src.gamelib.events import (
    eventhandler,
    BaseEvent,
    MessageBus,
    find_handlers,
)


class TestInternalIntegration:
    def test_normal_event_should_be_called(self):
        container = HandlerContainer()
        mb = MessageBus(find_handlers(container))

        mb.post_event(BaseEvent())

        assert 1 == container.calls[BaseEvent]

    def test_normal_event_should_not_be_called(self):
        class OtherEvent(BaseEvent):
            pass

        container = HandlerContainer()
        mb = MessageBus(find_handlers(container))

        mb.post_event(OtherEvent())

        assert 0 == container.calls[BaseEvent]

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

    def test_register_marked_handlers_shorthand(self):
        container = HandlerContainer()
        mb1 = MessageBus(find_handlers(container))
        mb2 = MessageBus()

        mb2.register_marked_handlers(container)

        assert mb1.handlers == mb2.handlers

    def test_unregister_marked_handlers_shorthand(self):
        container = HandlerContainer()
        mb = MessageBus()
        mb.register_marked_handlers(container)

        mb.unregister_marked_handlers(container)
        mb.post_event(BaseEvent())
        mb.post_event(KeyedEvent(), key="ABC")
        mb.post_event(KeyDown(), key=Keys.J)

        assert not container.calls[BaseEvent]
        assert not container.calls[KeyedEvent]
        assert not container.calls[KeyDown]


class KeyedEvent(BaseEvent):
    pass


class HandlerContainer:
    def __init__(self):
        self.calls = defaultdict(int)

    @eventhandler(BaseEvent)
    def some_event_handler(self, event: BaseEvent):
        self.calls[BaseEvent] += 1

    @eventhandler(KeyedEvent.ABC)
    def keyed_event_handler(self, event: BaseEvent):
        self.calls[KeyedEvent] += 1

    @eventhandler(KeyDown.J)
    def j_down_handler(self, event):
        self.calls[KeyDown] += 1

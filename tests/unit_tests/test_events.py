from __future__ import annotations

import time
from multiprocessing.connection import Pipe

from src.gamelib import events
from src.gamelib.events import MessageBus, Event, handler, find_handlers


class SomeEvent(Event):
    pass


class SomeOtherEvent(Event):
    pass


class TestMessageBus:
    def test_calls_registered_callbacks_when_an_event_is_received(
        self, recorded_callback, example_event
    ):
        mb = MessageBus()
        mb.register(type(example_event), recorded_callback)

        mb.handle(example_event)

        assert recorded_callback.called

    def test_event_callback_receives_event_as_an_argument(
        self, recorded_callback, example_event
    ):
        mb = MessageBus()
        mb.register(type(example_event), recorded_callback)

        mb.handle(example_event)

        assert recorded_callback.args[0] is example_event

    def test_event_callback_stops_being_called_if_unregistered(
        self, recorded_callback, example_event
    ):
        mb = MessageBus()
        mb.register(type(example_event), recorded_callback)

        mb.unregister(type(example_event), recorded_callback)
        mb.handle(example_event)

        assert not recorded_callback.called

    def test_callback_is_not_called_upon_handling_a_different_type_of_event(
        self, example_event, recorded_callback
    ):
        class NotExampleEvent(Event):
            pass

        other_event = NotExampleEvent()
        mb = MessageBus()
        mb.register(type(example_event), recorded_callback)

        mb.handle(other_event)

        assert not recorded_callback.called

    def test_can_feed_events_into_a_serviced_pipe(self, example_event):
        a, b = Pipe()
        mb = MessageBus()
        mb.service_connection(a, [type(example_event)])

        mb.handle(example_event)

        assert b.recv() == example_event

    def test_will_handle_events_that_get_sent_through_a_serviced_pipe(
        self, example_event, recorded_callback
    ):
        a, b = Pipe()
        mb = MessageBus()
        mb.service_connection(a, [type(example_event)])
        mb.register(type(example_event), recorded_callback)

        b.send(example_event)
        i = 0
        while True:
            # wait up to 10ms for pipe to clear
            if not a.poll(0):
                break
            time.sleep(0.001)
            i += 1
            if i > 10:
                raise AssertionError("The Event is not being read from the pipe.")

        assert recorded_callback.called

    def test_a_pipe_stops_receiving_events_when_its_service_has_stopped(
        self, example_event
    ):
        a, b = Pipe()
        mb = MessageBus()
        mb.service_connection(a, [type(example_event)])

        mb.stop_connection_service(a)
        mb.handle(example_event)

        assert not b.poll(0)

    def test_initial_handlers_can_be_passed_to_init_method(
        self, example_event, recorded_callback
    ):
        handlers = {type(example_event): [recorded_callback]}
        mb = MessageBus(handlers)

        mb.handle(example_event)

        assert recorded_callback.called


class TestHandlerDecorator:
    class ExampleUsage:
        field: int = 0

        @handler(SomeEvent)
        def field_incrementer(self, event):
            self.field += 1

        @handler(SomeEvent)
        def some_dummy_method(self, event):
            pass

        @handler(SomeOtherEvent)
        def another_dummy_method(self, event):
            pass

    def test_handler_marks_methods_on_type_object(self):
        expected = {
            SomeEvent: [
                self.ExampleUsage.field_incrementer,
                self.ExampleUsage.some_dummy_method,
            ],
            SomeOtherEvent: [self.ExampleUsage.another_dummy_method],
        }
        assert expected == getattr(self.ExampleUsage, events._HANDLER_INJECTION_NAME)

    def test_methods_marked_as_handlers_can_be_called_normally(self):
        inst = self.ExampleUsage()
        inst.field_incrementer(SomeEvent())

        assert inst.field == 1

    def test_methods_discovered_by_events_module_are_bound_to_the_given_instance(self):
        inst = self.ExampleUsage()
        handlers = find_handlers(inst)
        for handler_ in handlers[SomeEvent]:
            handler_(SomeEvent())

        assert inst.field == 1
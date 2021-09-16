from __future__ import annotations

import abc
import multiprocessing as mp
from dataclasses import dataclass
from multiprocessing.connection import Connection
from typing import Type

from . import events


class StopEvent(events.Event):
    pass


@dataclass
class UpdateComplete(events.Event):
    system: Type[System]


class System(mp.Process):
    def __init__(self, conn: Connection):
        self.HANDLERS = events.find_handlers(self)
        self._conn = conn
        self._running = True
        super().__init__()

    def run(self):
        while self._running:
            while self._conn.poll(0):
                self._handle_incoming_event(self._conn.recv())

    @abc.abstractmethod
    def update(self):
        """Stub for subclass defined behavior."""

    def post_event(self, event: events.Event):
        """Send event back to main process."""
        self._conn.send(event)

    def _handle_incoming_event(self, event: events.Event):
        for handler in self.HANDLERS[type(event)]:
            handler(event)

    @events.handler(events.Update)
    def _update(self, event):
        self.update()
        self.post_event(UpdateComplete(type(self)))

    @events.handler(StopEvent)
    def _stop(self, event):
        self._running = False

"""Experimental bounded CPU pipeline; no GPU or ComfyUI integration.

Uses bounded queue and consumer acknowledgement. Producers block when capacity is reached.
This is not an inference acceleration implementation.
"""
from __future__ import annotations
from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar("T")
_SENTINEL = object()

@dataclass
class FlowStats:
    produced: int = 0
    consumed: int = 0

class BoundedFlow(Generic[T]):
    def __init__(self, max_items: int = 2):
        if max_items < 1:
            raise ValueError("max_items must be >= 1")
        self.max_items = max_items

    def run(self, source: Iterable[T], consume: Callable[[T], None]) -> FlowStats:
        queue: Queue[object] = Queue(maxsize=self.max_items)
        stats = FlowStats()
        failures: list[BaseException] = []

        def producer() -> None:
            try:
                for item in source:
                    queue.put(item)
                    stats.produced += 1
            except BaseException as exc:
                failures.append(exc)
            finally:
                queue.put(_SENTINEL)

        worker = Thread(target=producer, daemon=True)
        worker.start()
        try:
            while True:
                item = queue.get()
                try:
                    if item is _SENTINEL:
                        break
                    consume(item)  # type: ignore[arg-type]
                    stats.consumed += 1
                finally:
                    queue.task_done()
        finally:
            # A consumer failure may leave producer blocked on a full queue.
            # This minimal prototype should only be used with non-failing consumers.
            pass
        worker.join()
        if failures:
            raise RuntimeError("Flow producer failed") from failures[0]
        return stats

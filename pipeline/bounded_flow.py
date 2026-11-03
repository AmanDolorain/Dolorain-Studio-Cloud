"""Experimental bounded CPU producer/consumer pipeline (not GPU/ComfyUI integrated)."""
from __future__ import annotations
from dataclasses import dataclass
from queue import Queue, Full, Empty
from threading import Event, Thread
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar("T")
_END = object()

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
        q: Queue[object] = Queue(maxsize=self.max_items)
        stop = Event()
        stats = FlowStats()
        producer_error: list[BaseException] = []
        consumer_error: list[BaseException] = []

        def offer(value: object) -> bool:
            while not stop.is_set():
                try:
                    q.put(value, timeout=0.1)
                    return True
                except Full:
                    continue
            return False

        def produce() -> None:
            try:
                for item in source:
                    if stop.is_set() or not offer(item):
                        break
                    stats.produced += 1
            except BaseException as exc:
                producer_error.append(exc)
            finally:
                offer(_END)

        worker = Thread(target=produce, daemon=True)
        worker.start()
        try:
            while True:
                try:
                    item = q.get(timeout=0.1)
                except Empty:
                    if not worker.is_alive() and q.empty():
                        break
                    continue
                try:
                    if item is _END:
                        break
                    consume(item)  # type: ignore[arg-type]
                    stats.consumed += 1
                finally:
                    q.task_done()
        except BaseException as exc:
            consumer_error.append(exc)
            stop.set()
        finally:
            stop.set()
            worker.join(timeout=2.0)
        if consumer_error:
            raise RuntimeError("Flow consumer failed") from consumer_error[0]
        if producer_error:
            raise RuntimeError("Flow producer failed") from producer_error[0]
        return stats

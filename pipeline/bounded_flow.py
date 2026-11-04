"""Dependency-free, application-agnostic bounded CPU transport.

Item and byte budgets apply to queued AND currently consumed payloads until
consumer acknowledgement (return). A caller supplies size_of; no payload
inspection, GPU interception, graph parsing, or disk/network side effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from queue import Queue, Full, Empty
from threading import Condition, Event, Thread
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar('T')


@dataclass
class FlowStats:
    produced: int = 0
    consumed: int = 0
    peak_reserved_bytes: int = 0
    peak_reserved_items: int = 0
    backpressure_waits: int = 0


class BoundedFlow(Generic[T]):
    def __init__(self, max_items: int = 2, max_bytes: int = 8 * 1024 * 1024):
        if type(max_items) is not int or not 1 <= max_items <= 256:
            raise ValueError('max_items must be between 1 and 256')
        if type(max_bytes) is not int or max_bytes < 1:
            raise ValueError('max_bytes must be a positive integer')
        self.max_items = max_items
        self.max_bytes = max_bytes

    def run(self, source: Iterable[T], consume: Callable[[T], None],
            size_of: Callable[[T], int] | None = None) -> FlowStats:
        # With no size_of each packet is 1 accounted unit, NOT a byte estimate.
        # Callers moving actual buffers MUST supply their exact byte size.
        weight = size_of if size_of is not None else (lambda _item: 1)
        queue: Queue[tuple[T, int]] = Queue(maxsize=self.max_items)
        stop, producer_done = Event(), Event()
        changed = Condition()
        stats = FlowStats()
        reserved_bytes = reserved_items = 0
        producer_error: list[Exception] = []
        consumer_error: list[Exception] = []

        def release(nbytes: int) -> None:
            nonlocal reserved_bytes, reserved_items
            with changed:
                reserved_bytes -= nbytes
                reserved_items -= 1
                changed.notify_all()

        def produce() -> None:
            nonlocal reserved_bytes, reserved_items
            try:
                for item in source:
                    if stop.is_set():
                        break
                    nbytes = weight(item)
                    if type(nbytes) is not int or nbytes < 0:
                        raise ValueError('size_of must return a non-negative integer')
                    if nbytes > self.max_bytes:
                        raise ValueError('One packet exceeds the Box Engine byte budget')
                    with changed:
                        while not stop.is_set() and (reserved_bytes + nbytes > self.max_bytes or
                                                      reserved_items >= self.max_items):
                            stats.backpressure_waits += 1
                            changed.wait(0.05)
                        if stop.is_set():
                            break
                        reserved_bytes += nbytes
                        reserved_items += 1
                        stats.peak_reserved_bytes = max(stats.peak_reserved_bytes, reserved_bytes)
                        stats.peak_reserved_items = max(stats.peak_reserved_items, reserved_items)
                    sent = False
                    while not stop.is_set():
                        try:
                            queue.put((item, nbytes), timeout=0.05)
                            sent = True
                            stats.produced += 1
                            break
                        except Full:
                            stats.backpressure_waits += 1
                    if not sent:
                        release(nbytes)
                        break
            except Exception as exc:
                producer_error.append(exc)
            finally:
                producer_done.set()

        worker = Thread(target=produce, daemon=True)
        worker.start()
        try:
            while not (producer_done.is_set() and queue.empty()):
                try:
                    item, nbytes = queue.get(timeout=0.05)
                except Empty:
                    continue
                try:
                    consume(item)
                    stats.consumed += 1
                finally:
                    release(nbytes)  # ACK: consumer finished, then release buffer credit.
                    queue.task_done()
        except Exception as exc:
            consumer_error.append(exc)
        finally:
            stop.set()
            with changed:
                changed.notify_all()
            worker.join(timeout=2)
            # Fail closed: release credits for items never handed to the consumer.
            while True:
                try:
                    _, nbytes = queue.get_nowait()
                except Empty:
                    break
                release(nbytes)
                queue.task_done()
        if worker.is_alive():
            raise RuntimeError('Producer did not stop; source may be blocking')
        if consumer_error:
            raise RuntimeError('Flow consumer failed') from consumer_error[0]
        if producer_error:
            raise RuntimeError('Flow producer failed') from producer_error[0]
        return stats

"""Model-agnostic, byte-bounded, route-fair priority dispatcher.

Priorities: 0=low, 1=normal, 2=urgent. High priority has bounded bursts;
within a priority each opaque route is served round-robin. Credit is released
only on the consumer's synchronous acknowledgement (callback return).
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Condition, Event, Thread
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class Scheduled:
    payload: Any
    size_bytes: int
    route: str = ''
    priority: int = 1


@dataclass
class SchedulerStats:
    produced: int = 0
    consumed: int = 0
    peak_reserved_bytes: int = 0
    peak_reserved_items: int = 0
    backpressure_waits: int = 0
    priority_switches: int = 0


class FairScheduler:
    def __init__(self, max_items: int = 2, max_bytes: int = 8 * 1024 * 1024,
                 urgent_burst: int = 3):
        if type(max_items) is not int or not 1 <= max_items <= 256:
            raise ValueError('max_items must be between 1 and 256')
        if type(max_bytes) is not int or max_bytes < 1:
            raise ValueError('max_bytes must be positive')
        if type(urgent_burst) is not int or not 1 <= urgent_burst <= 100:
            raise ValueError('urgent_burst must be 1..100')
        self.max_items, self.max_bytes, self.urgent_burst = max_items, max_bytes, urgent_burst

    def run(self, source: Iterable[Scheduled], consume: Callable[[Scheduled], None]) -> SchedulerStats:
        changed, stop, producer_done = Condition(), Event(), Event()
        # priority -> route -> FIFO; route_order is per-priority round robin.
        queues: dict[int, dict[str, deque[Scheduled]]] = defaultdict(dict)
        route_order: dict[int, deque[str]] = defaultdict(deque)
        reserved_items = reserved_bytes = streak = 0
        last_priority: int | None = None
        producer_error: list[Exception] = []
        consumer_error: list[Exception] = []
        stats = SchedulerStats()

        def choose_priority() -> int:
            nonlocal streak, last_priority
            available = sorted((p for p, lanes in queues.items() if lanes), reverse=True)
            top = available[0]
            # After a bounded burst, give the lowest waiting class a turn.
            chosen = available[-1] if len(available) > 1 and last_priority == top and streak >= self.urgent_burst else top
            if chosen != last_priority:
                stats.priority_switches += 1
                streak = 0
            last_priority = chosen
            streak += 1
            return chosen

        def produce() -> None:
            nonlocal reserved_bytes, reserved_items
            try:
                for item in source:
                    if stop.is_set():
                        break
                    if not isinstance(item, Scheduled) or type(item.size_bytes) is not int or item.size_bytes < 0:
                        raise ValueError('Expected scheduled packet and non-negative byte size')
                    if type(item.priority) is not int or item.priority not in (0, 1, 2):
                        raise ValueError('Priority must be 0, 1 or 2')
                    if not isinstance(item.route, str) or len(item.route) > 256:
                        raise ValueError('Invalid opaque route')
                    if item.size_bytes > self.max_bytes:
                        raise ValueError('Scheduled item exceeds memory budget')
                    with changed:
                        while not stop.is_set() and (reserved_items >= self.max_items or
                                                     reserved_bytes + item.size_bytes > self.max_bytes):
                            stats.backpressure_waits += 1
                            changed.wait(timeout=0.05)
                        if stop.is_set():
                            break
                        reserved_items += 1
                        reserved_bytes += item.size_bytes
                        stats.peak_reserved_items = max(stats.peak_reserved_items, reserved_items)
                        stats.peak_reserved_bytes = max(stats.peak_reserved_bytes, reserved_bytes)
                        lane = queues[item.priority]
                        if item.route not in lane:
                            lane[item.route] = deque()
                            route_order[item.priority].append(item.route)
                        lane[item.route].append(item)
                        stats.produced += 1
                        changed.notify_all()
            except Exception as exc:
                producer_error.append(exc)
            finally:
                producer_done.set()
                with changed:
                    changed.notify_all()

        worker = Thread(target=produce, daemon=True)
        worker.start()
        try:
            while True:
                with changed:
                    while not any(queues.values()) and not producer_done.is_set():
                        changed.wait(timeout=0.05)
                    if not any(queues.values()) and producer_done.is_set():
                        break
                    priority = choose_priority()
                    route = route_order[priority].popleft()
                    item = queues[priority][route].popleft()
                    if queues[priority][route]:
                        route_order[priority].append(route)
                    else:
                        del queues[priority][route]
                try:
                    consume(item)
                    stats.consumed += 1
                finally:
                    with changed:
                        reserved_items -= 1
                        reserved_bytes -= item.size_bytes
                        changed.notify_all()
        except Exception as exc:
            consumer_error.append(exc)
        finally:
            stop.set()
            with changed:
                changed.notify_all()
            worker.join(timeout=2)
            with changed:
                queues.clear()
                route_order.clear()
        if worker.is_alive():
            raise RuntimeError('Scheduled producer did not stop')
        if consumer_error:
            raise RuntimeError('Scheduled consumer failed') from consumer_error[0]
        if producer_error:
            raise RuntimeError('Scheduled producer failed') from producer_error[0]
        return stats

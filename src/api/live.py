"""The synthetic "LIVE" venue.

A testing venue that is not stored in the database. Its occupancy is
estimated from a real `BluetoothCounter` scanning in a background
thread, combined with the current Manchester weather.
"""

from __future__ import annotations

import asyncio
import logging
import threading

from src.db import Venue

log = logging.getLogger(__name__)

LIVE_VENUE_NAME = "LIVE"
LIVE_VENUE_LOCATION = "Manchester"
LIVE_VENUE_CAPACITY = 100

LIVE_VENUE = Venue(LIVE_VENUE_NAME, LIVE_VENUE_LOCATION, LIVE_VENUE_CAPACITY)


def is_live_venue(name: str) -> bool:
    return name.casefold() == LIVE_VENUE_NAME.casefold()


class LiveBluetoothCounter:
    """Runs `BluetoothCounter.scan_loop` on a lazily started daemon thread.

    Scanning needs a Bluetooth adapter, which may be missing in dev or CI,
    so every failure degrades to a count of zero rather than raising.
    """

    def __init__(self) -> None:
        self._counter = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._failed = False

    @property
    def available(self) -> bool:
        return self._counter is not None and not self._failed

    @property
    def count(self) -> int:
        self.start()
        counter = self._counter
        return int(counter.count) if counter is not None else 0

    def start(self) -> None:
        """Begin scanning if it is not already running."""
        with self._lock:
            if self._thread is not None or self._failed:
                return

            try:
                from src.bluetooth import BluetoothCounter
            except Exception as exc:
                log.warning("Bluetooth scanning unavailable: %s", exc)
                self._failed = True
                return

            self._counter = BluetoothCounter()
            self._thread = threading.Thread(
                target=self._run, name="bluetooth-scan", daemon=True
            )
            self._thread.start()
            log.info("Bluetooth scanner started for the LIVE venue")

    def _run(self) -> None:
        try:
            asyncio.run(self._counter.scan_loop())
        except Exception as exc:
            log.warning("Bluetooth scan loop stopped: %s", exc)
            self._failed = True


live_counter = LiveBluetoothCounter()

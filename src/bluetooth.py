
import asyncio
import logging
import time
from bleak import BleakScanner

log = logging.getLogger(__name__)

# Configuration
MIN_PRESENCE = 20
MAX_GAP = 5
REMOVE_AFTER = MIN_PRESENCE
RSSI_THRESHOLD = -70

class BluetoothCounter:
    def __init__(self):
        self.count = 0
        self.devices = {}

    async def scan_loop(self):
        while True:

            now = time.monotonic()

            discovered = {}

            def detection_callback(device, advertisement_data):
                discovered[device.address] = {
                        "device": device,
                        "rssi": advertisement_data.rssi
                }

            scanner = BleakScanner(detection_callback)

            await scanner.start()
            await asyncio.sleep(2)
            await scanner.stop()

            # Process discovered devices
            in_range = 0

            for address, data in discovered.items():

                rssi = data["rssi"]

                if rssi < RSSI_THRESHOLD:
                    continue

                in_range += 1

                if address not in self.devices:
                    self.devices[address] = {
                        "first_seen": now,
                        "last_seen": now
                    }

                else:
                    record = self.devices[address]

                    # Reset presence timer if device disappeared
                    # for longer than the permitted gap
                    if now - record["last_seen"] > MAX_GAP:
                        record["first_seen"] = now

                    record["last_seen"] = now

            # Remove devices that have disappeared
            for address in list(self.devices.keys()):

                if now - self.devices[address]["last_seen"] > REMOVE_AFTER:
                    del self.devices[address]

            # Calculate qualifying devices
            current_count = sum(
                1 for record in self.devices.values()
                if (
                    now - record["first_seen"] >= MIN_PRESENCE
                    and now - record["last_seen"] <= REMOVE_AFTER
                )
            )

            self.count = current_count

            log.info(
                "[bluetooth] advertising=%d in-range=%d tracked=%d "
                "qualifying=%d rssi_threshold=%ddBm min_presence=%ds",
                len(discovered),
                in_range,
                len(self.devices),
                current_count,
                RSSI_THRESHOLD,
                MIN_PRESENCE,
            )

            await asyncio.sleep(1)

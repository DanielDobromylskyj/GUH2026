
import asyncio
import time
from bleak import BleakScanner

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
            for address, data in discovered.items():

                rssi = data["rssi"]

                if rssi < RSSI_THRESHOLD:
                    continue


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

            await asyncio.sleep(1)

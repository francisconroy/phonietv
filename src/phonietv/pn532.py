import logging
import threading
import time

import board
import busio
from adafruit_pn532.spi import PN532_SPI
from digitalio import DigitalInOut

from .event import PhonieTVEvent
from .nfc import parse_ntag213_text
from .threading import PhonieTVTask

LOGGER = logging.getLogger(__name__)
PN532_TASK_SLEEP_TIME_S = 0.1

NTAG213_DATA_OFFSET = 0x04


class Pn532Task(PhonieTVTask):
    def __init__(self, task_name: str, stop_event):
        super().__init__(task_name, stop_event)

        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs_pin = DigitalInOut(board.D4)
        self.pn532 = PN532_SPI(spi, cs_pin, debug=False)

        ic, ver, rev, support = self.pn532.firmware_version
        LOGGER.info(f"Found PN532 with firmware version: {ver}.{rev}")
        self.previous_text = ""

    def task_function(self, stop_event: threading.Event):
        while not stop_event.is_set():
            # Check for events
            # try:
            #     event_to_process = self.inbound_queue.get_nowait()
            #     LOGGER.info(f"got event {event_to_process.event_type}")
            #     if event_to_process.event_type == "play_media":
            #         # Handle play_media event
            #         pass
            #
            # except queue.Empty:
            #     pass

            if self._check_for_card():
                text = self._extract_string_data()
                if text:
                    LOGGER.debug(f"Extracted text: {text}")
                    if text != self.previous_text:
                        self.previous_text = text
                        # Send event to main thread
                        self.publish_event(
                            PhonieTVEvent("token_detected", text)
                        )
                        LOGGER.info(f"Text changed to: {text}")
            elif self.previous_text:
                LOGGER.debug(f"No card detected")
                self.previous_text = ""
                self.publish_event(PhonieTVEvent("token_removed", None))
            time.sleep(PN532_TASK_SLEEP_TIME_S)

    def _check_for_card(self) -> bool:
        uid = self.pn532.read_passive_target(timeout=0.5)
        if uid is not None:
            LOGGER.debug(f"Found card with UID: {[hex(i) for i in uid]}")
            return True
        return False

    def _extract_string_data(self) -> str:
        data = bytes()
        for i in range(35):
            block_data = self.pn532.ntag2xx_read_block(NTAG213_DATA_OFFSET + i)
            if block_data is None:
                LOGGER.debug(f"Failed to read block {NTAG213_DATA_OFFSET + i}")
                break
            data += block_data
            try:
                language, text = parse_ntag213_text(data)
                return text
            except ValueError as e:
                LOGGER.debug(f"Failed to parse NDEF text: {e}")
                pass
        LOGGER.error("Failed to extract string data from card, possibly because card was removed early.")
        return ""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # LOGGER.setLevel(level=logging.DEBUG)
    if True:
        stop_event = threading.Event()
        pn532_task = Pn532Task("test_pn532", stop_event)
        pn532_task.start()
    else:
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs_pin = DigitalInOut(board.D4)
        pn532 = PN532_SPI(spi, cs_pin, debug=False)

        ic, ver, rev, support = pn532.firmware_version
        print(f"Found PN532 with firmware version: {ver}.{rev}")

        # Configure PN532 to communicate with MiFare cards
        pn532.SAM_configuration()

        print("Waiting for RFID/NFC card to write to!")
        while True:
            # Check if a card is available to read
            uid = pn532.read_passive_target(timeout=0.5)
            print(".", end="")
            # Try again if no card is available.
            if uid is not None:
                break

        print("")
        print("Found card with UID:", [hex(i) for i in uid])

        # # Set 4 bytes of block to 0xFEEDBEEF
        # data = bytearray(4)
        # data[0:4] = b"\xfe\xed\xbe\xef"
        # # Write 4 byte block.
        # pn532.ntag2xx_write_block(6, data)
        # # Read block #6
        # ntag2xx_block = pn532.ntag2xx_read_block(4)
        data = bytes()
        for i in range(35):
            block_data = pn532.ntag2xx_read_block(NTAG213_DATA_OFFSET + i)
            if block_data is None:
                print(f"Failed to read block {NTAG213_DATA_OFFSET + i}")
                break
            data += block_data
        language, text = parse_ntag213_text(data)
        print(language, text)

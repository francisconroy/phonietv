import board
import busio
from digitalio import DigitalInOut

from adafruit_pn532.spi import PN532_SPI





if __name__ == "__main__":
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    cs_pin = DigitalInOut(board.D4)
    pn532 = PN532_SPI(spi, cs_pin, debug=False)

    ic, ver, rev, support = pn532.firmware_version
    print(f"Found PN532 with firmware version: {ver}.{rev}")

    # Configure PN532 to communicate with MiFare cards
    pn532.SAM_configuration()

    print("Waiting for RFID/NFC card...")
    while True:
        # Check if a card is available to read
        uid = pn532.read_passive_target(timeout=0.5)
        print(".", end="")
        # Try again if no card is available.
        if uid is None:
            continue
        print("Found card with UID:", [hex(i) for i in uid])
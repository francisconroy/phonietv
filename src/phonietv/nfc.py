def parse_ntag213_text(data: bytes):
    """
    Parse an NTAG213 memory dump and return (language, text).

    `data` should contain the raw 4-byte pages starting at the first page of user data

    Handles:
      - Type 2 Tag TLVs
      - Lock Control TLV (0x01)
      - NDEF Message TLV (0x03)
      - NDEF Text Records (TNF=0x01, type='T')
      - UTF-8 and UTF-16 text
    """



    pos = 0

    while pos < len(data):
        tlv_type = data[pos]
        pos += 1

        # NULL TLV: padding, no length/value
        if tlv_type == 0x00:
            continue

        # Terminator TLV
        if tlv_type == 0xFE:
            break

        if pos >= len(data):
            raise ValueError("Truncated TLV")

        length = data[pos]
        pos += 1

        # Extended TLV length
        if length == 0xFF:
            if pos + 2 > len(data):
                raise ValueError("Truncated extended TLV length")

            length = (data[pos] << 8) | data[pos + 1]
            pos += 2

        if pos + length > len(data):
            raise ValueError("Truncated TLV value")

        value = data[pos:pos + length]
        pos += length

        # NDEF Message TLV
        if tlv_type == 0x03:
            return parse_ndef_text(value)

        # Other TLVs (e.g. Lock Control 0x01) are ignored.

    raise ValueError("No NDEF Message TLV found")


def parse_ndef_text(ndef: bytes):
    """
    Parse a single NDEF Text Record.

    Returns:
        (language, text)
    """

    if len(ndef) < 4:
        raise ValueError("NDEF message too short")

    pos = 0

    header = ndef[pos]
    pos += 1

    # Header flags
    mb = bool(header & 0x80)       # Message Begin
    me = bool(header & 0x40)       # Message End
    cf = bool(header & 0x20)       # Chunk Flag
    sr = bool(header & 0x10)       # Short Record
    il = bool(header & 0x08)       # ID Length present
    tnf = header & 0x07            # Type Name Format

    if not mb:
        raise ValueError("Not the beginning of an NDEF message")

    if not me:
        raise ValueError("Multiple NDEF records not supported")

    if cf:
        raise ValueError("Chunked NDEF records not supported")

    if tnf != 0x01:
        raise ValueError(
            f"Not a Well-Known Type record (TNF={tnf})"
        )

    if pos >= len(ndef):
        raise ValueError("Missing type length")

    type_length = ndef[pos]
    pos += 1

    # Payload length is 1 byte for a Short Record,
    # otherwise 4 bytes.
    if sr:
        if pos >= len(ndef):
            raise ValueError("Missing payload length")

        payload_length = ndef[pos]
        pos += 1
    else:
        if pos + 4 > len(ndef):
            raise ValueError("Missing payload length")

        payload_length = int.from_bytes(
            ndef[pos:pos + 4], "big"
        )
        pos += 4

    # Optional ID length
    if il:
        if pos >= len(ndef):
            raise ValueError("Missing ID length")

        id_length = ndef[pos]
        pos += 1
    else:
        id_length = 0

    # Type
    if pos + type_length > len(ndef):
        raise ValueError("Truncated record type")

    record_type = ndef[pos:pos + type_length]
    pos += type_length

    if record_type != b"T":
        raise ValueError(
            f"Not a Text Record (type={record_type!r})"
        )

    # ID
    pos += id_length

    # Payload
    if pos + payload_length > len(ndef):
        raise ValueError("Truncated record payload")

    payload = ndef[pos:pos + payload_length]

    if not payload:
        raise ValueError("Empty Text Record payload")

    # Text Record status byte
    status = payload[0]

    # Bit 7: encoding
    encoding = "utf-16" if (status & 0x80) else "utf-8"

    # Bits 5-0: language code length
    language_length = status & 0x3F

    if 1 + language_length > len(payload):
        raise ValueError("Invalid language code length")

    # Language code
    language = payload[
        1:1 + language_length
    ].decode("ascii")

    # Text
    text_bytes = payload[1 + language_length:]

    try:
        text = text_bytes.decode(encoding)
    except UnicodeDecodeError as e:
        raise ValueError(
            f"Invalid {encoding} text"
        ) from e

    return language, text
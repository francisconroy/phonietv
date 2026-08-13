from unittest import TestCase

from phonietv.nfc import parse_ntag213_text


class TestNFC(TestCase):
    def test_parse_ntag213_text_with_full_page_dump(self):
        data = bytes(
            [
                0x01, 0x03, 0xA0, 0x0C,
                0x34, 0x03, 0x0D, 0xD1,
                0x01, 0x09, 0x54, 0x02,
                0x65, 0x6E, 0x47, 0x72,
                0x69, 0x6E, 0x63, 0x68,
                0xFE, 0x00, 0x00, 0x68,
            ]
        )

        language, text = parse_ntag213_text(data)

        self.assertEqual(language, "en")
        self.assertEqual(text, "Grinch")

    def test_parse_ntag213_text_stops_at_terminator(self):
        data = bytes(
            [
                0x01, 0x03, 0xA0, 0x0C,
                0x34, 0x03, 0x0D, 0xD1,
                0x01, 0x09, 0x54, 0x02,
                0x65, 0x6E, 0x47, 0x72,
                0x69, 0x6E, 0x63, 0x68,
                0xFE,
            ]
        )

        language, text = parse_ntag213_text(data)

        self.assertEqual(language, "en")
        self.assertEqual(text, "Grinch")

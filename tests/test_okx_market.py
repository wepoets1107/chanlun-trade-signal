import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from app.market.okx import OKXCandle, fetch_okx_candles, parse_okx_candle


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.payload


def okx_raw(ts):
    return [
        str(ts),
        "68000.0",
        "68100.0",
        "67900.0",
        "68050.0",
        "10.0",
        "680500.0",
        "680500.0",
        "1",
    ]


class OKXMarketTests(unittest.TestCase):
    def test_parse_okx_candle_maps_fields_and_confirms_closed_bar(self):
        raw = [
            "1710000000000",
            "68000.1",
            "68120.5",
            "67950.0",
            "68080.2",
            "123.4",
            "8390000.0",
            "8390000.0",
            "1",
        ]

        candle = parse_okx_candle(raw)

        self.assertIsInstance(candle, OKXCandle)
        self.assertEqual(candle.ts, 1710000000000)
        self.assertEqual(candle.open, 68000.1)
        self.assertEqual(candle.high, 68120.5)
        self.assertEqual(candle.low, 67950.0)
        self.assertEqual(candle.close, 68080.2)
        self.assertEqual(candle.volume, 123.4)
        self.assertTrue(candle.confirmed)

    def test_parse_okx_candle_rejects_incomplete_payload(self):
        with self.assertRaises(ValueError):
            parse_okx_candle(["1710000000000", "68000.1"])

    def test_fetch_okx_candles_paginates_up_to_1000(self):
        calls = []

        def fake_urlopen(request, timeout):
            url = request.full_url
            calls.append(url)
            query = parse_qs(urlparse(url).query)
            page_limit = int(query["limit"][0])
            offset = len(calls) - 1
            newest = 1_710_000_000_000 - offset * 300 * 60_000
            data = [okx_raw(newest - index * 60_000) for index in range(page_limit)]
            payload = ('{"code":"0","data":' + str(data).replace("'", '"') + "}").encode("utf-8")
            return FakeResponse(payload)

        with patch("app.market.okx.urlopen", fake_urlopen):
            candles = fetch_okx_candles("5m", limit=1000)

        self.assertEqual(len(candles), 1000)
        self.assertEqual(len(calls), 4)
        self.assertIn("/api/v5/market/candles", calls[0])
        self.assertIn("/api/v5/market/history-candles", calls[1])
        self.assertIn("after=", calls[1])


if __name__ == "__main__":
    unittest.main()

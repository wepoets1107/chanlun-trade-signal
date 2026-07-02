import unittest

from app.chanlun.engine import analyze_chanlun
from app.market.okx import OKXCandle


def candle(index, high, low, close=None):
    close_price = close if close is not None else (high + low) / 2
    return OKXCandle(
        ts=1_700_000_000_000 + index * 60_000,
        open=close_price,
        high=high,
        low=low,
        close=close_price,
        volume=100 + index,
        confirmed=True,
    )


def structured_candles():
    points = [
        (10, 5),
        (12, 7),
        (15, 10),
        (14, 9),
        (13, 8),
        (11, 6),
        (9, 3),
        (11, 5),
        (13, 7),
        (15, 9),
        (17, 12),
        (16, 10),
        (14, 8),
        (12, 6),
        (10, 4),
        (12, 6),
        (14, 8),
        (16, 10),
        (18, 13),
        (17, 11),
    ]
    return [candle(index, high, low) for index, (high, low) in enumerate(points)]


class ChanLunEngineTests(unittest.TestCase):
    def test_strict_fractals_ignore_loose_local_highs_and_lows(self):
        candles = [
            candle(0, 10, 5),
            candle(1, 12, 7),
            candle(2, 11, 6),  # loose local high only; low is not above both neighbors
            candle(3, 13, 8),
            candle(4, 9, 4),
            candle(5, 11, 6),
            candle(6, 8, 3),  # strict bottom
            candle(7, 10, 5),
            candle(8, 14, 9),  # strict top
            candle(9, 12, 7),
        ]

        result = analyze_chanlun(candles, timeframe="5m", min_stroke_bars=2)

        fractal_keys = [(item.index, item.kind, item.price) for item in result.fractals]
        self.assertNotIn((2, "top", 11), fractal_keys)
        self.assertEqual(
            fractal_keys,
            [(3, "top", 13), (6, "bottom", 3)],
        )

    def test_contained_candles_do_not_create_extra_fractals(self):
        candles = [
            candle(0, 10, 5),
            candle(1, 12, 7),
            candle(2, 11, 8),  # included by candle 1 while moving up
            candle(3, 13, 9),
            candle(4, 12, 6),
            candle(5, 10, 4),
            candle(6, 11, 5),  # included during the down leg
            candle(7, 9, 3),
            candle(8, 12, 6),
            candle(9, 14, 8),
            candle(10, 13, 7),
        ]

        result = analyze_chanlun(candles, timeframe="30m", min_stroke_bars=2)

        fractal_keys = [(item.index, item.kind, item.price) for item in result.fractals]
        self.assertEqual(fractal_keys, [(3, "top", 13), (7, "bottom", 3)])

    def test_analyze_chanlun_detects_fractals_strokes_and_center(self):
        candles = structured_candles()

        result = analyze_chanlun(candles, timeframe="5m", min_stroke_bars=2)

        self.assertGreaterEqual(len(result.fractals), 5)
        self.assertGreaterEqual(len(result.strokes), 4)
        self.assertEqual(result.strokes[0].start_price, 15)
        self.assertEqual(result.strokes[0].end_price, 3)
        self.assertGreaterEqual(len(result.centers), 1)
        self.assertEqual(result.segments, [])
        self.assertIn("segments", result.to_dict())
        self.assertIn("indicators", result.to_dict())
        self.assertEqual(len(result.indicators["macd"]), len(candles))
        self.assertEqual(len(result.indicators["volume"]), len(candles))
        self.assertIn("dif", result.indicators["macd"][-1])
        self.assertIn("dea", result.indicators["macd"][-1])
        self.assertIn("histogram", result.indicators["macd"][-1])
        self.assertIn(result.structure_state, {"uptrend", "downtrend", "range"})
        self.assertEqual(result.timeframe, "5m")

    def test_analyze_chanlun_exposes_chanlun_buy_sell_point_labels(self):
        candles = structured_candles()

        result = analyze_chanlun(candles, timeframe="4H", min_stroke_bars=2)
        labels = [point.label for point in result.buy_sell_points]

        self.assertTrue(set(labels).issubset({"买1", "买2", "买3", "卖1", "卖2", "卖3"}))
        if set(labels) & {"买2", "买3"}:
            self.assertIn("买1", labels)
        if set(labels) & {"卖2", "卖3"}:
            self.assertIn("卖1", labels)
        self.assertIn(result.signal_label, {"买1", "买2", "买3", "卖1", "卖2", "卖3", "无"})
        self.assertIn("buy_sell_points", result.to_dict())

    def test_analyze_chanlun_returns_insufficient_state_for_small_input(self):
        result = analyze_chanlun([candle(0, 10, 8), candle(1, 11, 9)], timeframe="30m")

        self.assertEqual(result.structure_state, "insufficient_data")
        self.assertEqual(result.fractals, [])
        self.assertEqual(result.strokes, [])


if __name__ == "__main__":
    unittest.main()

import unittest

from app.chanlun.kline import normalize_candles
from app.chanlun.fractal import detect_fractals
from app.chanlun.center import build_centers
from app.chanlun.bsp import classify_buy_sell_points, signal
from app.chanlun.models import Center, Fractal, Stroke
from app.chanlun.stroke import build_strokes
from tests.test_chanlun_engine import candle, structured_candles


class ChanLunLayerTests(unittest.TestCase):
    def test_kline_layer_merges_included_candles_with_source_indexes(self):
        candles = [
            candle(0, 10, 5),
            candle(1, 12, 7),
            candle(2, 11, 8),
            candle(3, 13, 9),
        ]

        normalized = normalize_candles(candles)

        self.assertEqual(len(normalized), 3)
        self.assertEqual((normalized[1].high, normalized[1].low), (12, 8))
        self.assertEqual(normalized[1].high_index, 1)
        self.assertEqual(normalized[1].low_index, 2)

    def test_fractal_and_stroke_layers_are_usable_without_engine(self):
        fractals = detect_fractals(structured_candles())
        strokes = build_strokes(fractals, min_stroke_bars=2)

        self.assertEqual([(item.index, item.kind) for item in fractals[:3]], [(2, "top"), (6, "bottom"), (10, "top")])
        self.assertEqual([(item.direction, item.start_index, item.end_index) for item in strokes[:3]], [
            ("down", 2, 6),
            ("up", 6, 10),
            ("down", 10, 14),
        ])

    def test_stroke_layer_rejects_price_direction_conflicts(self):
        fractals = [
            Fractal(0, 1000, "bottom", 100),
            Fractal(3, 1180, "top", 90),
            Fractal(6, 1360, "bottom", 70),
            Fractal(9, 1540, "top", 120),
        ]

        strokes = build_strokes(fractals, min_stroke_bars=2)

        self.assertEqual([(item.direction, item.start_price, item.end_price) for item in strokes], [
            ("down", 90, 70),
            ("up", 70, 120),
        ])

    def test_stroke_layer_uses_last_bottom_before_next_top(self):
        fractals = [
            Fractal(0, 1000, "top", 100),
            Fractal(3, 1180, "bottom", 90),
            Fractal(6, 1360, "bottom", 80),
            Fractal(9, 1540, "top", 110),
        ]

        strokes = build_strokes(fractals, min_stroke_bars=2)

        self.assertEqual([(item.direction, item.start_index, item.end_index, item.start_price, item.end_price) for item in strokes], [
            ("down", 0, 6, 100, 80),
            ("up", 6, 9, 80, 110),
        ])

    def test_stroke_layer_uses_last_top_before_next_bottom(self):
        fractals = [
            Fractal(0, 1000, "bottom", 50),
            Fractal(3, 1180, "top", 60),
            Fractal(6, 1360, "top", 70),
            Fractal(9, 1540, "bottom", 40),
        ]

        strokes = build_strokes(fractals, min_stroke_bars=2)

        self.assertEqual([(item.direction, item.start_index, item.end_index, item.start_price, item.end_price) for item in strokes], [
            ("up", 0, 6, 50, 70),
            ("down", 6, 9, 70, 40),
        ])

    def test_stroke_layer_keeps_strokes_connected_when_endpoint_extends(self):
        fractals = [
            Fractal(0, 1000, "top", 100),
            Fractal(3, 1180, "bottom", 90),
            Fractal(6, 1360, "top", 110),
            Fractal(9, 1540, "bottom", 80),
            Fractal(12, 1720, "bottom", 70),
            Fractal(15, 1900, "top", 120),
        ]

        strokes = build_strokes(fractals, min_stroke_bars=2)

        self.assertEqual([(item.direction, item.start_index, item.end_index, item.start_price, item.end_price) for item in strokes], [
            ("down", 0, 3, 100, 90),
            ("up", 3, 6, 90, 110),
            ("down", 6, 12, 110, 70),
            ("up", 12, 15, 70, 120),
        ])
        for previous, current in zip(strokes, strokes[1:]):
            self.assertEqual((previous.end_index, previous.end_price), (current.start_index, current.start_price))
            self.assertNotEqual(previous.direction, current.direction)

    def test_stroke_layer_extends_previous_endpoint_when_short_rebound_is_rejected(self):
        fractals = [
            Fractal(53, 1000, "bottom", 58978.2),
            Fractal(58, 1180, "top", 59677.0),
            Fractal(65, 1360, "bottom", 59174.3),
            Fractal(68, 1540, "top", 59552.8),
            Fractal(73, 1720, "bottom", 58858.6),
            Fractal(88, 1900, "top", 60209.9),
        ]

        strokes = build_strokes(fractals, min_stroke_bars=5)

        self.assertEqual([(item.direction, item.start_index, item.end_index, item.start_price, item.end_price) for item in strokes], [
            ("up", 53, 58, 58978.2, 59677.0),
            ("down", 58, 73, 59677.0, 58858.6),
            ("up", 73, 88, 58858.6, 60209.9),
        ])
        for previous, current in zip(strokes, strokes[1:]):
            self.assertEqual((previous.end_index, previous.end_price), (current.start_index, current.start_price))
            self.assertNotEqual(previous.direction, current.direction)

    def test_center_extends_right_until_first_detached_stroke(self):
        strokes = [
            Stroke(0, 4, "down", 100, 80, 100, 80),
            Stroke(4, 8, "up", 80, 95, 95, 80),
            Stroke(8, 12, "down", 95, 85, 95, 85),
            Stroke(12, 16, "up", 85, 92, 92, 85),
            Stroke(16, 20, "down", 105, 98, 105, 98),
        ]

        centers = build_centers(strokes)

        self.assertEqual(len(centers), 1)
        center = centers[0]
        self.assertEqual((center.start_index, center.end_index), (0, 16))
        self.assertEqual((center.low, center.high), (85, 92))
        self.assertEqual((center.entry_start_index, center.entry_end_index), (0, 4))
        self.assertEqual((center.exit_start_index, center.exit_end_index), (16, 20))
        self.assertEqual(center.exit_direction, "up")
        self.assertEqual(center.stroke_count, 4)

    def test_buy_and_sell_followups_require_first_point(self):
        center = Center(
            start_index=0,
            end_index=9,
            low=90,
            high=100,
            mid=95,
            exit_start_index=9,
            exit_end_index=12,
            exit_direction="up",
        )
        points = classify_buy_sell_points(
            [Fractal(15, 1900, "bottom", 111)],
            [
                Stroke(0, 3, "down", 110, 95, 110, 95),
                Stroke(3, 6, "up", 95, 105, 105, 95),
                Stroke(6, 9, "down", 105, 98, 105, 98),
                Stroke(12, 15, "down", 120, 111, 120, 111),
            ],
            [center],
            divergence=None,
            current_structure_state="uptrend_pullback",
        )

        self.assertEqual(points, [])

        center = Center(
            start_index=0,
            end_index=9,
            low=100,
            high=110,
            mid=105,
            exit_start_index=9,
            exit_end_index=12,
            exit_direction="down",
        )
        points = classify_buy_sell_points(
            [Fractal(15, 1900, "top", 95)],
            [
                Stroke(0, 3, "up", 90, 105, 105, 90),
                Stroke(3, 6, "down", 105, 98, 105, 98),
                Stroke(6, 9, "up", 98, 108, 108, 98),
                Stroke(12, 15, "up", 90, 95, 95, 90),
            ],
            [center],
            divergence=None,
            current_structure_state="downtrend_rebound",
        )

        self.assertEqual(points, [])

    def test_buy_and_sell_followups_must_come_after_first_point(self):
        early_buy_center = Center(
            start_index=0,
            end_index=9,
            low=90,
            high=100,
            mid=95,
            exit_start_index=9,
            exit_end_index=12,
            exit_direction="up",
        )
        latest_buy_context = Center(
            start_index=18,
            end_index=24,
            low=80,
            high=95,
            mid=87.5,
            exit_start_index=24,
            exit_end_index=30,
            exit_direction="down",
        )
        buy_points = classify_buy_sell_points(
            [
                Fractal(15, 1900, "bottom", 111),
                Fractal(30, 2800, "bottom", 70),
            ],
            [
                Stroke(0, 3, "down", 110, 95, 110, 95),
                Stroke(3, 6, "up", 95, 105, 105, 95),
                Stroke(6, 9, "down", 105, 98, 105, 98),
                Stroke(12, 15, "down", 120, 111, 120, 111),
                Stroke(24, 30, "down", 100, 70, 100, 70),
            ],
            [early_buy_center, latest_buy_context],
            divergence="bullish",
            current_structure_state="downtrend",
        )

        self.assertEqual([point.code for point in buy_points], ["B1"])

        early_sell_center = Center(
            start_index=0,
            end_index=9,
            low=100,
            high=110,
            mid=105,
            exit_start_index=9,
            exit_end_index=12,
            exit_direction="down",
        )
        latest_sell_context = Center(
            start_index=18,
            end_index=24,
            low=105,
            high=120,
            mid=112.5,
            exit_start_index=24,
            exit_end_index=30,
            exit_direction="up",
        )
        sell_points = classify_buy_sell_points(
            [
                Fractal(15, 1900, "top", 95),
                Fractal(30, 2800, "top", 130),
            ],
            [
                Stroke(0, 3, "up", 90, 105, 105, 90),
                Stroke(3, 6, "down", 105, 98, 105, 98),
                Stroke(6, 9, "up", 98, 108, 108, 98),
                Stroke(12, 15, "up", 90, 95, 95, 90),
                Stroke(24, 30, "up", 100, 130, 130, 100),
            ],
            [early_sell_center, latest_sell_context],
            divergence="bearish",
            current_structure_state="uptrend",
        )

        self.assertEqual([point.code for point in sell_points], ["S1"])

    def test_signal_does_not_promote_second_points_without_first_point(self):
        name, label, code, strength = signal(
            "uptrend_pullback",
            None,
            [],
            [Stroke(0, 4, "down", 100, 80, 100, 80)],
            [],
        )

        self.assertEqual((name, label, code, strength), ("neutral", "无", "NONE", 0.2))


if __name__ == "__main__":
    unittest.main()

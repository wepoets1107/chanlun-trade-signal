import unittest

from app.chanlun.models import ChanLunResult, Center, Fractal, Stroke
from app.risk.planner import build_risk_plan


class RiskPlannerTests(unittest.TestCase):
    def test_build_risk_plan_prefers_watch_when_signal_is_not_confirmed(self):
        analysis = ChanLunResult(
            timeframe="30m",
            structure_state="range",
            fractals=[],
            strokes=[],
            centers=[],
            divergence=None,
            signal="neutral",
            signal_strength=0.2,
            latest_close=68000.0,
        )

        plan = build_risk_plan(analysis, max_leverage=3, risk_per_trade=0.01)

        self.assertEqual(plan.action, "watch")
        self.assertEqual(plan.risk_level, "low")
        self.assertIn("结构信号不足", plan.reason)

    def test_build_risk_plan_creates_long_watch_plan_from_second_buy(self):
        analysis = ChanLunResult(
            timeframe="5m",
            structure_state="uptrend_pullback",
            fractals=[
                Fractal(index=10, ts=10, kind="bottom", price=66600.0),
                Fractal(index=20, ts=20, kind="top", price=69000.0),
            ],
            strokes=[
                Stroke(
                    start_index=10,
                    end_index=20,
                    direction="up",
                    start_price=66600.0,
                    end_price=69000.0,
                    high=69000.0,
                    low=66600.0,
                )
            ],
            centers=[
                Center(start_index=8, end_index=18, high=68400.0, low=67200.0, mid=67800.0)
            ],
            divergence="bullish",
            signal="second_buy_watch",
            signal_strength=0.74,
            latest_close=68100.0,
        )

        plan = build_risk_plan(analysis, max_leverage=3, risk_per_trade=0.01)

        self.assertEqual(plan.action, "watch_long")
        self.assertEqual(plan.risk_level, "medium")
        self.assertLess(plan.stop_loss, 68100.0)
        self.assertGreater(plan.entry_zone[1], plan.entry_zone[0])
        self.assertLessEqual(plan.suggested_leverage, 3)


if __name__ == "__main__":
    unittest.main()

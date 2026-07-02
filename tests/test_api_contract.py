import unittest

from app.services.analysis import build_multi_timeframe_payload


class APIContractTests(unittest.TestCase):
    def test_build_multi_timeframe_payload_has_fixed_btc_swap_defaults(self):
        payload = build_multi_timeframe_payload({})

        self.assertEqual(payload["symbol"], "BTC-USDT-SWAP")
        self.assertEqual(payload["inst_type"], "SWAP")
        self.assertEqual(payload["timeframes"], ["5m", "30m", "4H", "1D"])
        self.assertIn("analysis_id", payload)
        self.assertIn("timeframes_detail", payload)


if __name__ == "__main__":
    unittest.main()

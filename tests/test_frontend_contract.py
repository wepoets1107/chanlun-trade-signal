from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FrontendContractTests(unittest.TestCase):
    def test_legend_distinguishes_strokes_fractals_centers_and_buy_sell_points(self):
        html = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "app" / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "app" / "static" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("缠论交易工作台", html)
        self.assertNotIn("缠论 BTC 永续风险工作台", html)
        self.assertIn("/vendor/lightweight-charts.standalone.production.js", html)
        self.assertIn('/styles.css?v=', html)
        self.assertIn('/app.js?v=', html)
        self.assertIn('id="priceChart"', html)
        self.assertIn('id="volumeChart"', html)
        self.assertIn('id="macdChart"', html)
        self.assertIn('max="1000"', html)
        self.assertIn('value="1000"', html)
        self.assertNotIn("<canvas", html)
        self.assertIn("笔级中枢", html)
        self.assertIn("笔端顶/底", html)
        self.assertIn("买1/2/3 · 卖1/2/3", html)
        self.assertNotIn('<span><i class="signal"></i>信号</span>', html)
        self.assertIn("LightweightCharts.createChart", script)
        self.assertIn("initIndicatorCharts", script)
        self.assertIn("ensureRuntimeStyles", script)
        self.assertIn('setAttribute("class", "center-overlay")', script)
        self.assertIn("drawVolume", script)
        self.assertIn("drawMacd", script)
        self.assertIn("macdHistogramSeries", script)
        self.assertIn("macdDifSeries", script)
        self.assertIn("macdDeaSeries", script)
        self.assertIn("setMarkers", script)
        self.assertIn("buildStrokeEndpointMarkers", script)
        self.assertIn("drawCenterRectangle", script)
        self.assertIn("buildStrokeLineData", script)
        self.assertNotIn("analysis.segments", script)
        self.assertIn("return analysis.strokes || [];", script)
        self.assertNotIn("analysis.fractals || []", script)
        self.assertNotIn(".slice(-18)", script)
        self.assertNotIn(".slice(-6)", script)
        self.assertNotIn(".slice(-24)", script)
        self.assertIn('color: "#9aa3ad"', script)
        self.assertIn("drawBuySellPoints", script)
        self.assertNotIn("getContext", script)
        self.assertIn(".center-overlay", styles)
        self.assertIn(".indicator-chart", styles)
        self.assertIn("grid-column: 1 / -1", styles)
        self.assertIn("grid-row: 1", styles)
        self.assertIn(".controls {\n  grid-column: 1", styles)
        self.assertIn(".conclusion {\n  grid-column: 2", styles)
        self.assertIn("height: 680px", styles)
        for label in ["买1", "买2", "买3", "卖1", "卖2", "卖3"]:
            self.assertIn(label, script)


if __name__ == "__main__":
    unittest.main()

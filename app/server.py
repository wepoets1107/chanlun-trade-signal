from __future__ import annotations

from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app import __version__
from app.market.okx import DEFAULT_SYMBOL, DEFAULT_TIMEFRAMES, fetch_okx_candles
from app.services.analysis import DEFAULT_LIMITS, build_multi_timeframe_payload


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
HOST = "127.0.0.1"
PORT = 8040


class ChanLunHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self._json(
                {
                    "ok": True,
                    "service": "ChanLun BTC Risk MCP Workbench",
                    "version": __version__,
                    "host": HOST,
                    "port": PORT,
                    "symbol": DEFAULT_SYMBOL,
                    "timeframes": DEFAULT_TIMEFRAMES,
                    "mode": "read_only",
                }
            )
            return
        if parsed.path == "/api/market/candles":
            self._handle_candles(parsed.query)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/analyze/multi-timeframe":
            self._handle_multi_timeframe()
            return
        if parsed.path == "/api/analyze":
            self._handle_analyze()
            return
        self._json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_candles(self, query: str):
        params = parse_qs(query)
        bar = (params.get("bar") or ["5m"])[0]
        limit = int((params.get("limit") or [str(DEFAULT_LIMITS.get(bar, 300))])[0])
        try:
            candles = fetch_okx_candles(bar=bar, limit=limit)
            self._json(
                {
                    "symbol": DEFAULT_SYMBOL,
                    "bar": bar,
                    "candles": [item.to_dict() for item in candles],
                }
            )
        except Exception as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)

    def _handle_analyze(self):
        body = self._read_json()
        timeframe = body.get("timeframe") or "5m"
        try:
            candles = fetch_okx_candles(timeframe, limit=int(body.get("limit") or DEFAULT_LIMITS.get(timeframe, 300)))
            payload = build_multi_timeframe_payload(
                {
                    "symbol": DEFAULT_SYMBOL,
                    "timeframes": [timeframe],
                    "candles_by_timeframe": {timeframe: candles},
                }
            )
            self._json(payload["timeframes_detail"][0])
        except Exception as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)

    def _handle_multi_timeframe(self):
        body = self._read_json()
        try:
            payload = build_multi_timeframe_payload(
                {
                    "symbol": DEFAULT_SYMBOL,
                    "timeframes": body.get("timeframes") or DEFAULT_TIMEFRAMES,
                    "fetch": True,
                    "limit": int(body.get("limit") or 1000),
                }
            )
            self._json(payload)
        except Exception as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        data = self.rfile.read(length).decode("utf-8")
        return json.loads(data or "{}")

    def _json(self, data: dict, status: HTTPStatus = HTTPStatus.OK):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


def run():
    with ThreadingHTTPServer((HOST, PORT), ChanLunHandler) as server:
        print(f"ChanLun BTC Risk MCP Workbench running at http://{HOST}:{PORT}/")
        server.serve_forever()


if __name__ == "__main__":
    run()

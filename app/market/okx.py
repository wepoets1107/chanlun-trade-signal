from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


OKX_BASE_URL = "https://www.okx.com"
DEFAULT_SYMBOL = "BTC-USDT-SWAP"
DEFAULT_TIMEFRAMES = ["5m", "30m", "4H", "1D"]
MAX_CANDLE_LIMIT = 1000
OKX_PAGE_LIMIT = 300


@dataclass(frozen=True)
class OKXCandle:
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    confirmed: bool

    def to_dict(self) -> dict:
        return asdict(self)


def parse_okx_candle(raw: list[str]) -> OKXCandle:
    if len(raw) < 9:
        raise ValueError("OKX candle payload must contain at least 9 fields")
    return OKXCandle(
        ts=int(raw[0]),
        open=float(raw[1]),
        high=float(raw[2]),
        low=float(raw[3]),
        close=float(raw[4]),
        volume=float(raw[5]),
        confirmed=raw[8] == "1",
    )


def fetch_okx_candles(
    bar: str,
    limit: int = 300,
    symbol: str = DEFAULT_SYMBOL,
    history: bool = False,
) -> list[OKXCandle]:
    if bar not in DEFAULT_TIMEFRAMES:
        raise ValueError(f"Unsupported timeframe: {bar}")
    bounded_limit = max(1, min(int(limit), MAX_CANDLE_LIMIT))
    candles: list[OKXCandle] = []
    seen_ts: set[int] = set()
    after: int | None = None
    while len(candles) < bounded_limit:
        page_limit = min(OKX_PAGE_LIMIT, bounded_limit - len(candles))
        page = fetch_okx_candle_page(
            bar=bar,
            limit=page_limit,
            symbol=symbol,
            history=history or after is not None,
            after=after,
        )
        if not page:
            break
        for item in page:
            if item.ts not in seen_ts:
                candles.append(item)
                seen_ts.add(item.ts)
        oldest_ts = min(item.ts for item in page)
        if len(page) < page_limit or after == oldest_ts:
            break
        after = oldest_ts
    return sorted(candles, key=lambda item: item.ts)


def fetch_okx_candle_page(
    bar: str,
    limit: int,
    symbol: str,
    history: bool,
    after: int | None = None,
) -> list[OKXCandle]:
    path = "/api/v5/market/history-candles" if history else "/api/v5/market/candles"
    query_items = {"instId": symbol, "bar": bar, "limit": str(limit)}
    if after is not None:
        query_items["after"] = str(after)
    query = urlencode(query_items)
    request = Request(
        f"{OKX_BASE_URL}{path}?{query}",
        headers={"User-Agent": "chanlun-risk-mcp/0.1"},
    )
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("code") != "0":
        raise RuntimeError(payload.get("msg") or "OKX market API returned an error")
    candles = [parse_okx_candle(item) for item in payload.get("data", [])]
    return sorted(candles, key=lambda item: item.ts)

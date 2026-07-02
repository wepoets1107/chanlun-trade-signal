from __future__ import annotations

from app.market.okx import OKXCandle


def build_indicators(candles: list[OKXCandle]) -> dict:
    return {
        "macd": build_macd(candles),
        "volume": build_volume(candles),
    }


def build_macd(
    candles: list[OKXCandle],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> list[dict]:
    fast = None
    slow = None
    dea = 0.0
    fast_alpha = 2 / (fast_period + 1)
    slow_alpha = 2 / (slow_period + 1)
    signal_alpha = 2 / (signal_period + 1)
    points = []
    for index, candle in enumerate(candles):
        close = candle.close
        fast = close if fast is None else fast + fast_alpha * (close - fast)
        slow = close if slow is None else slow + slow_alpha * (close - slow)
        dif = fast - slow
        dea = dif if index == 0 else dea + signal_alpha * (dif - dea)
        histogram = (dif - dea) * 2
        points.append(
            {
                "index": index,
                "ts": candle.ts,
                "dif": round(dif, 8),
                "dea": round(dea, 8),
                "histogram": round(histogram, 8),
            }
        )
    return points


def build_volume(candles: list[OKXCandle]) -> list[dict]:
    points = []
    for index, candle in enumerate(candles):
        points.append(
            {
                "index": index,
                "ts": candle.ts,
                "value": candle.volume,
                "color": "#22c55e" if candle.close >= candle.open else "#ef4444",
            }
        )
    return points

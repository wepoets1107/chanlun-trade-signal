from __future__ import annotations

from app.chanlun.kline import normalize_candles
from app.chanlun.models import Fractal
from app.market.okx import OKXCandle


MIN_EFFECTIVE_FRACTAL_BARS = 3


def detect_fractals(candles: list[OKXCandle], min_effective_bars: int = MIN_EFFECTIVE_FRACTAL_BARS) -> list[Fractal]:
    normalized = normalize_candles(candles)
    fractals: list[Fractal] = []
    for index in range(1, len(normalized) - 1):
        prev_item = normalized[index - 1]
        item = normalized[index]
        next_item = normalized[index + 1]
        if (
            item.high > prev_item.high
            and item.high > next_item.high
            and item.low > prev_item.low
            and item.low > next_item.low
        ):
            source = candles[item.high_index]
            fractals.append(Fractal(index=item.high_index, ts=source.ts, kind="top", price=item.high))
        elif (
            item.low < prev_item.low
            and item.low < next_item.low
            and item.high < prev_item.high
            and item.high < next_item.high
        ):
            source = candles[item.low_index]
            fractals.append(Fractal(index=item.low_index, ts=source.ts, kind="bottom", price=item.low))
    return filter_effective_fractals(fractals, min_effective_bars)


def dedupe_adjacent_fractals(fractals: list[Fractal]) -> list[Fractal]:
    result: list[Fractal] = []
    for item in fractals:
        if not result:
            result.append(item)
            continue
        last = result[-1]
        if item.kind != last.kind:
            result.append(item)
            continue
        result[-1] = more_extreme(last, item)
    return result


def filter_effective_fractals(fractals: list[Fractal], min_bars: int) -> list[Fractal]:
    result: list[Fractal] = []
    for item in dedupe_adjacent_fractals(fractals):
        if not result:
            result.append(item)
            continue
        last = result[-1]
        if item.kind == last.kind:
            result[-1] = more_extreme(last, item)
            continue
        if item.index - last.index >= min_bars:
            result.append(item)
    return result


def more_extreme(left: Fractal, right: Fractal) -> Fractal:
    if left.kind == "top":
        return right if right.price > left.price else left
    return right if right.price < left.price else left

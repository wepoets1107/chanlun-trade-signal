from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.market.okx import OKXCandle


Trend = Literal["up", "down"]


@dataclass(frozen=True)
class NormalizedCandle:
    start_index: int
    end_index: int
    high: float
    low: float
    high_index: int
    low_index: int
    ts: int


def normalize_candles(candles: list[OKXCandle]) -> list[NormalizedCandle]:
    normalized: list[NormalizedCandle] = []
    for index, candle in enumerate(candles):
        item = NormalizedCandle(
            start_index=index,
            end_index=index,
            high=candle.high,
            low=candle.low,
            high_index=index,
            low_index=index,
            ts=candle.ts,
        )
        if not normalized:
            normalized.append(item)
            continue
        last = normalized[-1]
        if is_included(last, item):
            direction = normalization_direction(normalized, item)
            normalized[-1] = merge_included(last, item, direction)
        else:
            normalized.append(item)
    return normalized


def is_included(left: NormalizedCandle, right: NormalizedCandle) -> bool:
    left_contains_right = left.high >= right.high and left.low <= right.low
    right_contains_left = right.high >= left.high and right.low <= left.low
    return left_contains_right or right_contains_left


def normalization_direction(normalized: list[NormalizedCandle], incoming: NormalizedCandle) -> Trend:
    if len(normalized) >= 2:
        previous = normalized[-2]
        current = normalized[-1]
        if current.high > previous.high and current.low > previous.low:
            return "up"
        if current.high < previous.high and current.low < previous.low:
            return "down"
    current = normalized[-1]
    return "up" if incoming.high >= current.high else "down"


def merge_included(left: NormalizedCandle, right: NormalizedCandle, direction: Trend) -> NormalizedCandle:
    if direction == "up":
        high, high_index = pick_high(left, right)
        low, low_index = pick_higher_low(left, right)
    else:
        high, high_index = pick_lower_high(left, right)
        low, low_index = pick_low(left, right)
    return NormalizedCandle(
        start_index=left.start_index,
        end_index=right.end_index,
        high=high,
        low=low,
        high_index=high_index,
        low_index=low_index,
        ts=right.ts,
    )


def pick_high(left: NormalizedCandle, right: NormalizedCandle) -> tuple[float, int]:
    return (right.high, right.high_index) if right.high >= left.high else (left.high, left.high_index)


def pick_low(left: NormalizedCandle, right: NormalizedCandle) -> tuple[float, int]:
    return (right.low, right.low_index) if right.low <= left.low else (left.low, left.low_index)


def pick_higher_low(left: NormalizedCandle, right: NormalizedCandle) -> tuple[float, int]:
    return (right.low, right.low_index) if right.low >= left.low else (left.low, left.low_index)


def pick_lower_high(left: NormalizedCandle, right: NormalizedCandle) -> tuple[float, int]:
    return (right.high, right.high_index) if right.high <= left.high else (left.high, left.high_index)

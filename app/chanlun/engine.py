from __future__ import annotations

from app.chanlun.bsp import classify_buy_sell_points, detect_divergence, signal, structure_state
from app.chanlun.center import build_centers
from app.chanlun.fractal import detect_fractals
from app.chanlun.indicator import build_indicators
from app.chanlun.models import ChanLunResult
from app.chanlun.stroke import build_strokes
from app.market.okx import OKXCandle


def analyze_chanlun(
    candles: list[OKXCandle],
    timeframe: str,
    min_stroke_bars: int = 5,
) -> ChanLunResult:
    closed = [item for item in candles if item.confirmed]
    if len(closed) < 5:
        latest = closed[-1].close if closed else 0.0
        return ChanLunResult(
            timeframe,
            "insufficient_data",
            [],
            [],
            [],
            None,
            "neutral",
            0.0,
            latest,
            indicators=build_indicators(closed),
        )

    indicators = build_indicators(closed)
    fractals = detect_fractals(closed)
    strokes = build_strokes(fractals, min_stroke_bars)
    centers = build_centers(strokes)
    divergence = detect_divergence(closed, strokes, indicators)
    current_structure_state = structure_state(strokes, centers)
    buy_sell_points = classify_buy_sell_points(fractals, strokes, centers, divergence, current_structure_state)
    signal_name, label, code, strength = signal(
        current_structure_state,
        divergence,
        centers,
        strokes,
        buy_sell_points,
    )

    return ChanLunResult(
        timeframe=timeframe,
        structure_state=current_structure_state,
        fractals=fractals,
        strokes=strokes,
        centers=centers,
        divergence=divergence,
        signal=signal_name,
        signal_strength=strength,
        latest_close=closed[-1].close,
        segments=[],
        buy_sell_points=buy_sell_points,
        indicators=indicators,
        signal_label=label,
        signal_code=code,
    )

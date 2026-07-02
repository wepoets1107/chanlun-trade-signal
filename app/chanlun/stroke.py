from __future__ import annotations

from app.chanlun.fractal import more_extreme
from app.chanlun.models import Fractal, Stroke


def build_strokes(fractals: list[Fractal], min_stroke_bars: int) -> list[Stroke]:
    strokes: list[Stroke] = []
    anchor: Fractal | None = None
    candidate: Fractal | None = None
    index = 0

    while index < len(fractals):
        item = fractals[index]
        if anchor is None:
            anchor = item
            index += 1
            continue

        if item.kind != anchor.kind:
            candidate = more_extreme_or_later(candidate, item) if candidate else item
            index += 1
            continue

        if candidate is None:
            anchor = move_anchor(anchor, item, strokes)
            index += 1
            continue

        if can_build_stroke(anchor, candidate, min_stroke_bars):
            strokes.append(make_stroke(anchor, candidate))
            anchor = candidate
            candidate = None
            continue

        if strokes:
            anchor = move_anchor(anchor, item, strokes)
            candidate = None
            index += 1
            continue

        if can_build_stroke(candidate, item, min_stroke_bars):
            anchor = candidate
            candidate = None
            continue

        anchor = more_extreme_or_later(anchor, item)
        candidate = None
        index += 1

    if anchor and candidate and can_build_stroke(anchor, candidate, min_stroke_bars):
        strokes.append(make_stroke(anchor, candidate))
    return strokes


def more_extreme_or_later(left: Fractal, right: Fractal) -> Fractal:
    selected = more_extreme(left, right)
    if selected.price == left.price and selected.price == right.price:
        return right
    return selected


def move_anchor(anchor: Fractal, item: Fractal, strokes: list[Stroke]) -> Fractal:
    updated = more_extreme_or_later(anchor, item)
    if updated == anchor:
        return anchor
    if strokes and strokes[-1].end_index == anchor.index:
        strokes[-1] = replace_stroke_end(strokes[-1], updated)
    return updated


def replace_stroke_end(stroke: Stroke, endpoint: Fractal) -> Stroke:
    return Stroke(
        start_index=stroke.start_index,
        end_index=endpoint.index,
        direction=stroke.direction,
        start_price=stroke.start_price,
        end_price=endpoint.price,
        high=max(stroke.start_price, endpoint.price),
        low=min(stroke.start_price, endpoint.price),
    )


def can_build_stroke(anchor: Fractal, item: Fractal, min_stroke_bars: int) -> bool:
    if anchor.kind == item.kind:
        return False
    if item.index - anchor.index < min_stroke_bars:
        return False
    return is_price_direction_valid(anchor, item, stroke_direction(anchor, item))


def make_stroke(anchor: Fractal, item: Fractal) -> Stroke:
    direction = stroke_direction(anchor, item)
    return Stroke(
        start_index=anchor.index,
        end_index=item.index,
        direction=direction,
        start_price=anchor.price,
        end_price=item.price,
        high=max(anchor.price, item.price),
        low=min(anchor.price, item.price),
    )


def stroke_direction(anchor: Fractal, item: Fractal) -> str:
    return "up" if anchor.kind == "bottom" and item.kind == "top" else "down"


def is_price_direction_valid(anchor: Fractal, item: Fractal, direction: str) -> bool:
    if direction == "up":
        return anchor.price < item.price
    return anchor.price > item.price

from __future__ import annotations

from app.chanlun.models import Segment, Stroke


def build_segments(strokes: list[Stroke], min_segment_strokes: int = 3) -> list[Segment]:
    if min_segment_strokes < 3 or len(strokes) < min_segment_strokes:
        return []

    segments: list[Segment] = []
    for start in range(0, len(strokes) - min_segment_strokes + 1):
        group = strokes[start : start + min_segment_strokes]
        if group[0].direction != group[-1].direction:
            continue
        first = group[0]
        last = group[-1]
        segments.append(
            Segment(
                start_index=first.start_index,
                end_index=last.end_index,
                direction=first.direction,
                start_price=first.start_price,
                end_price=last.end_price,
                high=max(item.high for item in group),
                low=min(item.low for item in group),
                stroke_count=len(group),
            )
        )
    return merge_adjacent_segments(segments)


def merge_adjacent_segments(segments: list[Segment]) -> list[Segment]:
    result: list[Segment] = []
    for item in segments:
        if not result:
            result.append(item)
            continue
        last = result[-1]
        if item.direction != last.direction:
            result.append(item)
            continue
        if item.direction == "up" and item.high > last.high:
            result[-1] = extend_segment(last, item)
        elif item.direction == "down" and item.low < last.low:
            result[-1] = extend_segment(last, item)
    return result


def extend_segment(left: Segment, right: Segment) -> Segment:
    return Segment(
        start_index=left.start_index,
        end_index=right.end_index,
        direction=left.direction,
        start_price=left.start_price,
        end_price=right.end_price,
        high=max(left.high, right.high),
        low=min(left.low, right.low),
        stroke_count=max(left.stroke_count, right.stroke_count),
    )

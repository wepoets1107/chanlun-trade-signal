from __future__ import annotations

from app.chanlun.models import Center, Stroke


def build_centers(strokes: list[Stroke]) -> list[Center]:
    centers: list[Center] = []
    index = 0
    while index <= len(strokes) - 3:
        group = strokes[index : index + 3]
        low = max(item.low for item in group)
        high = min(item.high for item in group)
        if low > high:
            index += 1
            continue

        end_stroke = group[-1]
        stroke_count = 3
        exit_stroke: Stroke | None = None
        exit_direction = None
        cursor = index + 3
        while cursor < len(strokes):
            candidate = strokes[cursor]
            if candidate.low <= high and candidate.high >= low:
                low = max(low, candidate.low)
                high = min(high, candidate.high)
                end_stroke = candidate
                stroke_count += 1
                cursor += 1
                continue
            exit_stroke = candidate
            exit_direction = "up" if candidate.low > high else "down"
            break

        centers.append(
            Center(
                start_index=group[0].start_index,
                end_index=end_stroke.end_index,
                high=high,
                low=low,
                mid=(high + low) / 2,
                entry_start_index=group[0].start_index,
                entry_end_index=group[0].end_index,
                exit_start_index=exit_stroke.start_index if exit_stroke else None,
                exit_end_index=exit_stroke.end_index if exit_stroke else None,
                exit_direction=exit_direction,
                stroke_count=stroke_count,
            )
        )
        index = cursor if exit_stroke else len(strokes)
    return centers

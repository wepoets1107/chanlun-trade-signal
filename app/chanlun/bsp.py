from __future__ import annotations

from app.chanlun.models import BuySellPoint, Center, Fractal, Stroke
from app.market.okx import OKXCandle


# 买卖点检测参数
MAX_BS2_RATE = 1.0  # 二买/二卖最大回撤率（回调笔range / 突破笔range），0.618为黄金分割
MIN_DIVERGENCE_RATE = 1.0  # 一买/一卖最大力度比（离开笔range / 进入笔range），<此值视为背驰


# ── 背离检测（保留作为辅助信号，不再作为买卖点唯一入口） ──

def detect_divergence(candles: list[OKXCandle], strokes: list[Stroke], indicators: dict | None = None) -> str | None:
    if len(strokes) < 3:
        return None
    last = strokes[-1]
    previous = next((item for item in reversed(strokes[:-1]) if item.direction == last.direction), None)
    if previous is None:
        return None
    if last.direction == "down" and last.low < previous.low:
        return "bullish" if is_stroke_power_weaker(last, previous, indicators) else None
    if last.direction == "up" and last.high > previous.high:
        return "bearish" if is_stroke_power_weaker(last, previous, indicators) else None
    return None


def is_stroke_power_weaker(last: Stroke, previous: Stroke, indicators: dict | None) -> bool:
    last_range = last.high - last.low
    previous_range = previous.high - previous.low
    return last_range <= previous_range * 1.15


# ── 结构状态判断 ──

def structure_state(strokes: list[Stroke], centers: list[Center]) -> str:
    if len(strokes) < 2:
        return "insufficient_structure"
    last = strokes[-1]
    last_center = centers[-1] if centers else None
    if last_center and last_center.exit_direction == "up":
        if last.direction == "down" and last.low > last_center.high:
            return "uptrend_pullback"
        return "uptrend"
    if last_center and last_center.exit_direction == "down":
        if last.direction == "up" and last.high < last_center.low:
            return "downtrend_rebound"
        return "downtrend"
    if len(strokes) >= 4 and strokes[-1].high > strokes[-3].high and strokes[-2].low > strokes[-4].low:
        return "uptrend"
    if len(strokes) >= 4 and strokes[-1].low < strokes[-3].low and strokes[-2].high < strokes[-4].high:
        return "downtrend"
    if last_center and last.direction == "down" and last.low >= last_center.low:
        return "uptrend_pullback"
    if last_center and last.direction == "up" and last.high <= last_center.high:
        return "downtrend_rebound"
    return "range"


# ── 买卖点主入口 ──

def classify_buy_sell_points(
    fractals: list[Fractal],
    strokes: list[Stroke],
    centers: list[Center],
    divergence: str | None,
    current_structure_state: str,
) -> list[BuySellPoint]:
    points: list[BuySellPoint] = []
    if not fractals:
        return points

    # === 收集所有潜在买1/卖1，过滤连续同向点后衍生买2/买3/卖2/卖3 ===
    all_b1 = _filter_same_side_list(
        collect_all_first_buy(fractals, strokes, centers), "sell"
    )
    all_s1 = _filter_same_side_list(
        collect_all_first_sell(fractals, strokes, centers), "buy"
    )

    # 如果中枢路径没出买1，尝试趋势背离再补一个
    if not all_b1:
        tb1 = build_first_buy_by_trend(fractals, strokes, divergence)
        if tb1:
            all_b1.append(tb1)
    if not all_s1:
        ts1 = build_first_sell_by_trend(fractals, strokes, divergence)
        if ts1:
            all_s1.append(ts1)

    # 从每个买1衍生买2、买3
    for b1 in all_b1:
        points.append(b1)
        b2 = build_second_buy(fractals, strokes, b1)
        if b2:
            points.append(b2)
        for center in centers:
            b3 = build_third_buy(fractals, strokes, center)
            if b3 and b3.index > b1.index:
                points.append(b3)

    # 从每个卖1衍生卖2、卖3
    for s1 in all_s1:
        points.append(s1)
        s2 = build_second_sell(fractals, strokes, s1)
        if s2:
            points.append(s2)
        for center in centers:
            s3 = build_third_sell(fractals, strokes, center)
            if s3 and s3.index > s1.index:
                points.append(s3)

    # === 第二路：如果以上都没有产生买卖点，用结构后备方案 ===
    if not points:
        for center in centers:
            fallback = build_fallback_second_points(fractals, center, current_structure_state)
            points.extend(fallback)

    points = dedupe_points(points)
    return dedupe_points(points)


def _filter_same_side_list(points: list[BuySellPoint], opposite_side: str) -> list[BuySellPoint]:
    """过滤连续的同类买1/卖1：两个买1之间必须有卖点，两个卖1之间必须有买点
    
    在派生B2/B3/S2/S3之前执行，确保衍生点不会从被过滤的基点上生成。
    opposite_side: 两个同向点之间必须存在的反方向side
    """
    if len(points) < 2:
        return points
    sorted_pts = sorted(points, key=lambda p: p.index)
    result: list[BuySellPoint] = [sorted_pts[0]]
    for p in sorted_pts[1:]:
        between = [x for x in sorted_pts if result[-1].index < x.index < p.index and x.side == opposite_side]
        if between:
            result.append(p)
    return result


# ── 买1：全量回溯所有中枢的离开笔弱于进入笔 → 收集所有买1 ──

def collect_all_first_buy(
    fractals: list[Fractal],
    strokes: list[Stroke],
    centers: list[Center],
) -> list[BuySellPoint]:
    """全量回溯：收集所有买1
    
    两路并行：
        1. 下离开中枢 → 离开笔弱于进入笔 → 离开笔端点（底分型）
        2. 上离开中枢 → 中枢起点为反转底分型（下跌结束后的第一个向上中枢）
    """
    results: list[BuySellPoint] = []

    # ── 第一路：下离开中枢，离开笔弱于进入笔（标准中枢背驰） ──
    for center in centers:
        if center.exit_direction != "down":
            continue
        _collect_b1_from_down_exit(center, fractals, strokes, results)

    # ── 第二路：上离开中枢，中枢起点为反转确认（下跌→上涨的拐点） ──
    prev_down_exit_found = False
    for center in centers:
        if center.exit_direction == "down":
            prev_down_exit_found = True
            continue
        if center.exit_direction != "up":
            continue
        # 这个中枢之前有下离开中枢（即经历过下跌段），且本次向上离开
        # → 中枢入口笔的起点就是下跌结束的底分型 = 买1
        if not prev_down_exit_found:
            continue
        entry_stroke = _find_stroke_by_start(center.entry_start_index, strokes)
        if not entry_stroke or entry_stroke.direction != "up":
            continue
        bottom = fractal_at(fractals, entry_stroke.start_index, "bottom")
        if not bottom:
            continue
        results.append(make_point(
            bottom, "买1", "B1", "buy", 0.58,
            "下跌后形成中枢并向上离开，中枢起点按一买观察（趋势反转确认）。",
        ))
        prev_down_exit_found = False  # 只加一次，避免连续买1

    return results


def collect_all_first_sell(
    fractals: list[Fractal],
    strokes: list[Stroke],
    centers: list[Center],
) -> list[BuySellPoint]:
    """全量回溯：收集所有卖1
    
    两路并行：
        1. 上离开中枢 → 离开笔弱于进入笔 → 离开笔端点（顶分型）
        2. 下离开中枢 → 中枢起点为反转顶分型（上涨结束后的第一个向下中枢）
    """
    results: list[BuySellPoint] = []

    # ── 第一路：上离开中枢，离开笔弱于进入笔（标准中枢背驰） ──
    for center in centers:
        if center.exit_direction != "up":
            continue
        _collect_s1_from_up_exit(center, fractals, strokes, results)

    # ── 第二路：下离开中枢，中枢起点为反转确认（上涨→下跌的拐点） ──
    prev_up_exit_found = False
    for center in centers:
        if center.exit_direction == "up":
            prev_up_exit_found = True
            continue
        if center.exit_direction != "down":
            continue
        if not prev_up_exit_found:
            continue
        entry_stroke = _find_stroke_by_start(center.entry_start_index, strokes)
        if not entry_stroke or entry_stroke.direction != "down":
            continue
        top = fractal_at(fractals, entry_stroke.start_index, "top")
        if not top:
            continue
        results.append(make_point(
            top, "卖1", "S1", "sell", 0.58,
            "上涨后形成中枢并向下离开，中枢起点按一卖观察（趋势反转确认）。",
        ))
        prev_up_exit_found = False  # 只加一次，避免连续卖1

    return results


def _collect_b1_from_down_exit(
    center: Center, fractals: list[Fractal],
    strokes: list[Stroke], results: list[BuySellPoint],
) -> None:
    """下离开中枢 → 离开笔弱于进入笔 → 买1"""
    entry_stroke = _find_stroke_by_start(center.entry_start_index, strokes)
    if not entry_stroke:
        return
    exit_stroke = _find_downward_exit_stroke(center, strokes)
    if not exit_stroke:
        return
    bottom = fractal_at(fractals, exit_stroke.end_index, "bottom")
    if not bottom:
        return

    entry_range = _stroke_range(entry_stroke)
    exit_range = _stroke_range(exit_stroke)
    if exit_range >= entry_range * MIN_DIVERGENCE_RATE:
        return

    ratio = exit_range / entry_range if entry_range > 0 else 1.0
    if ratio < 0.85:
        c, r = 0.70, "向下离开中枢笔力度明显弱于进入笔，中枢背驰成立，按一买观察。"
    elif ratio < 0.95:
        c, r = 0.65, "向下离开中枢笔力度弱于进入笔，中枢背驰成立，按一买观察。"
    else:
        c, r = 0.58, "向下离开中枢笔力度略弱于进入笔，中枢背驰偏弱，按一买观察。"

    results.append(make_point(bottom, "买1", "B1", "buy", c, r))


def _collect_s1_from_up_exit(
    center: Center, fractals: list[Fractal],
    strokes: list[Stroke], results: list[BuySellPoint],
) -> None:
    """上离开中枢 → 离开笔弱于进入笔 → 卖1"""
    entry_stroke = _find_stroke_by_start(center.entry_start_index, strokes)
    if not entry_stroke:
        return
    exit_stroke = _find_upward_exit_stroke(center, strokes)
    if not exit_stroke:
        return
    top = fractal_at(fractals, exit_stroke.end_index, "top")
    if not top:
        return

    entry_range = _stroke_range(entry_stroke)
    exit_range = _stroke_range(exit_stroke)
    if exit_range >= entry_range * MIN_DIVERGENCE_RATE:
        return

    ratio = exit_range / entry_range if entry_range > 0 else 1.0
    if ratio < 0.85:
        c, r = 0.70, "向上离开中枢笔力度明显弱于进入笔，中枢背驰成立，按一卖观察。"
    elif ratio < 0.95:
        c, r = 0.65, "向上离开中枢笔力度弱于进入笔，中枢背驰成立，按一卖观察。"
    else:
        c, r = 0.58, "向上离开中枢笔力度略弱于进入笔，中枢背驰偏弱，按一卖观察。"

    results.append(make_point(top, "卖1", "S1", "sell", c, r))


def _find_upward_exit_stroke(center: Center, strokes: list[Stroke]) -> Stroke | None:
    """在中枢之后找到第一根向上突破中枢上沿的笔"""
    for s in strokes:
        if s.start_index < center.end_index:
            continue
        if s.direction == "up" and s.high > center.high:
            return s
    return None


def _find_downward_exit_stroke(center: Center, strokes: list[Stroke]) -> Stroke | None:
    """在中枢之后找到第一根向下跌破中枢下沿的笔"""
    for s in strokes:
        if s.start_index < center.end_index:
            continue
        if s.direction == "down" and s.low < center.low:
            return s
    return None


# ── 买1/卖1 备选：趋势相邻笔力度对比（无中枢场景） ──

def build_first_buy_by_trend(
    fractals: list[Fractal],
    strokes: list[Stroke],
    divergence: str | None,
) -> BuySellPoint | None:
    """无中枢时的买1备选：下跌趋势中最新两根同向笔力度递减"""
    if divergence != "bullish":
        return None
    last = strokes[-1] if strokes else None
    bottom = last_fractal(fractals, "bottom")
    if not bottom or not last or last.direction != "down" or last.end_index != bottom.index:
        return None
    return make_point(
        bottom, "买1", "B1", "buy", 0.55,
        "下跌笔创新低但力度减弱，趋势背驰，按一买观察。",
    )


def build_first_sell_by_trend(
    fractals: list[Fractal],
    strokes: list[Stroke],
    divergence: str | None,
) -> BuySellPoint | None:
    """无中枢时的卖1备选：上涨趋势中最新两根同向笔力度递减"""
    if divergence != "bearish":
        return None
    last = strokes[-1] if strokes else None
    top = last_fractal(fractals, "top")
    if not top or not last or last.direction != "up" or last.end_index != top.index:
        return None
    return make_point(
        top, "卖1", "S1", "sell", 0.55,
        "上涨笔创新高但力度减弱，趋势背驰，按一卖观察。",
    )


# ── 买2 / 卖2 ──

def build_second_buy(fractals: list[Fractal], strokes: list[Stroke], first_buy: BuySellPoint) -> BuySellPoint | None:
    """二买：一买后的回调未破一买低点，且回撤率在合理范围内"""
    for index, stroke in enumerate(strokes):
        if stroke.start_index != first_buy.index or stroke.direction != "up":
            continue
        # stroke 是买1后的第一笔向上（break_bi）
        pullback = next((item for item in strokes[index + 1:] if item.direction == "down"), None)
        if not pullback or pullback.end_price <= first_buy.price:
            continue
        # 回撤率过滤：回调笔力度 vs 突破笔力度
        if _retrace_rate(pullback, stroke) > MAX_BS2_RATE:
            continue
        bottom = fractal_at(fractals, pullback.end_index, "bottom")
        if bottom:
            return make_point(bottom, "买2", "B2", "buy", 0.64, "一买后的回调未跌破一买低点，按二买观察。")
    return None


def build_second_sell(fractals: list[Fractal], strokes: list[Stroke], first_sell: BuySellPoint) -> BuySellPoint | None:
    """二卖：一卖后的反弹未突破一卖高点，且回撤率在合理范围内"""
    for index, stroke in enumerate(strokes):
        if stroke.start_index != first_sell.index or stroke.direction != "down":
            continue
        # stroke 是卖1后的第一笔向下（break_bi）
        rebound = next((item for item in strokes[index + 1:] if item.direction == "up"), None)
        if not rebound or rebound.end_price >= first_sell.price:
            continue
        if _retrace_rate(rebound, stroke) > MAX_BS2_RATE:
            continue
        top = fractal_at(fractals, rebound.end_index, "top")
        if top:
            return make_point(top, "卖2", "S2", "sell", 0.64, "一卖后的反弹未突破一卖高点，按二卖观察。")
    return None


# ── 买3 / 卖3 ──

def build_third_buy(fractals: list[Fractal], strokes: list[Stroke], center: Center) -> BuySellPoint | None:
    """三买：向上离开中枢后回踩不跌回中枢"""
    if center.exit_direction != "up" or center.exit_end_index is None:
        return None
    for stroke in strokes:
        if stroke.start_index < center.exit_end_index:
            continue
        if stroke.low <= center.high:
            return None
        if stroke.direction == "down":
            bottom = fractal_at(fractals, stroke.end_index, "bottom")
            if bottom:
                return make_point(bottom, "买3", "B3", "buy", 0.7, "向上离开中枢后回踩不回中枢，按三买观察。")
    return None


def build_third_sell(fractals: list[Fractal], strokes: list[Stroke], center: Center) -> BuySellPoint | None:
    """三卖：向下离开中枢后反抽不升回中枢"""
    if center.exit_direction != "down" or center.exit_end_index is None:
        return None
    for stroke in strokes:
        if stroke.start_index < center.exit_end_index:
            continue
        if stroke.high >= center.low:
            return None
        if stroke.direction == "up":
            top = fractal_at(fractals, stroke.end_index, "top")
            if top:
                return make_point(top, "卖3", "S3", "sell", 0.7, "向下离开中枢后反抽不回中枢，按三卖观察。")
    return None


# ── 后备方案：无买卖点时从中枢结构推断弱二买/二卖 ──

def build_fallback_second_points(
    fractals: list[Fractal],
    center: Center,
    current_structure_state: str,
) -> list[BuySellPoint]:
    points: list[BuySellPoint] = []
    if current_structure_state in {"uptrend", "uptrend_pullback", "range"}:
        bottom = last_fractal_after(fractals, "bottom", center.start_index)
        if bottom and bottom.price >= center.low:
            points.append(make_point(bottom, "买2", "B2", "buy", 0.56, "回调未破中枢下沿，按弱二买观察。"))
    if current_structure_state in {"downtrend", "downtrend_rebound", "range"}:
        top = last_fractal_after(fractals, "top", center.start_index)
        if top and top.price <= center.high:
            points.append(make_point(top, "卖2", "S2", "sell", 0.56, "反弹未破中枢上沿，按弱二卖观察。"))
    return points


# ── 信号聚合 ──

def signal(
    current_structure_state: str,
    divergence: str | None,
    centers: list[Center],
    strokes: list[Stroke],
    buy_sell_points: list[BuySellPoint],
) -> tuple[str, str, str, float]:
    if buy_sell_points:
        point = buy_sell_points[-1]
        signal_name = {
            "B1": "first_buy_watch",
            "B2": "second_buy_watch",
            "B3": "third_buy_watch",
            "S1": "first_sell_watch",
            "S2": "second_sell_watch",
            "S3": "third_sell_watch",
        }[point.code]
        return signal_name, point.label, point.code, point.confidence
    if centers and strokes:
        return "center_observe", "无", "NONE", 0.42
    return "neutral", "无", "NONE", 0.2


# ── 工具函数 ──

def _stroke_range(stroke: Stroke) -> float:
    return stroke.high - stroke.low


def _retrace_rate(pullback: Stroke, breaker: Stroke) -> float:
    """回撤率 = 回调笔range / 突破笔range"""
    br = _stroke_range(breaker)
    return _stroke_range(pullback) / br if br > 0 else 1.0


def _find_stroke_by_start(start_index: int | None, strokes: list[Stroke]) -> Stroke | None:
    if start_index is None:
        return None
    for s in strokes:
        if s.start_index == start_index:
            return s
    return None


def make_point(
    fractal: Fractal,
    label: str,
    code: str,
    side: str,
    confidence: float,
    reason: str,
) -> BuySellPoint:
    return BuySellPoint(
        index=fractal.index,
        ts=fractal.ts,
        label=label,
        code=code,
        side=side,
        price=fractal.price,
        confidence=confidence,
        reason=reason,
    )


def last_fractal(fractals: list[Fractal], kind: str) -> Fractal | None:
    return next((item for item in reversed(fractals) if item.kind == kind), None)


def last_fractal_after(fractals: list[Fractal], kind: str, start_index: int) -> Fractal | None:
    return next((item for item in reversed(fractals) if item.kind == kind and item.index >= start_index), None)


def fractal_at(fractals: list[Fractal], index: int, kind: str) -> Fractal | None:
    return next((item for item in fractals if item.index == index and item.kind == kind), None)


def dedupe_points(points: list[BuySellPoint]) -> list[BuySellPoint]:
    unique: dict[tuple[int, str], BuySellPoint] = {}
    for point in points:
        unique[(point.index, point.code)] = point
    deduped = sorted(unique.values(), key=lambda item: item.index)

    # 合并同index的同侧点：B2和B3重合 → 只保留B3；S2和S3重合 → 只保留S3
    final: list[BuySellPoint] = []
    for point in deduped:
        if final and final[-1].index == point.index:
            prev = final[-1]
            # 同侧合并：B2+B3→B3, S2+S3→S3, B1+B2→B2, S1+S2→S2
            merge_map = {
                ("B2", "B3"): "B3", ("B3", "B2"): "B3",
                ("S2", "S3"): "S3", ("S3", "S2"): "S3",
                ("B1", "B2"): "B2", ("B2", "B1"): "B2",
                ("S1", "S2"): "S2", ("S2", "S1"): "S2",
            }
            key = (prev.code, point.code)
            if key in merge_map:
                keep_code = merge_map[key]
                keeper = point if point.code == keep_code else prev
                final[-1] = keeper
            else:
                final.append(point)
        else:
            final.append(point)
    return final

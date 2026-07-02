from __future__ import annotations

from dataclasses import asdict, dataclass

from app.chanlun.models import ChanLunResult


@dataclass(frozen=True)
class RiskPlan:
    action: str
    risk_level: str
    entry_zone: tuple[float, float]
    stop_loss: float
    invalid_if: str
    suggested_leverage: int
    reason: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["entry_zone"] = list(self.entry_zone)
        return data


def build_risk_plan(
    analysis: ChanLunResult,
    max_leverage: int = 3,
    risk_per_trade: float = 0.01,
) -> RiskPlan:
    latest = analysis.latest_close
    leverage = max(1, min(int(max_leverage), 5))
    if analysis.signal_strength < 0.5 or analysis.signal in {"neutral", "center_observe"}:
        return RiskPlan(
            action="watch",
            risk_level="low",
            entry_zone=(latest, latest),
            stop_loss=latest,
            invalid_if="等待更清晰的分型、笔或中枢突破确认。",
            suggested_leverage=1,
            reason="结构信号不足，第一版默认只观察，不给主动交易动作。",
        )

    buffer = max(latest * 0.0035, latest * risk_per_trade * 0.35)
    if "buy" in analysis.signal or analysis.divergence == "bullish":
        stop = _last_support(analysis) or latest - buffer * 2
        entry_low = max(stop + buffer, latest * 0.996)
        entry_high = latest * 1.004
        return RiskPlan(
            action="watch_long",
            risk_level="medium" if analysis.signal_strength < 0.8 else "high",
            entry_zone=(round(entry_low, 2), round(entry_high, 2)),
            stop_loss=round(min(stop, latest - buffer), 2),
            invalid_if="价格有效跌破最近底分型或中枢下沿，且反弹无法重新站回。",
            suggested_leverage=min(leverage, 3),
            reason="存在多头观察信号，但第一版只给计划，不自动下单。",
        )

    resistance = _last_resistance(analysis) or latest + buffer * 2
    entry_low = latest * 0.996
    entry_high = min(resistance - buffer, latest * 1.004)
    return RiskPlan(
        action="watch_short",
        risk_level="medium" if analysis.signal_strength < 0.8 else "high",
        entry_zone=(round(entry_low, 2), round(max(entry_low, entry_high), 2)),
        stop_loss=round(max(resistance, latest + buffer), 2),
        invalid_if="价格有效突破最近顶分型或中枢上沿，且回落无法重新跌回。",
        suggested_leverage=min(leverage, 3),
        reason="存在空头观察信号，但第一版只给计划，不自动下单。",
    )


def _last_support(analysis: ChanLunResult) -> float | None:
    bottoms = [item.price for item in analysis.fractals if item.kind == "bottom"]
    center_lows = [item.low for item in analysis.centers]
    values = bottoms + center_lows
    return min(values[-3:]) if values else None


def _last_resistance(analysis: ChanLunResult) -> float | None:
    tops = [item.price for item in analysis.fractals if item.kind == "top"]
    center_highs = [item.high for item in analysis.centers]
    values = tops + center_highs
    return max(values[-3:]) if values else None

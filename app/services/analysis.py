from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.chanlun.engine import analyze_chanlun
from app.market.okx import DEFAULT_SYMBOL, DEFAULT_TIMEFRAMES, OKXCandle, fetch_okx_candles
from app.risk.planner import build_risk_plan


DEFAULT_LIMITS = {
    "5m": 1000,
    "30m": 1000,
    "4H": 1000,
    "1D": 1000,
}


def build_multi_timeframe_payload(options: dict) -> dict:
    symbol = options.get("symbol") or DEFAULT_SYMBOL
    timeframes = list(options.get("timeframes") or DEFAULT_TIMEFRAMES)
    payload = {
        "analysis_id": str(uuid4()),
        "symbol": symbol,
        "inst_type": "SWAP",
        "timeframes": timeframes,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "timeframes_detail": [],
        "summary": {
            "bias": "neutral",
            "confidence": 0.0,
            "message": "等待行情数据。",
        },
    }
    supplied = options.get("candles_by_timeframe") or {}
    details = []
    for timeframe in timeframes:
        candles = supplied.get(timeframe)
        if candles is None and options.get("fetch", False):
            candles = fetch_okx_candles(
                timeframe,
                limit=int(options.get("limit") or DEFAULT_LIMITS.get(timeframe, 300)),
                symbol=symbol,
            )
        candles = _coerce_candles(candles or [])
        analysis = analyze_chanlun(candles, timeframe=timeframe)
        plan = build_risk_plan(analysis)
        details.append(
            {
                "timeframe": timeframe,
                "analysis": analysis.to_dict(),
                "risk_plan": plan.to_dict(),
                "candles": [item.to_dict() for item in candles],
            }
        )
    payload["timeframes_detail"] = details
    payload["summary"] = _summarize(details)
    return payload


def _coerce_candles(items: list) -> list[OKXCandle]:
    candles: list[OKXCandle] = []
    for item in items:
        if isinstance(item, OKXCandle):
            candles.append(item)
        elif isinstance(item, dict):
            candles.append(
                OKXCandle(
                    ts=int(item["ts"]),
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=float(item.get("volume", 0)),
                    confirmed=bool(item.get("confirmed", True)),
                )
            )
    return candles


def _summarize(details: list[dict]) -> dict:
    long_count = sum(1 for item in details if item["risk_plan"]["action"] == "watch_long")
    short_count = sum(1 for item in details if item["risk_plan"]["action"] == "watch_short")
    if long_count > short_count:
        return {
            "bias": "long_watch",
            "confidence": round(long_count / max(1, len(details)), 2),
            "message": "多周期略偏多，但第一版仍要求等待价格触发和失效条件确认。",
        }
    if short_count > long_count:
        return {
            "bias": "short_watch",
            "confidence": round(short_count / max(1, len(details)), 2),
            "message": "多周期略偏空，但第一版仍要求等待价格触发和失效条件确认。",
        }
    return {
        "bias": "neutral",
        "confidence": 0.0,
        "message": "多周期没有形成清晰共振，观望优先。",
    }

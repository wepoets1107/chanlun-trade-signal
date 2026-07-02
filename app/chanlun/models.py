from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


FractalKind = Literal["top", "bottom"]
Direction = Literal["up", "down"]
PointSide = Literal["buy", "sell"]


@dataclass(frozen=True)
class Fractal:
    index: int
    ts: int
    kind: FractalKind
    price: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Stroke:
    start_index: int
    end_index: int
    direction: Direction
    start_price: float
    end_price: float
    high: float
    low: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Segment:
    start_index: int
    end_index: int
    direction: Direction
    start_price: float
    end_price: float
    high: float
    low: float
    stroke_count: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Center:
    start_index: int
    end_index: int
    high: float
    low: float
    mid: float
    entry_start_index: int | None = None
    entry_end_index: int | None = None
    exit_start_index: int | None = None
    exit_end_index: int | None = None
    exit_direction: Direction | None = None
    stroke_count: int = 3

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BuySellPoint:
    index: int
    ts: int
    label: str
    code: str
    side: PointSide
    price: float
    confidence: float
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ChanLunResult:
    timeframe: str
    structure_state: str
    fractals: list[Fractal]
    strokes: list[Stroke]
    centers: list[Center]
    divergence: str | None
    signal: str
    signal_strength: float
    latest_close: float
    segments: list[Segment] = field(default_factory=list)
    buy_sell_points: list[BuySellPoint] = field(default_factory=list)
    indicators: dict = field(default_factory=dict)
    signal_label: str = "无"
    signal_code: str = "NONE"

    def to_dict(self) -> dict:
        return {
            "timeframe": self.timeframe,
            "structure_state": self.structure_state,
            "fractals": [item.to_dict() for item in self.fractals],
            "strokes": [item.to_dict() for item in self.strokes],
            "segments": [item.to_dict() for item in self.segments],
            "centers": [item.to_dict() for item in self.centers],
            "divergence": self.divergence,
            "signal": self.signal,
            "signal_label": self.signal_label,
            "signal_code": self.signal_code,
            "signal_strength": self.signal_strength,
            "latest_close": self.latest_close,
            "buy_sell_points": [item.to_dict() for item in self.buy_sell_points],
            "indicators": self.indicators,
        }

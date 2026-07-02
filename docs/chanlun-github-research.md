# ChanLun GitHub Research

Date: 2026-07-01

This project should not keep growing a one-file, hand-rolled ChanLun approximation.
The next algorithm pass should use mature open-source projects as references for
module boundaries, terminology, test fixtures, and edge cases.

## References

### Vespa314/chan.py

URL: https://github.com/Vespa314/chan.py

Useful points from the public README:

- It explicitly covers fractals, strokes, segments, centers, buy/sell points,
  multi-timeframe linkage, divergence, and strategy buy/sell points.
- Its directory model is a good blueprint for our own boundaries:
  `KLine`, `Bi`, `Seg`, `ZS`, and buy/sell point modules are separate concerns.
- It supports multiple segment algorithms, including an original-text-style
  implementation and definition-based implementations.
- It warns that the public version is only the basic static calculation subset,
  so we should treat it as a reference, not a drop-in trading engine.

### waditu/czsc

URL: https://github.com/waditu/czsc

Useful points from the public README:

- Current 1.0.x versions moved the core ChanLun algorithms, including fractals,
  strokes, and centers, into Rust exposed through PyO3.
- It exposes Python-facing objects such as `CZSC`, `FX`, `BI`, `ZS`, `RawBar`,
  `NewBar`, and `BarGenerator`.
- It has a mature signal/event/trader architecture and many signal functions.
- It has lightweight-charts visualization utilities, which is aligned with our
  current frontend choice.
- It is heavier than our local-first prototype because it needs Python 3.10+
  and may involve native/Rust wheels or builds.

## Recommendation For This Prototype

Do not import either project immediately into the first version.

For V1.1, keep this local app dependency-light and refactor our engine around the
same boundaries:

1. `KLine` layer: raw candles, inclusion handling, normalized candles.
2. `FX` layer: strict top/bottom fractals with deterministic tie handling.
3. `BI` layer: stroke construction with configurable rules and invalidation.
4. `SEG` layer: segment construction from strokes.
5. `ZS` layer: center construction from strokes or segments.
6. `BSP` layer: buy1/buy2/buy3 and sell1/sell2/sell3 classification.

For V2, evaluate a switchable backend:

- `native`: our audited minimal implementation for OKX BTC perpetual.
- `czsc`: optional mature engine adapter if installation works cleanly on the
  target Windows environment.
- `chan.py`: reference-compatible adapter only if its public subset covers the
  required BTC futures workflow and license/dependency constraints are acceptable.

## Immediate Engineering Notes

- Keep source attribution in docs; do not copy code blindly.
- Use public fixtures and our own synthetic K-line fixtures to compare output.
- Before changing trading signals, add tests for each rule:
  inclusion, fractal, stroke, segment, center, and each buy/sell point type.
- The frontend should be considered a renderer of engine output, not a place to
  infer ChanLun structures.

## V1.1 Implementation Status

Implemented after this research:

- Split the prototype engine into focused modules:
  `kline.py`, `fractal.py`, `stroke.py`, `segment.py`, `center.py`, and `bsp.py`.
- Kept `engine.py` as the orchestration layer only.
- Added a minimal three-stroke segment layer and exposed `segments` in the
  analysis API payload.
- Updated the frontend to prefer segment lines for the blue structure overlay,
  while falling back to strokes when segments are unavailable.

Known limitation:

- The segment layer is still a conservative V1 approximation, not a full clone
  of `chan.py` or `czsc`. The next serious correctness pass should compare this
  output against mature fixtures from those projects.

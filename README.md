# ChanLun Trade Signal

**缠论交易信号工作台 — BTC/USDT 缠论结构分析与买卖点检测**

ChanLun (缠论) trade signal workbench — BTC/USDT stroke, center, and buy/sell point detection with OKX public market data.

[![GitHub](https://img.shields.io/badge/GitHub-chanlun--trade--signal-blue)](https://github.com/wepoets1107/chanlun-trade-signal)

---

## 功能 / Features

| 中文 | English |
|------|---------|
| **缠论核心引擎**：分型 → 笔 → 段 → 中枢 → 买卖点 | **ChanLun engine**: fractal → stroke → segment → center → buy/sell point |
| **三大买卖点**：基于中枢进出笔力度对比 | **Three buy/sell points**: center entry/exit stroke power comparison |
| **多周期同步**：5m / 30m / 4H / 1D 四级别联动 | **Multi-timeframe**: 5m / 30m / 4H / 1D synchronized |
| **MACD + 成交量**辅助指标 | **MACD + Volume** auxiliary indicators |
| **风控规划**：入场区间、止损、杠杆建议 | **Risk plan**: entry zone, stop-loss, leverage suggestion |
| **前端展示**：TradingView Lightweight Charts | **Frontend**: TradingView Lightweight Charts |

---

## 快速开始 / Quick Start

### 依赖 / Dependencies

```bash
pip install -r requirements.txt
```

### 启动 / Run

```bash
python run_server.py
```

Open browser at `http://127.0.0.1:8040`

---

## 项目结构 / Project Structure

```
chanlun-trade-signal/
├── run_server.py              # Entry point
├── app/
│   ├── server.py              # HTTP server (port 8040)
│   ├── chanlun/               # ChanLun core algorithm
│   │   ├── kline.py           # K-line inclusion handling
│   │   ├── fractal.py         # Top/bottom fractals
│   │   ├── stroke.py          # Strokes (Bi)
│   │   ├── segment.py         # Segments (Duan)
│   │   ├── center.py          # Centers (ZhongShu)
│   │   ├── bsp.py             # Buy/sell point classifier (core)
│   │   ├── indicator.py       # MACD / Volume
│   │   ├── engine.py          # Analysis engine
│   │   └── models.py          # Data models
│   ├── market/
│   │   └── okx.py             # OKX public market API
│   ├── risk/
│   │   └── planner.py         # Risk planning
│   ├── services/
│   │   └── analysis.py        # Analysis aggregator
│   └── static/                # Frontend
│       ├── index.html
│       ├── app.js
│       ├── styles.css
│       └── vendor/            # TradingView (vendored)
└── tests/
    ├── test_chanlun_engine.py
    ├── test_chanlun_layers.py
    ├── test_okx_market.py
    ├── test_risk_planner.py
    ├── test_api_contract.py
    └── test_frontend_contract.py
```

---

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Service status |
| GET | `/api/market/candles?bar=5m&limit=1000` | OHLCV candlestick data |
| POST | `/api/analyze` | Single-timeframe ChanLun analysis |
| POST | `/api/analyze/multi-timeframe` | Multi-timeframe synced analysis |

---

## 买卖点算法 / Buy/Sell Point Algorithm

买卖点检测基于标准缠论中枢定义 / Detection follows standard ChanLun center theory:

| 点位 / Point | 条件 / Condition |
|-------------|-----------------|
| **买1 / Buy1** | 下跌趋势中，中枢离开笔力度弱于进入笔 → 离开笔底分型 / Downtrend: center exit stroke weaker than entry stroke → exit bottom fractal |
| **卖1 / Sell1** | 上涨趋势中，中枢离开笔力度弱于进入笔 → 离开笔顶分型 / Uptrend: center exit stroke weaker than entry stroke → exit top fractal |
| **买2 / Buy2** | 一买后回调不破前低 / Pullback after Buy1 does not break the prior low |
| **卖2 / Sell2** | 一卖后反弹不破前高 / Rebound after Sell1 does not break the prior high |
| **买3 / Buy3** | 向上离开中枢后回踩不跌回中枢 / After upside center exit, pullback stays above center |
| **卖3 / Sell3** | 向下离开中枢后反抽不升回中枢 / After downside center exit, rebound stays below center |

---

## 数据源 / Data Source

- **Exchange**: OKX
- **Symbol**: BTC-USDT-SWAP
- **Mode**: Read-only. No API key required, no order placement.

---

## 打赏支持冰火岛社区 / Support Binghuodao Community

**EVM Wallet**: `0x29f091DAA3dfee8100645ee24239bCC3ae174B42`

---

## License

MIT

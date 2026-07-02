# ChanLun Trade Signal

缠论交易信号工作台 — 基于 OKX 公共行情数据的 BTC/USDT 缠论结构分析与买卖点检测。

## 功能

- **缠论核心引擎**：分型 → 笔 → 段 → 中枢 → 买卖点
- **三大买卖点**：基于中枢进出笔力度对比的买1/卖1、买2/卖2、买3/卖3
- **多周期同步**：5m / 30m / 4H / 1D 四级别联动
- **MACD + 成交量**：辅助指标，不支持背离检测
- **风控规划**：基于缠论信号生成入场区间、止损、杠杆建议
- **前端展示**：TradingView Lightweight Charts 实时图表

## 快速开始

```bash
pip install -r requirements.txt
python run_server.py
```

打开浏览器访问 `http://127.0.0.1:8040`

## 项目结构

```
chanlun-trade-signal/
├── run_server.py          # 启动入口
├── app/
│   ├── server.py          # HTTP 服务（8040端口）
│   ├── chanlun/           # 缠论核心算法
│   │   ├── kline.py       # K线包含处理
│   │   ├── fractal.py     # 顶底分型
│   │   ├── stroke.py      # 笔
│   │   ├── segment.py     # 段
│   │   ├── center.py      # 中枢
│   │   ├── bsp.py         # 买卖点分类（核心）
│   │   ├── indicator.py   # MACD/成交量
│   │   ├── engine.py      # 分析引擎
│   │   └── models.py      # 数据模型
│   ├── market/
│   │   └── okx.py         # OKX 公共行情接口
│   ├── risk/
│   │   └── planner.py     # 风控规划
│   ├── services/
│   │   └── analysis.py    # 分析服务聚合
│   └── static/            # 前端
│       ├── index.html
│       ├── app.js
│       ├── styles.css
│       └── vendor/        # TradingView (vendored)
└── tests/
    ├── test_chanlun_engine.py
    ├── test_chanlun_layers.py
    ├── test_okx_market.py
    ├── test_risk_planner.py
    ├── test_api_contract.py
    └── test_frontend_contract.py
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/status` | 服务状态 |
| GET | `/api/market/candles?bar=5m&limit=1000` | K线数据 |
| POST | `/api/analyze` | 单级别缠论分析 |
| POST | `/api/analyze/multi-timeframe` | 多级别同步分析 |

## 买卖点算法

买卖点检测基于标准缠论中枢定义：

- **买1**：下跌趋势中，中枢离开笔力度弱于进入笔 → 离开笔底分型
- **卖1**：上涨趋势中，中枢离开笔力度弱于进入笔 → 离开笔顶分型
- **买2**：一买后回调不破前低
- **卖2**：一卖后反弹不破前高
- **买3**：向上离开中枢后回踩不跌回中枢
- **卖3**：向下离开中枢后反抽不升回中枢

## 数据源

- 交易所：OKX
- 交易对：BTC-USDT-SWAP
- 模式：只读，不下单，不存 API Key

## License

MIT

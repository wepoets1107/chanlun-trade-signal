const state = {
  timeframes: ["5m", "30m", "4H", "1D"],
  active: "5m",
  payload: null,
  chart: null,
  candleSeries: null,
  volumeChart: null,
  volumeSeries: null,
  macdChart: null,
  macdHistogramSeries: null,
  macdDifSeries: null,
  macdDeaSeries: null,
  overlaySeries: [],
  centerOverlay: null,
  currentCenters: [],
  currentTimeByIndex: [],
  resizeObserver: null,
  indicatorResizeObserver: null,
};

const els = {
  status: document.querySelector("#apiStatus"),
  latestPrice: document.querySelector("#latestPrice"),
  updatedAt: document.querySelector("#updatedAt"),
  refreshBtn: document.querySelector("#refreshBtn"),
  analyzeBtn: document.querySelector("#analyzeBtn"),
  limitInput: document.querySelector("#limitInput"),
  timeframeGrid: document.querySelector("#timeframeGrid"),
  chartTitle: document.querySelector("#chartTitle"),
  chartSubtitle: document.querySelector("#chartSubtitle"),
  chartContainer: document.querySelector("#priceChart"),
  volumeContainer: document.querySelector("#volumeChart"),
  macdContainer: document.querySelector("#macdChart"),
  summaryBox: document.querySelector("#summaryBox"),
  detailBox: document.querySelector("#detailBox"),
  riskBox: document.querySelector("#riskBox"),
  logList: document.querySelector("#logList"),
};

function init() {
  ensureRuntimeStyles();
  renderTimeframes();
  bindEvents();
  initChart();
  initIndicatorCharts();
  loadStatus();
  analyzeAll();
}

function bindEvents() {
  els.refreshBtn.addEventListener("click", analyzeAll);
  els.analyzeBtn.addEventListener("click", analyzeAll);
}

function initChart() {
  state.chart = LightweightCharts.createChart(els.chartContainer, {
    width: els.chartContainer.clientWidth,
    height: els.chartContainer.clientHeight,
    layout: {
      background: { color: "#0f1215" },
      textColor: "#9aa3ad",
    },
    grid: {
      vertLines: { color: "#1e252b" },
      horzLines: { color: "#1e252b" },
    },
    rightPriceScale: {
      borderColor: "#2a2f35",
    },
    timeScale: {
      borderColor: "#2a2f35",
      timeVisible: true,
      secondsVisible: false,
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
    },
  });
  state.candleSeries = state.chart.addCandlestickSeries({
    upColor: "#22c55e",
    downColor: "#ef4444",
    borderUpColor: "#22c55e",
    borderDownColor: "#ef4444",
    wickUpColor: "#22c55e",
    wickDownColor: "#ef4444",
  });
  state.centerOverlay = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  state.centerOverlay.setAttribute("class", "center-overlay");
  els.chartContainer.appendChild(state.centerOverlay);
  state.chart.timeScale().subscribeVisibleLogicalRangeChange(() => {
    redrawCenters();
  });
  state.resizeObserver = new ResizeObserver(() => {
    if (!state.chart) return;
    state.chart.applyOptions({
      width: els.chartContainer.clientWidth,
      height: els.chartContainer.clientHeight,
    });
    redrawCenters();
  });
  state.resizeObserver.observe(els.chartContainer);
}

function ensureRuntimeStyles() {
  if (document.querySelector("#chanlunRuntimeStyles")) return;
  const style = document.createElement("style");
  style.id = "chanlunRuntimeStyles";
  style.textContent = `
    #priceChart.price-chart { position: relative; height: 680px; overflow: visible; }
    #priceChart .center-overlay { position: absolute; inset: 0; pointer-events: none; z-index: 10; }
    #priceChart .center-rect { fill: rgba(245, 158, 11, 0.08); stroke: #f59e0b; stroke-width: 1.5; stroke-dasharray: none; }
    .indicator-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
    .indicator-row h3 { margin: 0 0 6px; color: #9aa3ad; font-size: 12px; font-weight: 600; }
    .indicator-chart { width: 100%; height: 180px; min-height: 180px; background: #0f1215; border: 1px solid #2a2f35; border-radius: 6px; }
    @media (max-width: 1100px) { .indicator-row { grid-template-columns: 1fr; } }
  `;
  document.head.appendChild(style);
}

function initIndicatorCharts() {
  state.volumeChart = createIndicatorChart(els.volumeContainer);
  state.volumeSeries = state.volumeChart.addHistogramSeries({
    priceFormat: { type: "volume" },
    priceLineVisible: false,
    lastValueVisible: false,
  });
  state.macdChart = createIndicatorChart(els.macdContainer);
  state.macdHistogramSeries = state.macdChart.addHistogramSeries({
    priceLineVisible: false,
    lastValueVisible: false,
  });
  state.macdDifSeries = state.macdChart.addLineSeries({
    color: "#38bdf8",
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: false,
  });
  state.macdDeaSeries = state.macdChart.addLineSeries({
    color: "#f59e0b",
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: false,
  });
  state.indicatorResizeObserver = new ResizeObserver(() => {
    resizeIndicatorChart(state.volumeChart, els.volumeContainer);
    resizeIndicatorChart(state.macdChart, els.macdContainer);
  });
  state.indicatorResizeObserver.observe(els.volumeContainer);
  state.indicatorResizeObserver.observe(els.macdContainer);
}

function createIndicatorChart(container) {
  return LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: container.clientHeight,
    layout: {
      background: { color: "#0f1215" },
      textColor: "#9aa3ad",
    },
    grid: {
      vertLines: { color: "#1e252b" },
      horzLines: { color: "#1e252b" },
    },
    rightPriceScale: {
      borderColor: "#2a2f35",
    },
    timeScale: {
      borderColor: "#2a2f35",
      timeVisible: true,
      secondsVisible: false,
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
    },
  });
}

function resizeIndicatorChart(chart, container) {
  if (!chart || !container) return;
  chart.applyOptions({
    width: container.clientWidth,
    height: container.clientHeight,
  });
}

function renderTimeframes() {
  els.timeframeGrid.innerHTML = "";
  state.timeframes.forEach((timeframe) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = timeframe;
    button.className = timeframe === state.active ? "active" : "";
    button.addEventListener("click", () => {
      state.active = timeframe;
      renderTimeframes();
      renderCurrent();
    });
    els.timeframeGrid.appendChild(button);
  });
}

async function loadStatus() {
  try {
    const status = await getJson("/api/status");
    els.status.textContent = status.ok ? "OKX 公共行情" : "连接异常";
  } catch (error) {
    els.status.textContent = "本地服务异常";
  }
}

async function analyzeAll() {
  setBusy(true);
  try {
    const limit = Number(els.limitInput.value || 1000);
    const payload = await postJson("/api/analyze/multi-timeframe", {
      timeframes: state.timeframes,
      limit,
    });
    if (payload.error) {
      throw new Error(payload.error);
    }
    state.payload = payload;
    renderSummary(payload.summary);
    renderCurrent();
    addLog(`完成 ${payload.symbol} 四级别分析`, payload.generated_at);
  } catch (error) {
    addLog(`分析失败：${error.message}`, new Date().toISOString());
    els.status.textContent = "数据异常";
  } finally {
    setBusy(false);
  }
}

function setBusy(isBusy) {
  els.analyzeBtn.disabled = isBusy;
  els.refreshBtn.disabled = isBusy;
  els.analyzeBtn.textContent = isBusy ? "分析中" : "分析四级别";
}

function renderCurrent() {
  if (!state.payload) return;
  const detail = state.payload.timeframes_detail.find((item) => item.timeframe === state.active);
  if (!detail) return;
  const candles = detail.candles || [];
  const last = candles[candles.length - 1];
  els.chartTitle.textContent = `${state.active} 结构图`;
  els.chartSubtitle.textContent = `${detail.analysis.structure_state} · ${detail.analysis.signal_label || "无"} · ${detail.analysis.signal}`;
  els.latestPrice.textContent = last ? formatPrice(last.close) : "--";
  els.updatedAt.textContent = last ? formatTime(last.ts) : "--";
  renderDefinitionList(els.detailBox, [
    ["结构", detail.analysis.structure_state],
    ["信号", `${detail.analysis.signal_label || "无"} · ${detail.analysis.signal}`],
    ["强度", detail.analysis.signal_strength.toFixed(2)],
    ["背驰", detail.analysis.divergence || "无"],
    ["笔端顶/底", String(detail.analysis.fractals.length)],
    ["笔", String(detail.analysis.strokes.length)],
    ["笔级中枢", String(detail.analysis.centers.length)],
    ["买卖点", String((detail.analysis.buy_sell_points || []).length)],
  ]);
  renderDefinitionList(els.riskBox, [
    ["动作", detail.risk_plan.action],
    ["风险", detail.risk_plan.risk_level],
    ["入场区间", detail.risk_plan.entry_zone.map(formatPrice).join(" - ")],
    ["止损", formatPrice(detail.risk_plan.stop_loss)],
    ["杠杆", `${detail.risk_plan.suggested_leverage}x`],
    ["失效", detail.risk_plan.invalid_if],
    ["理由", detail.risk_plan.reason],
  ]);
  renderTradingViewChart(detail);
}

function renderTradingViewChart(detail) {
  const candles = detail.candles || [];
  const timeByIndex = candles.map((candle) => toChartTime(candle.ts));
  const candleData = candles.map((candle) => ({
    time: toChartTime(candle.ts),
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
  }));

  clearOverlays();
  state.candleSeries.setData(candleData);
  state.candleSeries.setMarkers(buildMarkers(detail.analysis, timeByIndex));
  const structureLines = selectStructureLines(detail.analysis);
  drawStructureLines(structureLines, timeByIndex, 2);
  drawBuySellPoints(detail.analysis.buy_sell_points || [], timeByIndex);
  state.chart.timeScale().fitContent();
  drawVolume(detail.analysis.indicators?.volume || []);
  drawMacd(detail.analysis.indicators?.macd || []);
  drawCenters(detail.analysis.centers || [], timeByIndex);
}

function selectStructureLines(analysis) {
  return analysis.strokes || [];
}

function buildMarkers(analysis, timeByIndex) {
  const endpointMarkers = buildStrokeEndpointMarkers(selectStructureLines(analysis), timeByIndex);
  const pointMarkers = buildBuySellPointMarkers(analysis.buy_sell_points || [], timeByIndex);
  return [...endpointMarkers, ...pointMarkers].sort((left, right) => left.time - right.time);
}

function buildStrokeEndpointMarkers(strokes, timeByIndex) {
  const endpoints = new Map();
  strokes.forEach((stroke) => {
    const startKind = stroke.direction === "up" ? "bottom" : "top";
    const endKind = stroke.direction === "up" ? "top" : "bottom";
    addStrokeEndpoint(endpoints, stroke.start_index, stroke.start_price, startKind, timeByIndex);
    addStrokeEndpoint(endpoints, stroke.end_index, stroke.end_price, endKind, timeByIndex);
  });
  return Array.from(endpoints.values());
}

function addStrokeEndpoint(endpoints, index, price, kind, timeByIndex) {
  const time = timeByIndex[index];
  if (!time) return;
  const key = `${index}:${kind}`;
  endpoints.set(key, {
    time,
    position: kind === "top" ? "aboveBar" : "belowBar",
    color: "#9aa3ad",
    shape: "circle",
    text: kind === "top" ? "顶" : "底",
    size: 0.65,
    price,
  });
}

function buildBuySellPointMarkers(points, timeByIndex) {
  return points
    .filter((point) => timeByIndex[point.index])
    .map((point) => ({
      time: timeByIndex[point.index],
      position: point.side === "buy" ? "belowBar" : "aboveBar",
      color: point.side === "buy" ? "#22c55e" : "#ef4444",
      shape: point.side === "buy" ? "arrowUp" : "arrowDown",
      text: point.label,
      size: 1.8,
    }));
}

function drawStructureLines(lines, timeByIndex, lineWidth) {
  const data = buildStrokeLineData(lines, timeByIndex);
  if (data.length < 2) return;
  const series = state.chart.addLineSeries({
    color: "#38bdf8",
    lineWidth,
    priceLineVisible: false,
    lastValueVisible: false,
    crosshairMarkerVisible: false,
  });
  series.setData(data);
  state.overlaySeries.push(series);
}

function buildStrokeLineData(strokes, timeByIndex) {
  const data = [];
  strokes.forEach((stroke, index) => {
    const startTime = timeByIndex[stroke.start_index];
    const endTime = timeByIndex[stroke.end_index];
    if (!startTime || !endTime) return;
    if (index === 0) {
      data.push({ time: startTime, value: stroke.start_price });
    }
    data.push({ time: endTime, value: stroke.end_price });
  });
  return data;
}

function drawCenters(centers, timeByIndex) {
  state.currentCenters = centers;
  state.currentTimeByIndex = timeByIndex;
  requestAnimationFrame(redrawCenters);
}

function redrawCenters() {
  clearCenterOverlay();
  if (!state.centerOverlay || !state.chart || !state.candleSeries) return;
  state.centerOverlay.setAttribute("width", String(els.chartContainer.clientWidth));
  state.centerOverlay.setAttribute("height", String(els.chartContainer.clientHeight));
  state.currentCenters.forEach((center) => drawCenterRectangle(center, state.currentTimeByIndex));
}

function drawCenterRectangle(center, timeByIndex) {
  const startTime = timeByIndex[center.start_index];
  const endTime = timeByIndex[center.end_index];
  if (!startTime || !endTime) return;
  const x1 = state.chart.timeScale().timeToCoordinate(startTime);
  const x2 = state.chart.timeScale().timeToCoordinate(endTime);
  const y1 = state.candleSeries.priceToCoordinate(center.high);
  const y2 = state.candleSeries.priceToCoordinate(center.low);
  if ([x1, x2, y1, y2].some((value) => !Number.isFinite(value))) return;
  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  const left = Math.min(x1, x2);
  const top = Math.min(y1, y2);
  rect.setAttribute("x", String(left));
  rect.setAttribute("y", String(top));
  rect.setAttribute("width", String(Math.abs(x2 - x1)));
  rect.setAttribute("height", String(Math.abs(y2 - y1)));
  rect.classList.add("center-rect");
  state.centerOverlay.appendChild(rect);
}

function drawVolume(volume) {
  if (!state.volumeSeries || !state.volumeChart) return;
  state.volumeSeries.setData(
    volume.map((point) => ({
      time: toChartTime(point.ts),
      value: point.value,
      color: point.color,
    }))
  );
  state.volumeChart.timeScale().fitContent();
}

function drawMacd(macd) {
  if (!state.macdChart || !state.macdHistogramSeries || !state.macdDifSeries || !state.macdDeaSeries) return;
  state.macdHistogramSeries.setData(
    macd.map((point) => ({
      time: toChartTime(point.ts),
      value: point.histogram,
      color: point.histogram >= 0 ? "rgba(34, 197, 94, 0.75)" : "rgba(239, 68, 68, 0.75)",
    }))
  );
  state.macdDifSeries.setData(macd.map((point) => ({ time: toChartTime(point.ts), value: point.dif })));
  state.macdDeaSeries.setData(macd.map((point) => ({ time: toChartTime(point.ts), value: point.dea })));
  state.macdChart.timeScale().fitContent();
}

function drawBuySellPoints(points, timeByIndex) {
  const labels = ["买1", "买2", "买3", "卖1", "卖2", "卖3"];
  labels.forEach(() => {});
  points.forEach((point) => {
    const time = timeByIndex[point.index];
    if (!time) return;
    const series = state.chart.addLineSeries({
      color: point.side === "buy" ? "#22c55e" : "#ef4444",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });
    series.setData([{ time, value: point.price }]);
    state.overlaySeries.push(series);
  });
}

function clearOverlays() {
  state.overlaySeries.forEach((series) => state.chart.removeSeries(series));
  state.overlaySeries = [];
  clearCenterOverlay();
}

function clearCenterOverlay() {
  if (!state.centerOverlay) return;
  state.centerOverlay.replaceChildren();
}

function renderSummary(summary) {
  els.summaryBox.innerHTML = `<strong>${summary.bias}</strong><p>${summary.message}</p>`;
}

function renderDefinitionList(node, rows) {
  node.innerHTML = rows.map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd>`).join("");
}

async function getJson(url) {
  const response = await fetch(url);
  return response.json();
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json();
}

function addLog(message, iso) {
  const item = document.createElement("div");
  item.className = "log-item";
  item.innerHTML = `<span>${escapeHtml(message)}</span><time>${escapeHtml(formatIso(iso))}</time>`;
  els.logList.prepend(item);
  while (els.logList.children.length > 8) {
    els.logList.lastChild.remove();
  }
}

function toChartTime(ts) {
  return Math.floor(Number(ts) / 1000);
}

function formatPrice(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return number.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

function formatTime(ts) {
  return new Date(Number(ts)).toLocaleString("zh-CN", { hour12: false });
}

function formatIso(iso) {
  return new Date(iso).toLocaleString("zh-CN", { hour12: false });
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

init();

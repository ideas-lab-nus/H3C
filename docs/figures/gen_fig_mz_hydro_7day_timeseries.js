#!/usr/bin/env node
"use strict";

/**
 * Generate the frozen MZ_Hydro seven-day baseline/Agent time-series figure.
 *
 * This script intentionally reads only immutable run artifacts. It uses SVG for
 * the vector source and Playwright only for deterministic PDF/PNG export.
 *
 * Usage (PowerShell):
 *   $env:NODE_PATH='<workspace node_modules>'
 *   node gen_fig_mz_hydro_7day_timeseries.js
 */

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASELINE_RUN = "20260827T231553926586Z-ebaf1f6d2f43";
const AGENT_RUN = "20260827T232744965507Z-2b5dd8e99955";
const H3C_ROOT = path.resolve(__dirname, "..", "..");
const RUN_ROOT = path.join(H3C_ROOT, "outputs", "runs", "main", "MZ_Hydro");

const WIDTH = 1200;
const HEIGHT = 960;
const LEFT = 92;
const RIGHT = 34;
const PLOT_WIDTH = WIDTH - LEFT - RIGHT;
const PANEL_HEIGHT = 170;
const PANEL_TOPS = [120, 326, 532, 738];

const COLORS = {
  baseline: "#0072B2", // Okabe-Ito blue
  agent: "#D55E00", // Okabe-Ito vermillion
  grid: "#D8DDE3",
  text: "#263238",
  muted: "#607D8B",
  comfort: "#009E73",
  invalid: "#A61B1B",
};

function parseCsvLine(line) {
  const fields = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (quoted && line[i + 1] === '"') {
        field += '"';
        i += 1;
      } else {
        quoted = !quoted;
      }
    } else if (char === "," && !quoted) {
      fields.push(field);
      field = "";
    } else {
      field += char;
    }
  }
  fields.push(field);
  return fields;
}

function readPerformance(runId) {
  const csvPath = path.join(RUN_ROOT, runId, "performance.csv");
  const lines = fs.readFileSync(csvPath, "utf8").trim().split(/\r?\n/);
  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    const row = Object.fromEntries(headers.map((header, index) => [header, values[index]]));
    return {
      hour: Number(row.step) / 4,
      powerKw: Number(row.total_power_w) / 1000,
      stepCost: Number(row.step_cost),
      setpoints: JSON.parse(row.zone_setpoints_c),
      pmv: JSON.parse(row.zone_pmv),
      occupancy: JSON.parse(row.zone_occupancy),
    };
  });
}

function trailingMean(values, window) {
  let sum = 0;
  return values.map((value, index) => {
    sum += value;
    if (index >= window) sum -= values[index - window];
    return sum / Math.min(index + 1, window);
  });
}

function cumulative(values) {
  let sum = 0;
  return values.map((value) => {
    sum += value;
    return sum;
  });
}

function occupiedPeak(rows) {
  return rows.map((row) => {
    const occupied = row.pmv
      .map((value, index) => ({ value: Math.abs(value), occupied: row.occupancy[index] > 0 }))
      .filter((item) => item.occupied)
      .map((item) => item.value);
    return occupied.length ? Math.max(...occupied) : null;
  });
}

function extent(series, includeZero = false) {
  const values = series.flat().filter((value) => value !== null && Number.isFinite(value));
  let minimum = Math.min(...values);
  let maximum = Math.max(...values);
  if (includeZero) minimum = Math.min(0, minimum);
  if (maximum === minimum) maximum = minimum + 1;
  const padding = (maximum - minimum) * 0.08;
  return [minimum - padding, maximum + padding];
}

function xScale(hour) {
  return LEFT + (hour / 168) * PLOT_WIDTH;
}

function yScale(value, top, domain) {
  const [minimum, maximum] = domain;
  return top + PANEL_HEIGHT - ((value - minimum) / (maximum - minimum)) * PANEL_HEIGHT;
}

function linePath(hours, values, top, domain) {
  let drawing = false;
  const parts = [];
  values.forEach((value, index) => {
    if (value === null || !Number.isFinite(value)) {
      drawing = false;
      return;
    }
    const command = drawing ? "L" : "M";
    parts.push(`${command}${xScale(hours[index]).toFixed(2)},${yScale(value, top, domain).toFixed(2)}`);
    drawing = true;
  });
  return parts.join(" ");
}

function numberLabel(value, span) {
  if (span < 1) return value.toFixed(2);
  if (span < 20) return value.toFixed(1);
  return value.toFixed(0);
}

function panelFrame(top, domain, ylabel, label) {
  const [minimum, maximum] = domain;
  const span = maximum - minimum;
  const elements = [];
  elements.push(`<text x="20" y="${top - 7}" class="panel-label">${label}</text>`);
  elements.push(`<text x="${LEFT}" y="${top - 7}" class="panel-title">${ylabel}</text>`);
  for (let tick = 0; tick <= 4; tick += 1) {
    const value = minimum + (span * tick) / 4;
    const y = yScale(value, top, domain);
    elements.push(`<line x1="${LEFT}" y1="${y}" x2="${WIDTH - RIGHT}" y2="${y}" class="grid"/>`);
    elements.push(`<text x="${LEFT - 10}" y="${y + 4}" text-anchor="end" class="tick">${numberLabel(value, span)}</text>`);
  }
  for (let day = 0; day <= 7; day += 1) {
    const x = xScale(day * 24);
    elements.push(`<line x1="${x}" y1="${top}" x2="${x}" y2="${top + PANEL_HEIGHT}" class="day-grid"/>`);
    if (top === PANEL_TOPS[PANEL_TOPS.length - 1]) {
      elements.push(`<text x="${x}" y="${top + PANEL_HEIGHT + 24}" text-anchor="middle" class="tick">${day}</text>`);
    }
  }
  elements.push(`<line x1="${LEFT}" y1="${top + PANEL_HEIGHT}" x2="${WIDTH - RIGHT}" y2="${top + PANEL_HEIGHT}" class="axis"/>`);
  return elements.join("\n");
}

function plotPath(hours, values, top, domain, color, dash = "", width = 2.2) {
  const dashAttr = dash ? ` stroke-dasharray="${dash}"` : "";
  return `<path d="${linePath(hours, values, top, domain)}" fill="none" stroke="${color}" stroke-width="${width}"${dashAttr} stroke-linejoin="round" stroke-linecap="round"/>`;
}

function buildSvg() {
  const baseline = readPerformance(BASELINE_RUN);
  const agent = readPerformance(AGENT_RUN);
  if (baseline.length !== 672 || agent.length !== 672) {
    throw new Error("Expected exactly 672 evaluation rows per arm");
  }
  const hours = baseline.map((row) => row.hour);
  const baselineSetpoints = [0, 1].map((zone) => baseline.map((row) => row.setpoints[zone]));
  const agentSetpoints = [0, 1].map((zone) => agent.map((row) => row.setpoints[zone]));
  const baselinePmv = occupiedPeak(baseline);
  const agentPmv = occupiedPeak(agent);
  const baselinePower = trailingMean(baseline.map((row) => row.powerKw), 4);
  const agentPower = trailingMean(agent.map((row) => row.powerKw), 4);
  const baselineCost = cumulative(baseline.map((row) => row.stepCost));
  const agentCost = cumulative(agent.map((row) => row.stepCost));

  const domains = [
    extent([...baselineSetpoints, ...agentSetpoints]),
    [0, Math.max(0.65, ...baselinePmv.filter(Boolean), ...agentPmv.filter(Boolean)) * 1.08],
    [0, Math.max(...baselinePower, ...agentPower) * 1.08],
    [0, Math.max(...baselineCost, ...agentCost) * 1.08],
  ];

  const svg = [];
  svg.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-labelledby="title desc">`);
  svg.push(`<title id="title">MZ_Hydro seven-day baseline and H3C Agent time series</title>`);
  svg.push(`<desc id="desc">Four panels compare setpoints, occupied PMV, HVAC power, and cumulative cost. The Agent run is classified RUN-INVALID because of model contract failures.</desc>`);
  svg.push(`<style>
    text { font-family: "Times New Roman", "DejaVu Serif", serif; fill: ${COLORS.text}; }
    .title { font-size: 27px; font-weight: 700; }
    .subtitle { font-size: 16px; fill: ${COLORS.invalid}; font-weight: 600; }
    .panel-label { font-size: 17px; font-weight: 700; }
    .panel-title { font-size: 17px; font-weight: 600; }
    .tick { font-size: 13px; fill: ${COLORS.muted}; }
    .legend { font-size: 14px; }
    .axis { stroke: #455A64; stroke-width: 1.1; }
    .grid { stroke: ${COLORS.grid}; stroke-width: 0.8; opacity: 0.72; }
    .day-grid { stroke: ${COLORS.grid}; stroke-width: 0.8; opacity: 0.5; }
  </style>`);
  svg.push(`<rect width="${WIDTH}" height="${HEIGHT}" fill="#FFFFFF"/>`);
  svg.push(`<text x="${LEFT}" y="40" class="title">MZ_Hydro: seven-day evaluation from a shared conditioned boundary</text>`);
  svg.push(`<text x="${LEFT}" y="68" class="subtitle">H3C Agent classification: RUN-INVALID — 77 Executor schema rejections and 1 Orchestrator fallback</text>`);

  // Compact method/zone legend.
  const legendY = 94;
  svg.push(`<line x1="${LEFT}" y1="${legendY}" x2="${LEFT + 34}" y2="${legendY}" stroke="${COLORS.baseline}" stroke-width="2" stroke-dasharray="8 5"/><text x="${LEFT + 42}" y="${legendY + 5}" class="legend">Deterministic baseline</text>`);
  svg.push(`<line x1="${LEFT + 205}" y1="${legendY}" x2="${LEFT + 239}" y2="${legendY}" stroke="${COLORS.agent}" stroke-width="2.8"/><text x="${LEFT + 247}" y="${legendY + 5}" class="legend">H3C Agent</text>`);
  svg.push(`<line x1="${LEFT + 366}" y1="${legendY}" x2="${LEFT + 400}" y2="${legendY}" stroke="#424242" stroke-width="2"/><text x="${LEFT + 408}" y="${legendY + 5}" class="legend">NZ</text>`);
  svg.push(`<line x1="${LEFT + 458}" y1="${legendY}" x2="${LEFT + 492}" y2="${legendY}" stroke="#424242" stroke-width="2" stroke-dasharray="3 4"/><text x="${LEFT + 500}" y="${legendY + 5}" class="legend">SZ</text>`);

  svg.push(panelFrame(PANEL_TOPS[0], domains[0], "Cooling setpoint (°C)", "(a)"));
  svg.push(plotPath(hours, baselineSetpoints[0], PANEL_TOPS[0], domains[0], COLORS.baseline, "8 5", 1.8));
  svg.push(plotPath(hours, baselineSetpoints[1], PANEL_TOPS[0], domains[0], COLORS.baseline, "2 4", 1.8));
  svg.push(plotPath(hours, agentSetpoints[0], PANEL_TOPS[0], domains[0], COLORS.agent, "", 2.5));
  svg.push(plotPath(hours, agentSetpoints[1], PANEL_TOPS[0], domains[0], COLORS.agent, "3 4", 2.5));

  svg.push(panelFrame(PANEL_TOPS[1], domains[1], "Occupied max |PMV|", "(b)"));
  const comfortY = yScale(0.5, PANEL_TOPS[1], domains[1]);
  svg.push(`<line x1="${LEFT}" y1="${comfortY}" x2="${WIDTH - RIGHT}" y2="${comfortY}" stroke="${COLORS.comfort}" stroke-width="1.4" stroke-dasharray="5 5"/>`);
  svg.push(`<text x="${WIDTH - RIGHT - 4}" y="${comfortY - 7}" text-anchor="end" class="tick" fill="${COLORS.comfort}">comfort limit 0.5</text>`);
  svg.push(plotPath(hours, baselinePmv, PANEL_TOPS[1], domains[1], COLORS.baseline, "8 5", 2.0));
  svg.push(plotPath(hours, agentPmv, PANEL_TOPS[1], domains[1], COLORS.agent, "", 2.7));

  svg.push(panelFrame(PANEL_TOPS[2], domains[2], "HVAC power, 1 h mean (kW)", "(c)"));
  svg.push(plotPath(hours, baselinePower, PANEL_TOPS[2], domains[2], COLORS.baseline, "8 5", 2.0));
  svg.push(plotPath(hours, agentPower, PANEL_TOPS[2], domains[2], COLORS.agent, "", 2.6));

  svg.push(panelFrame(PANEL_TOPS[3], domains[3], "Cumulative electricity cost", "(d)"));
  svg.push(plotPath(hours, baselineCost, PANEL_TOPS[3], domains[3], COLORS.baseline, "8 5", 2.0));
  svg.push(plotPath(hours, agentCost, PANEL_TOPS[3], domains[3], COLORS.agent, "", 2.7));
  svg.push(`<text x="${LEFT + PLOT_WIDTH / 2}" y="${HEIGHT - 8}" text-anchor="middle" class="panel-title">Evaluation day</text>`);
  svg.push(`</svg>`);
  return svg.join("\n");
}

function browserExecutable() {
  const candidates = [
    process.env.H3C_CHROMIUM_EXECUTABLE,
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  ].filter(Boolean);
  const selected = candidates.find((candidate) => fs.existsSync(candidate));
  if (!selected) {
    throw new Error("No local Chromium-compatible browser is available for PDF/PNG export");
  }
  return selected;
}

async function main() {
  const svg = buildSvg();
  const svgPath = path.join(__dirname, "fig_mz_hydro_7day_timeseries.svg");
  const pngPath = path.join(__dirname, "fig_mz_hydro_7day_timeseries.png");
  const pdfPath = path.join(__dirname, "fig_mz_hydro_7day_timeseries.pdf");
  fs.writeFileSync(svgPath, svg, "utf8");

  const browser = await chromium.launch({
    headless: true,
    executablePath: browserExecutable(),
  });
  try {
    const page = await browser.newPage({
      viewport: { width: 2160, height: 1728 },
      deviceScaleFactor: 1,
    });
    await page.setContent(
      `<!doctype html><html><head><style>html,body{margin:0;width:100%;height:100%;background:#fff}svg{display:block;width:100%;height:100%}</style></head><body>${svg}</body></html>`,
      { waitUntil: "load" },
    );
    await page.locator("svg").screenshot({ path: pngPath, type: "png" });
    await page.pdf({
      path: pdfPath,
      width: "7.2in",
      height: "5.76in",
      printBackground: true,
      margin: { top: "0in", right: "0in", bottom: "0in", left: "0in" },
    });
  } finally {
    await browser.close();
  }
  console.log(`Saved ${svgPath}`);
  console.log(`Saved ${pdfPath}`);
  console.log(`Saved ${pngPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

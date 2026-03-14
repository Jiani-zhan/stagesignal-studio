(() => {
  "use strict";

  const PALETTE = Object.freeze({
    accent: "#b16a2c",
    accent2: "#4f7f6e",
    text: "#2b241b",
    grid: "rgba(72, 61, 49, 0.16)",
    heatLow: "#efe5d7",
    heatHigh: "#8db2a5"
  });

  function renderThemePrevalence(containerId, themes) {
    const container = getElement(containerId);
    if (!container) {
      return;
    }

    const records = Array.isArray(themes) ? themes : [];
    if (!records.length) {
      container.classList.add("is-empty");
      container.innerHTML = "No theme data available.";
      return;
    }

    container.classList.remove("is-empty");

    if (isPlotlyAvailable()) {
      window.Plotly.newPlot(
        container,
        [
          {
            type: "bar",
            orientation: "h",
            y: records.map((item) => item.theme),
            x: records.map((item) => item.count),
            marker: { color: PALETTE.accent }
          }
        ],
        {
          margin: { t: 10, r: 20, b: 30, l: 130 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: PALETTE.text, family: "Instrument Sans, sans-serif" },
          xaxis: { title: "Weighted mentions", zeroline: false, gridcolor: PALETTE.grid },
          yaxis: { automargin: true }
        },
        { displayModeBar: false, responsive: true }
      );
      return;
    }

    renderTable(container, ["Theme", "Weighted Mentions"], records.map((item) => [item.theme, String(item.count)]));
  }

  function renderFoundationCoverage(containerId, datasets) {
    const container = getElement(containerId);
    if (!container) {
      return;
    }

    const records = Array.isArray(datasets)
      ? datasets.filter((item) => item && Number.isFinite(Number(item.rows)) && Number(item.rows) >= 0)
      : [];

    if (!records.length) {
      container.classList.add("is-empty");
      container.innerHTML = "No dataset coverage available.";
      return;
    }

    container.classList.remove("is-empty");

    const labels = records.map((item) => compactDatasetLabel(item.name));
    const fullNames = records.map((item) => item.name);

    if (isPlotlyAvailable()) {
      window.Plotly.newPlot(
        container,
        [
          {
            type: "bar",
            x: labels,
            y: records.map((item) => Number(item.rows)),
            marker: { color: PALETTE.accent2 },
            customdata: fullNames,
            hovertemplate: "%{customdata}<br>Rows: %{y}<extra></extra>"
          }
        ],
        {
          margin: { t: 10, r: 20, b: 84, l: 50 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: PALETTE.text, family: "Instrument Sans, sans-serif" },
          xaxis: {
            title: "Curated dataset",
            tickangle: -18,
            automargin: true,
            tickfont: { size: 11 }
          },
          yaxis: { title: "Rows", gridcolor: PALETTE.grid }
        },
        { displayModeBar: false, responsive: true }
      );
      return;
    }

    renderTable(
      container,
      ["Dataset", "Rows"],
      records.map((item) => [item.name, String(item.rows)])
    );
  }

  function compactDatasetLabel(name) {
    const mapping = {
      "Comparable Events Panel": "Events",
      "Audience Text Corpus": "Audience Text",
      "Micro-survey Responses": "Survey",
      "Channel Metrics Table": "Channels"
    };

    if (mapping[name]) {
      return mapping[name];
    }

    const text = String(name || "Dataset").trim();
    if (!text.includes(" ")) {
      return text;
    }

    const parts = text.split(/\s+/);
    if (parts.length <= 2) {
      return text;
    }

    const mid = Math.ceil(parts.length / 2);
    return `${parts.slice(0, mid).join(" ")}<br>${parts.slice(mid).join(" ")}`;
  }

  function renderDemandScenarios(containerId, scenarios) {
    const container = getElement(containerId);
    if (!container) {
      return;
    }

    const records = Array.isArray(scenarios) ? scenarios : [];
    if (!records.length) {
      container.classList.add("is-empty");
      container.innerHTML = "No scenario data available.";
      return;
    }

    container.classList.remove("is-empty");

    if (isPlotlyAvailable()) {
      window.Plotly.newPlot(
        container,
        [
          {
            type: "bar",
            name: "Attendance",
            x: records.map((scenario) => toTitleCase(scenario.scenario_name)),
            y: records.map((scenario) => scenario.expected_attendance),
            marker: { color: PALETTE.accent2 }
          },
          {
            type: "scatter",
            mode: "lines+markers",
            name: "Revenue",
            x: records.map((scenario) => toTitleCase(scenario.scenario_name)),
            y: records.map((scenario) => scenario.expected_revenue),
            yaxis: "y2",
            line: { color: PALETTE.accent, width: 3 }
          }
        ],
        {
          margin: { t: 10, r: 56, b: 30, l: 40 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: PALETTE.text, family: "Instrument Sans, sans-serif" },
          xaxis: { title: "Scenario" },
          yaxis: { title: "Attendance", gridcolor: PALETTE.grid },
          yaxis2: {
            title: "Revenue ($)",
            overlaying: "y",
            side: "right",
            tickprefix: "$"
          },
          legend: { orientation: "h", y: 1.15 }
        },
        { displayModeBar: false, responsive: true }
      );
      return;
    }

    renderTable(
      container,
      ["Scenario", "Attendance", "Occupancy", "Revenue"],
      records.map((scenario) => [
        toTitleCase(scenario.scenario_name),
        String(scenario.expected_attendance),
        toPercent(scenario.expected_occupancy_pct),
        formatCurrency(scenario.expected_revenue)
      ])
    );
  }

  function renderPurchaseProbability(containerId, purchaseCurve) {
    const container = getElement(containerId);
    if (!container) {
      return;
    }

    const records = Array.isArray(purchaseCurve) ? purchaseCurve : [];
    if (!records.length) {
      container.classList.add("is-empty");
      container.innerHTML = "No purchase probability data available.";
      return;
    }

    container.classList.remove("is-empty");

    if (isPlotlyAvailable()) {
      window.Plotly.newPlot(
        container,
        [
          {
            type: "scatter",
            mode: "lines+markers",
            x: records.map((point) => point.price),
            y: records.map((point) => Number((point.probability * 100).toFixed(2))),
            line: { color: PALETTE.accent2, width: 3 },
            marker: { size: 6 }
          }
        ],
        {
          margin: { t: 10, r: 20, b: 36, l: 46 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: PALETTE.text, family: "Instrument Sans, sans-serif" },
          xaxis: { title: "Price ($)", tickprefix: "$" },
          yaxis: { title: "Purchase probability (%)", range: [0, 100], gridcolor: PALETTE.grid }
        },
        { displayModeBar: false, responsive: true }
      );
      return;
    }

    renderTable(
      container,
      ["Price", "Probability"],
      records.map((point) => [formatCurrency(point.price), `${(point.probability * 100).toFixed(1)}%`])
    );
  }

  function renderRevenuePrice(containerId, revenueCurve) {
    const container = getElement(containerId);
    if (!container) {
      return;
    }

    const records = Array.isArray(revenueCurve) ? revenueCurve : [];
    if (!records.length) {
      container.classList.add("is-empty");
      container.innerHTML = "No revenue curve data available.";
      return;
    }

    container.classList.remove("is-empty");

    if (isPlotlyAvailable()) {
      window.Plotly.newPlot(
        container,
        [
          {
            type: "scatter",
            mode: "lines+markers",
            x: records.map((point) => point.price),
            y: records.map((point) => point.revenue),
            line: { color: PALETTE.accent, width: 3 },
            marker: { size: 6 }
          }
        ],
        {
          margin: { t: 10, r: 20, b: 36, l: 46 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: PALETTE.text, family: "Instrument Sans, sans-serif" },
          xaxis: { title: "Price ($)", tickprefix: "$" },
          yaxis: { title: "Expected revenue ($)", tickprefix: "$", gridcolor: PALETTE.grid }
        },
        { displayModeBar: false, responsive: true }
      );
      return;
    }

    renderTable(
      container,
      ["Price", "Expected Revenue"],
      records.map((point) => [formatCurrency(point.price), formatCurrency(point.revenue)])
    );
  }

  function renderPredictionVsActual(containerId, rows, options = {}) {
    const container = getElement(containerId);
    if (!container) {
      return;
    }

    const records = Array.isArray(rows)
      ? rows.filter((row) => Number.isFinite(Number(row.actual)) && Number.isFinite(Number(row.predicted)))
      : [];

    if (!records.length) {
      container.classList.add("is-empty");
      container.innerHTML = "Prediction data unavailable.";
      return;
    }

    container.classList.remove("is-empty");

    if (isPlotlyAvailable()) {
      const actualValues = records.map((row) => Number(row.actual));
      const predictedValues = records.map((row) => Number(row.predicted));
      const minimum = Math.min(...actualValues, ...predictedValues);
      const maximum = Math.max(...actualValues, ...predictedValues);
      const actualLabel = typeof options.actualLabel === "string" ? options.actualLabel : "Actual";
      const predictedLabel = typeof options.predictedLabel === "string" ? options.predictedLabel : "Predicted";

      window.Plotly.newPlot(
        container,
        [
          {
            type: "scatter",
            mode: "markers",
            name: "Holdout rows",
            x: actualValues,
            y: predictedValues,
            marker: {
              size: 7,
               color: PALETTE.accent2,
               opacity: 0.8
             },
            text: records.map((row) => row.week_date || `Row ${row.row_id || "--"}`),
            hovertemplate: `%{text}<br>${actualLabel}: %{x}<br>${predictedLabel}: %{y}<extra></extra>`
          },
          {
            type: "scatter",
            mode: "lines",
            name: "Perfect fit",
            x: [minimum, maximum],
            y: [minimum, maximum],
            line: {
               color: PALETTE.accent,
               width: 2,
               dash: "dash"
             },
            hoverinfo: "skip"
          }
        ],
        {
          margin: { t: 10, r: 20, b: 44, l: 50 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: PALETTE.text, family: "Instrument Sans, sans-serif" },
          xaxis: { title: `${actualLabel}` },
          yaxis: { title: `${predictedLabel}`, gridcolor: PALETTE.grid },
          legend: { orientation: "h", y: 1.15 }
        },
        { displayModeBar: false, responsive: true }
      );
      return;
    }

    renderTable(
      container,
      ["Week", "Predicted", "Actual", "Error"],
      records.slice(0, 8).map((row) => {
        const predicted = Number(row.predicted);
        const actual = Number(row.actual);
        const error = Number.isFinite(Number(row.error)) ? Number(row.error) : predicted - actual;
        return [
          row.week_date || String(row.row_id || "--"),
          formatCompactNumber(predicted),
          formatCompactNumber(actual),
          formatCompactNumber(error)
        ];
      })
    );
  }

  function renderSelloutConfusionChart(containerId, confusion) {
    const container = getElement(containerId);
    if (!container) {
      return;
    }

    const matrix = normalizeConfusionMatrix(confusion);
    if (!matrix) {
      container.classList.add("is-empty");
      container.innerHTML = "Confusion matrix unavailable.";
      return;
    }

    container.classList.remove("is-empty");

    if (isPlotlyAvailable()) {
      window.Plotly.newPlot(
        container,
        [
          {
            type: "heatmap",
            z: [
              [matrix.tn, matrix.fp],
              [matrix.fn, matrix.tp]
            ],
            x: ["Predicted: No Sellout", "Predicted: Sellout"],
            y: ["Actual: No Sellout", "Actual: Sellout"],
             colorscale: [
               [0, PALETTE.heatLow],
               [1, PALETTE.heatHigh]
             ],
            text: [
              [String(matrix.tn), String(matrix.fp)],
              [String(matrix.fn), String(matrix.tp)]
            ],
            texttemplate: "%{text}",
             textfont: { color: PALETTE.text, size: 14 },
             hovertemplate: "%{y}<br>%{x}<br>Count: %{z}<extra></extra>"
           }
         ],
         {
           margin: { t: 10, r: 20, b: 40, l: 120 },
           paper_bgcolor: "transparent",
           plot_bgcolor: "transparent",
           font: { color: PALETTE.text, family: "Instrument Sans, sans-serif" },
           xaxis: { side: "bottom" },
           yaxis: { automargin: true }
         },
        { displayModeBar: false, responsive: true }
      );
      return;
    }

    renderTable(
      container,
      ["", "Predicted: No Sellout", "Predicted: Sellout"],
      [
        ["Actual: No Sellout", String(matrix.tn), String(matrix.fp)],
        ["Actual: Sellout", String(matrix.fn), String(matrix.tp)]
      ]
    );
  }

  function resetChart(containerId, placeholderText) {
    const container = getElement(containerId);
    if (!container) {
      return;
    }

    if (isPlotlyAvailable() && typeof window.Plotly.purge === "function") {
      window.Plotly.purge(container);
    }

    container.classList.add("is-empty");
    container.innerHTML = placeholderText || "";
  }

  function renderTable(container, headers, rows) {
    const headerHtml = headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("");
    const rowsHtml = rows
      .map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`)
      .join("");

    container.innerHTML =
      `<div class="chart-table-wrap">` +
      `<table class="chart-table">` +
      `<thead><tr>${headerHtml}</tr></thead>` +
      `<tbody>${rowsHtml}</tbody>` +
      `</table>` +
      `</div>`;
  }

  function getElement(id) {
    if (typeof id !== "string") {
      return null;
    }
    return document.getElementById(id);
  }

  function isPlotlyAvailable() {
    return Boolean(window.Plotly && typeof window.Plotly.newPlot === "function");
  }

  function formatCurrency(value) {
    return Number.isFinite(value) ? `$${Number(value).toFixed(2)}` : "--";
  }

  function formatCompactNumber(value) {
    if (!Number.isFinite(value)) {
      return "--";
    }

    const absValue = Math.abs(value);
    if (absValue >= 1000) {
      return Number(value).toLocaleString("en-US", { maximumFractionDigits: 0 });
    }
    if (absValue >= 1) {
      return Number(value).toLocaleString("en-US", { maximumFractionDigits: 2 });
    }
    return Number(value).toFixed(4);
  }

  function normalizeConfusionMatrix(confusion) {
    if (!confusion || typeof confusion !== "object") {
      return null;
    }

    const tp = Number(confusion.tp);
    const fp = Number(confusion.fp);
    const tn = Number(confusion.tn);
    const fn = Number(confusion.fn);

    if (![tp, fp, tn, fn].every((value) => Number.isFinite(value))) {
      return null;
    }

    return {
      tp,
      fp,
      tn,
      fn
    };
  }

  function toPercent(value) {
    return Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "--";
  }

  function toTitleCase(value) {
    if (typeof value !== "string") {
      return "Unknown";
    }
    return value.charAt(0).toUpperCase() + value.slice(1);
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  window.StageSignalCharts = {
    renderFoundationCoverage,
    renderThemePrevalence,
    renderDemandScenarios,
    renderPurchaseProbability,
    renderRevenuePrice,
    renderPredictionVsActual,
    renderSelloutConfusionChart,
    resetChart,
    isPlotlyAvailable
  };
})();

(() => {
  "use strict";

  const SCENARIO_ORDER = ["conservative", "base", "optimistic"];

  const FOUNDATION_DATASETS = Object.freeze([
    {
      key: "events_comps",
      title: "Comparable Events Panel",
      role: "Benchmark launches by venue, pricing, and sellout proxy.",
      missingAuditKey: "events_comps_missing_ticket_mid",
      jsonFile: "assets/data/events_comps.json",
      csvFile: "assets/data/events_comps.csv"
    },
    {
      key: "audience_text",
      title: "Audience Text Corpus",
      role: "Qualitative signal for theme extraction and motivation mapping.",
      missingAuditKey: "audience_text_missing_engagement",
      jsonFile: "assets/data/audience_text.json",
      csvFile: "assets/data/audience_text.csv"
    },
    {
      key: "survey_responses",
      title: "Micro-survey Responses",
      role: "Price sensitivity and conversion intent calibration.",
      missingAuditKey: "survey_missing_price_fields",
      jsonFile: "assets/data/survey_responses.json",
      csvFile: "assets/data/survey_responses.csv"
    },
    {
      key: "channel_metrics",
      title: "Channel Metrics Table",
      role: "Media planning priors for launch channel mix.",
      missingAuditKey: "channel_missing_cost_proxy",
      jsonFile: "assets/data/channel_metrics.json",
      csvFile: "assets/data/channel_metrics.csv"
    }
  ]);

  document.addEventListener("DOMContentLoaded", () => {
    initialize().catch((error) => {
      console.error("Failed to initialize StageSignal report", error);
      setText("source-health-summary", "Report failed to load data.");
      setText("model-overall-gate", "Model artifacts unavailable.");
    });
  });

  async function initialize() {
    if (!window.StageSignalDataLoader || !window.StageSignalCharts) {
      throw new Error("Required modules are unavailable.");
    }

    const data = await window.StageSignalDataLoader.loadAllData();

    renderHero(data);
    renderOverview(data);
    renderSources(data);
    renderAudience(data);
    renderDemand(data);
    renderPricing(data);
    renderValidation(data);
    renderConclusions(data);
  }

  function renderHero(data) {
    const sourceHealth = data && data.sourceHealth ? data.sourceHealth : {};
    const inventory = Array.isArray(sourceHealth.source_inventory) ? sourceHealth.source_inventory : [];
    const broadwaySource = inventory.find((entry) => String(entry.source_file || "").includes("Data Collection & Visualization.xlsx"));
    const broadwayRows =
      broadwaySource && broadwaySource.row_counts && Number.isFinite(broadwaySource.row_counts["Broadway Revenue"])
        ? Number(broadwaySource.row_counts["Broadway Revenue"])
        : null;
    const modelCount = data && data.modelPerformance && Array.isArray(data.modelPerformance.models)
      ? data.modelPerformance.models.length
      : 0;

    setText("hero-data-window", broadwayRows ? `${broadwayRows} weekly rows` : "Broadway rows unavailable");
    setText("hero-model-count", modelCount ? `${modelCount} trained models` : "No models");
  }

  function renderOverview(data) {
    const sourceHealth = data && data.sourceHealth ? data.sourceHealth : {};
    const inventory = Array.isArray(sourceHealth.source_inventory) ? sourceHealth.source_inventory : [];
    const sourceCount = inventory.filter((item) => item.status === "parsed").length;
    const segments = Array.isArray(data && data.segments) ? data.segments : [];
    const baseScenario = getBaseScenario(data);
    const pricing = data && data.pricingRecommendation ? data.pricingRecommendation : {};
    const performance = data && data.modelPerformance ? data.modelPerformance : null;

    setText("overview-source-count", sourceCount ? String(sourceCount) : "--");
    setText("overview-segment-count", segments.length ? String(segments.length) : "--");
    setText(
      "overview-base-attendance",
      baseScenario && Number.isFinite(baseScenario.expected_attendance)
        ? formatInteger(baseScenario.expected_attendance)
        : "--"
    );
    setText(
      "overview-ga-price",
      Number.isFinite(Number(pricing.recommended_ga_price))
        ? formatCurrency(Number(pricing.recommended_ga_price))
        : "--"
    );
    setText(
      "overview-model-gate",
      performance && typeof performance.all_models_passed === "boolean"
        ? performance.all_models_passed
          ? "PASS"
          : "FAIL"
        : "--"
    );
  }

  function renderSources(data) {
    const sourceHealth = data && data.sourceHealth ? data.sourceHealth : {};
    const inventory = Array.isArray(sourceHealth.source_inventory) ? sourceHealth.source_inventory : [];
    const warnings = Array.isArray(sourceHealth.warnings) ? sourceHealth.warnings : [];
    const parsedCount = inventory.filter((item) => item.status === "parsed").length;
    const tableRowCounts =
      sourceHealth.table_row_counts && typeof sourceHealth.table_row_counts === "object"
        ? sourceHealth.table_row_counts
        : {};
    const missingAudit =
      sourceHealth.missing_value_audit && typeof sourceHealth.missing_value_audit === "object"
        ? sourceHealth.missing_value_audit
        : {};

    const curatedCoverage = FOUNDATION_DATASETS.map((dataset) => ({
      name: dataset.title,
      rows: Number(tableRowCounts[dataset.key] || 0)
    }));

    setText(
      "source-health-summary",
      `Processed ${parsedCount} source files into ${FOUNDATION_DATASETS.length} curated analytical datasets. Build seed: ${sourceHealth.deterministic_seed || "--"}.`
    );

    renderList("source-warning-list", warnings, "No warnings reported.");

    window.StageSignalCharts.renderFoundationCoverage("foundation-coverage-chart", curatedCoverage);
    setText(
      "foundation-chart-note",
      window.StageSignalCharts.isPlotlyAvailable()
        ? "Row volumes across curated analysis tables."
        : "Plotly unavailable: using table fallback."
    );

    const tableBody = getElement("foundation-table-body");
    if (!tableBody) {
      return;
    }

    if (!FOUNDATION_DATASETS.length) {
      tableBody.innerHTML = "<tr><td colspan=\"5\">No curated datasets available.</td></tr>";
      return;
    }

    tableBody.innerHTML = FOUNDATION_DATASETS.map((dataset) => {
      const rows = Number(tableRowCounts[dataset.key] || 0);
      const missingFields = Number(missingAudit[dataset.missingAuditKey] || 0);
      const downloadHtml =
        `<a class=\"download-link\" href=\"${escapeHtml(dataset.csvFile)}\" download>CSV</a>` +
        ` <span class=\"download-sep\">|</span> ` +
        `<a class=\"download-link\" href=\"${escapeHtml(dataset.jsonFile)}\" download>JSON</a>`;

      return (
        `<tr>` +
        `<td>${escapeHtml(dataset.title)}</td>` +
        `<td>${escapeHtml(dataset.role)}</td>` +
        `<td>${escapeHtml(formatInteger(rows))}</td>` +
        `<td>${escapeHtml(formatInteger(missingFields))}</td>` +
        `<td>${downloadHtml}</td>` +
        `</tr>`
      );
      })
      .join("");
  }

  function renderAudience(data) {
    const segments = Array.isArray(data && data.segments) ? [...data.segments] : [];
    const audienceText = Array.isArray(data && data.audienceText) ? data.audienceText : [];

    segments.sort((a, b) => {
      const scoreA = Number(a.segment_size_pct || 0) * Number(a.expected_conversion_base || 0);
      const scoreB = Number(b.segment_size_pct || 0) * Number(b.expected_conversion_base || 0);
      return scoreB - scoreA;
    });

    const topSegment = segments[0] || null;
    if (topSegment) {
      const share = Number(topSegment.segment_size_pct || 0) * 100;
      const conversion = Number(topSegment.expected_conversion_base || 0) * 100;
      setText(
        "segment-summary",
        `${topSegment.segment_name} leads with ${share.toFixed(1)}% share and ${conversion.toFixed(1)}% base conversion expectation.`
      );
    } else {
      setText("segment-summary", "Segment data unavailable.");
    }

    const findings = segments.slice(0, 3).map((segment, index) => {
      const share = Number(segment.segment_size_pct || 0) * 100;
      return `#${index + 1} ${segment.segment_name}: ${share.toFixed(1)}% of target audience.`;
    });
    renderList("audience-key-findings", findings, "No audience findings available.");

    const themes = computeThemePrevalence(audienceText);
    window.StageSignalCharts.renderThemePrevalence("theme-prevalence-chart", themes);
    setText(
      "theme-chart-note",
      window.StageSignalCharts.isPlotlyAvailable()
        ? "Keyword themes weighted by engagement signal."
        : "Plotly unavailable: using table fallback."
    );
  }

  function renderDemand(data) {
    const scenarios = getOrderedScenarios(data);
    const baseScenario = scenarios.find((scenario) => scenario.scenario_name === "base") || scenarios[0] || null;

    setText(
      "expected-attendance-value",
      baseScenario && Number.isFinite(baseScenario.expected_attendance)
        ? formatInteger(baseScenario.expected_attendance)
        : "--"
    );
    setText(
      "occupancy-band-value",
      baseScenario && Number.isFinite(baseScenario.expected_occupancy_pct)
        ? `${(baseScenario.expected_occupancy_pct * 100).toFixed(1)}%`
        : "--"
    );
    setText(
      "expected-revenue-value",
      baseScenario && Number.isFinite(baseScenario.expected_revenue)
        ? formatCurrency(baseScenario.expected_revenue)
        : "--"
    );

    window.StageSignalCharts.renderDemandScenarios("demand-scenarios-chart", scenarios);
    setText("demand-chart-note", "Bars show attendance while line shows revenue across scenarios.");

    const tableBody = getElement("scenario-table-body");
    if (!tableBody) {
      return;
    }

    if (!scenarios.length) {
      tableBody.innerHTML = "<tr><td colspan=\"4\">No demand scenarios available.</td></tr>";
      return;
    }

    tableBody.innerHTML = scenarios
      .map((scenario) => {
        const name = toTitleCase(scenario.scenario_name);
        const attendance = formatInteger(Number(scenario.expected_attendance));
        const occupancy = Number.isFinite(Number(scenario.expected_occupancy_pct))
          ? `${(Number(scenario.expected_occupancy_pct) * 100).toFixed(1)}%`
          : "--";
        const revenue = formatCurrency(Number(scenario.expected_revenue));
        return `<tr><td>${escapeHtml(name)}</td><td>${escapeHtml(attendance)}</td><td>${escapeHtml(occupancy)}</td><td>${escapeHtml(revenue)}</td></tr>`;
      })
      .join("");
  }

  function renderPricing(data) {
    const pricing = data && data.pricingRecommendation ? data.pricingRecommendation : {};
    const baseScenario = getBaseScenario(data);
    const eventBrief = data && data.eventBrief ? data.eventBrief : {};
    const venueCapacity = Number.isFinite(Number(eventBrief.venue_capacity)) ? Number(eventBrief.venue_capacity) : 280;
    const baseAttendance = baseScenario && Number.isFinite(Number(baseScenario.expected_attendance))
      ? Number(baseScenario.expected_attendance)
      : Math.round(venueCapacity * 0.9);
    const baseRevenue = baseScenario && Number.isFinite(Number(baseScenario.expected_revenue))
      ? Number(baseScenario.expected_revenue)
      : null;
    const purchaseCurve = buildPurchaseCurve(pricing, venueCapacity, baseAttendance);
    const revenueCurve = buildRevenueCurve(
      purchaseCurve,
      baseAttendance,
      venueCapacity,
      baseRevenue,
      Number(pricing.recommended_ga_price)
    );

    setText(
      "acceptable-price-range",
      Number.isFinite(Number(pricing.acceptable_range_low)) && Number.isFinite(Number(pricing.acceptable_range_high))
        ? `${formatCurrency(Number(pricing.acceptable_range_low))} - ${formatCurrency(Number(pricing.acceptable_range_high))}`
        : "--"
    );
    setText(
      "recommended-ga-price",
      Number.isFinite(Number(pricing.recommended_ga_price))
        ? formatCurrency(Number(pricing.recommended_ga_price))
        : "--"
    );
    setText(
      "recommended-premium-price",
      Number.isFinite(Number(pricing.recommended_premium_price))
        ? formatCurrency(Number(pricing.recommended_premium_price))
        : "--"
    );
    setText(
      "recommended-student-price",
      Number.isFinite(Number(pricing.recommended_student_price))
        ? formatCurrency(Number(pricing.recommended_student_price))
        : "--"
    );

    window.StageSignalCharts.renderPurchaseProbability("purchase-probability-chart", purchaseCurve);
    window.StageSignalCharts.renderRevenuePrice("revenue-price-chart", revenueCurve);
    setText("purchase-curve-note", "Probability declines as price rises away from anchor point.");
    setText("revenue-curve-note", "Revenue response combines attendance decay with price expansion.");

    const rationale = Array.isArray(pricing.rationale) ? pricing.rationale : [];
    renderList("pricing-rationale-list", rationale, "No pricing rationale available.");
  }

  function renderValidation(data) {
    const performance = data && data.modelPerformance && typeof data.modelPerformance === "object" ? data.modelPerformance : null;
    const predictions = data && data.modelPredictions && typeof data.modelPredictions === "object" ? data.modelPredictions : null;
    const featureData = data && data.modelFeatures && typeof data.modelFeatures === "object" ? data.modelFeatures : null;

    const grossReport = resolveModelReport(performance, "weekly_gross_regression");
    const avgTicketReport = resolveModelReport(performance, "average_ticket_regression");
    const selloutReport = resolveModelReport(performance, "sellout_flag_classifier");

    setText("model-gross-r2", formatMetric(grossReport && grossReport.metrics ? grossReport.metrics.r2 : null));
    setText("model-seats-r2", formatMetric(avgTicketReport && avgTicketReport.metrics ? avgTicketReport.metrics.r2 : null));
    setText(
      "model-sellout-accuracy",
      formatPercentMetric(selloutReport && selloutReport.metrics ? selloutReport.metrics.accuracy : null)
    );

    setGateBadge("model-gross-gate", grossReport ? grossReport.passed : null);
    setGateBadge("model-seats-gate", avgTicketReport ? avgTicketReport.passed : null);
    setGateBadge("model-sellout-gate", selloutReport ? selloutReport.passed : null);

    if (performance && typeof performance.all_models_passed === "boolean") {
      setText(
        "model-overall-gate",
        performance.all_models_passed
          ? "Validation gate passed: all model thresholds met."
          : "Validation gate failed: at least one model missed threshold."
      );
    } else {
      setText("model-overall-gate", "Model artifacts unavailable.");
    }

    renderFeatureChips(
      "model-feature-gross",
      getModelFeatureNames(featureData, "weekly_gross_regression")
    );
    renderFeatureChips(
      "model-feature-seats",
      getModelFeatureNames(featureData, "average_ticket_regression")
    );
    renderFeatureChips(
      "model-feature-sellout",
      getModelFeatureNames(featureData, "sellout_flag_classifier")
    );

    const grossRows = resolvePredictionRows(predictions, "weekly_gross_regression");
    const avgTicketRows = resolvePredictionRows(predictions, "average_ticket_regression");
    const selloutRows = resolvePredictionRows(predictions, "sellout_flag_classifier");

    if (grossRows.length) {
      window.StageSignalCharts.renderPredictionVsActual("gross-prediction-chart", grossRows, {
        actualLabel: "Actual Gross",
        predictedLabel: "Predicted Gross"
      });
      renderPredictionSampleRows("prediction-sample-gross", grossRows, (row) => [
        row.week_date || "--",
        formatCurrency(Number(row.predicted)),
        formatCurrency(Number(row.actual))
      ]);
    } else {
      window.StageSignalCharts.resetChart("gross-prediction-chart", "Prediction data unavailable.");
      renderPredictionSampleFallback("prediction-sample-gross", "Gross sample rows unavailable.");
    }

    if (avgTicketRows.length) {
      window.StageSignalCharts.renderPredictionVsActual("seats-prediction-chart", avgTicketRows, {
        actualLabel: "Actual Avg Ticket",
        predictedLabel: "Predicted Avg Ticket"
      });
      renderPredictionSampleRows("prediction-sample-seats", avgTicketRows, (row) => [
        row.week_date || "--",
        formatCurrency(Number(row.predicted)),
        formatCurrency(Number(row.actual))
      ]);
    } else {
      window.StageSignalCharts.resetChart("seats-prediction-chart", "Prediction data unavailable.");
      renderPredictionSampleFallback("prediction-sample-seats", "Average ticket rows unavailable.");
    }

    if (selloutReport && selloutReport.metrics && selloutReport.metrics.confusion_matrix) {
      window.StageSignalCharts.renderSelloutConfusionChart("sellout-confusion-chart", selloutReport.metrics.confusion_matrix);
    } else {
      window.StageSignalCharts.resetChart("sellout-confusion-chart", "Confusion matrix unavailable.");
    }

    if (selloutRows.length) {
      renderPredictionSampleRows("prediction-sample-sellout", selloutRows, (row) => [
        row.week_date || "--",
        normalizeSelloutLabel(row.predicted),
        normalizeSelloutLabel(row.actual)
      ]);
    } else {
      renderPredictionSampleFallback("prediction-sample-sellout", "Sellout sample rows unavailable.");
    }
  }

  function renderConclusions(data) {
    const memo = data && data.memo && typeof data.memo === "object" ? data.memo : {};

    const headline = typeof memo.headline === "string" && memo.headline.trim().length
      ? memo.headline
      : "Recommendation summary unavailable.";
    const objective = typeof memo.objective === "string" && memo.objective.trim().length
      ? memo.objective
      : "No objective summary available.";

    setText("memo-conclusion-headline", headline);
    setText("memo-conclusion-summary", objective);

    const actions = [memo.pricing_decision, memo.channel_decision, memo.positioning_decision, memo.next_experiment].filter(
      (value) => typeof value === "string" && value.trim().length
    );
    renderList("memo-conclusion-actions", actions, "No action recommendations available.");

    const risks = Array.isArray(memo.key_risks) ? memo.key_risks : [];
    renderList("memo-conclusion-risks", risks, "No risk notes available.");

    const evidence = [];
    if (memo.support_metrics && typeof memo.support_metrics === "object") {
      if (Number.isFinite(Number(memo.support_metrics.expected_attendance_base))) {
        evidence.push(
          `Base expected attendance: ${formatInteger(Number(memo.support_metrics.expected_attendance_base))}.`
        );
      }
      if (Number.isFinite(Number(memo.support_metrics.recommended_ga_price))) {
        evidence.push(
          `Recommended GA anchor: ${formatCurrency(Number(memo.support_metrics.recommended_ga_price))}.`
        );
      }
      if (typeof memo.support_metrics.revenue_interval_base === "string") {
        evidence.push(`Revenue interval (base): ${memo.support_metrics.revenue_interval_base}.`);
      }
    }

    if (memo.evidence_links && typeof memo.evidence_links === "object") {
      Object.entries(memo.evidence_links).forEach(([key, value]) => {
        evidence.push(`${toTitleCase(key)} evidence: ${value}`);
      });
    }

    renderList("memo-conclusion-evidence", evidence, "No evidence trace available.");
  }

  function getOrderedScenarios(data) {
    const scenarios = Array.isArray(data && data.demandScenarios) ? data.demandScenarios : [];
    const ordered = SCENARIO_ORDER.map((name) => scenarios.find((scenario) => scenario.scenario_name === name)).filter(Boolean);
    return ordered.length ? ordered : scenarios;
  }

  function getBaseScenario(data) {
    const scenarios = getOrderedScenarios(data);
    return scenarios.find((scenario) => scenario.scenario_name === "base") || scenarios[0] || null;
  }

  function computeThemePrevalence(audienceText) {
    const dictionary = [
      { theme: "Immersion", patterns: ["immersive", "interactive", "atmosphere", "sensory"] },
      { theme: "Storytelling", patterns: ["narrative", "story", "staging", "beethoven"] },
      { theme: "Value & Pricing", patterns: ["price", "value", "premium", "student", "pricing"] },
      { theme: "Social Discovery", patterns: ["social", "friends", "shareable", "group", "word of mouth"] },
      { theme: "Marketing Clarity", patterns: ["marketing", "trailer", "reels", "creator", "youtube", "tiktok"] }
    ];

    const counts = dictionary.map((entry) => ({ theme: entry.theme, count: 0 }));

    audienceText.forEach((entry) => {
      const text = typeof entry.raw_text === "string" ? entry.raw_text.toLowerCase() : "";
      const weight = Number.isFinite(entry.engagement_signal)
        ? Math.max(1, Math.round(Number(entry.engagement_signal) / 50))
        : 1;

      dictionary.forEach((item, index) => {
        if (item.patterns.some((pattern) => text.includes(pattern))) {
          counts[index].count += weight;
        }
      });
    });

    return counts.sort((a, b) => b.count - a.count);
  }

  function buildPurchaseCurve(pricing, venueCapacity, baseAttendance) {
    const low = Number(pricing.acceptable_range_low);
    const high = Number(pricing.acceptable_range_high);
    const ga = Number(pricing.recommended_ga_price);
    const minPrice = Number.isFinite(low)
      ? Math.max(15, low * 0.7)
      : Number.isFinite(ga)
        ? ga * 0.6
        : 30;
    const maxPrice = Number.isFinite(high)
      ? high * 1.3
      : Number.isFinite(ga)
        ? ga * 1.5
        : 130;

    const steps = 14;
    const stepSize = (maxPrice - minPrice) / (steps - 1);
    const centerPrice = Number.isFinite(ga) ? ga : (minPrice + maxPrice) / 2;
    const baseProbability = venueCapacity > 0
      ? clamp(baseAttendance / venueCapacity, 0.05, 0.98)
      : 0.84;
    const elasticity = Number.isFinite(ga) && ga > 0 ? 1 / ga : 0.013;

    const curve = [];
    for (let i = 0; i < steps; i += 1) {
      const price = minPrice + stepSize * i;
      const probability = clamp(baseProbability * Math.exp(-elasticity * (price - centerPrice)), 0.03, 0.995);
      curve.push({
        price: Number(price.toFixed(2)),
        probability: Number(probability.toFixed(4))
      });
    }

    return curve;
  }

  function buildRevenueCurve(purchaseCurve, baseAttendance, venueCapacity, baseRevenue, gaPrice) {
    const baseline = purchaseCurve[Math.floor(purchaseCurve.length / 2)] || { probability: 0.8 };
    const baselineProbability = Number.isFinite(baseline.probability) ? baseline.probability : 0.8;
    const revenueScale =
      Number.isFinite(baseRevenue) && Number.isFinite(gaPrice) && gaPrice > 0 && baseAttendance > 0
        ? baseRevenue / (gaPrice * baseAttendance)
        : 1;

    return purchaseCurve.map((point) => {
      const attendanceRatio = baselineProbability > 0 ? point.probability / baselineProbability : 0;
      const expectedAttendance = Math.min(venueCapacity, Math.max(0, baseAttendance * attendanceRatio));
      return {
        price: point.price,
        revenue: Number((point.price * expectedAttendance * revenueScale).toFixed(2))
      };
    });
  }

  function resolveModelReport(performance, modelId) {
    if (!performance || !Array.isArray(performance.models)) {
      return null;
    }
    return performance.models.find((model) => model && model.model_id === modelId) || null;
  }

  function resolvePredictionRows(predictions, modelId) {
    if (!predictions || !Array.isArray(predictions.models)) {
      return [];
    }
    const model = predictions.models.find((entry) => entry && entry.model_id === modelId);
    return model && Array.isArray(model.rows) ? model.rows : [];
  }

  function getModelFeatureNames(featureData, modelId) {
    if (!featureData || !Array.isArray(featureData.models)) {
      return [];
    }
    const model = featureData.models.find((entry) => entry && entry.model_id === modelId);
    if (!model || !Array.isArray(model.feature_definitions)) {
      return [];
    }
    return model.feature_definitions
      .map((item) => item && item.name)
      .filter((name) => typeof name === "string" && name.trim().length);
  }

  function renderFeatureChips(containerId, features) {
    const container = getElement(containerId);
    if (!container) {
      return;
    }

    const names = Array.isArray(features) ? features : [];
    if (!names.length) {
      container.innerHTML = "<span class=\"chip\">No features</span>";
      return;
    }

    container.innerHTML = names.map((name) => `<span class=\"chip\">${escapeHtml(name)}</span>`).join("");
  }

  function setGateBadge(id, passed) {
    const badge = getElement(id);
    if (!badge) {
      return;
    }

    badge.classList.remove("is-pass", "is-fail");
    if (passed === true) {
      badge.classList.add("is-pass");
      badge.textContent = "Pass";
      return;
    }

    badge.classList.add("is-fail");
    badge.textContent = passed === false ? "Fail" : "N/A";
  }

  function renderPredictionSampleRows(tbodyId, rows, mapRow) {
    const body = getElement(tbodyId);
    if (!body) {
      return;
    }

    const records = Array.isArray(rows) ? rows.slice(0, 6) : [];
    if (!records.length) {
      renderPredictionSampleFallback(tbodyId, "Prediction rows unavailable.");
      return;
    }

    body.innerHTML = records
      .map((row) => {
        const cells = mapRow(row)
          .map((cell) => `<td>${escapeHtml(cell)}</td>`)
          .join("");
        return `<tr>${cells}</tr>`;
      })
      .join("");
  }

  function renderPredictionSampleFallback(tbodyId, message) {
    const body = getElement(tbodyId);
    if (!body) {
      return;
    }
    body.innerHTML = `<tr><td colspan=\"3\">${escapeHtml(message)}</td></tr>`;
  }

  function renderList(id, entries, fallback) {
    const list = getElement(id);
    if (!list) {
      return;
    }

    const records = Array.isArray(entries)
      ? entries.filter((entry) => typeof entry === "string" && entry.trim().length)
      : [];

    if (!records.length) {
      list.innerHTML = `<li>${escapeHtml(fallback)}</li>`;
      return;
    }

    list.innerHTML = records.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("");
  }

  function toTitleCase(value) {
    const text = String(value || "unknown");
    return text.charAt(0).toUpperCase() + text.slice(1);
  }

  function normalizeSelloutLabel(value) {
    if (Number(value) === 1) {
      return "Sellout";
    }
    if (Number(value) === 0) {
      return "No Sellout";
    }
    return "--";
  }

  function formatMetric(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric.toFixed(3) : "--";
  }

  function formatPercentMetric(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? `${(numeric * 100).toFixed(1)}%` : "--";
  }

  function formatCurrency(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric)
      ? `$${numeric.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
      : "--";
  }

  function formatInteger(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric)
      ? numeric.toLocaleString("en-US", { maximumFractionDigits: 0 })
      : "--";
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function setText(id, value) {
    const element = getElement(id);
    if (element) {
      element.textContent = String(value);
    }
  }

  function getElement(id) {
    return typeof id === "string" ? document.getElementById(id) : null;
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
})();

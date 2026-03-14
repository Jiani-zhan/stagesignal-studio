(() => {
  "use strict";

  const AGENT_DEFINITIONS = [
    { id: 1, key: "brief", run: runBriefAgent },
    { id: 2, key: "research", run: runResearchAgent },
    { id: 3, key: "audience", run: runAudienceAgent },
    { id: 4, key: "demand", run: runDemandAgent },
    { id: 5, key: "pricing", run: runPricingAgent },
    { id: 6, key: "memo", run: runMemoAgent },
    { id: 7, key: "critic", run: runCriticAgent }
  ];

  class AgentRuntime {
    constructor(data, callbacks = {}) {
      this.data = data;
      this.callbacks = callbacks;
      this.isLocked = false;
      this.reset();
    }

    reset() {
      this.currentIndex = 0;
      this.outputs = {};
      this.agentStates = AGENT_DEFINITIONS.map((agent) => ({
        id: agent.id,
        key: agent.key,
        status: "idle",
        statusText: "Idle",
        error: ""
      }));
      this.emitStateChange();
      if (typeof this.callbacks.onReset === "function") {
        this.callbacks.onReset(this.getSnapshot());
      }
    }

    getSnapshot() {
      return {
        currentIndex: this.currentIndex,
        outputs: { ...this.outputs },
        agentStates: this.agentStates.map((agentState) => ({ ...agentState })),
        hasError: this.agentStates.some((agentState) => agentState.status === "error"),
        isComplete: this.currentIndex >= AGENT_DEFINITIONS.length && !this.agentStates.some((agentState) => agentState.status === "error")
      };
    }

    async step() {
      if (this.isLocked || this.currentIndex >= AGENT_DEFINITIONS.length) {
        return false;
      }

      const definition = AGENT_DEFINITIONS[this.currentIndex];
      const agentState = this.agentStates[this.currentIndex];
      this.isLocked = true;

      this.updateAgentState(agentState, "running", "Running", "");

      try {
        const context = {
          data: this.data,
          outputs: this.outputs,
          currentIndex: this.currentIndex
        };

        await delay(180);
        const output = definition.run(context);

        this.outputs[definition.key] = output;
        this.updateAgentState(agentState, "complete", "Complete", "");
        this.currentIndex += 1;

        if (typeof this.callbacks.onAgentComplete === "function") {
          this.callbacks.onAgentComplete({
            agentId: definition.id,
            agentKey: definition.key,
            output,
            snapshot: this.getSnapshot()
          });
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        this.updateAgentState(agentState, "error", "Error", message);

        if (typeof this.callbacks.onError === "function") {
          this.callbacks.onError({
            agentId: definition.id,
            agentKey: definition.key,
            error: message,
            snapshot: this.getSnapshot()
          });
        }
      } finally {
        this.isLocked = false;
      }

      return true;
    }

    async runFullPipeline() {
      while (!this.getSnapshot().hasError && this.currentIndex < AGENT_DEFINITIONS.length) {
        const progressed = await this.step();
        if (!progressed) {
          break;
        }
      }
      return this.getSnapshot();
    }

    updateAgentState(agentState, status, statusText, error) {
      agentState.status = status;
      agentState.statusText = statusText;
      agentState.error = error || "";
      this.emitStateChange();
    }

    emitStateChange() {
      if (typeof this.callbacks.onStateChange === "function") {
        this.callbacks.onStateChange(this.getSnapshot());
      }
    }
  }

  function runBriefAgent(context) {
    const brief = context.data.eventBrief || {};
    const eventName = brief.event_name || "Unknown Event";
    const city = brief.city || "Unknown City";
    const venue = brief.venue_name || "Unknown Venue";

    return {
      ...brief,
      launchNarrative: `${eventName} in ${city} at ${venue}`,
      candidateRange: [brief.candidate_price_low, brief.candidate_price_high].filter((value) => Number.isFinite(value))
    };
  }

  function runResearchAgent(context) {
    const sourceHealth = context.data.sourceHealth || {};
    const inventory = Array.isArray(sourceHealth.source_inventory) ? sourceHealth.source_inventory : [];
    const parsedCount = inventory.filter((source) => source.status === "parsed").length;
    const warningCount = Array.isArray(sourceHealth.warnings) ? sourceHealth.warnings.length : 0;

    return {
      sourceCount: inventory.length,
      parsedCount,
      warningCount,
      deterministicSeed: sourceHealth.deterministic_seed,
      summary: `Loaded ${inventory.length} sources (${parsedCount} parsed) with ${warningCount} warning${warningCount === 1 ? "" : "s"}.`,
      sourceHealth
    };
  }

  function runAudienceAgent(context) {
    const segments = Array.isArray(context.data.segments) ? context.data.segments : [];
    const audienceText = Array.isArray(context.data.audienceText) ? context.data.audienceText : [];
    const rankedSegments = [...segments].sort((a, b) => {
      const scoreA = Number(a.segment_size_pct || 0) * Number(a.expected_conversion_base || 0);
      const scoreB = Number(b.segment_size_pct || 0) * Number(b.expected_conversion_base || 0);
      return scoreB - scoreA;
    });
    const topSegment = rankedSegments[0] || null;
    const themePrevalence = computeThemePrevalence(audienceText);

    return {
      segments: rankedSegments,
      segmentCount: rankedSegments.length,
      topSegment,
      themePrevalence,
      summary: topSegment
        ? `${topSegment.segment_name} leads at ${(topSegment.segment_size_pct * 100).toFixed(1)}% of target audience.`
        : "No segment data available."
    };
  }

  function runDemandAgent(context) {
    const demandScenarios = Array.isArray(context.data.demandScenarios) ? context.data.demandScenarios : [];
    const byOrder = ["conservative", "base", "optimistic"];
    const orderedScenarios = byOrder
      .map((name) => demandScenarios.find((scenario) => scenario.scenario_name === name))
      .filter(Boolean);

    const baseScenario =
      orderedScenarios.find((scenario) => scenario.scenario_name === "base") || orderedScenarios[0] || demandScenarios[0] || null;

    return {
      scenarios: orderedScenarios.length ? orderedScenarios : demandScenarios,
      baseScenario,
      expectedAttendance: baseScenario ? baseScenario.expected_attendance : 0,
      occupancyBand: baseScenario ? toPercent(baseScenario.expected_occupancy_pct) : "--",
      summary: baseScenario
        ? `Base scenario projects ${baseScenario.expected_attendance} attendees at ${toPercent(baseScenario.expected_occupancy_pct)} occupancy.`
        : "No demand scenarios available."
    };
  }

  function runPricingAgent(context) {
    const pricing = context.data.pricingRecommendation || {};
    const brief = context.outputs.brief || context.data.eventBrief || {};
    const demand = context.outputs.demand || {};
    const venueCapacity = Number.isFinite(brief.venue_capacity) ? brief.venue_capacity : 0;
    const baseScenario = demand.baseScenario || null;
    const occupancyEstimate = demand.baseScenario && Number.isFinite(demand.baseScenario.expected_occupancy_pct)
      ? demand.baseScenario.expected_occupancy_pct
      : 0.9;
    const baseAttendance =
      baseScenario && Number.isFinite(baseScenario.expected_attendance)
        ? baseScenario.expected_attendance
        : venueCapacity * occupancyEstimate;
    const baseRevenue =
      baseScenario && Number.isFinite(baseScenario.expected_revenue)
        ? baseScenario.expected_revenue
        : null;
    const gaPrice = Number(pricing.recommended_ga_price);

    const purchaseCurve = buildPurchaseCurve(pricing, venueCapacity, baseAttendance);
    const baselinePoint =
      purchaseCurve.find((point) => point.isBaseline) || purchaseCurve[Math.floor(purchaseCurve.length / 2)] || null;
    const baselineProbability = baselinePoint ? baselinePoint.probability : 0.8;
    const revenueScale =
      Number.isFinite(baseRevenue) && Number.isFinite(gaPrice) && gaPrice > 0 && baseAttendance > 0
        ? baseRevenue / (gaPrice * baseAttendance)
        : 1;

    const revenueCurve = purchaseCurve.map((point) => {
      const attendanceRatio = baselineProbability > 0 ? point.probability / baselineProbability : 0;
      const expectedAttendance = Math.min(venueCapacity, Math.max(0, baseAttendance * attendanceRatio));
      return {
        price: point.price,
        revenue: Number((point.price * expectedAttendance * revenueScale).toFixed(2))
      };
    });

    return {
      ...pricing,
      purchaseCurve,
      revenueCurve,
      acceptableRangeLabel: formatCurrencyRange(pricing.acceptable_range_low, pricing.acceptable_range_high),
      recommendedGaLabel: formatCurrency(pricing.recommended_ga_price),
      summary: `Recommended GA ${formatCurrency(pricing.recommended_ga_price)} within acceptable range ${formatCurrencyRange(
        pricing.acceptable_range_low,
        pricing.acceptable_range_high
      )}.`
    };
  }

  function runMemoAgent(context) {
    const memo = context.data.memo || {};
    const actions = [memo.pricing_decision, memo.channel_decision, memo.positioning_decision, memo.next_experiment].filter(Boolean);
    const risks = Array.isArray(memo.key_risks) ? memo.key_risks : [];

    return {
      ...memo,
      actions,
      risks,
      exportedAtUtc: new Date().toISOString()
    };
  }

  function runCriticAgent(context) {
    const memo = context.outputs.memo || context.data.memo || {};
    const pricing = context.outputs.pricing || context.data.pricingRecommendation || {};
    const demand = context.outputs.demand || {};
    const issues = [];

    const memoGa = memo.support_metrics ? memo.support_metrics.recommended_ga_price : undefined;
    if (Number.isFinite(memoGa) && Number.isFinite(pricing.recommended_ga_price) && Math.abs(memoGa - pricing.recommended_ga_price) > 0.01) {
      issues.push("Memo recommended GA price does not match pricing output.");
    }

    const memoAttendance = memo.support_metrics ? memo.support_metrics.expected_attendance_base : undefined;
    const demandAttendance = demand.baseScenario ? demand.baseScenario.expected_attendance : undefined;
    if (Number.isFinite(memoAttendance) && Number.isFinite(demandAttendance) && memoAttendance !== demandAttendance) {
      issues.push("Memo expected attendance differs from demand base scenario.");
    }

    return {
      passed: issues.length === 0,
      issues,
      statusLabel: issues.length === 0 ? "QA checks passed." : `QA found ${issues.length} issue${issues.length === 1 ? "" : "s"}.`
    };
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
      const weight = Number.isFinite(entry.engagement_signal) ? Math.max(1, Math.round(entry.engagement_signal / 50)) : 1;

      dictionary.forEach((dictEntry, index) => {
        if (dictEntry.patterns.some((pattern) => text.includes(pattern))) {
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
    const baseProbability =
      venueCapacity > 0
        ? clamp(baseAttendance / venueCapacity, 0.05, 0.98)
        : 0.84;
    const elasticity = Number.isFinite(ga) && ga > 0 ? 1 / ga : 0.013;

    const curve = [];
    let baselineIndex = 0;
    let smallestDistance = Number.POSITIVE_INFINITY;
    for (let i = 0; i < steps; i += 1) {
      const price = minPrice + stepSize * i;
      const distance = Math.abs(price - centerPrice);
      if (distance < smallestDistance) {
        smallestDistance = distance;
        baselineIndex = i;
      }

      const probability = clamp(baseProbability * Math.exp(-elasticity * (price - centerPrice)), 0.03, 0.995);
      curve.push({
        price: Number(price.toFixed(2)),
        probability: Number(probability.toFixed(4)),
        isBaseline: false
      });
    }

    if (curve[baselineIndex]) {
      curve[baselineIndex].isBaseline = true;
    }

    return curve;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function formatCurrency(value) {
    return Number.isFinite(value) ? `$${Number(value).toFixed(2)}` : "--";
  }

  function formatCurrencyRange(low, high) {
    if (!Number.isFinite(low) || !Number.isFinite(high)) {
      return "--";
    }
    return `${formatCurrency(low)} - ${formatCurrency(high)}`;
  }

  function toPercent(value) {
    return Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "--";
  }

  function delay(milliseconds) {
    return new Promise((resolve) => {
      setTimeout(resolve, milliseconds);
    });
  }

  window.StageSignalAgentSystem = {
    createAgentRuntime(data, callbacks) {
      return new AgentRuntime(data, callbacks);
    }
  };
})();

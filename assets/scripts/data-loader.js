(() => {
  "use strict";

  const DATA_FILES = Object.freeze({
    heroEventBrief: "assets/data/hero_event_brief.json",
    heroSegments: "assets/data/hero_segments.json",
    heroDemandScenarios: "assets/data/hero_demand_scenarios.json",
    heroPricingRecommendation: "assets/data/hero_pricing_recommendation.json",
    heroMemo: "assets/data/hero_memo.json",
    sourceHealthReport: "assets/data/source_health_report.json",
    audienceText: "assets/data/audience_text.json",
    modelPerformance: "assets/data/model_performance.json",
    modelPredictions: "assets/data/model_predictions.json",
    modelFeatures: "assets/data/model_features.json"
  });

  const OPTIONAL_DATA_KEYS = new Set(["modelPerformance", "modelPredictions", "modelFeatures"]);

  let cachePromise = null;
  let cacheData = null;

  async function fetchJson(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to load ${path}: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  function normalizeData(raw) {
    return {
      eventBrief: raw.heroEventBrief && typeof raw.heroEventBrief === "object" ? raw.heroEventBrief : {},
      segments: Array.isArray(raw.heroSegments) ? raw.heroSegments : [],
      demandScenarios: Array.isArray(raw.heroDemandScenarios) ? raw.heroDemandScenarios : [],
      pricingRecommendation:
        raw.heroPricingRecommendation && typeof raw.heroPricingRecommendation === "object"
          ? raw.heroPricingRecommendation
          : {},
      memo: raw.heroMemo && typeof raw.heroMemo === "object" ? raw.heroMemo : {},
      sourceHealth: raw.sourceHealthReport && typeof raw.sourceHealthReport === "object" ? raw.sourceHealthReport : {},
      audienceText: Array.isArray(raw.audienceText) ? raw.audienceText : [],
      modelPerformance: raw.modelPerformance && typeof raw.modelPerformance === "object" ? raw.modelPerformance : null,
      modelPredictions: raw.modelPredictions && typeof raw.modelPredictions === "object" ? raw.modelPredictions : null,
      modelFeatures: raw.modelFeatures && typeof raw.modelFeatures === "object" ? raw.modelFeatures : null
    };
  }

  async function loadAllData(options = {}) {
    const forceReload = Boolean(options.forceReload);

    if (!forceReload && cacheData) {
      return cacheData;
    }

    if (!forceReload && cachePromise) {
      return cachePromise;
    }

    const entries = Object.entries(DATA_FILES);
    cachePromise = Promise.all(
      entries.map(([key, path]) =>
        fetchJson(path)
          .then((payload) => [key, payload])
          .catch((error) => {
            if (OPTIONAL_DATA_KEYS.has(key)) {
              console.warn(`Optional artifact unavailable (${path}).`, error);
              return [key, null];
            }
            throw error;
          })
      )
    )
      .then((pairs) => {
        const raw = Object.fromEntries(pairs);
        cacheData = normalizeData(raw);
        return cacheData;
      })
      .catch((error) => {
        cachePromise = null;
        throw error;
      });

    return cachePromise;
  }

  function clearCache() {
    cachePromise = null;
    cacheData = null;
  }

  window.StageSignalDataLoader = {
    loadAllData,
    clearCache,
    getDataFiles() {
      return { ...DATA_FILES };
    }
  };
})();

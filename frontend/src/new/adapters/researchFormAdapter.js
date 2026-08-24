import {
  condenseAnalysisGoals,
  createTask,
  polishAnalysisGoals,
  recommendCompetitors,
} from "../../api/client";

export const DEPTH_MAP = {
  Quick: "quick",
  Standard: "standard",
  Deep: "deep",
};

export const EVIDENCE_POLICY_MAP = {
  Strict: "high",
  Balanced: "standard",
  Exploratory: "low",
};

export const WORKFLOW_MODE_MAP = {
  "Adaptive review": "adaptive_review",
  "Single pass": "single_pass",
};

export function createInitialResearchForm() {
  return {
    targetProduct: "",
    competitors: [],
    researchGoal: "",
    depth: "Standard",
    evidencePolicy: "Balanced",
    audience: "product team",
    advancedOptions: {
      domain: "general_product",
      notes: "",
      socialPlatform: "disabled",
      workflowMode: "Adaptive review",
    },
  };
}

export function toTaskConfig(form) {
  const targetProduct = form.targetProduct.trim();
  const competitors = form.competitors.map((item) => item.trim()).filter(Boolean);
  const researchGoal = form.researchGoal.trim();
  validateForm({ targetProduct, competitors, researchGoal });

  return {
    domain: form.advancedOptions.domain,
    target_product: targetProduct,
    competitors,
    analysis_goals: [researchGoal],
    depth: requiredMapping(DEPTH_MAP, form.depth, "research depth"),
    evidence_strictness: requiredMapping(EVIDENCE_POLICY_MAP, form.evidencePolicy, "evidence policy"),
    audience: form.audience,
    notes: form.advancedOptions.notes.trim(),
    workflow_mode: requiredMapping(WORKFLOW_MODE_MAP, form.advancedOptions.workflowMode, "workflow mode"),
    social_listening: socialListeningConfig(form.advancedOptions.socialPlatform),
  };
}

export async function getCompetitorRecommendations(form) {
  const targetProduct = form.targetProduct.trim();
  if (!targetProduct) throw new Error("Enter a target product before requesting recommendations.");
  return recommendCompetitors({
    target_product: targetProduct,
    domain: form.advancedOptions.domain,
    existing_competitors: form.competitors,
    audience: form.audience,
    max_results: 5,
  });
}

export async function getPolishedGoal(form) {
  const draft = form.researchGoal.trim();
  if (!draft) throw new Error("Enter a research goal before refining it.");
  const response = await polishAnalysisGoals(goalAssistPayload(form, draft));
  return response.formatted_text || response.goals?.join("\n") || "";
}

export async function getCondensedGoal(form) {
  const draft = form.researchGoal.trim();
  if (!draft) throw new Error("Enter a research goal before condensing it.");
  const response = await condenseAnalysisGoals({
    ...goalAssistPayload(form, draft),
    max_words: 1000,
  });
  return response.condensed_text || "";
}

export async function createResearch(form) {
  return createTask(toTaskConfig(form));
}

function goalAssistPayload(form, draft) {
  return {
    draft,
    domain: form.advancedOptions.domain,
    target_product: form.targetProduct.trim(),
    competitors: form.competitors,
    audience: form.audience,
  };
}

function socialListeningConfig(platform) {
  if (platform === "disabled") return { enabled: false, platforms: [] };
  if (platform === "xiaohongshu") {
    return { enabled: true, platforms: [{ platform: "xiaohongshu", enabled: true }] };
  }
  throw new Error(`Unsupported social listening selection: ${platform}`);
}

function validateForm({ targetProduct, competitors, researchGoal }) {
  if (!targetProduct) throw new Error("Target product is required.");
  if (!competitors.length) throw new Error("Add at least one competitor.");
  if (competitors.length > 5) throw new Error("EvidenceGraph supports at most five competitors.");
  const normalizedTarget = normalize(targetProduct);
  const normalizedCompetitors = competitors.map(normalize);
  if (normalizedCompetitors.includes(normalizedTarget)) throw new Error("The target product cannot also be a competitor.");
  if (new Set(normalizedCompetitors).size !== normalizedCompetitors.length) throw new Error("Competitors must be unique.");
  if (!researchGoal) throw new Error("Research goal is required.");
}

function requiredMapping(mapping, value, label) {
  const mapped = mapping[value];
  if (!mapped) throw new Error(`Unsupported ${label}: ${value}`);
  return mapped;
}

function normalize(value) {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

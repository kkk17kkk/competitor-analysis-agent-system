import { getTask } from "../../api/client";
import { toEvidenceViewModel } from "./evidenceAdapter";
import { toReviewViewModel } from "./reviewAdapter";

const SECTION_KEYS = {
  summary: ["executive_summary", "structured_summary"],
  insights: ["differentiated_insights"],
};

const CLAIM_TYPE_LABELS = {
  agent_capability: "Agent capability",
  comparative_browser_interaction: "Browser interaction",
  comparative_feature: "Feature comparison",
  comparative_positioning: "Positioning",
  feature: "Features",
  positioning: "Positioning",
  pricing: "Pricing",
  security: "Security",
  security_risk: "Security risk",
  target_user: "Target user",
  third_party_context: "Third-party context",
};

export async function loadReportViewModel(taskId) {
  return toReportViewModel(await getTask(taskId));
}

export async function loadReportWorkspace(taskId) {
  const payload = await getTask(taskId);
  return {
    dataSource: "backend",
    report: toReportViewModel(payload),
    evidence: toEvidenceViewModel(payload),
    reviews: toReviewViewModel(payload),
  };
}

export function toReportViewModel(payload) {
  const result = payload?.task ? payload : null;
  const task = result?.task || payload || null;
  const report = result?.report || null;
  const claims = Array.isArray(result?.claims) ? result.claims : [];
  const sections = Array.isArray(report?.sections) ? report.sections : [];
  const config = task?.config || {};
  const products = [config.target_product, ...(config.competitors || [])].filter(Boolean);
  const includedClaims = claims.filter((claim) => claim.included_in_report);
  const openTickets = Array.isArray(result?.review_tickets)
    ? result.review_tickets.filter((ticket) => !["resolved", "dismissed"].includes(ticket.status)).length
    : null;

  return {
    id: task?.task_id || null,
    title: report?.title || null,
    subject: config.target_product || null,
    competitors: Array.isArray(config.competitors) ? config.competitors : [],
    generatedAt: report?.created_at || null,
    updatedAt: task?.updated_at || null,
    status: report?.status || task?.status || null,
    sourceCount: Array.isArray(result?.sources) ? result.sources.length : null,
    evidenceCoverage: percentageOrNull(report?.evidence_coverage_rate),
    openReviews: openTickets,
    summary: sectionText(sections, SECTION_KEYS.summary),
    highlights: [],
    matrix: mapComparisonMatrix(includedClaims, products),
    insights: sectionText(sections, SECTION_KEYS.insights).map(mapGeneratedInsight),
    opportunities: Array.isArray(report?.swot?.opportunities) ? unique(report.swot.opportunities) : [],
    trust: mapTrust(result?.trust_summary, report),
    sections: sections.map((section) => ({
      id: section.section_id || null,
      key: section.section_key || null,
      title: section.title || null,
      markdown: section.markdown || "",
      status: section.status || null,
      claimIds: Array.isArray(section.claim_ids) ? section.claim_ids : [],
    })),
  };
}

function mapComparisonMatrix(claims, products) {
  const grouped = new Map();
  for (const claim of claims) {
    if (!claim.claim_type || !claim.product || !products.includes(claim.product)) continue;
    if (!grouped.has(claim.claim_type)) grouped.set(claim.claim_type, new Map());
    const byProduct = grouped.get(claim.claim_type);
    const values = byProduct.get(claim.product) || [];
    values.push(claim.claim);
    byProduct.set(claim.product, values);
  }
  return {
    columns: products,
    rows: [...grouped.entries()].map(([claimType, byProduct]) => ({
      dimension: CLAIM_TYPE_LABELS[claimType] || displayLabel(claimType),
      values: Object.fromEntries(products.map((product) => [product, byProduct.get(product)?.join(" ") || null])),
    })),
  };
}

function mapGeneratedInsight(text) {
  return {
    id: null,
    text,
    product: null,
    confidence: null,
    status: null,
    icon: "icon-insight-trend.svg",
    tone: "info",
  };
}

function mapTrust(trust, report) {
  if (!trust && !report) return null;
  return {
    bindingRate: percentageOrNull(trust?.claim_evidence_binding_rate),
    passedClaims: numberOrNull(trust?.passed_claim_count),
    totalClaims: numberOrNull(trust?.total_claim_count ?? report?.claim_count),
    totalEvidence: numberOrNull(trust?.total_evidence_count),
    totalSources: numberOrNull(trust?.total_source_count),
    unresolvedTickets: numberOrNull(trust?.unresolved_ticket_count),
    summary: trust?.summary || null,
  };
}

function sectionText(sections, keys) {
  const section = keys.map((key) => sections.find((item) => item.section_key === key)).find(Boolean);
  if (!section) return [];
  return markdownToDisplayItems(section.markdown).filter((item) => item !== section.title);
}

export function markdownToDisplayItems(markdown) {
  if (!markdown) return [];
  return markdown
    .split(/\r?\n/)
    .map((line) => line.replace(/^#{1,6}\s+/, "").replace(/^[-*]\s+/, "").trim())
    .filter(Boolean);
}

function displayLabel(value) {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function numberOrNull(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function percentageOrNull(value) {
  const number = numberOrNull(value);
  return number === null ? null : Math.round(number * 100);
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

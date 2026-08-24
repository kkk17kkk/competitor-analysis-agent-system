import { getTask } from "../../api/client";
import { toEvidenceViewModel } from "./evidenceAdapter";
import { toReviewViewModel } from "./reviewAdapter";

const HIGHLIGHT_PRESENTATION = {
  strongest_advantage: { label: "Strongest advantage", icon: "icon-advantage-trophy.svg", tone: "success" },
  biggest_risk: { label: "Biggest risk", icon: "icon-risk-alert-shield.svg", tone: "danger" },
  recommended_direction: { label: "Recommended direction", icon: "icon-direction-compass.svg", tone: "lilac" },
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
  const sections = Array.isArray(report?.sections) ? report.sections : [];
  const config = task?.config || {};
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
    summary: structuredItems(report?.executive_summary).map((item) => item.text),
    highlights: mapHighlights(report?.decision_highlights),
    matrix: mapComparisonMatrix(report?.comparison_matrix, [config.target_product, ...(config.competitors || [])].filter(Boolean)),
    insights: structuredItems(report?.key_insights).map(mapGeneratedInsight),
    opportunities: structuredItems(report?.strategic_opportunities).map((item) => item.text),
    limitations: Array.isArray(report?.limitations) ? report.limitations.filter(Boolean) : [],
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

function mapComparisonMatrix(rows, products) {
  return {
    columns: products,
    rows: Array.isArray(rows) ? rows.filter((row) => row?.dimension && row?.values).map((row) => ({
      dimension: row.dimension,
      values: Object.fromEntries(products.map((product) => [product, row.values[product] || null])),
    })) : [],
  };
}

function mapGeneratedInsight(item) {
  return {
    id: null,
    text: item.text,
    product: item.product || null,
    confidence: item.confidence ? displayLabel(item.confidence) : null,
    status: null,
    icon: "icon-insight-trend.svg",
    tone: "info",
  };
}

function mapHighlights(value) {
  if (!value || typeof value !== "object") return [];
  return Object.entries(HIGHLIGHT_PRESENTATION).flatMap(([key, presentation]) => {
    const item = value[key];
    if (!item?.title) return [];
    return [{
      ...presentation,
      title: item.title,
      body: item.body || null,
      confidence: item.confidence ? `${displayLabel(item.confidence)} confidence` : null,
    }];
  });
}

function structuredItems(value) {
  return Array.isArray(value) ? value.filter((item) => item?.text) : [];
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

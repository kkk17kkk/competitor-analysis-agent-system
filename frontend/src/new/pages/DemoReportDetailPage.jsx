import React from "react";
import { reportDetail } from "../mock/reports";
import { evidenceItems, reviewItems } from "../mock/evidence";
import { ReportDetailView } from "./ReportDetailPage";

export function DemoReportDetailPage() {
  return <ReportDetailView report={legacyReport(reportDetail)} evidence={legacyEvidence(evidenceItems)} reviews={legacyReviews(reviewItems)} />;
}

function legacyReport(report) {
  return {
    ...report,
    generatedAt: report.generated,
    sourceCount: report.sources,
    evidenceCoverage: report.coverage,
    matrix: {
      columns: [report.subject, ...report.competitors],
      rows: report.matrix.map((row) => ({ dimension: row.dimension, values: { [report.subject]: row.cursor, [report.competitors[0]]: row.copilot, [report.competitors[1]]: row.windsurf, [report.competitors[2]]: row.trae } })),
    },
    trust: { summary: "Static demo data", passedClaims: 136, totalEvidence: null },
  };
}

function legacyEvidence(items) {
  return items.map((item, index) => ({ id: `demo-claim-${index}`, text: item.claim, product: item.product, type: item.dimension, status: item.status === "Verified" ? "passed" : "uncertain", note: item.summary, evidence: [] }));
}

function legacyReviews(items) {
  return items.map((item) => ({ id: item.id, status: "open", severity: item.severity, missingEvidenceType: item.title, reason: item.detail, affectedArtifacts: [item.affected], rerunCount: Number(item.attempts.split(" ")[0]), maxReruns: Number(item.attempts.split(" ")[2]), resolutionSummary: null, product: null, preferredSourceType: null }));
}

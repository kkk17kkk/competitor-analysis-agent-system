import { excludeEvidence, getTask, restoreEvidence } from "../../api/client";

export async function loadEvidenceViewModel(taskId) {
  return toEvidenceViewModel(await getTask(taskId));
}

export function toEvidenceViewModel(payload) {
  const claims = Array.isArray(payload?.claims) ? payload.claims : [];
  const evidence = Array.isArray(payload?.evidence) ? payload.evidence : [];
  const sources = Array.isArray(payload?.sources) ? payload.sources : [];
  const evidenceById = new Map(evidence.map((item) => [item.evidence_id, item]));
  const sourceById = new Map(sources.map((item) => [item.source_id, item]));

  return claims.map((claim) => ({
    id: claim.claim_id || null,
    text: claim.claim || null,
    product: claim.product || null,
    type: claim.claim_type || null,
    confidence: claim.confidence || null,
    status: claim.verified_status || null,
    includedInReport: Boolean(claim.included_in_report),
    note: claim.note || null,
    evidence: (claim.supporting_evidence || []).map((evidenceId) => {
      const item = evidenceById.get(evidenceId);
      if (!item) return { id: evidenceId, unavailable: true, source: null };
      const source = sourceById.get(item.source_id);
      return {
        id: item.evidence_id || null,
        product: item.product || null,
        type: item.evidence_type || null,
        summary: item.summary || null,
        locator: item.quote_or_locator || null,
        confidence: item.confidence || null,
        risk: item.risk || null,
        status: item.status || null,
        excludedReason: item.excluded_reason || null,
        unavailable: false,
        source: source ? {
          id: source.source_id || null,
          title: source.title || null,
          url: source.url || null,
          type: source.source_type || null,
          product: source.product || null,
          retrievedAt: source.retrieved_at || null,
          confidence: source.confidence || null,
          risk: source.risk || null,
        } : null,
      };
    }),
  }));
}

export async function setEvidenceExcluded(evidenceId, reason) {
  return excludeEvidence(evidenceId, reason);
}

export async function setEvidenceRestored(evidenceId) {
  return restoreEvidence(evidenceId);
}

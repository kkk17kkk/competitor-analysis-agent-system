import {
  acceptReviewTicket,
  dismissReviewTicket,
  downgradeReviewTicket,
  getTask,
  markReviewTicketUnavailable,
  rerunReviewTicket,
  resolveReviewTicket,
} from "../../api/client";

const ACTIONS = {
  accept: (ticketId) => acceptReviewTicket(ticketId),
  rerun: (ticketId) => rerunReviewTicket(ticketId),
  resolve: (ticketId) => resolveReviewTicket(ticketId),
  dismiss: (ticketId) => dismissReviewTicket(ticketId),
  downgrade: (ticketId) => downgradeReviewTicket(ticketId),
  unavailable: (ticketId) => markReviewTicketUnavailable(ticketId),
};

export async function loadReviewViewModel(taskId) {
  return toReviewViewModel(await getTask(taskId));
}

export function toReviewViewModel(payload) {
  const tickets = Array.isArray(payload?.review_tickets) ? payload.review_tickets : [];
  return tickets.map(toReviewItem);
}

export function toReviewItem(ticket) {
  return {
    id: ticket.ticket_id || null,
    taskId: ticket.task_id || null,
    sourceNode: ticket.source_node || ticket.reviewer || null,
    targetNode: ticket.target_node || null,
    status: ticket.status || null,
    severity: ticket.severity || null,
    product: ticket.product || null,
    reason: ticket.reason || null,
    requiredAction: ticket.required_action || null,
    affectedArtifacts: Array.isArray(ticket.affected_artifacts) ? ticket.affected_artifacts : [],
    missingEvidenceType: ticket.missing_evidence_type || null,
    preferredSourceType: ticket.preferred_source_type || null,
    rerunCount: numberOrNull(ticket.rerun_count),
    maxReruns: numberOrNull(ticket.max_reruns),
    resolutionSummary: ticket.resolution_summary || ticket.resolution_note || null,
    addedEvidenceIds: Array.isArray(ticket.added_evidence_ids) ? ticket.added_evidence_ids : [],
    improvedClaimIds: Array.isArray(ticket.improved_claim_ids) ? ticket.improved_claim_ids : [],
    resolvedAt: ticket.resolved_at || null,
  };
}

export async function runReviewAction(action, ticketId) {
  const handler = ACTIONS[action];
  if (!handler) throw new Error(`Unsupported review action: ${action}`);
  return handler(ticketId);
}

function numberOrNull(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

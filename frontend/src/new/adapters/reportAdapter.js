import { getTask, getTasks } from "../../api/client";

const CLOSED_TICKET_STATUSES = new Set(["resolved", "dismissed"]);

export function toResearchSummary(taskPayload) {
  const task = taskPayload?.task || taskPayload;
  const result = taskPayload?.task ? taskPayload : null;
  const report = result?.report || null;
  const tickets = Array.isArray(result?.review_tickets) ? result.review_tickets : null;

  return {
    id: task?.task_id || null,
    title: report?.title || null,
    competitors: Array.isArray(task?.config?.competitors) ? task.config.competitors : [],
    targetProduct: task?.config?.target_product || null,
    updatedAt: task?.updated_at || null,
    status: task?.status || null,
    evidenceCoverage: percentageOrNull(report?.evidence_coverage_rate),
    reviewCount: tickets
      ? tickets.filter((ticket) => !CLOSED_TICKET_STATUSES.has(ticket.status)).length
      : null,
    sourceCount: Array.isArray(result?.sources) ? result.sources.length : null,
  };
}

export async function loadResearchSummaries() {
  const tasks = await getTasks();
  const details = await Promise.all(tasks.map((task) => getTask(task.task_id)));
  return details.map(toResearchSummary);
}

export function formatReportDate(value) {
  if (!value) return "Unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}

function numberOrNull(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function percentageOrNull(value) {
  const number = numberOrNull(value);
  return number === null ? null : Math.round(number * 100);
}

import { getTask, streamTaskRun } from "../../api/client";

export const RESEARCH_STAGES = [
  { id: "plan", label: "Plan research" },
  { id: "collect", label: "Collect sources" },
  { id: "evidence", label: "Build evidence" },
  { id: "verify", label: "Verify insights" },
  { id: "report", label: "Prepare report" },
];

const NODE_STAGE = {
  planner: "plan",
  template: "plan",
  research: "collect",
  source_normalizer: "collect",
  interaction: "collect",
  social_listening: "collect",
  evidence_extractor: "evidence",
  analyst: "evidence",
  critic: "verify",
  review_ticket: "verify",
  review_router: "verify",
  review_research: "verify",
  review_social: "verify",
  review_interaction: "verify",
  review_analyst: "verify",
  review_fallback: "verify",
  review_resolution: "verify",
  review_loop_stop: "verify",
  evidence_reviewer: "verify",
  trust_summary: "verify",
  writer: "report",
  finalize: "report",
};

const ACTIVITY_COPY = {
  brief_created: "Research scope and questions are ready",
  template_selected: "Research approach selected",
  search_completed: "Initial source collection completed",
  supplemental_search: "Collecting additional sources for evidence gaps",
  sources_normalized: "Sources organized and checked for relevance",
  interaction_evidence_created: "Product workflow observations added",
  interaction_completed: "Product workflows examined",
  interaction_skipped: "Interactive review was not required",
  social_listening_completed: "Public audience signals collected",
  social_listening_skipped: "Social listening was not included",
  evidence_extracted: "Source material converted into traceable evidence",
  claims_generated: "Evidence-backed insights assembled",
  quality_review_passed: "Evidence coverage passed review",
  review_tickets_created: "Evidence gaps identified for review",
  evidence_gate_completed: "Evidence and insight consistency checked",
  trust_summary_created: "Research confidence assessment prepared",
  report_drafted: "Decision report drafted",
  workflow_completed: "Research completed",
};

export function createResearchProgress(taskPayload, startedAt = Date.now()) {
  const task = taskPayload?.task || taskPayload;
  return {
    taskId: task?.task_id || null,
    title: researchTitle(task),
    competitors: task?.config?.competitors || [],
    startedAt,
    stage: "plan",
    label: "Plan research",
    progress: 4,
    activity: [{ id: "started", message: "Preparing the research plan", createdAt: startedAt }],
    metrics: { sources: 0, evidence: 0, insights: 0, reviewItems: 0 },
    needsAttention: null,
    status: "running",
  };
}

export async function runResearchWorkflow(taskId, onProgress) {
  const startedAt = Date.now();
  let progress = createResearchProgress({ task_id: taskId, config: {} }, startedAt);
  const publish = (next) => { progress = next; onProgress(next); };
  publish(progress);

  try {
    const task = await getTask(taskId);
    publish(createResearchProgress(task, startedAt));
    if (task?.task?.task_id === taskId) {
      publish(completedProgress(progress));
      return { status: "completed", result: task };
    }
    if (task?.status === "cancelled") {
      publish(cancelledProgress(progress));
      return { status: "cancelled", result: task };
    }
    if (task?.status === "failed") throw new Error("The research task previously failed.");
    if (task?.status === "running") {
      publish(existingRunProgress(progress));
      return { status: "tracking" };
    }
    const streamedResult = await streamTaskRun(taskId, {
      onStart: () => publish({ ...progress, status: "running" }),
      onTrace: (event) => publish(applyTrace(progress, event)),
      onState: (state) => publish(applyState(progress, state)),
      onResult: (result) => publish(applyResult(progress, result)),
      onDone: (event) => {
        if (event.status === "cancelled") publish(cancelledProgress(progress));
      },
    });

    const status = streamedResult?.task?.status;
    if (status === "cancelled") return { status: "cancelled", result: streamedResult };
    if (!streamedResult?.task) throw new Error("The research result was not returned.");
    const storedResult = await waitForStoredResult(taskId);
    publish(completedProgress(progress, storedResult));
    return { status: "completed", result: storedResult };
  } catch (error) {
    const failure = toWorkflowFailure(error);
    publish({ ...progress, status: failure.status, needsAttention: failure.attention, activity: appendActivity(progress.activity, failure.message, `failure-${Date.now()}`) });
    return { status: failure.status, error: failure.message };
  }
}

export async function trackExistingResearch(taskId, onProgress, shouldContinue = () => true) {
  let progress = existingRunProgress(createResearchProgress({ task_id: taskId, config: {} }));
  const publish = (next) => { progress = next; onProgress(next); };
  publish(progress);
  try {
    while (shouldContinue()) {
      const payload = await getTask(taskId);
      if (payload?.task?.task_id === taskId) {
        publish(completedProgress(applyResult(progress, payload)));
        return { status: "completed", result: payload };
      }
      if (payload?.status === "failed") throw new Error("The research task failed.");
      if (payload?.status === "cancelled") {
        publish(cancelledProgress(progress));
        return { status: "cancelled", result: payload };
      }
      await delay(1500);
    }
    return { status: "stopped" };
  } catch (error) {
    const failure = toWorkflowFailure(error);
    publish({ ...progress, status: failure.status, needsAttention: failure.attention, activity: appendActivity(progress.activity, failure.message, `failure-${Date.now()}`) });
    return { status: failure.status, error: failure.message };
  }
}

export function applyTrace(progress, event) {
  const stage = NODE_STAGE[event?.node] || progress.stage;
  const index = stageIndex(stage);
  const message = ACTIVITY_COPY[event?.event_type] || stageActivity(stage);
  const attention = traceAttention(event);
  return {
    ...progress,
    stage,
    label: RESEARCH_STAGES[index].label,
    progress: Math.max(progress.progress, [12, 30, 50, 70, 88][index]),
    activity: appendActivity(progress.activity, message, event?.event_id || `${stage}-${progress.activity.length}`),
    needsAttention: attention || progress.needsAttention,
    status: attention ? "needs_attention" : progress.status,
  };
}

export function applyState(progress, state) {
  const metrics = {
    sources: finiteCount(state?.source_count, progress.metrics.sources),
    evidence: finiteCount(state?.evidence_count, progress.metrics.evidence),
    insights: finiteCount(state?.claim_count, progress.metrics.insights),
    reviewItems: finiteCount(state?.ticket_count, progress.metrics.reviewItems),
  };
  let activity = progress.activity;
  if (metrics.sources > progress.metrics.sources) activity = appendActivity(activity, `Collected ${metrics.sources} sources`, `sources-${metrics.sources}`);
  if (metrics.evidence > progress.metrics.evidence) activity = appendActivity(activity, `Built ${metrics.evidence} evidence items`, `evidence-${metrics.evidence}`);
  if (metrics.insights > progress.metrics.insights) activity = appendActivity(activity, `Prepared ${metrics.insights} insights for verification`, `insights-${metrics.insights}`);
  return { ...progress, metrics, activity };
}

function applyResult(progress, result) {
  const metrics = {
    sources: result.sources?.length ?? progress.metrics.sources,
    evidence: result.evidence?.length ?? progress.metrics.evidence,
    insights: result.claims?.length ?? progress.metrics.insights,
    reviewItems: result.review_tickets?.filter((ticket) => !["resolved", "dismissed"].includes(ticket.status)).length ?? progress.metrics.reviewItems,
  };
  return { ...progress, stage: "report", label: "Prepare report", progress: Math.max(progress.progress, 96), metrics };
}

async function waitForStoredResult(taskId) {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const payload = await getTask(taskId);
    if (payload?.task?.task_id === taskId) return payload;
    await delay(150);
  }
  throw new Error("The completed research result is still being saved.");
}

function completedProgress(progress) {
  return { ...progress, stage: "report", label: "Prepare report", progress: 100, status: "completed", needsAttention: null, activity: appendActivity(progress.activity, "Research completed", "completed") };
}

function cancelledProgress(progress) {
  return { ...progress, status: "cancelled", needsAttention: { title: "Research was cancelled", message: "No report was generated for this run." } };
}

function existingRunProgress(progress) {
  return { ...progress, stage: null, label: "Research in progress", progress: 0, status: "tracking", activity: appendActivity(progress.activity, "Research is currently running", "existing-run") };
}

export function toWorkflowFailure(error) {
  const detail = String(error?.message || "").toLowerCase();
  if (detail.includes("cancel")) return { status: "cancelled", message: "Research was cancelled", attention: { title: "Research was cancelled", message: "No report was generated for this run." } };
  if (detail.includes("login") || detail.includes("xiaohongshu") || detail.includes("xhs")) return { status: "needs_attention", message: "A social research source needs attention", attention: { title: "Social source login required", message: "Sign in to the selected social source before starting this research again." } };
  if (detail.includes("provider") || detail.includes("not ready") || detail.includes("unavailable")) return { status: "needs_attention", message: "Research service needs attention", attention: { title: "Research service needs attention", message: "A required research service is currently unavailable. Check workspace settings before trying again." } };
  if (detail.includes("review required")) return { status: "needs_attention", message: "Research review is required", attention: { title: "Review required", message: "This research needs a decision before it can continue." } };
  if (detail.includes("connection") || detail.includes("network") || detail.includes("fetch")) return { status: "failed", message: "Connection to the research service was interrupted. The task may still be running.", attention: null };
  return { status: "failed", message: "Research could not be completed. Review the task later or start a new research.", attention: null };
}

function traceAttention(event) {
  const type = String(event?.event_type || "").toLowerCase();
  if (type.includes("login_required")) return { title: "Social source login required", message: "Sign in to the selected social source to continue this research." };
  if (type.includes("provider_error") || type.includes("provider_unavailable")) return { title: "Research service needs attention", message: "A required research service is currently unavailable." };
  return null;
}

function researchTitle(task) {
  const target = task?.config?.target_product || "Competitive research";
  const competitors = task?.config?.competitors || [];
  return competitors.length ? `${target} vs ${competitors.join(", ")}` : target;
}
function stageIndex(stage) { return Math.max(0, RESEARCH_STAGES.findIndex((item) => item.id === stage)); }
function stageActivity(stage) { return { plan: "Planning the research", collect: "Collecting and organizing sources", evidence: "Building traceable evidence", verify: "Checking evidence coverage", report: "Preparing the decision report" }[stage]; }
function finiteCount(value, previous) { return Number.isFinite(value) ? value : previous; }
function appendActivity(items, message, id) { return message && items.at(-1)?.message !== message ? [...items, { id, message, createdAt: Date.now() }].slice(-12) : items; }
function delay(milliseconds) { return new Promise((resolve) => setTimeout(resolve, milliseconds)); }

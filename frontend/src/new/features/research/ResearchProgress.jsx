import React from "react";
import { RESEARCH_STAGES } from "../../adapters/workflowProgressAdapter";
import { Card } from "../../components/ui";

export function ResearchProgressStepper({ progress }) {
  const currentIndex = RESEARCH_STAGES.findIndex((item) => item.id === progress.stage);
  return <Card className="eg-progress-card"><div className="eg-progress-track" aria-label="Research progress"><span style={{ width: `${progress.progress}%` }} /></div><ol className="eg-progress-steps">{RESEARCH_STAGES.map((stage, index) => { const state = stageState(progress, index, currentIndex); return <li key={stage.id} className={`is-${state}`} aria-current={state === "current" ? "step" : undefined}><span>{state === "completed" ? "✓" : index + 1}</span><div><strong>{stage.label}</strong><small>{stageDescription(stage.id)}</small></div></li>; })}</ol></Card>;
}

export function ResearchMetrics({ metrics }) {
  return <section className="eg-running-metrics" aria-label="Research metrics">{[["Sources", metrics.sources],["Evidence", metrics.evidence],["Insights", metrics.insights],["Review items", metrics.reviewItems]].map(([label, value]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}</section>;
}

export function ActivityFeed({ activity }) {
  return <Card className="eg-activity-card"><header><span className="eg-live-dot" /> <h2>Live activity</h2></header><ol aria-live="polite">{[...activity].reverse().map((item, index) => <li key={item.id}><span className={index === 0 ? "is-current" : ""} /><div><strong>{item.message}</strong><small>{formatTime(item.createdAt)}</small></div></li>)}</ol></Card>;
}

function stageState(progress, index, currentIndex) {
  if (["failed", "cancelled"].includes(progress.status) && index === currentIndex) return "failed";
  if (progress.status === "completed" || index < currentIndex) return "completed";
  if (index === currentIndex) return "current";
  return "pending";
}
function stageDescription(stage) { return { plan: "Scope and research approach", collect: "Relevant, credible sources", evidence: "Claims linked to evidence", verify: "Coverage and consistency review", report: "Decision-ready synthesis" }[stage]; }
function formatTime(value) { return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date(value)); }

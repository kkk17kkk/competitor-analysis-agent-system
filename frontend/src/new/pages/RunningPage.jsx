import React, { useEffect, useRef, useState } from "react";
import { runResearchWorkflow, trackExistingResearch } from "../adapters/workflowProgressAdapter";
import { Badge, Button } from "../components/ui";
import { ActivityFeed, ResearchMetrics, ResearchProgressStepper } from "../features/research/ResearchProgress";

export function RunningPage({ taskId, navigate }) {
  const [progress, setProgress] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [tracking, setTracking] = useState(false);
  const trackingActive = useRef(true);

  useEffect(() => {
    let active = true;
    const startedAt = Date.now();
    const timer = window.setInterval(() => setElapsed(Date.now() - startedAt), 1000);
    runResearchWorkflow(taskId, (next) => active && setProgress(next)).then((outcome) => {
      if (!active || outcome.status !== "completed") return;
      navigate(`/reports/${encodeURIComponent(taskId)}`);
    });
    return () => { active = false; trackingActive.current = false; window.clearInterval(timer); };
  }, [taskId, navigate]);

  async function continueTracking() {
    setTracking(true);
    trackingActive.current = true;
    const outcome = await trackExistingResearch(taskId, setProgress, () => trackingActive.current);
    if (!trackingActive.current) return;
    trackingActive.current = false;
    setTracking(false);
    if (outcome.status === "completed") navigate(`/reports/${encodeURIComponent(taskId)}`);
  }

  if (!progress) return <div className="eg-page eg-running-page"><div className="eg-running-loading" role="status">Connecting to your research…</div></div>;
  const tone = progress.status === "completed" ? "success" : progress.status === "needs_attention" || progress.status === "tracking" ? "warning" : progress.status === "failed" || progress.status === "cancelled" ? "danger" : "info";
  return <div className="eg-page eg-running-page" data-data-source="backend">
    <header className="eg-running-header"><div><span className="eg-eyebrow">Research in progress</span><h1>{progress.title}</h1><p>{progress.competitors.length ? `Comparing ${progress.competitors.join(", ")}` : "Competitive research"}</p></div><div className="eg-running-status"><Badge tone={tone}>{statusLabel(progress.status)}</Badge><span>{formatElapsed(elapsed)}</span></div></header>
    {progress.needsAttention && <section className="eg-attention-panel" role="alert"><div><strong>{progress.needsAttention.title}</strong><p>{progress.needsAttention.message}</p></div>{progress.status === "needs_attention" ? <Button onClick={() => navigate("/settings")}>Open settings</Button> : <Button onClick={() => navigate("/reports")}>Check reports</Button>}</section>}
    {progress.status === "tracking" && <section className="eg-attention-panel" role="status"><div><strong>Research is currently running</strong><p>This page will check the existing backend task without starting a second workflow.</p></div><Button onClick={continueTracking} disabled={tracking}>{tracking ? "Tracking…" : "Continue tracking"}</Button></section>}
    {progress.status === "failed" && <section className="eg-attention-panel eg-attention-panel--failed" role="alert"><div><strong>Research stopped</strong><p>{progress.activity.at(-1)?.message}</p></div><div><Button onClick={() => navigate("/reports")}>Check reports</Button><Button onClick={() => navigate("/research/new")}>Start new research</Button></div></section>}
    <ResearchProgressStepper progress={progress} />
    <ResearchMetrics metrics={progress.metrics} />
    <ActivityFeed activity={progress.activity} />
    {progress.status === "running" && <footer className="eg-running-note"><span className="eg-live-dot" /> Keep this page open while the research is running.</footer>}
  </div>;
}

function statusLabel(status) { return { running: "Running", tracking: "Currently running", completed: "Completed", needs_attention: "Needs attention", failed: "Failed", cancelled: "Cancelled" }[status] || "Running"; }
function formatElapsed(milliseconds) { const seconds = Math.floor(milliseconds / 1000); const minutes = Math.floor(seconds / 60); return `${String(minutes).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")} elapsed`; }

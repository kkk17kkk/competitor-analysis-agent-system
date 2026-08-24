import React, { useCallback, useEffect, useState } from "react";
import { Badge, Button, Tabs } from "../components/ui";
import { Illustration } from "../components/Illustration";
import { loadReportWorkspace } from "../adapters/reportViewModel";
import { setEvidenceExcluded, setEvidenceRestored } from "../adapters/evidenceAdapter";
import { runReviewAction } from "../adapters/reviewAdapter";
import { AuditPanel } from "../features/audit/AuditPanel";
import { EvidencePanel } from "../features/report/EvidencePanel";
import { ComparisonMatrix, DecisionHighlights, ExecutiveSummary, KeyInsights, ReportLimitations, StrategicOpportunities } from "../features/report/ReportSections";

const tabs = [{ id: "report", label: "Report" }, { id: "evidence", label: "Evidence" }, { id: "audit", label: "Audit" }];

export function ReportDetailPage({ taskId }) {
  const [active, setActive] = useState("report");
  const [workspace, setWorkspace] = useState(null);
  const [state, setState] = useState({ loading: true, error: "" });
  const [busy, setBusy] = useState({ evidenceId: null, ticketId: null });
  const [actionMessage, setActionMessage] = useState("");

  const load = useCallback(async () => {
    setState({ loading: true, error: "" });
    try {
      setWorkspace(await loadReportWorkspace(taskId));
      setState({ loading: false, error: "" });
    } catch (error) {
      setState({ loading: false, error: error.message });
    }
  }, [taskId]);

  useEffect(() => { load(); }, [load]);

  async function mutateEvidence(action, evidenceId) {
    setBusy({ evidenceId, ticketId: null });
    setActionMessage("");
    try {
      if (action === "exclude") await setEvidenceExcluded(evidenceId, "Excluded during evidence review.");
      else await setEvidenceRestored(evidenceId);
      await load();
      setActionMessage("");
    } catch (error) {
      setActionMessage(error.message);
    } finally {
      setBusy({ evidenceId: null, ticketId: null });
    }
  }

  async function mutateReview(action, ticketId) {
    setBusy({ evidenceId: null, ticketId });
    setActionMessage(action === "rerun" ? "Finding more evidence" : "");
    try {
      await runReviewAction(action, ticketId);
      await load();
      setActionMessage("");
    } catch (error) {
      setActionMessage(error.message);
    } finally {
      setBusy({ evidenceId: null, ticketId: null });
    }
  }

  if (state.loading && !workspace) return <PageState title="Loading report" body="Reading the workflow result from EvidenceGraph." />;
  if (state.error && !workspace) return <PageState tone="danger" title="Report unavailable" body={state.error} />;
  if (!workspace) return null;
  const report = workspace.report;

  return <div className="eg-page eg-report-page" data-data-source={report.dataSource}><DataModeNotice mode={report.dataSource} /><ReportHeader report={report} /><Tabs tabs={tabs} active={active} onChange={setActive} label="Report sections" />
    {state.error && <p className="eg-action-message" role="alert">{state.error}</p>}
    {active === "report" && <ReportView report={report} />}
    {active === "evidence" && <>{actionMessage && <p className="eg-action-message" role="alert">{actionMessage}</p>}<EvidencePanel claims={workspace.evidence} onMutation={mutateEvidence} busyEvidenceId={busy.evidenceId} /></>}
    {active === "audit" && <AuditPanel items={workspace.reviews} onAction={mutateReview} busyTicketId={busy.ticketId} actionMessage={actionMessage} />}
  </div>;
}

export function ReportDetailView({ report, evidence, reviews }) {
  const [active, setActive] = useState("report");
  return <div className="eg-page eg-report-page" data-data-source={report.dataSource}><DataModeNotice mode={report.dataSource} /><ReportHeader report={report} /><Tabs tabs={tabs} active={active} onChange={setActive} label="Report sections" />{active === "report" && <ReportView report={report} />}{active === "evidence" && <EvidencePanel claims={evidence} onMutation={() => {}} busyEvidenceId={null} />}{active === "audit" && <AuditPanel items={reviews} onAction={() => {}} busyTicketId={null} actionMessage="Static demo: actions are not persisted." />}</div>;
}

function DataModeNotice({ mode }) {
  if (mode === "demo") return <aside className="eg-demo-notice"><Badge tone="lilac">Sample Report</Badge><div><strong>This is an example report showing EvidenceGraph capabilities.</strong><span>It is showcase data and is not a backend research result.</span></div></aside>;
  return <div className="eg-backend-mode"><Badge tone="info">Backend data</Badge></div>;
}

function ReportHeader({ report }) {
  return <header className="eg-report-header"><div><span className="eg-eyebrow">Competitive intelligence</span><h1>{report.title || "Report unavailable"}</h1><p><strong>{report.subject || "Target unavailable"}</strong>{report.competitors.length ? ` vs ${report.competitors.join(", ")}` : ""}</p><small>Generated {formatDateTime(report.generatedAt)} · {displayCount(report.sourceCount, "sources analyzed")}</small></div><div className="eg-report-actions"><Badge tone="success">{displayPercent(report.evidenceCoverage, "Evidence coverage")}</Badge><Badge tone="warning">{displayCount(report.openReviews, "items need review")}</Badge><Button disabled>Export ↓</Button></div></header>;
}

function ReportView({ report }) {
  return <div className="eg-report-layout"><main><ExecutiveSummary report={report} /><DecisionHighlights highlights={report.highlights} /><ComparisonMatrix matrix={report.matrix} /><StrategicOpportunities items={report.opportunities} /></main><aside><TrustPanel report={report} /><KeyInsights insights={report.insights} /><ReportLimitations items={report.limitations} /></aside></div>;
}

function TrustPanel({ report }) {
  const trust = report.trust;
  return <div className="eg-trust-panel"><span className="eg-kicker">Trust & confidence</span><h2>{displayPercent(report.evidenceCoverage, "evidence coverage")}</h2><p>{trust?.summary || "Trust summary unavailable."}</p><div><span><Illustration name="icon-evidence-shield.svg" alt="" decorative /><b>Passed claims</b><strong>{displayValue(trust?.passedClaims)}</strong></span><span><Illustration name="icon-adaptive-rerun.svg" alt="" decorative /><b>Total evidence</b><strong>{displayValue(trust?.totalEvidence)}</strong></span><span><Illustration name="icon-review-chat.svg" alt="" decorative /><b>Open reviews</b><strong>{displayValue(report.openReviews)}</strong></span></div></div>;
}

function PageState({ title, body, tone = "neutral" }) { return <div className="eg-page"><section className={`eg-data-state eg-data-state--${tone}`} role={tone === "danger" ? "alert" : "status"}><h1>{title}</h1><p>{body}</p></section></div>; }
function displayValue(value) { return value === null || value === undefined ? "Unavailable" : value; }
function displayPercent(value, label) { return value === null || value === undefined ? `${label}: unavailable` : `${value}% ${label}`; }
function displayCount(value, label) { return value === null || value === undefined ? `${label}: unavailable` : `${value} ${label}`; }
function formatDateTime(value) { if (!value) return "unavailable"; const date = new Date(value); return Number.isNaN(date.getTime()) ? String(value) : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date); }

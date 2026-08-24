import React, { useEffect, useMemo, useState } from "react";
import { Button, MetricCard, SectionHeader } from "../components/ui";
import { Illustration } from "../components/Illustration";
import { formatReportDate, loadResearchSummaries } from "../adapters/reportAdapter";

export function OverviewPage({ navigate }) {
  const [reports, setReports] = useState([]);
  const [state, setState] = useState({ loading: true, error: "" });

  useEffect(() => {
    let active = true;
    loadResearchSummaries()
      .then((items) => active && setReports(items))
      .catch((error) => active && setState({ loading: false, error: error.message }))
      .finally(() => active && setState((current) => ({ ...current, loading: false })));
    return () => { active = false; };
  }, []);

  const metrics = useMemo(() => overviewMetrics(reports, state), [reports, state]);
  const recent = reports.slice(0, 3);
  const attention = reports.filter((item) => Number.isFinite(item.reviewCount) && item.reviewCount > 0);

  return (
    <div className="eg-page eg-overview-page">
      <div className="eg-page-top"><div><span className="eg-eyebrow">Competitive research workspace</span><h1>Welcome to EvidenceGraph.</h1></div><Button variant="primary" onClick={() => navigate("/research/new")}>Start new research <span>→</span></Button></div>
      <section className="eg-hero"><div className="eg-hero-copy"><span className="eg-eyebrow">EvidenceGraph</span><h2>Turn competitor signals<br />into decisions <em>you can verify.</em></h2><p>AI-powered competitive research with traceable evidence, adaptive review, and decision-ready insights.</p><div><Button variant="primary" onClick={() => navigate("/research/new")}>Start new research</Button><Button onClick={() => navigate("/reports/demo")}>View sample report</Button></div></div><div className="eg-hero-art" aria-label="Connected evidence and report illustrations"><Illustration name="hero-pie-chart-card.svg" alt="" decorative /><Illustration name="hero-connected-nodes.svg" alt="" decorative /><Illustration name="hero-bar-chart-card.svg" alt="" decorative /></div></section>
      <section className="eg-metrics" aria-label="Workspace metrics">{metrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}</section>
      <div className="eg-overview-grid"><section className="eg-recent"><SectionHeader eyebrow="Workspace" title="Recent research" description="Resume a backend report or review where evidence still needs attention." action={<button className="eg-text-link" onClick={() => navigate("/reports")}>View all reports →</button>} />
        {state.loading && <OverviewState title="Loading research" body="Reading your EvidenceGraph workspace." />}
        {state.error && <OverviewState tone="danger" title="Research unavailable" body={state.error} />}
        {!state.loading && !state.error && recent.length === 0 && <OverviewState title="No research yet" body="Create your first research project to populate this workspace." action={<Button variant="primary" onClick={() => navigate("/research/new")}>Start your first research</Button>} />}
        {!state.loading && !state.error && recent.length > 0 && <div className="eg-research-list">{recent.map((item) => <button key={item.id} onClick={() => navigate(`/reports/${encodeURIComponent(item.id)}`)}><Illustration name="decor-sidebar-node-cluster.svg" alt="" decorative /><span className="eg-research-title"><strong>{item.title || "Unavailable"}</strong><small>{researchContext(item)} · Updated {formatReportDate(item.updatedAt)}</small></span><span className="eg-coverage"><strong>{item.evidenceCoverage === null ? "Unavailable" : `${item.evidenceCoverage}%`}</strong><small>Evidence coverage</small></span><span className={`eg-status-text is-${statusTone(item.status)}`}>{item.status || "Unavailable"}</span><b>›</b></button>)}</div>}
      </section><aside className="eg-overview-side"><section className="eg-attention-queue"><SectionHeader eyebrow="Attention" title="Review queue" />{state.loading && <p>Loading review status…</p>}{!state.loading && !state.error && attention.length === 0 && <div className="eg-attention-empty"><strong>No items need attention</strong><p>Open review tickets will appear here.</p></div>}{attention.slice(0, 3).map((item) => <button key={item.id} onClick={() => navigate(`/reports/${encodeURIComponent(item.id)}`)}><Illustration name="icon-review-chat.svg" alt="" decorative /><span><strong>{item.title || item.targetProduct || "Research report"}</strong><small>{item.reviewCount} review item{item.reviewCount === 1 ? "" : "s"}</small></span><b>›</b></button>)}</section><section className="eg-how"><SectionHeader eyebrow="Method" title="How it works" /><div>{[["icon-research-search.svg","Research","Explore multiple sources to collect signals and context."],["icon-verify-shield.svg","Verify","Cross-check claims and resolve evidence gaps."],["icon-decide-target.svg","Decide","Turn verified insights into actionable decisions."]].map(([icon,title,body], index) => <article key={title}><span>{index + 1}</span><Illustration name={icon} alt="" decorative /><h3>{title}</h3><p>{body}</p></article>)}</div></section></aside></div>
    </div>
  );
}

function overviewMetrics(reports, state) {
  if (state.loading) return metricDefinitions().map((metric) => ({ ...metric, value: "Loading", note: "Backend data" }));
  if (state.error) return metricDefinitions().map((metric) => ({ ...metric, value: "Unavailable", note: "Backend unavailable" }));
  const coverages = reports.map((item) => item.evidenceCoverage).filter((value) => value !== null);
  const reviews = reports.map((item) => item.reviewCount).filter((value) => value !== null);
  const reruns = reports.map((item) => item.adaptiveRuns).filter((value) => value !== null);
  const values = [
    reports.filter((item) => item.title).length,
    coverages.length ? `${Math.round(coverages.reduce(sum, 0) / coverages.length)}%` : "Unavailable",
    reviews.length ? reviews.reduce(sum, 0) : "Unavailable",
    reruns.length ? reruns.reduce(sum, 0) : "Unavailable",
  ];
  return metricDefinitions().map((metric, index) => ({ ...metric, value: values[index], note: reports.length ? "From backend tasks" : "No data yet" }));
}

function metricDefinitions() {
  return [
    { label: "Reports generated", icon: "icon-reports-generated.svg", tone: "coral" },
    { label: "Evidence coverage", icon: "icon-evidence-shield.svg", tone: "mint" },
    { label: "Open reviews", icon: "icon-review-chat.svg", tone: "orange" },
    { label: "Adaptive runs", icon: "icon-adaptive-rerun.svg", tone: "blue" },
  ];
}

function researchContext(item) {
  return [item.targetProduct, ...item.competitors].filter(Boolean).join(" vs ") || "Products unavailable";
}
function statusTone(status) { return status === "completed" ? "success" : "warning"; }
function sum(total, value) { return total + value; }
function OverviewState({ title, body, tone = "neutral", action }) { return <div className={`eg-overview-state eg-overview-state--${tone}`} role={tone === "danger" ? "alert" : "status"}><h3>{title}</h3><p>{body}</p>{action}</div>; }

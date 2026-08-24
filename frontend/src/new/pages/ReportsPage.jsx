import React, { useEffect, useMemo, useState } from "react";
import { Button, Badge, SectionHeader } from "../components/ui";
import { Illustration } from "../components/Illustration";
import { formatReportDate, loadResearchSummaries } from "../adapters/reportAdapter";

export function ReportsPage({ navigate }) {
  const [reports, setReports] = useState([]);
  const [state, setState] = useState({ loading: true, error: "" });
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");

  useEffect(() => {
    let active = true;
    loadResearchSummaries()
      .then((items) => active && setReports(items))
      .catch((error) => active && setState({ loading: false, error: error.message }))
      .finally(() => active && setState((current) => ({ ...current, loading: false })));
    return () => { active = false; };
  }, []);

  const visibleReports = useMemo(() => reports.filter((report) => {
    const matchesQuery = [report.title, report.targetProduct, ...report.competitors]
      .filter(Boolean).join(" ").toLowerCase().includes(query.toLowerCase());
    if (!matchesQuery) return false;
    if (filter === "complete") return report.status === "completed";
    if (filter === "review") return report.reviewCount !== null && report.reviewCount > 0;
    return true;
  }), [filter, query, reports]);

  return (
    <div className="eg-page eg-reports-page">
      <div className="eg-page-top"><SectionHeader eyebrow="Research library" title="Reports" description="Decision-ready competitive research, organized by evidence quality and review status." /><Button variant="primary" onClick={() => navigate("/research/new")}>New research</Button></div>
      <div className="eg-report-filters">
        <button className={filter === "all" ? "is-active" : ""} onClick={() => setFilter("all")}>All reports</button>
        <button className={filter === "complete" ? "is-active" : ""} onClick={() => setFilter("complete")}>Complete</button>
        <button className={filter === "review" ? "is-active" : ""} onClick={() => setFilter("review")}>Needs review</button>
        <label><span className="sr-only">Search reports</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search reports" /></label>
      </div>
      {state.loading && <PageState title="Loading reports" body="Reading completed research from EvidenceGraph." />}
      {state.error && <PageState tone="danger" title="Reports unavailable" body={state.error} />}
      {!state.loading && !state.error && visibleReports.length === 0 && <PageState title="No reports found" body="No backend research matches this view." />}
      {!state.loading && !state.error && visibleReports.length > 0 && <div className="eg-reports-table">
        <div className="eg-reports-head"><span>Research</span><span>Evidence coverage</span><span>Status</span><span>Updated</span><span></span></div>
        {visibleReports.map((report) => <ReportRow key={report.id} report={report} navigate={navigate} />)}
      </div>}
    </div>
  );
}

function ReportRow({ report, navigate }) {
  const title = report.title || "Unavailable";
  const context = [report.targetProduct, ...report.competitors].filter(Boolean).join(" vs ") || "Competitors unavailable";
  const sources = report.sourceCount === null ? "Sources unavailable" : `${report.sourceCount} sources`;
  return <button className="eg-report-row" onClick={() => navigate(`/reports/${encodeURIComponent(report.id)}`)}><span className="eg-report-name"><Illustration name="decor-sidebar-node-cluster.svg" alt="" decorative /><span><strong>{title}</strong><small>{context} · {sources}</small></span></span><Coverage value={report.evidenceCoverage} /><Badge tone={statusTone(report.status)}>{report.status || "Unavailable"}</Badge><span>{formatReportDate(report.updatedAt)}</span><b>›</b></button>;
}

function Coverage({ value }) {
  if (value === null) return <span className="eg-unavailable">Unavailable</span>;
  return <span className="eg-report-coverage"><span><i style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></span><strong>{value}%</strong></span>;
}

function statusTone(status) {
  if (status === "completed") return "success";
  if (status === "blocked" || status === "failed") return "danger";
  if (status === "running") return "info";
  return "warning";
}

function PageState({ title, body, tone = "neutral" }) {
  return <section className={`eg-data-state eg-data-state--${tone}`} role={tone === "danger" ? "alert" : "status"}><h2>{title}</h2><p>{body}</p></section>;
}

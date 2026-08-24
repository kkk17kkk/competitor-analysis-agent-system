import React from "react";
import { Button, MetricCard, SectionHeader } from "../components/ui";
import { Illustration } from "../components/Illustration";
import { recentResearch, workspaceMetrics } from "../mock/research";

export function OverviewPage({ navigate }) {
  return (
    <div className="eg-page eg-overview-page">
      <div className="eg-page-top"><div><span className="eg-eyebrow">Competitive research workspace</span><h1>Welcome back, Alex.</h1></div><Button variant="primary" onClick={() => navigate("/research/new")}>Start new research <span>→</span></Button></div>
      <section className="eg-hero"><div className="eg-hero-copy"><span className="eg-eyebrow">EvidenceGraph</span><h2>Turn competitor signals<br />into decisions <em>you can verify.</em></h2><p>AI-powered competitive research with traceable evidence, adaptive review, and decision-ready insights.</p><div><Button variant="primary" onClick={() => navigate("/research/new")}>Start new research</Button><Button onClick={() => navigate("/reports/demo")}>View sample report</Button></div></div><div className="eg-hero-art" aria-label="Connected evidence and report illustrations"><Illustration name="hero-pie-chart-card.svg" alt="" decorative /><Illustration name="hero-connected-nodes.svg" alt="" decorative /><Illustration name="hero-bar-chart-card.svg" alt="" decorative /></div></section>
      <section className="eg-metrics" aria-label="Workspace metrics">{workspaceMetrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}</section>
      <div className="eg-overview-grid"><section className="eg-recent"><SectionHeader eyebrow="Workspace" title="Recent research" description="Resume a report or review where evidence still needs attention." action={<button className="eg-text-link" onClick={() => navigate("/reports")}>View all reports →</button>} /><div className="eg-research-list">{recentResearch.map((item) => <button key={item.id} onClick={() => navigate("/reports/demo")}><Illustration name={item.productIcon} alt="" decorative /><span className="eg-research-title"><strong>{item.title}</strong><small>{item.label} · {item.sources} sources · Updated {item.updated}</small></span><span className="eg-coverage"><strong>{item.coverage}%</strong><small>Evidence coverage</small></span><span className={`eg-status-text is-${item.tone}`}>{item.status}</span><b>›</b></button>)}</div></section><aside className="eg-how"><SectionHeader eyebrow="Method" title="How it works" /><div>{[["icon-research-search.svg","Research","Explore multiple sources to collect signals and context."],["icon-verify-shield.svg","Verify","Cross-check claims and resolve evidence gaps."],["icon-decide-target.svg","Decide","Turn verified insights into actionable decisions."]].map(([icon,title,body], index) => <article key={title}><span>{index + 1}</span><Illustration name={icon} alt="" decorative /><h3>{title}</h3><p>{body}</p></article>)}</div></aside></div>
    </div>
  );
}

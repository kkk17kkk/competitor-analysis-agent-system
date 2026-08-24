import React from "react";
import { Badge, Card } from "../../components/ui";
import { Illustration } from "../../components/Illustration";

export function ExecutiveSummary({ report }) {
  return (
    <Card className="eg-executive-summary">
      <div className="eg-summary-copy"><span className="eg-kicker">Executive summary</span>{report.summary.length ? report.summary.map((paragraph) => <p key={paragraph}>{paragraph}</p>) : <EmptyText label="Executive summary unavailable" />}</div>
      <Illustration name="report-summary-card.svg" alt="Illustrated evidence report" />
    </Card>
  );
}

export function DecisionHighlights({ highlights }) {
  if (!highlights.length) return <EmptySection label="Decision highlights unavailable" />;
  return <div className="eg-highlight-grid">{highlights.map((item) => <Card key={item.label} className="eg-highlight"><Illustration name={item.icon} alt="" decorative /><div><span>{item.label}</span><h3 className={`text-${item.tone}`}>{item.title}</h3>{item.body && <p>{item.body}</p>}{item.confidence && <Badge tone={item.tone}>{item.confidence}</Badge>}</div></Card>)}</div>;
}

export function ComparisonMatrix({ matrix }) {
  if (!matrix.rows.length || !matrix.columns.length) return <EmptySection label="Comparison matrix unavailable" />;
  return (
    <section className="eg-report-section">
      <header><div><span className="eg-kicker">Competitive comparison</span><h2>How the products differ</h2></div><p>Qualitative findings are shown as evidence-backed statements, not artificial scores.</p></header>
      <div className="eg-table-wrap"><table className="eg-comparison-table"><thead><tr><th>Dimension</th>{matrix.columns.map((product) => <th key={product}>{product}</th>)}</tr></thead><tbody>{matrix.rows.map((row) => <tr key={row.dimension}><th>{row.dimension}</th>{matrix.columns.map((product, index) => <td className={index === 0 ? "is-target" : ""} key={product}>{row.values[product] || "Unavailable"}</td>)}</tr>)}</tbody></table></div>
    </section>
  );
}

export function KeyInsights({ insights }) {
  if (!insights.length) return <EmptySection label="Key insights unavailable" />;
  return (
    <section className="eg-insights"><span className="eg-kicker">Key insights</span><h2>What matters now</h2><div>{insights.map((item) => <article key={item.text}><span className={`eg-icon-tile eg-icon-tile--${item.tone}`}><Illustration name={item.icon} alt="" decorative /></span><p>{item.text}</p><Badge tone={item.tone}>{item.confidence}</Badge></article>)}</div></section>
  );
}

export function StrategicOpportunities({ items }) {
  if (!items.length) return <EmptySection label="Strategic opportunities unavailable" />;
  return (
    <Card className="eg-opportunities"><div><span className="eg-kicker">Strategic opportunities</span><h2>Recommended next actions</h2><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></div><Illustration name="report-strategic-target.svg" alt="Strategic target illustration" /></Card>
  );
}

function EmptySection({ label }) { return <Card className="eg-data-state"><h3>{label}</h3><p>The backend result does not contain this section.</p></Card>; }
function EmptyText({ label }) { return <p className="eg-unavailable">{label}</p>; }

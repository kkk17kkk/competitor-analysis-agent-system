import React, { useState } from "react";
import { Badge, Button, Card, SectionHeader } from "../../components/ui";

const TERMINAL_STATUSES = new Set(["resolved", "dismissed", "blocked"]);

export function AuditPanel({ items, onAction, busyTicketId, actionMessage }) {
  const [expanded, setExpanded] = useState(null);
  return (
    <section className="eg-audit-panel">
      <SectionHeader eyebrow="Review queue" title="Items that need a decision" description="Resolve evidence exceptions before treating the report as publication-ready." />
      {actionMessage && <p className="eg-action-message" role="status">{actionMessage}</p>}
      {items.length === 0 && <div className="eg-data-state"><h3>No review tickets</h3><p>The backend result does not contain review tickets.</p></div>}
      <div className="eg-review-list">{items.map((item) => {
        const busy = busyTicketId === item.id;
        const closed = TERMINAL_STATUSES.has(item.status);
        return <Card key={item.id} className={`eg-review-item ${closed ? "is-resolved" : ""}`}><div className="eg-review-status"><Badge tone={ticketTone(item.status)}>{item.status || "Unavailable"}</Badge><span>{item.id || "ID unavailable"} · {item.severity || "Priority unavailable"}</span></div><div><h3>{item.missingEvidenceType || item.requiredAction || "Review item"}</h3><p>{item.reason || "Reason unavailable"}</p><dl><div><dt>Affected artifacts</dt><dd>{item.affectedArtifacts.length ? item.affectedArtifacts.join(", ") : "Unavailable"}</dd></div><div><dt>Evidence attempts</dt><dd>{item.rerunCount === null || item.maxReruns === null ? "Unavailable" : `${item.rerunCount} of ${item.maxReruns}`}</dd></div></dl>{item.resolutionSummary && <p className="eg-resolution-summary">{item.resolutionSummary}</p>}</div><div className="eg-review-actions"><Button disabled={busy || closed} onClick={() => onAction("rerun", item.id)}>{busy ? "Finding more evidence" : "Find more evidence"}</Button><Button variant="primary" disabled={busy || closed} onClick={() => onAction("resolve", item.id)}>Resolve</Button><button className="eg-more-actions" aria-expanded={expanded === item.id} onClick={() => setExpanded(expanded === item.id ? null : item.id)}>More actions</button>{expanded === item.id && <div className="eg-review-menu"><button disabled={busy || closed} onClick={() => onAction("accept", item.id)}>Accept</button><button disabled={busy || closed} onClick={() => onAction("downgrade", item.id)}>Downgrade</button><button disabled={busy || closed} onClick={() => onAction("unavailable", item.id)}>Mark unavailable</button><button disabled={busy || closed} onClick={() => onAction("dismiss", item.id)}>Dismiss</button></div>}</div></Card>;
      })}</div>
      <details className="eg-technical-details"><summary>Technical details</summary><div><p>Task ID and ticket routing fields remain available for audit inspection.</p>{items.map((item) => <p key={item.id}>{item.id}: {item.sourceNode || "source unavailable"} → {item.targetNode || "target unavailable"}; {item.product || "product unavailable"}; {item.preferredSourceType || "source preference unavailable"}</p>)}</div></details>
    </section>
  );
}

function ticketTone(status) {
  if (status === "resolved") return "success";
  if (["blocked", "dismissed"].includes(status)) return "danger";
  if (["accepted", "rerun_started"].includes(status)) return "info";
  return "warning";
}

import React, { useMemo, useState } from "react";
import { Badge, Button } from "../../components/ui";

export function EvidencePanel({ claims, onMutation, busyEvidenceId }) {
  const [query, setQuery] = useState("");
  const visibleClaims = useMemo(() => claims.filter((claim) => [claim.text, claim.product, claim.type]
    .filter(Boolean).join(" ").toLowerCase().includes(query.toLowerCase())), [claims, query]);

  return <section className="eg-evidence-panel"><header><div><span className="eg-eyebrow">Evidence explorer</span><h2>Claims and supporting sources</h2><p>The backend Claim → Evidence → Source relationship is preserved below.</p></div><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search evidence" /></header>
    {visibleClaims.length === 0 && <div className="eg-data-state"><h3>No evidence available</h3><p>This workflow result does not contain matching claims.</p></div>}
    {visibleClaims.map((claim) => <article key={claim.id || claim.text}><div><Badge tone={claimTone(claim.status)}>{claim.status || "Unavailable"}</Badge><span>{claim.product || "Product unavailable"} · {claim.type || "Type unavailable"}</span></div><h3>{claim.text || "Claim unavailable"}</h3>{claim.note && <p>{claim.note}</p>}
      <div className="eg-claim-evidence">{claim.evidence.length === 0 && <p>No supporting evidence is linked to this claim.</p>}{claim.evidence.map((item) => <EvidenceItem key={item.id} item={item} busy={busyEvidenceId === item.id} onMutation={onMutation} />)}</div>
    </article>)}
  </section>;
}

function EvidenceItem({ item, busy, onMutation }) {
  if (item.unavailable) return <section className="eg-evidence-source"><strong>{item.id}</strong><p>Referenced evidence is unavailable.</p></section>;
  const excluded = item.status === "excluded";
  return <section className="eg-evidence-source"><header><div><strong>{item.summary || "Evidence summary unavailable"}</strong><span>{item.type || "Type unavailable"} · {item.confidence || "Confidence unavailable"}</span></div><Badge tone={excluded ? "danger" : "success"}>{item.status || "Unavailable"}</Badge></header>{item.locator && <p>{item.locator}</p>}{item.excludedReason && <p className="eg-evidence-reason">{item.excludedReason}</p>}<footer><span>{item.source?.title || "Source unavailable"}</span>{item.source?.url && <a href={item.source.url} target="_blank" rel="noreferrer">Open source</a>}<Button disabled={busy} onClick={() => onMutation(excluded ? "restore" : "exclude", item.id)}>{busy ? "Updating…" : excluded ? "Restore evidence" : "Exclude evidence"}</Button></footer></section>;
}

function claimTone(status) {
  if (status === "passed") return "success";
  if (["blocked", "unsupported", "contradicted"].includes(status)) return "danger";
  if (["downgraded", "stale"].includes(status)) return "warning";
  return "info";
}

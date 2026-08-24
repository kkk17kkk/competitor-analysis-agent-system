import React from "react";
import { Badge, Card, SectionHeader } from "../components/ui";
import { Illustration } from "../components/Illustration";

const settings = [
  ["Research services", "Search and language-model credentials are managed by the deployment environment. In-product editing is unavailable.", "icon-workspace-agent.svg", "Environment managed"],
  ["Connections", "Social-source connections require deployment-level setup. No connection controls are available in this workspace yet.", "icon-workspace-data-source.svg", "Unavailable"],
  ["Research methods", "Depth, evidence policy, workflow mode, and source guidance are configured for each new research.", "icon-verify-shield.svg", "Per research"],
];

export function SettingsPage() {
  return <div className="eg-page eg-settings-page"><SectionHeader eyebrow="Workspace" title="Settings" description="Current configuration boundaries for this EvidenceGraph deployment." /><div className="eg-settings-grid">{settings.map(([title, body, icon, status]) => <Card key={title}><Illustration name={icon} alt="" decorative /><div><h2>{title}</h2><p>{body}</p><Badge>{status}</Badge></div></Card>)}</div></div>;
}

import React from "react";
import { Illustration } from "./Illustration";

export function Button({ children, variant = "secondary", className = "", ...props }) {
  return <button className={`eg-button eg-button--${variant} ${className}`} {...props}>{children}</button>;
}

export function Card({ children, className = "", tone = "default", as: Tag = "section" }) {
  return <Tag className={`eg-card eg-card--${tone} ${className}`}>{children}</Tag>;
}

export function Badge({ children, tone = "neutral" }) {
  return <span className={`eg-badge eg-badge--${tone}`}>{children}</span>;
}

export function Tabs({ tabs, active, onChange, label }) {
  return (
    <div className="eg-tabs" role="tablist" aria-label={label}>
      {tabs.map((tab) => <button key={tab.id} role="tab" aria-selected={active === tab.id} className={active === tab.id ? "is-active" : ""} onClick={() => onChange(tab.id)}>{tab.label}</button>)}
    </div>
  );
}

export function MetricCard({ metric }) {
  return (
    <div className="eg-metric">
      <span className={`eg-icon-tile eg-icon-tile--${metric.tone}`}><Illustration name={metric.icon} alt="" decorative /></span>
      <div><strong>{metric.value}</strong><span>{metric.label}</span><small>{metric.note}</small></div>
    </div>
  );
}

export function SectionHeader({ eyebrow, title, description, action }) {
  return (
    <header className="eg-section-header">
      <div>{eyebrow && <span className="eg-eyebrow">{eyebrow}</span>}<h2>{title}</h2>{description && <p>{description}</p>}</div>
      {action}
    </header>
  );
}

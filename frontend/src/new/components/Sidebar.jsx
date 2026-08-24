import React from "react";
import { Illustration } from "./Illustration";

const items = [
  { href: "/overview", label: "Overview", icon: "icon-nav-home.svg" },
  { href: "/research/new", label: "New Research", icon: "icon-nav-sparkles.svg" },
  { href: "/reports", label: "Reports", icon: "icon-nav-reports.svg" },
  { href: "/settings", label: "Settings", icon: "icon-nav-settings.svg" },
];

export function Sidebar({ path, onNavigate, mobileOpen, onClose }) {
  return (
    <aside className={`eg-sidebar ${mobileOpen ? "is-open" : ""}`} aria-label="Workspace navigation">
      <a className="eg-brand" href="/overview" onClick={(e) => onNavigate(e, "/overview")}>
        <Illustration name="brand-evidencegraph.svg" alt="" decorative />
        <span>EvidenceGraph</span>
      </a>
      <nav className="eg-nav">
        {items.map((item) => {
          const active = path === item.href || (item.href === "/reports" && path.startsWith("/reports/"));
          return <a key={item.href} className={active ? "is-active" : ""} href={item.href} aria-current={active ? "page" : undefined} onClick={(e) => { onNavigate(e, item.href); onClose(); }}><Illustration name={item.icon} alt="" decorative /><span>{item.label}</span></a>;
        })}
      </nav>
      <div className="eg-sidebar-story">
        <Illustration name="decor-sidebar-node-cluster.svg" alt="" decorative />
        <p>AI research.<br />Traceable evidence.<br /><strong>Smarter decisions.</strong></p>
      </div>
      <Illustration name="sidebar-pastel-landscape.svg" alt="" decorative className="eg-sidebar-landscape" />
    </aside>
  );
}

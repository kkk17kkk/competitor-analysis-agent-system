import React, { useState } from "react";
import { Sidebar } from "../components/Sidebar";

export function WorkspaceShell({ path, navigate, children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  function onNavigate(event, href) { event.preventDefault(); navigate(href); }
  return (
    <div className="eg-app">
      <a className="eg-skip-link" href="#eg-main">Skip to main content</a>
      <Sidebar path={path} onNavigate={onNavigate} mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      {mobileOpen && <button className="eg-backdrop" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
      <div className="eg-workspace">
        <header className="eg-mobile-header"><button aria-label="Open navigation" onClick={() => setMobileOpen(true)}>Menu</button><span>EvidenceGraph</span></header>
        <main id="eg-main" className="eg-main" tabIndex="-1">{children}</main>
      </div>
    </div>
  );
}

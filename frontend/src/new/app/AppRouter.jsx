import React, { useEffect, useState } from "react";
import { WorkspaceShell } from "../layouts/WorkspaceShell";
import { NewResearchPage } from "../pages/NewResearchPage";
import { OverviewPage } from "../pages/OverviewPage";
import { ReportDetailPage } from "../pages/ReportDetailPage";
import { DemoReportDetailPage } from "../pages/DemoReportDetailPage";
import { ReportsPage } from "../pages/ReportsPage";
import { SettingsPage } from "../pages/SettingsPage";

export const prototypePaths = ["/overview", "/research/new", "/reports", "/reports/demo", "/settings"];

export function isPrototypePath(pathname) {
  return prototypePaths.includes(pathname) || pathname.startsWith("/reports/");
}

export function StaticPrototypeApp() {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    document.title = "EvidenceGraph · Competitive Research";
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);
  function navigate(href) {
    if (href === path) return;
    window.history.pushState({}, "", href);
    setPath(href);
    window.scrollTo({ top: 0, behavior: "instant" });
  }
  let page = <OverviewPage navigate={navigate} />;
  if (path === "/research/new") page = <NewResearchPage />;
  if (path === "/reports") page = <ReportsPage navigate={navigate} />;
  if (path === "/reports/demo") page = <DemoReportDetailPage />;
  if (path.startsWith("/reports/") && path !== "/reports/demo") page = <ReportDetailPage taskId={decodeURIComponent(path.slice("/reports/".length))} />;
  if (path === "/settings") page = <SettingsPage />;
  return <WorkspaceShell path={path} navigate={navigate}>{page}</WorkspaceShell>;
}

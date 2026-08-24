import React from "react";
import { Illustration } from "../components/Illustration";
import { ResearchFlow } from "../features/research/ResearchSteps";

export function NewResearchPage({ navigate }) {
  return <div className="eg-page eg-new-research-page"><header className="eg-research-header"><div><span className="eg-eyebrow">New research</span><h1>Start a new competitive research</h1><p>Define your target, questions, and evidence policy. EvidenceGraph will create the research task.</p></div><Illustration name="decor-new-research-network.svg" alt="" decorative /></header><ResearchFlow onCreated={(taskId) => navigate(`/research/running/${encodeURIComponent(taskId)}`)} /></div>;
}

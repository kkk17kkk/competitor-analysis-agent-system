import React from "react";
import { Illustration } from "../components/Illustration";
import { ResearchFlow } from "../features/research/ResearchSteps";
import { researchDraft } from "../demo/research";

export function NewResearchPage() {
  return <div className="eg-page eg-new-research-page"><header className="eg-research-header"><div><span className="eg-eyebrow">New research</span><h1>Start a new competitive research</h1><p>Define your target, questions, and evidence policy. EvidenceGraph will handle the rest.</p></div><Illustration name="decor-new-research-network.svg" alt="" decorative /></header><ResearchFlow researchDraft={researchDraft} /></div>;
}

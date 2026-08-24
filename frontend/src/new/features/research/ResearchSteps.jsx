import React, { useState } from "react";
import { Button, Card } from "../../components/ui";
import { Illustration } from "../../components/Illustration";

const productIcons = { "GitHub Copilot": "product-github.svg", Windsurf: "product-windsurf.svg", TRAE: "product-trae.svg", "Claude Code": "product-claude-code.svg", "Gemini CLI": "product-gemini-cli.svg" };

export function ResearchFlow({ researchDraft }) {
  const [competitors, setCompetitors] = useState(researchDraft.competitors);
  const [goal, setGoal] = useState(researchDraft.goal);
  const [depth, setDepth] = useState("Standard");
  const [policy, setPolicy] = useState("Balanced");
  const [audience, setAudience] = useState("Product team");
  const [advanced, setAdvanced] = useState(false);
  const [notice, setNotice] = useState("");
  function addCompetitor(name) { if (!competitors.includes(name) && competitors.length < 5) setCompetitors([...competitors, name]); }
  return (
    <div className="eg-research-flow">
      <Card className="eg-step eg-step--blue"><span className="eg-step-index">1</span><div className="eg-step-content"><header><h2>Competitors</h2><p>What products are you comparing?</p></header><div className="eg-field-grid"><label><span>Target product</span><div className="eg-product-input"><Illustration name="product-cursor.svg" alt="" decorative /><input value={researchDraft.target} readOnly /></div></label><fieldset><legend>Competitors</legend><div className="eg-chip-field">{competitors.map((name) => <button key={name} onClick={() => setCompetitors(competitors.filter((item) => item !== name))}><Illustration name={productIcons[name]} alt="" decorative />{name}<span>×</span></button>)}</div></fieldset></div><div className="eg-suggestions"><span>Suggested</span>{researchDraft.suggestions.filter((item) => !competitors.includes(item)).map((name) => <button key={name} onClick={() => addCompetitor(name)}><Illustration name={productIcons[name]} alt="" decorative />{name}<b>+</b></button>)}</div></div></Card>
      <Card className="eg-step eg-step--mint"><span className="eg-step-index">2</span><div className="eg-step-content"><header className="eg-step-heading"><div><h2>Research goal</h2><p>What decision should this research support?</p></div><Button onClick={() => setGoal(`${goal} Prioritize findings by decision impact and evidence confidence.`)}><Illustration name="icon-nav-sparkles.svg" alt="" decorative />Refine with AI</Button></header><label className="eg-goal-field"><span className="sr-only">Research goal</span><textarea rows="4" value={goal} onChange={(e) => setGoal(e.target.value)} /></label><div className="eg-dimensions"><span>Suggested dimensions</span>{researchDraft.dimensions.map((item) => <button key={item}>{item}</button>)}</div></div></Card>
      <Card className="eg-step eg-step--orange"><span className="eg-step-index">3</span><div className="eg-step-content"><header><h2>Research setup</h2><p>Choose the depth, evidence policy, and intended reader.</p></header><div className="eg-setup-grid"><Segmented label="Research depth" values={["Quick", "Standard", "Deep"]} active={depth} setActive={setDepth} /><Segmented label="Evidence policy" values={["Strict", "Balanced", "Exploratory"]} active={policy} setActive={setPolicy} /><label><span>Audience</span><select value={audience} onChange={(e) => setAudience(e.target.value)}><option>Product team</option><option>Leadership</option><option>Go-to-market team</option></select></label></div><button className="eg-advanced-toggle" aria-expanded={advanced} onClick={() => setAdvanced(!advanced)}><span>{advanced ? "−" : "+"}</span>Advanced options <small>Social listening, date range, and source guidance</small></button>{advanced && <div className="eg-advanced-panel"><label><span>Source guidance</span><input placeholder="Optional source or geography preferences" /></label><label><span>Social listening</span><select><option>Not configured</option><option>Include public social signals</option></select></label></div>}</div></Card>
      <div className="eg-research-summary"><div><span>Research summary</span><div className="eg-summary-items"><SummaryItem icon="product-cursor.svg" label="Target" value={researchDraft.target} /><SummaryItem icon="icon-workspace-agent.svg" label="Competitors" value={`${competitors.length} products`} /><SummaryItem icon="icon-research-depth.svg" label="Depth" value={depth} /><SummaryItem icon="icon-evidence-policy-scale.svg" label="Evidence" value={policy} /></div></div><div><Button variant="primary" onClick={() => setNotice("Static prototype only. API submission begins in Phase 2.")}>Start research <span>→</span></Button>{notice && <small role="status">{notice}</small>}</div></div>
    </div>
  );
}

function Segmented({ label, values, active, setActive }) { return <fieldset className="eg-segmented"><legend>{label}</legend><div>{values.map((value) => <button type="button" key={value} className={active === value ? "is-active" : ""} onClick={() => setActive(value)}>{value}</button>)}</div></fieldset>; }
function SummaryItem({ icon, label, value }) { return <span><Illustration name={icon} alt="" decorative /><small>{label}</small><strong>{value}</strong></span>; }

import React, { useState } from "react";
import { Button, Card } from "../../components/ui";
import { Illustration } from "../../components/Illustration";
import {
  createInitialResearchForm,
  createResearch,
  getCompetitorRecommendations,
  getCondensedGoal,
  getPolishedGoal,
} from "../../adapters/researchFormAdapter";

export function ResearchFlow({ onCreated }) {
  const [form, setForm] = useState(createInitialResearchForm);
  const [competitorDraft, setCompetitorDraft] = useState("");
  const [advanced, setAdvanced] = useState(false);
  const [recommend, setRecommend] = useState({ loading: false, error: "", items: [] });
  const [assist, setAssist] = useState({ mode: "polish", loading: false, error: "", suggestion: "" });
  const [submit, setSubmit] = useState({ loading: false, error: "" });

  function update(patch) { setForm((current) => ({ ...current, ...patch })); }
  function updateAdvanced(patch) { setForm((current) => ({ ...current, advancedOptions: { ...current.advancedOptions, ...patch } })); }
  function addCompetitor(name) {
    const value = name.trim();
    if (!value || form.competitors.some((item) => normalize(item) === normalize(value)) || form.competitors.length >= 5) return;
    update({ competitors: [...form.competitors, value] });
    setCompetitorDraft("");
  }

  async function recommendCompetitors() {
    setRecommend({ loading: true, error: "", items: [] });
    try {
      const response = await getCompetitorRecommendations(form);
      setRecommend({ loading: false, error: "", items: response.competitors || [] });
    } catch (error) {
      setRecommend({ loading: false, error: error.message, items: [] });
    }
  }

  async function requestAssist(mode) {
    setAssist({ mode, loading: true, error: "", suggestion: "" });
    try {
      const suggestion = mode === "condense" ? await getCondensedGoal(form) : await getPolishedGoal(form);
      setAssist({ mode, loading: false, error: suggestion ? "" : "The AI service returned no suggestion.", suggestion });
    } catch (error) {
      setAssist({ mode, loading: false, error: error.message, suggestion: "" });
    }
  }

  async function startResearch() {
    setSubmit({ loading: true, error: "" });
    try {
      const task = await createResearch(form);
      onCreated(task.task_id);
    } catch (error) {
      setSubmit({ loading: false, error: error.message });
    }
  }

  return (
    <div className="eg-research-flow">
      <Card className="eg-step eg-step--blue"><span className="eg-step-index">1</span><div className="eg-step-content"><header><h2>Competitors</h2><p>What products are you comparing?</p></header><div className="eg-field-grid"><label><span>Target product</span><div className="eg-product-input"><Illustration name="decor-sidebar-node-cluster.svg" alt="" decorative /><input value={form.targetProduct} onChange={(event) => update({ targetProduct: event.target.value })} placeholder="Enter the product you are researching" /></div></label><fieldset><legend>Competitors</legend><div className="eg-chip-field">{form.competitors.map((name) => <button type="button" key={name} onClick={() => update({ competitors: form.competitors.filter((item) => item !== name) })}>{name}<span>×</span></button>)}<input value={competitorDraft} onChange={(event) => setCompetitorDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === ",") { event.preventDefault(); addCompetitor(competitorDraft); } }} placeholder="Type a competitor and press Enter" /></div></fieldset></div><div className="eg-suggestions"><Button onClick={recommendCompetitors} disabled={recommend.loading}>{recommend.loading ? "Finding competitors…" : recommend.error ? "Retry recommendations" : "Recommend competitors"}</Button>{recommend.items.filter((item) => !form.competitors.some((current) => normalize(current) === normalize(item))).map((name) => <button type="button" key={name} onClick={() => addCompetitor(name)}>{name}<b>+</b></button>)}</div>{recommend.error && <p className="eg-field-error" role="alert">{recommend.error}</p>}</div></Card>

      <Card className="eg-step eg-step--mint"><span className="eg-step-index">2</span><div className="eg-step-content"><header className="eg-step-heading"><div><h2>Research goal</h2><p>What decision should this research support?</p></div><div className="eg-assist-actions"><Button onClick={() => requestAssist("polish")} disabled={assist.loading}><Illustration name="icon-nav-sparkles.svg" alt="" decorative />{assist.loading && assist.mode === "polish" ? "Refining…" : "Refine with AI"}</Button><Button onClick={() => requestAssist("condense")} disabled={assist.loading}>{assist.loading && assist.mode === "condense" ? "Condensing…" : "Condense"}</Button></div></header><label className="eg-goal-field"><span className="sr-only">Research goal</span><textarea rows="5" value={form.researchGoal} onChange={(event) => update({ researchGoal: event.target.value })} placeholder="Describe the comparison and decision this research should support." /></label>{assist.error && <div className="eg-assist-error" role="alert"><p>{assist.error}</p><Button onClick={() => requestAssist(assist.mode)}>Retry</Button></div>}{assist.suggestion && <div className="eg-assist-suggestion"><span>AI suggestion — your original text is unchanged</span><p>{assist.suggestion}</p><div><Button variant="primary" onClick={() => { update({ researchGoal: assist.suggestion }); setAssist({ ...assist, suggestion: "" }); }}>Apply suggestion</Button><Button onClick={() => setAssist({ ...assist, suggestion: "" })}>Keep original</Button></div></div>}</div></Card>

      <Card className="eg-step eg-step--orange"><span className="eg-step-index">3</span><div className="eg-step-content"><header><h2>Research setup</h2><p>Choose the depth, evidence policy, and intended reader.</p></header><div className="eg-setup-grid"><Segmented label="Research depth" values={["Quick", "Standard", "Deep"]} active={form.depth} setActive={(depth) => update({ depth })} /><Segmented label="Evidence policy" values={["Strict", "Balanced", "Exploratory"]} active={form.evidencePolicy} setActive={(evidencePolicy) => update({ evidencePolicy })} /><label><span>Audience</span><select value={form.audience} onChange={(event) => update({ audience: event.target.value })}><option value="product team">Product team</option><option value="leadership">Leadership</option><option value="go-to-market team">Go-to-market team</option></select></label></div><button type="button" className="eg-advanced-toggle" aria-expanded={advanced} onClick={() => setAdvanced(!advanced)}><span>{advanced ? "−" : "+"}</span>Advanced options <small>Domain, workflow, source guidance, and social listening</small></button>{advanced && <div className="eg-advanced-panel eg-advanced-panel--research"><label><span>Product domain</span><select value={form.advancedOptions.domain} onChange={(event) => updateAdvanced({ domain: event.target.value })}><option value="general_product">General product</option><option value="saas">SaaS</option><option value="ai_tools">AI tools</option></select></label><label><span>Workflow mode</span><select value={form.advancedOptions.workflowMode} onChange={(event) => updateAdvanced({ workflowMode: event.target.value })}><option>Adaptive review</option><option>Single pass</option></select></label><label><span>Source guidance</span><input value={form.advancedOptions.notes} onChange={(event) => updateAdvanced({ notes: event.target.value })} placeholder="Optional source or geography guidance" /></label><label><span>Social listening</span><select value={form.advancedOptions.socialPlatform} onChange={(event) => updateAdvanced({ socialPlatform: event.target.value })}><option value="disabled">Disabled</option><option value="xiaohongshu">Xiaohongshu</option></select></label></div>}</div></Card>

      <div className="eg-research-summary"><div><span>Research summary</span><div className="eg-summary-items"><SummaryItem icon="decor-sidebar-node-cluster.svg" label="Target" value={form.targetProduct || "Not set"} /><SummaryItem icon="icon-workspace-agent.svg" label="Competitors" value={`${form.competitors.length} products`} /><SummaryItem icon="icon-research-depth.svg" label="Depth" value={form.depth} /><SummaryItem icon="icon-evidence-policy-scale.svg" label="Evidence" value={form.evidencePolicy} /></div></div><div><Button variant="primary" disabled={submit.loading} onClick={startResearch}>{submit.loading ? "Creating task…" : "Start research"} <span>→</span></Button>{submit.error && <small role="alert">{submit.error}</small>}</div></div>
    </div>
  );
}

function Segmented({ label, values, active, setActive }) { return <fieldset className="eg-segmented"><legend>{label}</legend><div>{values.map((value) => <button type="button" key={value} className={active === value ? "is-active" : ""} onClick={() => setActive(value)}>{value}</button>)}</div></fieldset>; }
function SummaryItem({ icon, label, value }) { return <span><Illustration name={icon} alt="" decorative /><small>{label}</small><strong>{value}</strong></span>; }
function normalize(value) { return value.trim().toLowerCase().replace(/\s+/g, " "); }

# Workflow Evaluation Results

Deterministic mock comparison across 8 cases. Values are aggregated from actual `WorkflowResult` traces, tool calls, evidence, claims, and Review Tickets.

| Metric | Single Pass | Adaptive Review | Delta |
|---|---:|---:|---:|
| claim_evidence_binding_rate | 73.7% | 75.8% | 2.1% |
| unsupported_claim_rate | 0.0% | 0.0% | 0.0% |
| uncertain_blocked_claim_rate | 26.3% | 24.2% | -2.1% |
| unresolved_ticket_rate | 100.0% | 82.6% | -17.4% |
| tickets_created | 23 | 23 | 0 |
| tickets_resolved | 0 | 4 | 4 |
| ticket_resolution_rate | 0.0% | 17.4% | 17.4% |
| tickets_with_new_evidence | 0 | 4 | 4 |
| claims_improved_after_rerun | 0 | 4 | 4 |
| rerun_improvement_rate | N/A | 40.0% | N/A |
| total_sources | 98 | 102 | 4 |
| total_evidence | 98 | 116 | 18 |
| passed_claims | 140 | 144 | 4 |
| report_evidence_coverage | 65.2% | 67.0% | 1.9% |
| total_llm_tokens | 64763 | 98256 | 33493 |
| total_workflow_latency_ms | 13375 | 38781 | 25406 |
| tool_calls | 264 | 308 | 44 |
| rerun_count | 0 | 14 | 14 |
| loop_count | 0 | 14 | 14 |

## Interpretation

Adaptive Review uses the same graph and provider fixtures as Single Pass. Its additional cost is visible in token, latency, tool-call, rerun, and loop metrics; unresolved tickets remain explicit rather than being counted as successful closure.

## Reproduction

```bash
python scripts/eval_workflow.py
```

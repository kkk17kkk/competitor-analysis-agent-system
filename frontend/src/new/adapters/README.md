# Phase 2A adapter mapping

Adapters are the only Phase 2A modules that import `src/api/client.js`. They map existing backend payloads into presentation models; they do not create conclusions or change workflow semantics.

| Adapter | Existing client/API | Mapping |
| --- | --- | --- |
| `reportAdapter.js` | `getTasks()` → `GET /api/tasks`; `getTask(id)` → `GET /api/tasks/{id}` | `Task`/`WorkflowResult` → `ResearchSummary`. Coverage, review count and source count are `null` when the result does not contain them. |
| `reportViewModel.js` | `getTask(id)` → `GET /api/tasks/{id}` | `WorkflowResult.report`, report sections, claims, SWOT and trust summary → report view model. Missing sections remain empty. |
| `evidenceAdapter.js` | `getTask(id)` plus existing exclude/restore client methods | Preserves `Claim.supporting_evidence` and `Evidence.source_id` relationships. Missing referenced records are marked unavailable, not synthesized. |
| `reviewAdapter.js` | `getTask(id)` plus existing ticket mutation methods | Preserves ticket status, severity, required action, rerun counts and mutation responses. No optimistic success state is generated. |

Display-only transformations are limited to date formatting, human-readable field labels, Markdown line extraction, grouping claims by backend `claim_type` and counting existing records.

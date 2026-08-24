# Phase 2A adapter mapping

Adapters are the only Phase 2A modules that import `src/api/client.js`. They map existing backend payloads into presentation models; they do not create conclusions or change workflow semantics.

| Adapter | Existing client/API | Mapping |
| --- | --- | --- |
| `reportAdapter.js` | `getTasks()` → `GET /api/tasks`; `getTask(id)` → `GET /api/tasks/{id}` | `Task`/`WorkflowResult` → `ResearchSummary`. Coverage, review count and source count are `null` when the result does not contain them. |
| `reportViewModel.js` | `getTask(id)` → `GET /api/tasks/{id}` | `WorkflowResult.report`, report sections, claims, SWOT and trust summary → report view model. Missing sections remain empty. |
| `evidenceAdapter.js` | `getTask(id)` plus existing exclude/restore client methods | Preserves `Claim.supporting_evidence` and `Evidence.source_id` relationships. Missing referenced records are marked unavailable, not synthesized. |
| `reviewAdapter.js` | `getTask(id)` plus existing ticket mutation methods | Preserves ticket status, severity, required action, rerun counts and mutation responses. No optimistic success state is generated. |
| `researchFormAdapter.js` | Existing competitor recommendation, goal polish/condense, and `createTask()` client methods | Maps form state to the existing `TaskConfig` with explicit enum conversions and no API calls in components. |
| `workflowProgressAdapter.js` | Existing `getTask(id)` and `streamTaskRun(id, handlers)` client methods | Converts SSE callbacks into five user-facing research stages, aggregate metrics, safe activity copy and attention/failure states. It waits for the completed result to be readable before report navigation. |

Display-only transformations are limited to date formatting, human-readable field labels, Markdown line extraction, grouping claims by backend `claim_type` and counting existing records.

## Data modes

- `backend`: data returned by the existing API and mapped without sample fallbacks.
- `demo`: showcase content imported only by `/reports/demo` and static prototype pages.
- `empty`: the successful `GET /api/tasks` result contains no production tasks.

Real report content is fail-closed: executive summary uses only an `executive_summary` or `structured_summary` report section; key insights use only `differentiated_insights`; strategic opportunities use only `Report.swot.opportunities`. Core findings and generic included claims are not relabeled as those sections.

## Research request mapping

`targetProduct`, `competitors` and `researchGoal` become `target_product`, `competitors` and the single-item `analysis_goals` array. Quick/Standard/Deep map to `quick`/`standard`/`deep`; Strict/Balanced/Exploratory map to `high`/`standard`/`low`; Adaptive review/Single pass map to `adaptive_review`/`single_pass`. Domain, audience, notes and the optional Xiaohongshu platform are passed through existing schema fields only.

## Workflow progress mapping

Planner/template activity becomes **Plan research**; research, source organization, interaction and social collection become **Collect sources**; evidence extraction and analysis become **Build evidence**; critic, targeted review and trust checks become **Verify insights**; writing/finalization become **Prepare report**. Node names and raw trace payloads remain inside the adapter and are never rendered by the new UI.

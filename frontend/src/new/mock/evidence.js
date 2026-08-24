export const evidenceItems = [
  { claim: "Cursor provides the deepest real-time codebase context in this comparison.", product: "Cursor", dimension: "Code context", status: "Verified", confidence: "High", sources: 6, summary: "Official documentation and two independent evaluations describe repository indexing and context retrieval behavior." },
  { claim: "GitHub Copilot has the broadest enterprise distribution footprint.", product: "GitHub Copilot", dimension: "Team adoption", status: "Verified", confidence: "High", sources: 5, summary: "Enterprise plan documentation and adoption reports support broad distribution across IDEs and organizations." },
  { claim: "Windsurf reduces context switching through multi-file editing flows.", product: "Windsurf", dimension: "Agent workflow", status: "Needs review", confidence: "Medium", sources: 3, summary: "Product documentation supports the workflow, but independent usage evidence remains limited." },
];

export const reviewItems = [
  { id: "RT-104", severity: "High", status: "Needs review", title: "Missing official pricing evidence", affected: "TRAE enterprise readiness and pricing insight", detail: "The current claim relies on secondary sources. Locate a current official pricing or procurement source before publication.", attempts: "1 of 2" },
  { id: "RT-108", severity: "Medium", status: "Needs review", title: "Security claim needs corroboration", affected: "Cursor enterprise governance risk", detail: "One source describes admin controls, but the privacy and retention policy still needs cross-checking.", attempts: "0 of 2" },
];


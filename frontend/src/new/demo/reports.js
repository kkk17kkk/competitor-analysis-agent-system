import { recentResearch } from "./research";

export const reports = [
  ...recentResearch,
  { id: "figma", title: "Figma vs Penpot vs Sketch", label: "Design tools", productIcon: "decor-sidebar-node-cluster.svg", updated: "May 12, 2026", sources: 31, coverage: 84, status: "Complete", tone: "success" },
  { id: "linear", title: "Linear vs Jira vs Height", label: "Product management", productIcon: "decor-sidebar-node-cluster.svg", updated: "May 08, 2026", sources: 39, coverage: 71, status: "Review", tone: "warning" },
];

export const reportDetail = {
  title: "Competitive Intelligence Report",
  subject: "Cursor",
  competitors: ["GitHub Copilot", "Windsurf", "TRAE"],
  generated: "May 20, 2026 at 10:42 AM",
  sources: 42,
  coverage: 92,
  openReviews: 2,
  summary: [
    "Cursor leads on developer experience and deep codebase context, making it especially strong for individual developers and small teams moving quickly.",
    "GitHub Copilot has the broadest ecosystem reach, while Windsurf is emerging with capable multi-file workflows. TRAE is differentiated on affordability and localized experiences.",
    "Today, Cursor offers the strongest balance of productivity impact and enterprise readiness, with clear opportunity to strengthen governance and multi-repository context.",
  ],
  highlights: [
    { label: "Strongest advantage", title: "Contextual accuracy", body: "Deeper, real-time codebase awareness produces more relevant suggestions.", confidence: "High confidence", icon: "icon-advantage-trophy.svg", tone: "success" },
    { label: "Biggest risk", title: "Ecosystem lock-in", body: "Dependency on proprietary models and IDE integrations may constrain flexibility.", confidence: "Medium confidence", icon: "icon-risk-alert-shield.svg", tone: "danger" },
    { label: "Recommended direction", title: "Double down on context + enterprise", body: "Invest in workspace intelligence, admin controls, and multi-repository understanding.", confidence: "High confidence", icon: "icon-direction-compass.svg", tone: "lilac" },
  ],
  matrix: [
    { dimension: "Agent workflow", cursor: "Deep, autonomous", copilot: "Broad assistance", windsurf: "Strong multi-file", trae: "Emerging" },
    { dimension: "Code context", cursor: "High", copilot: "Medium-high", windsurf: "High", trae: "Medium" },
    { dimension: "Team adoption", cursor: "High", copilot: "Very high", windsurf: "Medium", trae: "Medium" },
    { dimension: "Pricing", cursor: "$$", copilot: "$$$", windsurf: "$$", trae: "$" },
    { dimension: "Enterprise readiness", cursor: "High", copilot: "High", windsurf: "Medium", trae: "Low" },
  ],
  insights: [
    { text: "Cursor's real-time codebase indexing drives more accurate context retrieval.", confidence: "High", icon: "icon-insight-trend.svg", tone: "success" },
    { text: "GitHub Copilot leads in mindshare and breadth of IDE integrations.", confidence: "High", icon: "icon-insight-users.svg", tone: "info" },
    { text: "Windsurf's multi-file editing reduces context switching in complex work.", confidence: "Medium", icon: "icon-insight-lightning.svg", tone: "lilac" },
    { text: "TRAE competes on price but lacks mature enterprise controls.", confidence: "Low", icon: "icon-insight-price.svg", tone: "danger" },
  ],
  opportunities: [
    "Invest in workspace intelligence and cross-repository understanding.",
    "Strengthen enterprise controls, SSO, and auditable administration.",
    "Expand integrations to become the team's system of record for AI-assisted development.",
    "Clarify usage limits and procurement paths for growing teams.",
  ],
};

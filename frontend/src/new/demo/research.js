export const workspaceMetrics = [
  { label: "Reports Generated", value: "24", note: "Across this workspace", icon: "icon-reports-generated.svg", tone: "coral" },
  { label: "Evidence Coverage", value: "78%", note: "Average verified coverage", icon: "icon-evidence-shield.svg", tone: "mint" },
  { label: "Open Reviews", value: "5", note: "Need analyst attention", icon: "icon-review-chat.svg", tone: "orange" },
  { label: "Adaptive Runs", value: "11", note: "Targeted evidence updates", icon: "icon-adaptive-rerun.svg", tone: "blue" },
];

export const recentResearch = [
  { id: "cursor", title: "Cursor vs GitHub Copilot vs Windsurf vs TRAE", label: "AI coding tools", productIcon: "product-cursor.svg", updated: "May 20, 2026", sources: 42, coverage: 92, status: "Complete", tone: "success" },
  { id: "notion", title: "Notion Calendar vs Google Calendar", label: "Productivity", productIcon: "product-google-calendar.svg", updated: "May 18, 2026", sources: 36, coverage: 76, status: "Complete", tone: "success" },
  { id: "feishu", title: "Feishu vs DingTalk", label: "Enterprise", productIcon: "product-feishu.svg", updated: "May 16, 2026", sources: 28, coverage: 69, status: "Review", tone: "warning" },
];

export const researchDraft = {
  target: "Cursor",
  competitors: ["GitHub Copilot", "Windsurf", "TRAE"],
  suggestions: ["Claude Code", "Gemini CLI"],
  goal: "Understand how Cursor compares to leading AI coding agents across positioning, agent workflow, codebase context, pricing, enterprise adoption, and security posture. Identify strengths, gaps, and risks that should inform our roadmap and go-to-market strategy.",
  dimensions: ["Positioning", "Agent workflow", "Pricing", "Enterprise", "Security"],
};

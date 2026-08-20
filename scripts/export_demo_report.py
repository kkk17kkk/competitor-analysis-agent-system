from __future__ import annotations

import html
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ["PUBLIC_DEMO_MODE"] = "true"
os.environ["USE_MOCK_SEARCH"] = "true"
os.environ["USE_MOCK_LLM"] = "true"

from app.core.graph import run_workflow  # noqa: E402
from app.core.nodes import _plain_summary  # noqa: E402
from app.models.schemas import Claim, Report, Task, TaskConfig, WorkflowResult  # noqa: E402


def _evidence_ids(claim: Claim) -> str:
    return ", ".join(claim.supporting_evidence[:4]) or "—"


_CLAIM_TYPE_LABELS = {
    "positioning": "定位",
    "pricing": "商业化",
    "feature": "能力覆盖",
    "target_user": "目标用户",
    "security": "安全与合规",
    "agent_capability": "AI/Agent 能力",
    "browser_interaction": "实际链路",
    "third_party_context": "外部视角",
    "social_sentiment": "社媒反馈",
    "llm_synthesis": "综合判断",
}
_CONFIDENCE_LABELS = {"high": "高", "medium": "中", "low": "低"}
_STATUS_LABELS = {
    "passed": "通过",
    "uncertain": "不确定",
    "blocked": "阻断",
    "unsupported": "不支持",
    "downgraded": "降级",
    "open": "开放",
    "accepted": "已接受",
    "rerun_started": "已开始重跑",
    "resolved": "已解决",
}
_SEVERITY_LABELS = {"low": "低", "medium": "中", "high": "高", "critical": "严重"}
_SOURCE_TYPE_LABELS = {
    "official_docs": "官方文档",
    "official_pricing": "官方定价",
    "official_product": "官方产品页",
    "third_party_relevant": "相关第三方",
    "third_party": "第三方",
    "browser_observed": "浏览器观察",
    "social_xiaohongshu": "小红书",
    "social_xiaohongshu_manual": "小红书（人工摘要）",
    "official_homepage": "官方主页",
    "official_pricing_page": "官方定价页",
    "website": "网站",
    "community": "社区",
    "search": "搜索结果",
    "official_or_independent": "官方或独立来源",
}
_VALUE_REPLACEMENTS = {
    "Cursor supports agent-like coding workflows using codebase context": "Cursor 支持利用代码库上下文的 Agent 式编码工作流",
    "GitHub Copilot is positioned as an AI pair programmer integrated into developer workflows": "GitHub Copilot 定位为融入开发工作流的 AI 结对程序员",
    "GitHub Copilot combines IDE assistance, chat, pull request support, and coding-agent capabilities": "GitHub Copilot 融合 IDE 辅助、对话、Pull Request 支持和 Coding Agent 能力",
    "Windsurf emphasizes an AI coding environment with agentic workflows": "Windsurf 强调具备 Agent 工作流的 AI 编程环境",
    "Windsurf feature coverage emphasizes agentic coding and codebase understanding": "Windsurf 的能力覆盖聚焦 Agent 式编程和代码库理解",
    "TRAE is positioned as an AI IDE for coding assistance": "TRAE 定位为提供编程辅助的 AI IDE",
    "TRAE feature coverage highlights AI IDE assistance and development workflow support": "TRAE 的能力覆盖突出 AI IDE 辅助和开发工作流支持",
    "TRAE's AI IDE workflow is represented as a path from assistant invocation to generated change review": "TRAE 的 AI IDE 路径覆盖助手调用、生成变更到变更审阅",
    "Third-party evidence is available and should be used to cross-check official positioning rather than simply repeat vendor messaging": "已有第三方证据，应将其用于校准官方定位，而不是简单复述厂商叙事",
    "Positioning differs across Cursor, GitHub Copilot, TRAE, Windsurf; this supports a matrix-style comparison rather than a single ranked verdict": "Cursor、GitHub Copilot、TRAE 与 Windsurf 的定位存在差异，应采用矩阵式比较，而不是给出单一排名",
    "Feature coverage differs enough to require a user-journey comparison instead of a flat checklist": "功能差异需要落到用户旅程比较，单纯功能清单无法解释真实选择",
    "Browser-observed workflow paths are available for multiple products, so the feature tree can separate real interaction coverage from source-only feature claims": "多个产品已有结构化路径，可把待实测体验假设和文档推断能力分开评估",
    "Pricing coverage is strongest where official pricing pages are present; unresolved pricing gaps should be treated as follow-up research rather than final conclusions": "只有官方定价页支撑的商业化判断可进入正文，价格缺口应保留为后续调研",
    "TRAE lacks reviewed target user evidence.": "TRAE 缺少已复核的目标用户证据。",
    "TRAE lacks reviewed security evidence.": "TRAE 缺少已复核的安全与合规证据。",
    "Contradiction scan has no explicit confirming or conflicting evidence.": "矛盾扫描未发现明确的支持或冲突证据。",
    "Search customer stories, community discussions, or persona material before finalizing personas.": "在最终确定用户画像前，检索客户案例、社区讨论或用户画像材料。",
    "Search security, privacy, incident, or compliance coverage before scoring enterprise adoption risk.": "在评估企业采用风险前，补充安全、隐私、事故或合规方面的资料。",
    "Run a contradiction-oriented source check before treating the comparison as externally publishable.": "在将比较结果用于对外发布前，执行面向矛盾的来源核查。",
    "Cursor contradiction needs verification before being stated as fact": "Cursor 的矛盾点需要进一步核验，暂不能作为事实陈述",
    "GitHub Copilot contradiction needs verification before being stated as fact": "GitHub Copilot 的矛盾点需要进一步核验，暂不能作为事实陈述",
    "Windsurf contradiction needs verification before being stated as fact": "Windsurf 的矛盾点需要进一步核验，暂不能作为事实陈述",
    "TRAE target user needs verification before being stated as fact": "TRAE 的目标用户结论需要进一步核验，暂不能作为事实陈述",
    "TRAE security needs verification before being stated as fact": "TRAE 的安全结论需要进一步核验，暂不能作为事实陈述",
    "TRAE lacks reviewed target user evidence": "TRAE 缺少已复核的目标用户证据",
    "TRAE lacks reviewed security evidence": "TRAE 缺少已复核的安全与合规证据",
    "Contradiction scan has no explicit confirming or conflicting evidence": "矛盾扫描未发现明确的支持或冲突证据",
    "Search customer stories, community discussions, or persona material before finalizing personas": "在最终确定用户画像前，检索客户案例、社区讨论或用户画像材料",
    "Search security, privacy, incident, or compliance coverage before scoring enterprise adoption risk": "在评估企业采用风险前，补充安全、隐私、事故或合规方面的资料",
        "Run a contradiction-oriented source check before treating the comparison as externally publishable": "在将比较结果用于对外发布前，执行面向矛盾的来源核查",
        "target_user": "目标用户",
        "security": "安全与合规",
        "contradiction": "矛盾核查",
    }


def _zh_text(value: object) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return "—"
    text = _plain_summary(text)
    for source, replacement in _VALUE_REPLACEMENTS.items():
        text = text.replace(source, replacement)
    text = {
        "MockSearchProvider": "模拟搜索 Provider",
        "MockLLMProvider": "模拟 LLM Provider",
        "unknown": "未知",
        "not available": "不可用",
    }.get(text, text)
    if text.startswith("Provider-assisted synthesis should compare "):
        products = text.removeprefix("Provider-assisted synthesis should compare ").replace(" only through bound evidence", "")
        return f"Provider 辅助的综合判断只能基于已绑定证据比较 {products}"
    return text


def _label(value: object, mapping: dict[str, str]) -> str:
    text = str(value or "")
    return mapping.get(text, text.replace("_", " ")) or "—"


def _report_status(value: object) -> str:
    return {"reviewing": "复核中", "draft": "草稿", "final": "已完成"}.get(str(value or ""), _zh_text(value))


def _report_title(report: Report | None) -> str:
    title = report.title if report else ""
    if not title or title == "Competitive Intelligence Report":
        return "竞品分析报告"
    if title == "Cursor Competitor Analysis":
        return "Cursor 竞品分析报告"
    return _zh_text(title)


def _pricing_text(value: object) -> str:
    text = _zh_text(value)
    replacements = {
        "Published subscription tiers": "已发布订阅套餐",
        "Published plan structure": "已发布套餐结构",
        "Individual": "个人版",
        "Business": "商业版",
        "Enterprise": "企业版",
        "Team": "团队版",
        "Free": "免费版",
        "Paid": "付费版",
    }
    for source, replacement in replacements.items():
        text = text.replace(source, replacement)
    return text


def _claim_rows(result: WorkflowResult, claim_types: set[str] | None = None) -> list[Claim]:
    claims = [claim for claim in result.claims if claim.included_in_report]
    if claim_types:
        claims = [claim for claim in claims if claim.claim_type in claim_types]
    return claims[:12]


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = [f"| {' | '.join(headers)} |", f"| {' | '.join('---' for _ in headers)} |"]
    for row in rows:
        cells = [str(cell).replace("|", "/").replace("\n", " ") for cell in row]
        lines.append(f"| {' | '.join(cells)} |")
    return lines


def _feature_tree_lines(node, depth: int = 0) -> list[str]:
    lines = [f"{'  ' * depth}- {node.name}: {_zh_text(node.description or '已观测能力')}"]
    for child in node.children[:8]:
        lines.extend(_feature_tree_lines(child, depth + 1))
    return lines


def build_demo_markdown(result: WorkflowResult) -> str:
    config = result.task.config
    report = result.report
    trust = result.trust_summary
    products = [config.target_product, *config.competitors]
    included_claims = _claim_rows(result)
    positioning = _claim_rows(result, {"positioning", "agent_capability"})
    capabilities = _claim_rows(result, {"feature", "browser_interaction", "agent_capability"})
    open_tickets = [ticket for ticket in result.review_tickets if ticket.status in {"open", "accepted", "rerun_started"}]
    coverage = trust.claim_evidence_binding_rate if trust else 0
    passed = trust.passed_claim_count if trust else 0
    total = trust.total_claim_count if trust else len(result.claims)

    lines = [
        "# 竞品分析报告",
        "",
        f"**{config.target_product}** 与 **{', '.join(config.competitors)}** 的对比",
        "",
        "> 本报告由真实 EvidenceGraph 工作流在确定性模拟模式下生成。以下结论均来自本次运行中的证据与 Claim，并非写死在 Writer 节点中的展示文案。",
        "",
        "## 执行摘要",
        "",
        f"本次工作流从 {len(result.sources)} 个来源和 {len(result.evidence)} 条证据中生成了 {passed} 条通过证据复核的结论。当前 Claim-Evidence 绑定率为 {coverage:.0%}；仍有 {len(open_tickets)} 个复核工单需要后续处理。",
        "",
        "### 决策信号",
        "",
        f"当前报告处于{_report_status(report.status if report else 'draft')}状态，可用于内部比较。证据支撑的定位与能力差异可作为第一轮信号；定价、交互覆盖度和未解决工单构成下一步验证边界。",
        "",
        "## 关键结论与要点",
        "",
    ]
    if included_claims:
        lines.extend(f"- **{claim.product} — {_label(claim.claim_type, _CLAIM_TYPE_LABELS)}：** {_zh_text(claim.claim)}（{_label(claim.confidence, _CONFIDENCE_LABELS)}置信度；证据：{_evidence_ids(claim)}）。" for claim in included_claims[:6])
    else:
        lines.append("- 暂无结论通过证据门禁；在补充证据前，请将本报告视为研究简报。")

    lines.extend(["", "## 产品定位", ""])
    lines.extend(_table(["产品", "证据支撑的定位", "置信度", "证据 ID"], [[claim.product, _zh_text(claim.claim), _label(claim.confidence, _CONFIDENCE_LABELS), _evidence_ids(claim)] for claim in positioning]) or ["没有定位结论通过证据门禁。"])

    lines.extend(["", "## 能力对比", ""])
    lines.extend(_table(["产品", "能力信号", "状态", "证据 ID"], [[claim.product, _zh_text(claim.claim), _label(claim.verified_status, _STATUS_LABELS), _evidence_ids(claim)] for claim in capabilities]) or ["没有能力结论通过证据门禁。"])

    lines.extend(["", "## 定价与套餐", ""])
    pricing_rows = []
    if report and report.pricing_model:
        for plan in report.pricing_model.plans:
            pricing_rows.append([plan.product, _pricing_text(plan.model), "; ".join(_pricing_text(item) for item in plan.tiers) or "未说明", "; ".join(_pricing_text(item) for item in plan.price_points) or "未说明", ", ".join(plan.evidence_ids) or "—"])
    lines.extend(_table(["产品", "模式", "套餐层级", "价格信息", "证据 ID"], pricing_rows) or ["定价证据绑定不足，暂不能形成可靠比较。"])

    lines.extend(["", "## 目标用户与画像", ""])
    personas = report.user_personas if report else []
    if personas:
        lines.extend(_table(["用户画像", "细分人群", "待完成任务", "决策标准"], [[persona.name, _zh_text(persona.segment), "; ".join(_zh_text(item) for item in persona.jobs_to_be_done[:3]) or "—", "; ".join(_zh_text(item) for item in persona.decision_criteria[:3]) or "—"] for persona in personas[:8]]))
    else:
        lines.append("本次运行没有可用的用户画像证据。")

    lines.extend(["", "## 工作流与用户旅程", ""])
    if report and report.feature_tree:
        lines.extend(_feature_tree_lines(report.feature_tree.root))
    else:
        lines.append("没有可用的已验证工作流树。")

    lines.extend(["", "## 竞争优势与差距", ""])
    advantages = [claim for claim in result.claims if claim.verified_status == "passed" and claim.included_in_report]
    gaps = [claim for claim in result.claims if claim.verified_status in {"uncertain", "blocked", "unsupported", "downgraded"}]
    lines.extend(_table(["类型", "产品 / 范围", "观察", "证据 ID"], [["优势 / 信号", claim.product, _zh_text(claim.claim), _evidence_ids(claim)] for claim in advantages[:5]] + [["差距 / 不确定性", claim.product, _zh_text(claim.claim), _evidence_ids(claim)] for claim in gaps[:5]]) or ["没有可用的证据支撑优势或差距。"])

    lines.extend(["", "## 用户反馈与社交信号", ""])
    if result.social_insights:
        lines.extend(_table(["平台", "状态", "摘要", "证据 ID"], [[insight.platform, _label(insight.status, _STATUS_LABELS), _zh_text(insight.summary), ", ".join(insight.evidence_ids) or "—"] for insight in result.social_insights[:8]]))
    else:
        lines.append("本次组合场景未配置社交聆听，因此不呈现社交结论。")

    lines.extend(["", "## 战略机会", ""])
    opportunity_claims = [claim for claim in result.claims if claim.product in {"Opportunity", "Cross-product", "External signal"}]
    if opportunity_claims:
        lines.extend(f"- {_zh_text(claim.claim)}（证据：{_evidence_ids(claim)}）。" for claim in opportunity_claims[:6])
    else:
        lines.append("可将上面的证据缺口作为下一轮机会发现队列；本次运行不足以支撑更强的战略判断。")

    lines.extend(["", "## 风险与不确定性", ""])
    lines.extend(f"- **{_label(ticket.severity, _SEVERITY_LABELS)} — {ticket.product or '横向比较'}：** {_zh_text(ticket.reason)} 后续动作：{_zh_text(ticket.required_action)}" for ticket in open_tickets[:8])
    if not open_tickets:
        lines.append("本次运行没有未解决的复核工单。")

    lines.extend(["", "## 建议的下一步动作", ""])
    if open_tickets:
        lines.extend(f"1. 通过请求的{_label(ticket.preferred_source_type, _SOURCE_TYPE_LABELS)}路径，补齐{ticket.product or '本次比较'}的{_zh_text(ticket.missing_evidence_type or '证据')}缺口。" for ticket in open_tickets[:5])
    else:
        lines.append("1. 在将结论用于演示环境之外前，使用真实 Provider 重跑相同场景。")
    lines.append("2. 将本次比较转化为产品决策时，保留 Evidence ID 和来源链接。")

    lines.extend(["", "## 证据与方法", "", "本次运行使用了正常工作流中的 Planner、Research、Normalization、Extraction、Interaction、Analyst、Critic、Reviewer、Trust 和 Writer 节点。Mock Provider 是用于本地验证的确定性固定数据，不代表真实市场调研。", ""])
    manifest = result.manifest
    manifest_rows = [
        ["工作流模式", {"adaptive_review": "自适应复核", "single_pass": "单次运行"}.get(config.workflow_mode, config.workflow_mode)],
        ["运行 ID", manifest.run_id if manifest else "不可用"],
        ["图版本", manifest.graph_version if manifest else "不可用"],
        ["固定数据模式", "是" if manifest and manifest.fixture_mode else "否" if manifest else "不可用"],
        ["搜索 / LLM Provider", f"{_zh_text(manifest.search_provider or 'unknown')} / {_zh_text(manifest.llm_provider or 'unknown')}" if manifest else "不可用"],
        ["启用的 Skills", ", ".join(manifest.enabled_skills) or "无" if manifest else "不可用"],
        ["来源数", len(result.sources)],
        ["证据条数", len(result.evidence)],
        ["结论数", len(result.claims)],
        ["已绑定结论", f"{coverage:.0%}"],
        ["复核工单数", len(result.review_tickets)],
        ["Trace 事件数", len(result.trace)],
        ["运行 Token 数", manifest.total_tokens if manifest else "不可用"],
        ["运行延迟（毫秒）", manifest.total_latency_ms if manifest else "不可用"],
        ["工具调用 / 重跑 / 循环", f"{manifest.total_tool_calls} / {manifest.total_reruns} / {manifest.total_loops}" if manifest else "不可用"],
    ]
    lines.extend(_table(["指标", "观测值"], manifest_rows))

    lines.extend(["", "## 置信度与可信度摘要", ""])
    if trust:
        provider_mode = {"Demo fixture run": "演示固定数据运行", "Live provider run": "真实 Provider 运行"}.get(trust.provider_mode_label, _zh_text(trust.provider_mode_label))
        lines.extend(_table(["指标", "值"], [["Claim-Evidence 绑定率", f"{trust.claim_evidence_binding_rate:.0%}"], ["官方来源占比", f"{trust.official_source_ratio:.0%}"], ["通过结论", f"{trust.passed_claim_count}/{trust.total_claim_count}"], ["不确定结论", trust.uncertain_claim_count], ["未解决工单", trust.unresolved_ticket_count], ["Provider 模式", provider_mode]]))

    lines.extend(["", "## 来源", ""])
    source_rows = []
    for source in result.sources[:16]:
        source_rows.append([source.product, _label(source.source_type, _SOURCE_TYPE_LABELS), source.title, source.url, _label(source.confidence, _CONFIDENCE_LABELS)])
    lines.extend(_table(["产品", "类型", "来源", "URL", "置信度"], source_rows) or ["没有来源通过标准化处理。"])

    lines.extend(["", "## 附录：审计轨迹", "", f"运行 Manifest：`{result.manifest.run_id if result.manifest else '不可用'}`；图版本：`{result.manifest.graph_version if result.manifest else '不可用'}`。", "", f"本次工作流产生了 {len(result.trace)} 个 Trace 事件，其中包含 {len([event for event in result.trace if event.event_type == 'review_ticket_selected'])} 次定向复核路由选择。原始技术细节仍可通过 API 的 Trace 和 Manifest 接口查看。"])
    return "\n".join(lines) + "\n"


def _inline(value: str) -> str:
    escaped = html.escape(value, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[([^]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def markdown_to_html(markdown: str, title: str) -> str:
    lines = markdown.splitlines()
    body: list[str] = []
    index = 0
    in_list = False
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            if in_list:
                body.append("</ul>")
                in_list = False
            index += 1
            continue
        if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
            if in_list:
                body.append("</ul>")
                in_list = False
            level = len(line) - len(line.lstrip("#"))
            tag = "h1" if level == 1 else "h2" if level == 2 else "h3"
            body.append(f"<{tag}>{_inline(line[level + 1:])}</{tag}>")
            index += 1
            continue
        if line.startswith("> "):
            body.append(f'<div class="callout">{_inline(line[2:])}</div>')
            index += 1
            continue
        bullet = re.match(r"^(\s*)-\s+(.*)$", line)
        numbered = re.match(r"^(\s*)\d+\.\s+(.*)$", line)
        if bullet or numbered:
            if not in_list:
                body.append("<ul>")
                in_list = True
            match = bullet or numbered
            indent = len(match.group(1))
            item = match.group(2)
            margin = f' style="margin-left:{indent * 12}px"' if indent else ""
            body.append(f"<li{margin}>{_inline(item)}</li>")
            index += 1
            continue
        if line.startswith("|") and index + 1 < len(lines) and lines[index + 1].startswith("|"):
            if in_list:
                body.append("</ul>")
                in_list = False
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip("|").split("|")]
                if not all(set(cell) <= {"-", ":", " "} for cell in cells):
                    rows.append(cells)
                index += 1
            if rows:
                body.append("<div class=\"table-wrap\"><table><thead><tr>" + "".join(f"<th>{_inline(cell)}</th>" for cell in rows[0]) + "</tr></thead><tbody>")
                for row in rows[1:]:
                    body.append("<tr>" + "".join(f"<td>{_inline(cell)}</td>" for cell in row) + "</tr>")
                body.append("</tbody></table></div>")
            continue
        body.append(f"<p>{_inline(line)}</p>")
        index += 1
    if in_list:
        body.append("</ul>")
    css = """
:root{--bg:#070b14;--surface:#0f1625;--surface2:#141d2e;--line:#273149;--text:#f5f7fb;--body:#d7deeb;--muted:#9ca9bd;--blue:#7c9cff;--violet:#a78bfa;--good:#45d6a7;--warn:#f4c36e}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.7 'Segoe UI','Microsoft YaHei UI',system-ui,sans-serif}.shell{max-width:1320px;margin:auto;padding:32px 34px 56px}.topbar{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:18px;color:var(--muted);font-size:13px;letter-spacing:.04em}.brand{color:var(--text);font-weight:700}.report{margin-top:28px;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:30px 34px}h1{font-size:38px;line-height:1.15;margin:0 0 8px;letter-spacing:-.03em}h2{font-size:23px;margin:34px 0 12px;border-top:1px solid var(--line);padding-top:20px}h3{font-size:17px;color:#c9d5ff;margin:22px 0 8px}p{color:var(--body);margin:9px 0}li{color:var(--body);margin:6px 0}.callout{margin:18px 0;padding:15px 17px;border-left:3px solid var(--blue);background:#0a1221;color:var(--body);border-radius:8px}.table-wrap{overflow-x:auto;margin:14px 0}table{width:100%;border-collapse:collapse;min-width:640px}th,td{text-align:left;vertical-align:top;padding:11px 12px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}th{color:var(--muted);font-size:12px;letter-spacing:.05em;text-transform:uppercase}td{color:var(--body)}code{color:#c9d5ff;background:#0a1020;border:1px solid var(--line);padding:1px 5px;border-radius:4px}a{color:var(--blue)}@media(max-width:700px){.shell{padding:16px}.report{padding:22px 18px}h1{font-size:30px}}@media print{body{background:#fff;color:#111}.shell{max-width:none;padding:0}.topbar{color:#555}.report{border:0;padding:0;background:#fff}h1,h2,h3,p,li,td,th{color:#111}.callout{background:#f2f5fa;border-color:#3e63c6}a{color:#1647ad}}
"""
    return f"<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta name=\"color-scheme\" content=\"dark light\"><title>{html.escape(title)}</title><style>{css}</style></head><body><main class=\"shell\"><header class=\"topbar\"><span class=\"brand\">EvidenceGraph · 竞品分析报告</span><span>确定性模拟工作流</span></header><article class=\"report\">{''.join(body)}</article></main></body></html>\n"


def main() -> int:
    task = Task(
        config=TaskConfig(
            domain="ai_tools",
            target_product="Cursor",
            competitors=["GitHub Copilot", "Windsurf", "TRAE"],
            analysis_goals=["Compare positioning, capabilities, pricing, users, workflow, and adoption risks."],
            audience="portfolio reader",
            workflow_mode="adaptive_review",
        )
    )
    result = run_workflow(task)
    markdown = build_demo_markdown(result)
    title = _report_title(result.report)
    (ROOT / "examples" / "demo-report.md").write_text(markdown, encoding="utf-8")
    (ROOT / "examples" / "demo-report.html").write_text(markdown_to_html(markdown, title), encoding="utf-8")
    print("examples/demo-report.md")
    print("examples/demo-report.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

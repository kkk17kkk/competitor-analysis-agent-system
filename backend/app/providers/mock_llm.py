from app.providers.llm import LLMProvider


class MockLLMProvider(LLMProvider):
    provider_name = "MockLLMProvider"

    def complete_structured(self, purpose: str, payload: dict, skill_prompt: str = "") -> dict:
        if purpose == "claim_enrichment":
            positioning_evidence = [
                item
                for item in payload.get("evidence", [])
                if item.get("evidence_type") == "positioning"
            ]
            if len(positioning_evidence) < 2:
                return {"claims": [], "__provider_meta": {"skill_prompt_used": bool(skill_prompt)}}
            products = sorted({item.get("product", "") for item in positioning_evidence if item.get("product")})
            return {
                "claims": [
                    {
                        "product": "Cross-product",
                        "claim_type": "llm_synthesis",
                        "claim": f"Provider-assisted synthesis should compare {', '.join(products[:4])} only through bound evidence.",
                        "supporting_evidence": [item["evidence_id"] for item in positioning_evidence[:4] if item.get("evidence_id")],
                        "confidence": "medium",
                    }
                ],
                "__provider_meta": {"skill_prompt_used": bool(skill_prompt)},
            }
        if purpose == "review_ticket_suggestions":
            return {"review_tickets": [], "__provider_meta": {"skill_prompt_used": bool(skill_prompt)}}
        if purpose == "report_enhancement":
            target = payload.get("task", {}).get("target_product", "target product")
            competitors = payload.get("task", {}).get("competitors", [])
            passed_claims = payload.get("trust_summary", {}).get("passed_claim_count", 0)
            total_claims = payload.get("trust_summary", {}).get("total_claim_count", 0)
            source_mix = payload.get("source_mix", {})
            third_party_ratio = source_mix.get("third_party_ratio", 0)
            included_claims = payload.get("included_claims", [])
            primary_claim = included_claims[0] if included_claims else {}
            secondary_claim = included_claims[1] if len(included_claims) > 1 else primary_claim
            primary_claim_id = primary_claim.get("claim_id", "")
            secondary_claim_id = secondary_claim.get("claim_id", "")
            primary_evidence = primary_claim.get("supporting_evidence", [])[:2] if isinstance(primary_claim.get("supporting_evidence"), list) else []
            secondary_evidence = secondary_claim.get("supporting_evidence", [])[:2] if isinstance(secondary_claim.get("supporting_evidence"), list) else []
            bound_items = [item for item in [primary_claim, secondary_claim] if item.get("claim_id")]
            matrix_rows = []
            for claim_type in sorted({item.get("claim_type") for item in included_claims if item.get("claim_type")}):
                matching = [item for item in included_claims if item.get("claim_type") == claim_type]
                matrix_rows.append(
                    {
                        "dimension": claim_type.replace("_", " ").title(),
                        "values": {item.get("product", ""): item.get("claim", "") for item in matching if item.get("product")},
                        "claim_ids": [item["claim_id"] for item in matching if item.get("claim_id")],
                        "evidence_ids": [evidence_id for item in matching for evidence_id in item.get("supporting_evidence", [])],
                    }
                )

            def bound_item(item: dict, text: str) -> dict:
                return {
                    "text": text,
                    "claim_ids": [item["claim_id"]],
                    "evidence_ids": item.get("supporting_evidence", [])[:2],
                    "confidence": "medium",
                    "product": item.get("product", ""),
                }

            summary_texts = [
                f"本报告围绕 {target} 与 {', '.join(competitors)} 的差异展开，当前有 {passed_claims}/{total_claims} 条结论通过证据复核。",
                f"第三方来源占比约为 {third_party_ratio:.0%}，应把它作为校准官方叙述的外部视角，而不是替代事实核验。",
            ]
            executive_summary = [bound_item(item, summary_texts[index]) for index, item in enumerate(bound_items)]
            primary_text = "当前优势判断已绑定通过复核的产品证据。" if primary_claim.get("claim") else ""
            secondary_text = "后续方向应以已验证差异为边界，并继续补齐证据缺口。" if secondary_claim.get("claim") else ""
            highlight = lambda item, title, body: {
                "title": title,
                "body": body,
                "claim_ids": [item["claim_id"]],
                "evidence_ids": item.get("supporting_evidence", [])[:2],
                "confidence": "medium",
            } if item.get("claim_id") and body else None
            return {
                "executive_summary": executive_summary,
                "decision_highlights": {
                    "strongest_advantage": highlight(primary_claim, "Evidence-backed advantage", primary_text),
                    "biggest_risk": None,
                    "recommended_direction": highlight(secondary_claim, "Evidence-backed direction", secondary_text),
                },
                "comparison_matrix": matrix_rows,
                "key_insights": executive_summary,
                "strategic_opportunities": [],
                "limitations": (["未绑定证据，需复核：当前没有可用于结构化结论的已验证证据。"] if not bound_items else []) + [
                    f"当前 {passed_claims}/{total_claims} 条结论通过复核；第三方来源占比为 {third_party_ratio:.0%}。",
                    "Mock LLM 输出仅用于无密钥工作流验证。",
                ],
                "__provider_meta": {"skill_prompt_used": bool(skill_prompt)},
            }
        if purpose == "competitor_recommendation":
            return {
                "competitors": ["GitHub Copilot", "Windsurf", "Codeium"],
                "rationale": "Mock recommendations for local validation.",
                "__provider_meta": {"skill_prompt_used": bool(skill_prompt)},
            }
        if purpose == "analysis_goal_condense":
            return {
                "condensed_text": "1. 对比目标产品与竞品的定位、核心功能、开放性、安全合规和落地风险。\n2. 输出证据支撑的差异结论、机会点和后续验证建议。",
                "__provider_meta": {"skill_prompt_used": bool(skill_prompt)},
            }
        if purpose == "survey_generation":
            product = payload.get("product_name") or "目标产品"
            target_users = payload.get("target_users") or "目标用户"
            return {
                "title": f"{product} 用户调研问卷",
                "research_objective": payload.get("research_goal") or f"验证 {product} 的用户需求、使用场景和购买/采用阻力。",
                "target_users": target_users,
                "screening_criteria": [
                    f"过去 3 个月内接触过 {product} 或同类产品",
                    "符合目标用户画像，并愿意分享真实使用经历",
                    "排除无相关使用经验或仅代填问卷的样本",
                ],
                "questions": [
                    {
                        "question_id": "Q1",
                        "type": "screening",
                        "text": f"你是否属于以下用户群体：{target_users}？",
                        "options": ["是", "否"],
                        "required": True,
                        "purpose": "确认样本资格",
                    },
                    {
                        "question_id": "Q2",
                        "type": "single_choice",
                        "text": f"你目前使用 {product} 或同类产品的频率是？",
                        "options": ["每天", "每周几次", "每月几次", "几乎不用"],
                        "required": True,
                        "purpose": "区分使用深度",
                    },
                    {
                        "question_id": "Q3",
                        "type": "likert",
                        "text": f"请评价 {product} 在你的核心任务中带来的效率提升。",
                        "options": ["1 非常不同意", "2", "3", "4", "5 非常同意"],
                        "required": True,
                        "purpose": "量化价值感知",
                    },
                    {
                        "question_id": "Q4",
                        "type": "multiple_choice",
                        "text": "你选择此类产品时最看重哪些因素？",
                        "options": ["功能完整度", "易用性", "价格", "数据安全", "团队协作", "生态集成"],
                        "required": True,
                        "purpose": "识别决策驱动因素",
                    },
                    {
                        "question_id": "Q5",
                        "type": "open_text",
                        "text": f"请描述一次你使用 {product} 或同类产品完成关键任务的经历。",
                        "options": [],
                        "required": False,
                        "purpose": "收集真实场景与任务链路",
                    },
                ],
                "analysis_plan": [
                    "先按筛选题剔除不符合目标样本的回答。",
                    "对量表题计算均值和分布，并按使用频率分组比较。",
                    "对开放题进行主题编码，提炼高频痛点、触发场景和替代方案。",
                ],
                "survey_json": {
                    "title": f"{product} 用户调研问卷",
                    "version": "1.0",
                    "groups": [
                        {
                            "nameID": "user_research",
                            "title": "用户调研",
                            "questions": ["Q1", "Q2", "Q3", "Q4", "Q5"],
                        }
                    ],
                },
                "__provider_meta": {"skill_prompt_used": bool(skill_prompt)},
            }
        if purpose == "social_insight_synthesis":
            refs = []
            for post in payload.get("posts", []):
                for comment in post.get("sample_comments", []):
                    comment_id = comment.get("comment_id")
                    if comment_id:
                        refs.append(comment_id)
            return {
                "findings": [
                    {
                        "category": "positive",
                        "title": "用户认可效率和教程价值",
                        "summary": "评论中出现好用、感谢、学到等表达，说明用户认可产品或教程带来的效率提升和上手帮助。",
                        "comment_refs": refs[:3],
                    },
                    {
                        "category": "pain",
                        "title": "价格与配置门槛仍需解释",
                        "summary": "评论也集中追问价格、Token、API 充值和配置问题，说明采用前仍需要更清楚的成本与上手说明。",
                        "comment_refs": refs[3:6],
                    },
                ],
                "__provider_meta": {"skill_prompt_used": bool(skill_prompt)},
            }
        return {"purpose": purpose, "mode": "mock", "payload_keys": sorted(payload.keys()), "__provider_meta": {"skill_prompt_used": bool(skill_prompt)}}

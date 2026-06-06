from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.providers.errors import ProviderConfigurationError, ProviderRequestError
from app.providers.llm import LLMProvider


PURPOSE_SCHEMAS = {
    "claim_enrichment": (
        "Return JSON: {\"claims\":[{\"product\":string,\"claim_type\":string,"
        "\"claim\":string,\"supporting_evidence\":[evidence_id],\"confidence\":\"low|medium|high\"}]}. "
        "Only use evidence_id values present in the input. Do not invent unsupported claims."
    ),
    "review_ticket_suggestions": (
        "Return JSON: {\"review_tickets\":[{\"target_node\":\"ResearchAgent|AnalystAgent\","
        "\"reason\":string,\"required_action\":string,\"severity\":\"critical|high|medium|low\","
        "\"affected_artifacts\":[string],\"product\":string,\"missing_evidence_type\":string,"
        "\"preferred_source_type\":string,\"source_query_hint\":string}]}. "
        "Suggest only actionable gaps that can improve evidence coverage or traceability."
    ),
    "report_enhancement": (
        "Return JSON: {\"executive_summary\":[string],\"strategic_recommendations\":[string],"
        "\"caveats\":[string]}. Keep every sentence evidence-bound and concise."
    ),
    "analysis_goal_polish": (
        "Return JSON: {\"goals\":[string],\"items\":[{\"title\":string,\"details\":[string]}]}. "
        "Rewrite the user's competitor-analysis target into clear numbered categories. "
        "Use polished Chinese unless the input is clearly English. Keep it practical for an analyst."
    ),
    "analysis_goal_condense": (
        "Return JSON: {\"condensed_text\":string}. "
        "Condense the user's competitor-analysis goals to fit within max_words while preserving product scope, "
        "comparison dimensions, constraints, and output expectations. Use Chinese unless the input is clearly English."
    ),
    "competitor_recommendation": (
        "Return JSON: {\"competitors\":[string],\"rationale\":string}. "
        "Recommend direct or adjacent competitors for the target product. "
        "Do not include the target product itself or products already listed in existing_competitors. "
        "Prefer real, currently recognizable products. Return concise product names only."
    ),
}

MODEL_ALIASES = {
    "deepseek-4-flash": "deepseek-v4-flash",
}


class DeepSeekLLMProvider(LLMProvider):
    provider_name = "DeepSeekLLMProvider"

    def __init__(self, api_key: str, base_url: str, model: str, timeout_seconds: int = 45):
        if not api_key:
            raise ProviderConfigurationError("DEEPSEEK_API_KEY is required when DeepSeek LLM is enabled.")
        if not base_url:
            raise ProviderConfigurationError("DEEPSEEK_BASE_URL is required when DeepSeek LLM is enabled.")
        if not model:
            raise ProviderConfigurationError("DEEPSEEK_MODEL is required when DeepSeek LLM is enabled.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = MODEL_ALIASES.get(model, model)
        self.timeout_seconds = timeout_seconds

    def complete_structured(self, purpose: str, payload: dict) -> dict:
        schema_instruction = PURPOSE_SCHEMAS.get(purpose, "Return strict JSON only.")
        request_body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"You are a structured-output assistant for {purpose}. "
                        f"{schema_instruction} Return only valid JSON, without markdown fences."
                    ),
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        request = Request(
            self.base_url,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                request_id = response.headers.get("x-request-id") or response.headers.get("x-ds-trace-id") or ""
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")[:500]
            raise ProviderRequestError(f"DeepSeek request failed with HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise ProviderRequestError(f"DeepSeek request failed: {exc.reason}.") from exc
        except TimeoutError as exc:
            raise ProviderRequestError("DeepSeek request timed out.") from exc
        except json.JSONDecodeError as exc:
            raise ProviderRequestError("DeepSeek returned invalid JSON.") from exc

        content = body.get("output") or body.get("content")
        if not content and body.get("choices"):
            content = body["choices"][0].get("message", {}).get("content")
        if isinstance(content, dict):
            parsed = content
        elif isinstance(content, str):
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ProviderRequestError("DeepSeek response content was not valid JSON.") from exc
        elif isinstance(body, dict):
            parsed = body
        else:
            raise ProviderRequestError("DeepSeek returned an unsupported response shape.")

        if isinstance(parsed, dict):
            parsed.setdefault(
                "__provider_meta",
                {
                    "request_id": request_id or body.get("id", ""),
                    "usage": body.get("usage", {}),
                    "model": body.get("model", self.model),
                },
            )
            return parsed
        raise ProviderRequestError("DeepSeek parsed content was not a JSON object.")

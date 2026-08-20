"""Optional live LLM/search smoke checks.

The default behavior is CI-safe: missing credentials produce a skipped check
and exit 0. Use --require-live when a manual environment must fail closed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def _run_search(provider_name: str) -> dict[str, object]:
    from app.models.schemas import SearchQuery
    from app.providers.anysearch import AnySearchProvider
    from app.providers.duckduckgo import DuckDuckGoSearchProvider
    from app.providers.errors import ProviderConfigurationError
    from app.providers.factory import load_provider_settings

    settings = load_provider_settings()
    if settings.use_mock_search or settings.public_demo_mode:
        raise ProviderConfigurationError("Search provider is configured for mock/demo mode.")
    selected = (provider_name or settings.search_provider).strip().lower()
    if selected == "duckduckgo":
        provider = DuckDuckGoSearchProvider(max_results=3)
    elif selected == "anysearch":
        provider = AnySearchProvider(
            api_key=settings.anysearch_api_key,
            base_url=settings.anysearch_base_url,
            max_results=3,
        )
    else:
        raise ProviderConfigurationError(f"Unsupported smoke SEARCH_PROVIDER: {selected}.")
    query = SearchQuery(
        query="official Cursor AI code editor features",
        product="Cursor",
        expected_evidence="feature",
        source_preference="official",
    )
    results = provider.search("live-smoke", query)
    if not results:
        raise RuntimeError(f"{provider.provider_name} returned no results.")
    return {"provider": provider.provider_name, "result_count": len(results)}


def _run_llm() -> dict[str, object]:
    from app.providers.deepseek import DeepSeekLLMProvider
    from app.providers.errors import ProviderConfigurationError
    from app.providers.factory import load_provider_settings

    settings = load_provider_settings()
    if settings.use_mock_llm or settings.public_demo_mode:
        raise ProviderConfigurationError("LLM provider is configured for mock/demo mode.")
    provider = DeepSeekLLMProvider(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
    )
    response = provider.complete_structured(
        "analysis_goal_condense",
        {
            "draft": "Compare an AI coding product's positioning, pricing, evidence coverage, and adoption risks.",
            "max_words": 40,
        },
    )
    if not isinstance(response, dict) or not response:
        raise RuntimeError("DeepSeek returned an empty structured response.")
    return {"provider": provider.provider_name, "model": provider.model, "response_keys": sorted(response.keys())}


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional live provider smoke checks.")
    parser.add_argument("--check", choices=("both", "llm", "search"), default="both")
    parser.add_argument("--search-provider", default="", help="anysearch or duckduckgo; defaults to SEARCH_PROVIDER")
    parser.add_argument("--require-live", action="store_true", help="fail when credentials/configuration are missing")
    args = parser.parse_args()

    from app.providers.errors import ProviderConfigurationError, ProviderRequestError

    checks: dict[str, object] = {}
    failures = []
    for name, enabled, callback in (
        ("llm", args.check in {"both", "llm"}, _run_llm),
        ("search", args.check in {"both", "search"}, lambda: _run_search(args.search_provider)),
    ):
        if not enabled:
            continue
        try:
            checks[name] = {"status": "passed", **callback()}
        except (ProviderConfigurationError, ProviderRequestError) as exc:
            checks[name] = {"status": "skipped", "reason": str(exc)}
            if args.require_live:
                failures.append(f"{name}: {exc}")
        except Exception as exc:
            checks[name] = {"status": "failed", "reason": str(exc)}
            failures.append(f"{name}: {exc}")

    print(json.dumps(checks, ensure_ascii=False, indent=2))
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

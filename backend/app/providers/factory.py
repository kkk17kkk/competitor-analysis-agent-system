from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from app.providers.anysearch import AnySearchProvider
from app.providers.deepseek import DeepSeekLLMProvider
from app.providers.duckduckgo import DuckDuckGoSearchProvider
from app.providers.errors import ProviderConfigurationError
from app.providers.llm import LLMProvider
from app.providers.mock_llm import MockLLMProvider
from app.providers.mock_search import MockSearchProvider
from app.providers.search import SearchProvider
from app.providers.seed import SeedLLMProvider


@dataclass(frozen=True)
class ProviderSettings:
    use_mock_search: bool
    use_mock_llm: bool
    search_provider: str
    anysearch_api_key: str
    anysearch_base_url: str
    anysearch_max_results: int
    anysearch_content_types: tuple[str, ...]
    llm_provider: str
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    seed_api_key: str
    seed_base_url: str
    seed_model: str
    lightweight_llm_provider: str
    lightweight_seed_api_key: str
    lightweight_seed_base_url: str
    lightweight_seed_model: str
    allow_provider_fallback: bool
    allow_empty_search_fallback: bool


@dataclass(frozen=True)
class ProviderBundle:
    search: SearchProvider
    llm: LLMProvider
    fixture_mode: bool
    search_mode: str
    llm_mode: str
    warnings: tuple[str, ...] = ()
    allow_provider_fallback: bool = True
    allow_empty_search_fallback: bool = True


def load_provider_settings() -> ProviderSettings:
    _load_env_files()
    return ProviderSettings(
        use_mock_search=_env_bool("USE_MOCK_SEARCH", False),
        use_mock_llm=_env_bool("USE_MOCK_LLM", False),
        search_provider=os.getenv("SEARCH_PROVIDER", "anysearch").strip().lower(),
        anysearch_api_key=os.getenv("ANYSEARCH_API_KEY", ""),
        anysearch_base_url=os.getenv("ANYSEARCH_BASE_URL", "https://api.anysearch.com/v1/search"),
        anysearch_max_results=_env_int("ANYSEARCH_MAX_RESULTS", 5),
        anysearch_content_types=_env_list("ANYSEARCH_CONTENT_TYPES"),
        llm_provider=os.getenv("LLM_PROVIDER", "deepseek").strip().lower(),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/chat/completions"),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        seed_api_key=os.getenv("SEED_API_KEY", ""),
        seed_base_url=os.getenv("SEED_BASE_URL", ""),
        seed_model=os.getenv("SEED_MODEL", ""),
        lightweight_llm_provider=os.getenv("LIGHTWEIGHT_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "deepseek")).strip().lower(),
        lightweight_seed_api_key=os.getenv("LIGHTWEIGHT_SEED_API_KEY", os.getenv("SEED_API_KEY", "")),
        lightweight_seed_base_url=os.getenv("LIGHTWEIGHT_SEED_BASE_URL", os.getenv("SEED_BASE_URL", "")),
        lightweight_seed_model=os.getenv("LIGHTWEIGHT_SEED_MODEL", os.getenv("SEED_MODEL", "")),
        allow_provider_fallback=_env_bool("ALLOW_PROVIDER_FALLBACK", False),
        allow_empty_search_fallback=_env_bool("ALLOW_EMPTY_SEARCH_FALLBACK", False),
    )


def build_provider_bundle(settings: ProviderSettings | None = None) -> ProviderBundle:
    cfg = settings or load_provider_settings()
    warnings: list[str] = []

    if cfg.use_mock_search:
        search: SearchProvider = MockSearchProvider()
        search_mode = "mock"
    else:
        try:
            if cfg.search_provider == "duckduckgo":
                search = DuckDuckGoSearchProvider(max_results=cfg.anysearch_max_results)
                search_mode = "duckduckgo"
            elif cfg.search_provider == "anysearch":
                search = AnySearchProvider(
                    api_key=cfg.anysearch_api_key,
                    base_url=cfg.anysearch_base_url,
                    max_results=cfg.anysearch_max_results,
                    content_types=list(cfg.anysearch_content_types),
                )
                search_mode = "anysearch"
            else:
                raise ProviderConfigurationError(f"Unsupported SEARCH_PROVIDER: {cfg.search_provider}.")
        except ProviderConfigurationError as exc:
            if not cfg.allow_provider_fallback:
                raise
            warnings.append(str(exc))
            search = MockSearchProvider()
            search_mode = "mock_fallback"

    if cfg.use_mock_llm:
        llm: LLMProvider = MockLLMProvider()
        llm_mode = "mock"
    else:
        try:
            if cfg.llm_provider == "deepseek":
                llm = DeepSeekLLMProvider(
                    api_key=cfg.deepseek_api_key,
                    base_url=cfg.deepseek_base_url,
                    model=cfg.deepseek_model,
                )
                llm_mode = "deepseek"
            elif cfg.llm_provider == "seed":
                llm = SeedLLMProvider(
                    api_key=cfg.seed_api_key,
                    base_url=cfg.seed_base_url,
                    model=cfg.seed_model,
                )
                llm_mode = "seed"
            else:
                raise ProviderConfigurationError(f"Unsupported LLM_PROVIDER: {cfg.llm_provider}.")
        except ProviderConfigurationError as exc:
            if not cfg.allow_provider_fallback:
                raise
            warnings.append(str(exc))
            llm = MockLLMProvider()
            llm_mode = "mock_fallback"

    return ProviderBundle(
        search=search,
        llm=llm,
        fixture_mode=search_mode.startswith("mock") or llm_mode.startswith("mock"),
        search_mode=search_mode,
        llm_mode=llm_mode,
        warnings=tuple(warnings),
        allow_provider_fallback=cfg.allow_provider_fallback,
        allow_empty_search_fallback=cfg.allow_empty_search_fallback,
    )


def build_lightweight_llm_provider(settings: ProviderSettings | None = None) -> tuple[LLMProvider, str]:
    cfg = settings or load_provider_settings()
    provider = cfg.lightweight_llm_provider
    if provider == "seed":
        return (
            SeedLLMProvider(
                api_key=cfg.lightweight_seed_api_key,
                base_url=cfg.lightweight_seed_base_url,
                model=cfg.lightweight_seed_model,
            ),
            "seed",
        )
    if provider == "deepseek":
        return (
            DeepSeekLLMProvider(
                api_key=cfg.deepseek_api_key,
                base_url=cfg.deepseek_base_url,
                model=cfg.deepseek_model,
            ),
            "deepseek",
        )
    if provider == "mock":
        return MockLLMProvider(), "mock"
    raise ProviderConfigurationError(f"Unsupported LIGHTWEIGHT_LLM_PROVIDER: {provider}.")


def _load_env_files() -> None:
    app_root = Path(__file__).resolve().parents[3]
    load_dotenv(app_root / ".env")
    load_dotenv(app_root / "backend" / ".env")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_list(name: str) -> tuple[str, ...]:
    raw = os.getenv(name, "")
    return tuple(item.strip() for item in raw.split(",") if item.strip())

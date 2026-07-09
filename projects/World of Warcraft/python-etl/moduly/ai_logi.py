from datetime import datetime, timezone
from typing import Any, Literal
from zoneinfo import ZoneInfo

from sqlalchemy import text

from langchain_core.messages import AIMessage
from langchain_qwq import ChatQwen
from langchain_openai import ChatOpenAI

from moduly.ai_modele import (
    TEMPERATURE_TRANSLATOR,
    TEMPERATURE_EDITOR,
    TEMPERATURE_SUMMARY_QUEST,
    TEMPERATURE_JSON_CORRECTOR,
    TEMPERATURE_LORE,
    TEMPERATURE_CONTEXT,
    TEMPERATURE_CHUNKER,
)

from moduly.ai_pricing import MODEL_PRICING
from moduly.utils import skompresuj_tekst


TEMPERATURE_BY_STAGE = {
    "translator": TEMPERATURE_TRANSLATOR,
    "editor": TEMPERATURE_EDITOR,
    "rag_questions": TEMPERATURE_LORE,
    "rag_context": TEMPERATURE_CONTEXT,
    "quest_summary": TEMPERATURE_SUMMARY_QUEST,
    "rag_chunking": TEMPERATURE_CHUNKER
}

def format_created_at(created_at: Any) -> str | None:
    if isinstance(created_at, (int, float)):
        return datetime.fromtimestamp(created_at, tz=timezone.utc).astimezone(ZoneInfo("Europe/Warsaw")).isoformat()
    return None


def get_nested(mapping: dict[str, Any], *path: str) -> Any:
    value: Any = mapping
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def calculate_price_for_tokens(
    model_name: str,
    tokens: int | None,
    stage: Literal["input", "output"]
) -> str:
    if model_name not in MODEL_PRICING:
        raise KeyError(f"---Brak cennika dla modelu: {model_name}")

    pricing = MODEL_PRICING[model_name]
    currency = pricing["currency"]
    tokens = tokens or 0

    if stage == "input":
        price_per_1m = pricing["input_per_1m"]
    else:
        price_per_1m = pricing["output_per_1m"]

    value = tokens / 1_000_000 * price_per_1m
    return f"{value:.5f} {currency}"


def create_logs(
    raw_response: AIMessage,
    llm: ChatQwen | ChatOpenAI,
    misja_id_moje_fk: int,
    input_chars: int,
    output_chars: int,
    stage: str,
    duration_ms: int | None = None,
    parsing_error: str | None = None,
    input_txt: str | None = None,
    output_txt: str | None = None
) -> dict[str, Any]:

    zapisz_tresc = stage in ("translator", "editor")

    response_metadata = raw_response.response_metadata or {}
    usage_metadata = raw_response.usage_metadata or {}
    additional_kwargs = raw_response.additional_kwargs or {}
    output_token_details = usage_metadata.get("output_token_details", {}) or {}
    input_token_details = usage_metadata.get("input_token_details", {}) or {}
    created_at = response_metadata.get("created_at")
    duration_s = round(duration_ms / 1000, 3) if duration_ms is not None else None

    model_name = llm.model_name
    input_cached_tokens = input_token_details.get("cache_read") or 0
    input_tokens = usage_metadata.get("input_tokens") or 0
    output_tokens = usage_metadata.get("output_tokens") or 0
    total_tokens = usage_metadata.get("total_tokens") or 0

    finish_reason = response_metadata.get("finish_reason")
    response_status = response_metadata.get("status")
    status = response_status or ("completed" if finish_reason in (None, "stop") else finish_reason)
    model_api = (
        response_metadata.get("model")
        or response_metadata.get("model_name")
        or model_name
    )
    service_tier = response_metadata.get("service_tier") or getattr(llm, "service_tier", None)
    if service_tier is None and isinstance(llm, ChatQwen):
        service_tier = "default"
    thinking_tokens = (
        output_token_details.get("reasoning")
        or output_token_details.get("reasoning_tokens")
        or get_nested(response_metadata, "token_usage", "completion_tokens_details", "reasoning_tokens")
        or get_nested(additional_kwargs, "usage", "completion_tokens_details", "reasoning_tokens")
    )
    reasoning_effort = getattr(llm, "reasoning_effort", None)
    if reasoning_effort is None and getattr(llm, "enable_thinking", None) is not None:
        reasoning_effort = "thinking" if llm.enable_thinking else "disabled"

    currency = MODEL_PRICING[model_name]["currency"]
    input_per_1m = MODEL_PRICING[model_name]["input_per_1m"]
    output_per_1m = MODEL_PRICING[model_name]["output_per_1m"]
    cache_hit_price_factor = MODEL_PRICING[model_name]["cache_prc"]
    input_uncached_tokens = max(input_tokens - input_cached_tokens, 0)

    input_tokens_price_value = (
        (input_uncached_tokens / 1_000_000) * input_per_1m
        + (input_cached_tokens / 1_000_000) * input_per_1m * cache_hit_price_factor
    )
    output_tokens_price_value = (output_tokens / 1_000_000) * output_per_1m

    input_tokens_price = round(input_tokens_price_value, 8)
    output_tokens_price = round(output_tokens_price_value, 8)

    return {
        "ANSWER_ID": raw_response.id or response_metadata.get("id"),
        "PROVIDER": response_metadata.get("model_provider"),
        "SERVICE_TIER": service_tier,
        "STAGE": stage,
        "STATUS": "error" if parsing_error else status,
        "DURATION_S": duration_s,
        "MISJA_ID_MOJE_FK": misja_id_moje_fk,
        "CREATED_AT": (
            format_created_at(created_at)
            or datetime.now(ZoneInfo("Europe/Warsaw")).isoformat()
        ),
        "MODEL": model_name,
        "MODEL_API": model_api,
        "TOTAL_TOKENS": total_tokens,
        "INPUT_TOKENS": input_tokens,
        "OUTPUT_TOKENS": output_tokens,
        "INPUT_TOKENS_PRICE": input_tokens_price,
        "OUTPUT_TOKENS_PRICE": output_tokens_price,
        "CURRENCY": currency,
        "CACHED_TOKENS": input_cached_tokens,
        "THINKING_TOKENS": thinking_tokens,
        "INPUT_CHARS_ONLY_JSON": input_chars,
        "OUTPUT_CHARS_ONLY_JSON": output_chars,
        "REASONING_EFFORT": reasoning_effort,
        "TEMPERATURE_FROM_LLM": getattr(llm, "temperature", None),
        "TEMPERATURE_FROM_CONST": (
            TEMPERATURE_JSON_CORRECTOR
            if stage.endswith("_json_correction")
            else TEMPERATURE_BY_STAGE.get(stage)
        ),
        "PARSING_ERROR": parsing_error[:1000] if parsing_error else parsing_error,
        "INPUT_SKOMPRESOWANY": skompresuj_tekst(input_txt) if zapisz_tresc else None,
        "OUTPUT_SKOMPRESOWANY": skompresuj_tekst(output_txt) if zapisz_tresc else None
    }


def save_ai_logs_to_db(
    silnik,
    logs
):
    with silnik.begin() as conn:
        q_insert = text("""
            INSERT INTO dbo.AI_LOGI (
                ANSWER_ID, PROVIDER, SERVICE_TIER, STAGE,
                STATUS, DURATION_S, MISJA_ID_MOJE_FK, CREATED_AT,
                MODEL, MODEL_API, TOTAL_TOKENS, INPUT_TOKENS,
                OUTPUT_TOKENS, INPUT_TOKENS_PRICE, OUTPUT_TOKENS_PRICE, CURRENCY,
                CACHED_TOKENS, THINKING_TOKENS, INPUT_CHARS_ONLY_JSON, OUTPUT_CHARS_ONLY_JSON,
                REASONING_EFFORT, TEMPERATURE_FROM_LLM, TEMPERATURE_FROM_CONST, PARSING_ERROR,
                INPUT_SKOMPRESOWANY, OUTPUT_SKOMPRESOWANY
            )
            VALUES (
                :ANSWER_ID, :PROVIDER, :SERVICE_TIER, :STAGE,
                :STATUS, :DURATION_S, :MISJA_ID_MOJE_FK, :CREATED_AT,
                :MODEL, :MODEL_API, :TOTAL_TOKENS, :INPUT_TOKENS,
                :OUTPUT_TOKENS, :INPUT_TOKENS_PRICE, :OUTPUT_TOKENS_PRICE, :CURRENCY,
                :CACHED_TOKENS, :THINKING_TOKENS, :INPUT_CHARS_ONLY_JSON, :OUTPUT_CHARS_ONLY_JSON,
                :REASONING_EFFORT, :TEMPERATURE_FROM_LLM, :TEMPERATURE_FROM_CONST, :PARSING_ERROR,
                :INPUT_SKOMPRESOWANY, :OUTPUT_SKOMPRESOWANY
            )
        """)
        conn.execute(q_insert, logs)

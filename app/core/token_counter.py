from typing import Any

import tiktoken

from app.core.billing import TokenUsage


def _get_encoding(model_name: str):
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def _count_text_tokens(text: str, model_name: str) -> int:
    encoding = _get_encoding(model_name)
    return len(encoding.encode(text or ""))


def estimate_usage_from_request(endpoint: str, payload: dict[str, Any], model_name: str) -> TokenUsage:
    if endpoint == "/v1/chat/completions":
        messages = payload.get("messages", [])
        text_parts: list[str] = []
        for message in messages:
            content = message.get("content", "")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(str(item.get("text", "")))
            else:
                text_parts.append(str(content))
        joined = "\n".join(text_parts)
        input_tokens = _count_text_tokens(joined, model_name)
        return TokenUsage(input_tokens=input_tokens, cached_input_tokens=0, output_tokens=0, is_estimated=True)

    if endpoint == "/v1/embeddings":
        inp = payload.get("input", "")
        if isinstance(inp, list):
            joined = "\n".join(str(x) for x in inp)
        else:
            joined = str(inp)
        input_tokens = _count_text_tokens(joined, model_name)
        return TokenUsage(input_tokens=input_tokens, cached_input_tokens=0, output_tokens=0, is_estimated=True)

    return TokenUsage(is_estimated=True)


def parse_usage_from_upstream(endpoint: str, payload: dict[str, Any], response_json: dict[str, Any], model_name: str) -> TokenUsage:
    usage = response_json.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)

    prompt_details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    cached_tokens = int(prompt_details.get("cached_tokens") or 0)

    if prompt_tokens > 0 or completion_tokens > 0 or cached_tokens > 0:
        return TokenUsage(
            input_tokens=prompt_tokens,
            cached_input_tokens=cached_tokens,
            output_tokens=completion_tokens,
            is_estimated=False,
        )

    return estimate_usage_from_request(endpoint=endpoint, payload=payload, model_name=model_name)

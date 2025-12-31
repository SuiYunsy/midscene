"""统一的模型调用封装，支持 HTTP 代理，移除 qwen2.5/doubao 兼容逻辑。"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional, Tuple

import httpx
from json_repair import repair_json

from ...shared.env import ModelConfig
from ...shared.logger import get_logger

logger = get_logger("service-caller")


def extract_json_from_code_block(response: str) -> str:
    """尽力从文本或代码块中提取 JSON。"""
    response = response.strip()
    if response.startswith("{") and response.endswith("}"):
        return response
    import re

    block = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
    if block:
        return block.group(1)
    inline = re.search(r"(\{[\s\S]*\})", response)
    if inline:
        return inline.group(1)
    return response


def normalize_json_object(obj: Any) -> Any:
    if obj is None:
        return obj
    if isinstance(obj, list):
        return [normalize_json_object(item) for item in obj]
    if isinstance(obj, dict):
        return {k.strip(): normalize_json_object(v) for k, v in obj.items()}
    if isinstance(obj, str):
        return obj.strip()
    return obj


def safe_parse_json(input_text: str) -> Any:
    candidate = extract_json_from_code_block(input_text)
    try:
        return normalize_json_object(json.loads(candidate))
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        repaired = repair_json(candidate)
        return normalize_json_object(json.loads(repaired))
    except (json.JSONDecodeError, ValueError, TypeError) as error:
        raise ValueError(
            f"Failed to parse model response into JSON. Response:\n{input_text}"
        ) from error


def _http_client(model_config: ModelConfig) -> httpx.Client:
    proxies = None
    if model_config.http_proxy:
        proxies = {"all": model_config.http_proxy}
        logger.info("Using HTTP proxy: %s", model_config.http_proxy)
    return httpx.Client(
        base_url=model_config.base_url,
        proxies=proxies,
        timeout=model_config.timeout,
        headers=model_config.as_http_headers(),
    )


def call_ai(
    messages: Iterable[Dict[str, Any]],
    model_config: ModelConfig,
    *,
    response_format: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    调用 openai 兼容接口，返回文本内容与 usage。

    :param messages: openai 风格的消息数组，包含 system/user/assistant。
    :param model_config: 模型配置（base_url、api_key、proxy、超时等）。
    :param response_format: 可选的 JSON Schema，用于强约束返回结构。
    :returns: (content, usage) 二元组，content 为字符串，usage 为 tokens 统计或 None。
    """
    payload: Dict[str, Any] = {
        "model": model_config.model_name,
        "messages": list(messages),
        "temperature": model_config.temperature,
    }
    if response_format:
        payload["response_format"] = response_format

    logger.info("Calling model=%s on %s", model_config.model_name, model_config.base_url)
    with _http_client(model_config) as client:
        resp = client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"Empty response from model: {data}")
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    usage = data.get("usage")
    logger.info("Model response received, tokens=%s", usage or {})
    return content, usage


def call_ai_with_object_response(
    messages: Iterable[Dict[str, Any]],
    model_config: ModelConfig,
    *,
    response_format: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    content, usage = call_ai(messages, model_config, response_format=response_format)
    parsed = safe_parse_json(content)
    return {"content": parsed, "content_string": content, "usage": usage}


def call_ai_with_string_response(
    messages: Iterable[Dict[str, Any]], model_config: ModelConfig
) -> Dict[str, Any]:
    content, usage = call_ai(messages, model_config)
    return {"content": content, "usage": usage}

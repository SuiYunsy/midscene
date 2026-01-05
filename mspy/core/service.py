"""AI服务调用模块"""
import json
import ssl
import httpx
from typing import Any, Dict, List, Optional, Tuple
from ..shared.config import Config, get_config
from ..shared.logger import get_logger
from ..shared.utils import mask_base64_in_text, truncate_text

logger = get_logger("ai-service")

class AIService:
    """AI服务调用器 - 支持OpenAI兼容API"""
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
    def _build_http_client(self) -> httpx.AsyncClient:
        """构建HTTP客户端，支持代理和SSL配置"""
        kwargs: Dict[str, Any] = {"timeout": httpx.Timeout(600.0)}  # 10分钟超时
        if self.config.timeout:
            kwargs["timeout"] = httpx.Timeout(self.config.timeout / 1000.0)
        # 代理配置
        proxy_url = None
        if self.config.http_proxy:
            proxy_url = self.config.http_proxy
            logger.info(f"使用HTTP代理: {self._sanitize_proxy_url(proxy_url)}")
        elif self.config.socks_proxy:
            proxy_url = self.config.socks_proxy
            logger.info(f"使用SOCKS代理: {self._sanitize_proxy_url(proxy_url)}")
        if proxy_url:
            kwargs["proxy"] = proxy_url
        # SSL配置
        if self.config.skip_cert_verification:
            logger.warning("已禁用SSL证书验证")
            kwargs["verify"] = False
        return httpx.AsyncClient(**kwargs)
    def _sanitize_proxy_url(self, url: str) -> str:
        """清理代理URL中的敏感信息"""
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(url)
            if parsed.password:
                netloc = f"{parsed.username}:****@{parsed.hostname}"
                if parsed.port:
                    netloc += f":{parsed.port}"
                return urlunparse(parsed._replace(netloc=netloc))
            return url
        except Exception:
            return url
    def _log_messages(self, messages: List[Dict[str, Any]], prefix: str = "请求") -> None:
        """打印消息日志，屏蔽base64内容"""
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "system":
                # system消息只打印前50个字符
                if isinstance(content, str):
                    text = truncate_text(content, 50)
                else:
                    text = truncate_text(str(content), 50)
                logger.info(f"[{prefix}] {role}: {text}")
            elif role in ("user", "assistant"):
                if isinstance(content, str):
                    # 屏蔽base64
                    text = mask_base64_in_text(content)
                    logger.info(f"[{prefix}] {role}: {text}")
                elif isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                parts.append(item.get("text", ""))
                            elif item.get("type") == "image_url":
                                parts.append("base64 is masked.")
                        else:
                            parts.append(str(item))
                    logger.info(f"[{prefix}] {role}: {' '.join(parts)}")
                else:
                    logger.info(f"[{prefix}] {role}: {content}")
    async def call_with_json_response(
        self,
        messages: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], str, Optional[Dict[str, Any]]]:
        """
        调用AI并返回JSON响应
        返回: (解析后的JSON, 原始响应字符串, usage信息)
        """
        self._log_messages(messages, "请求")
        async with self._build_http_client() as client:
            base_url = self.config.model_base_url.rstrip("/")
            url = f"{base_url}/chat/completions"
            headers = {
                "Content-Type": "application/json",
            }
            if self.config.model_api_key:
                headers["Authorization"] = f"Bearer {self.config.model_api_key}"
            payload = {
                "model": self.config.model_name,
                "messages": messages,
                "temperature": self.config.temperature,
            }
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
        # 提取响应内容
        choices = result.get("choices", [])
        if not choices:
            raise ValueError("AI返回空响应")
        content = choices[0].get("message", {}).get("content", "")
        usage = result.get("usage")
        # 打印响应日志
        logger.info(f"[响应] assistant: {mask_base64_in_text(content)}")
        # 解析JSON
        parsed = self._parse_json_response(content)
        return parsed, content, usage
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析JSON响应，支持多种格式"""
        content = content.strip()
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        # 尝试从代码块中提取
        import re
        code_block = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
        if code_block:
            try:
                return json.loads(code_block.group(1))
            except json.JSONDecodeError:
                pass
        # 尝试查找JSON对象
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"无法解析AI响应为JSON: {content[:200]}...")

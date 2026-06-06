"""OpenAI-compatible Chat Completions client."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Dict, List

from n2s_config import chat_completions_url, load_env, optional, required


Message = Dict[str, str]


class LLMClient:
    def __init__(self) -> None:
        values = load_env()
        self.api_key = required(values, "N2S_API_KEY")
        self.base_url = required(values, "N2S_BASE_URL")
        self.model = required(values, "N2S_MODEL")
        self.timeout = int(optional(values, "N2S_TIMEOUT", "120"))

    def complete_json(self, messages: List[Message], temperature: float = 0.4) -> Dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            chat_completions_url(self.base_url),
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"模型接口返回错误 {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"无法连接模型接口: {exc}") from exc

        try:
            content = json.loads(body)["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"模型返回不是可解析 JSON: {body[:1000]}") from exc

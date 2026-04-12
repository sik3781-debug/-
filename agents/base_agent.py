"""
BaseAgent: Anthropic SDK 기반 공통 에이전트 클래스
- 프롬프트 캐싱 적용
- per-agent 모델 선택 지원 (model 클래스 속성 오버라이드)
- 툴 호출 루프 내장
"""

from __future__ import annotations

import json
import os
from typing import Any

import anthropic

MODEL = "claude-sonnet-4-6"
MODEL_LIGHT = "claude-haiku-4-5-20251001"
MAX_TOKENS = 8192


class BaseAgent:
    """모든 컨설팅 에이전트의 베이스 클래스."""

    name: str = "BaseAgent"
    role: str = "일반 에이전트"
    system_prompt: str = "당신은 유능한 AI 어시스턴트입니다."
    model: str = MODEL  # 서브클래스에서 MODEL_LIGHT 등으로 오버라이드 가능

    def __init__(self, verbose: bool = False) -> None:
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.verbose = verbose
        self.conversation: list[dict[str, Any]] = []
        self.tools: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # 내부 유틸                                                             #
    # ------------------------------------------------------------------ #

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"  [{self.name}] {msg}")

    def _build_system(self) -> list[dict[str, Any]]:
        """캐시 제어 헤더를 포함한 시스템 블록 구성."""
        return [
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def _call_api(self, messages: list[dict[str, Any]]) -> anthropic.types.Message:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "system": self._build_system(),
            "messages": messages,
            "extra_headers": {"anthropic-beta": "prompt-caching-2024-07-31"},
        }
        if self.tools:
            kwargs["tools"] = self.tools
        return self.client.messages.create(**kwargs)

    # ------------------------------------------------------------------ #
    # 툴 처리 (서브클래스 오버라이드 가능)                                    #
    # ------------------------------------------------------------------ #

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """툴 호출 결과를 반환한다. 서브클래스에서 재정의."""
        return f"[{tool_name}] 툴이 등록되지 않았습니다."

    # ------------------------------------------------------------------ #
    # 핵심 실행 루프                                                         #
    # ------------------------------------------------------------------ #

    def run(self, user_message: str, *, reset: bool = False) -> str:
        """단일 사용자 메시지를 처리하고 최종 텍스트 응답을 반환한다."""
        if reset:
            self.conversation = []

        self.conversation.append({"role": "user", "content": user_message})
        self._log(f"입력: {user_message[:80]}...")

        while True:
            response = self._call_api(self.conversation)
            stop_reason = response.stop_reason

            assistant_content = response.content
            self.conversation.append({"role": "assistant", "content": assistant_content})

            if stop_reason in ("end_turn", "max_tokens"):
                text = next(
                    (b.text for b in assistant_content if hasattr(b, "text")), ""
                )
                if stop_reason == "max_tokens" and text:
                    text += "\n\n[※ 응답이 최대 토큰에 도달하여 일부 생략됨]"
                self._log(f"완료 ({len(text)} chars)")
                return text

            if stop_reason == "tool_use":
                tool_results: list[dict[str, Any]] = []
                for block in assistant_content:
                    if block.type == "tool_use":
                        self._log(f"툴 호출: {block.name}")
                        result = self.handle_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, ensure_ascii=False),
                            }
                        )
                self.conversation.append({"role": "user", "content": tool_results})
                continue

            break

        return "[에이전트 오류] 응답을 처리할 수 없습니다."

    # ------------------------------------------------------------------ #
    # 대화 관리                                                             #
    # ------------------------------------------------------------------ #

    def reset(self) -> None:
        self.conversation = []

    def history_summary(self) -> str:
        turns = len([m for m in self.conversation if m["role"] == "user"])
        return f"{self.name}: {turns}턴"

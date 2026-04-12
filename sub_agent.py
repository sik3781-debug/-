"""
SubAgent: 단일 목적 경량 에이전트
- 복잡한 메인 에이전트를 거치지 않고 단순 서브태스크 처리
- 라우터 / 요약기 / 질의분류기 등으로 활용
"""

from __future__ import annotations

import os
from typing import Any

import anthropic

MODEL = "claude-haiku-4-5-20251001"   # 빠른 서브태스크용 경량 모델
MAX_TOKENS = 1024


def run_sub_agent(
    task: str,
    context: str = "",
    system: str = "당신은 유능한 보조 에이전트입니다. 간결하게 답변하십시오.",
) -> str:
    """단일 호출로 서브태스크를 처리하고 결과 텍스트를 반환한다."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_content = f"{context}\n\n{task}".strip() if context else task

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return response.content[0].text


# ────────────────────────────────────────────────────────────────────────────
# 특화 서브에이전트 함수들
# ────────────────────────────────────────────────────────────────────────────

def classify_query(query: str) -> str:
    """컨설팅 질의를 전문 분야로 분류한다.
    반환값: 'tax' | 'stock' | 'succession' | 'finance' | 'general'
    """
    system = (
        "사용자의 컨설팅 질의를 아래 카테고리 중 하나로만 분류하십시오.\n"
        "카테고리: tax(법인세/절세), stock(비상장주식), succession(가업승계), "
        "finance(재무구조), general(기타)\n"
        "반드시 카테고리 키워드 하나만 출력하십시오. 설명 불필요."
    )
    result = run_sub_agent(query, system=system).strip().lower()
    valid = {"tax", "stock", "succession", "finance", "general"}
    return result if result in valid else "general"


def summarize_for_report(text: str, max_chars: int = 500) -> str:
    """긴 컨설팅 답변을 보고서용 요약문으로 압축한다."""
    system = (
        f"아래 컨설팅 답변을 {max_chars}자 이내의 핵심 요약문으로 작성하십시오. "
        "전문 용어는 유지하되 불필요한 문장은 제거하십시오."
    )
    return run_sub_agent(text, system=system)


def extract_risk_keywords(text: str) -> list[str]:
    """답변에서 주요 세무·법률 리스크 키워드를 추출한다."""
    system = (
        "아래 텍스트에서 세무·법률 리스크 관련 핵심 키워드를 최대 10개 추출하십시오. "
        "쉼표(,)로 구분하여 한 줄로만 출력하십시오."
    )
    raw = run_sub_agent(text, system=system)
    return [kw.strip() for kw in raw.split(",") if kw.strip()]

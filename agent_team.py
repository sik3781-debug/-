"""
AgentTeam: 전문 에이전트 오케스트레이터
- 질의 분류 → 담당 에이전트 라우팅 → 검증 → 결과 반환
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agents.consulting_agents import FinanceAgent, StockAgent, SuccessionAgent, TaxAgent
from agents.verify_agent import VerifyAgent, VerifyResult
from sub_agent import classify_query, summarize_for_report, extract_risk_keywords


@dataclass
class ConsultingResult:
    query: str
    category: str
    agent_name: str
    answer: str
    verify_result: VerifyResult
    summary: str
    risk_keywords: list[str] = field(default_factory=list)

    def display(self) -> None:
        sep = "=" * 70
        thin = "-" * 70
        print(sep)
        print(f"[질의 분류]  {self.category.upper()}  |  담당: {self.agent_name}")
        print(thin)
        print("[컨설팅 답변]")
        print(self.answer)
        print(thin)
        print(self.verify_result.summary())
        print(thin)
        print("[요약]")
        print(self.summary)
        if self.risk_keywords:
            print(f"[리스크 키워드]  {', '.join(self.risk_keywords)}")
        print(sep)


class AgentTeam:
    """전문 에이전트 팀을 관리하고 질의를 라우팅한다."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self._agents = {
            "tax": TaxAgent(verbose=verbose),
            "stock": StockAgent(verbose=verbose),
            "succession": SuccessionAgent(verbose=verbose),
            "finance": FinanceAgent(verbose=verbose),
        }
        self._verifier = VerifyAgent(verbose=verbose)

    # ------------------------------------------------------------------ #
    # 메인 실행                                                             #
    # ------------------------------------------------------------------ #

    def consult(self, query: str) -> ConsultingResult:
        """질의를 처리하고 검증된 컨설팅 결과를 반환한다."""
        # 1단계: 질의 분류
        if self.verbose:
            print(f"\n[AgentTeam] 질의 분류 중…")
        category = classify_query(query)
        agent = self._agents.get(category, self._agents["tax"])

        if self.verbose:
            print(f"[AgentTeam] 분류={category}, 에이전트={agent.name}")

        # 2단계: 전문 에이전트 실행
        answer = agent.run(query, reset=True)

        # 3단계: 검증
        if self.verbose:
            print(f"[AgentTeam] 검증 중…")
        verify_result = self._verifier.verify(query, answer)

        # 4단계: 서브에이전트 요약 & 키워드 추출
        summary = summarize_for_report(answer)
        risk_keywords = extract_risk_keywords(answer)

        return ConsultingResult(
            query=query,
            category=category,
            agent_name=agent.name,
            answer=answer,
            verify_result=verify_result,
            summary=summary,
            risk_keywords=risk_keywords,
        )

    # ------------------------------------------------------------------ #
    # 다중 질의 배치                                                         #
    # ------------------------------------------------------------------ #

    def batch_consult(self, queries: list[str]) -> list[ConsultingResult]:
        """여러 질의를 순차 처리한다."""
        results = []
        for i, q in enumerate(queries, 1):
            print(f"\n{'#'*70}")
            print(f"# 케이스 {i}/{len(queries)}")
            print(f"{'#'*70}")
            result = self.consult(q)
            result.display()
            results.append(result)
        return results

    def team_status(self) -> str:
        lines = ["[AgentTeam 현황]"]
        for cat, agent in self._agents.items():
            lines.append(f"  {cat:12s} → {agent.name} ({agent.history_summary()})")
        lines.append(f"  {'verifier':12s} → {self._verifier.name}")
        return "\n".join(lines)

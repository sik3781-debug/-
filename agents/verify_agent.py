"""
VerifyAgent: 다른 에이전트의 답변을 검증하는 전문 에이전트
- 세법·상법 오류 탐지
- 계산값 재검증
- 누락 리스크 지적
- 신뢰도 점수 산출 (0~100)
"""

from __future__ import annotations

import re
from typing import Any

from agents.base_agent import BaseAgent

_VERIFY_SYSTEM = (
    "당신은 세법·상법·판례에 정통한 검증 전문가입니다.\n"
    "주어진 컨설팅 답변을 아래 기준으로 엄격히 검토하십시오.\n\n"
    "【검증 항목】\n"
    "1. 적용 법령 정확성 (조문 번호, 시행령·시행규칙 포함)\n"
    "2. 계산식 및 수치 정확성 (산출 근거 명시)\n"
    "3. 리스크 누락 여부 (과세 리스크, 사후관리 요건 등)\n"
    "4. 최신 개정 세법 반영 여부\n"
    "5. 판례·예규 정합성\n\n"
    "【출력 형식】\n"
    "반드시 아래 구조로 출력하십시오:\n"
    "SCORE: (0~100 정수)\n"
    "STATUS: (PASS / WARNING / FAIL)\n"
    "ISSUES:\n"
    "- (발견된 문제점 목록, 없으면 '이슈 없음')\n"
    "RECOMMENDATION:\n"
    "(보완 권고 사항)"
    "\n\n【목표】\n모든 컨설팅 에이전트 출력의 법령 조문·계산 수치·리스크 누락을 엄격히 검증하여 SCORE(0~100)·STATUS·ISSUES를 출력한다. SCORE 90 미만 시 구체적 수정 사항을 명시하며, 2026년 귀속 최신 세법 반영 여부를 반드시 확인한다. 검증 목표: 오류 0건·SCORE 95+ 품질의 산출물 보증."
)


class VerifyAgent(BaseAgent):
    name = "VerifyAgent"
    role = "법령·계산 검증 전문가"
    system_prompt = _VERIFY_SYSTEM

    def verify(self, original_query: str, agent_response: str) -> "VerifyResult":
        """에이전트 응답을 검증하고 VerifyResult를 반환한다."""
        prompt = (
            f"【원본 질의】\n{original_query}\n\n"
            f"【검증 대상 답변】\n{agent_response}\n\n"
            "위 답변을 검증 기준에 따라 분석하십시오."
        )
        raw = self.run(prompt, reset=True)
        return VerifyResult.parse(raw)


# ────────────────────────────────────────────────────────────────────────────
# 검증 결과 데이터클래스
# ────────────────────────────────────────────────────────────────────────────
class VerifyResult:
    def __init__(
        self,
        score: int,
        status: str,
        issues: list[str],
        recommendation: str,
        raw: str,
    ) -> None:
        self.score = score
        self.status = status  # PASS / WARNING / FAIL
        self.issues = issues
        self.recommendation = recommendation
        self.raw = raw

    @classmethod
    def parse(cls, text: str) -> "VerifyResult":
        score = 50
        status = "WARNING"
        issues: list[str] = []
        recommendation = ""

        score_m = re.search(r"SCORE:\s*(\d+)", text)
        if score_m:
            score = int(score_m.group(1))

        status_m = re.search(r"STATUS:\s*(PASS|WARNING|FAIL)", text)
        if status_m:
            status = status_m.group(1)

        issues_m = re.search(r"ISSUES:\s*\n(.*?)(?=RECOMMENDATION:|$)", text, re.DOTALL)
        if issues_m:
            raw_issues = issues_m.group(1).strip()
            issues = [
                line.lstrip("- ").strip()
                for line in raw_issues.splitlines()
                if line.strip() and line.strip() != "이슈 없음"
            ]

        rec_m = re.search(r"RECOMMENDATION:\s*\n?(.*)", text, re.DOTALL)
        if rec_m:
            recommendation = rec_m.group(1).strip()

        return cls(score, status, issues, recommendation, text)

    def summary(self) -> str:
        icon = {"PASS": "[OK]", "WARNING": "[!!]", "FAIL": "[NG]"}.get(self.status, "[?]")
        lines = [
            f"[검증 결과] {icon} {self.status}  |  신뢰도 점수: {self.score}/100",
        ]
        if self.issues:
            lines.append("발견 이슈:")
            for iss in self.issues:
                lines.append(f"  - {iss}")
        if self.recommendation:
            lines.append(f"권고: {self.recommendation}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"VerifyResult(score={self.score}, status={self.status})"

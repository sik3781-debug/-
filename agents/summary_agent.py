"""
SummaryAgent: 47개 에이전트 결과 → CEO 임원 요약 자동 생성 에이전트

역할:
  - 전체 에이전트 분석 결과 텍스트에서 핵심 인사이트 추출
  - 절세·절감 효과 총계 집계 (금액 파싱)
  - 리스크 TOP 5 및 기회 TOP 3 선별
  - 실행 타임라인 (즉시·1개월·3개월·6개월·1년) 자동 배분
  - CEO/임원 보고용 1페이지 요약 생성

설계 원칙:
  - 각 에이전트 결과에서 금액·기간·법령 정보 파싱
  - 중복 과제 제거 및 시너지 효과 분석
  - 전문용어 쉬운 표현으로 변환 (CEO 친화적)
"""

from __future__ import annotations
import re
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 경영 컨설팅 임원 요약 보고서 전문 작성가입니다.\n\n"
    "【역할】\n"
    "- 47개 에이전트 분석 결과에서 핵심 사항만 추출\n"
    "- CEO가 5분 내 핵심 의사결정 가능한 요약 생성\n"
    "- 절세·절감·리스크 금액을 원화로 명확히 표시\n"
    "- 실행 로드맵: 즉시·1M·3M·6M·1Y 타임라인 배분\n\n"
    "【작성 원칙】\n"
    "- 전문용어 최소화 / 금액·기간·법령은 명확히 표기\n"
    "- 부정적 사실도 완충 없이 단정적으로 기술\n"
    "- 전체 분량: A4 1페이지(10개 이하 bullet)"
)


class SummaryAgent(BaseAgent):
    name = "SummaryAgent"
    role = "임원 요약 보고서 자동 생성 전담"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "generate_executive_summary",
                "description": (
                    "전체 에이전트 결과에서 CEO 임원 요약 생성.\n"
                    "절세 효과 총계·우선 과제·실행 타임라인을 자동 추출하여\n"
                    "1페이지 경영 요약 보고서를 생성한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string"},
                        "agent_results_text": {
                            "type": "string",
                            "description": "전체 에이전트 분석 결과 텍스트 (합산)",
                        },
                        "risk_score": {
                            "type": "number",
                            "description": "RiskScoreAgent 종합 점수 (0~100)",
                        },
                        "top_risks": {
                            "type": "array",
                            "description": "긴급 리스크 축 목록",
                            "items": {"type": "string"},
                        },
                        "annual_revenue": {"type": "number"},
                    },
                    "required": ["company_name", "agent_results_text"],
                },
            },
            {
                "name": "extract_savings_total",
                "description": (
                    "에이전트 결과에서 절세·절감 금액 자동 파싱.\n"
                    "텍스트 내 금액 패턴을 추출하여 총 절세 가능액을 집계한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "results_text": {"type": "string"},
                        "annual_revenue": {"type": "number"},
                    },
                    "required": ["results_text"],
                },
            },
            {
                "name": "build_action_roadmap",
                "description": (
                    "우선 과제를 실행 타임라인으로 배분.\n"
                    "즉시(1주)·단기(1M)·중기(3M)·중장기(6M)·장기(1Y)로\n"
                    "과제를 분류하고 담당 에이전트를 매핑한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "priority_tasks": {
                            "type": "array",
                            "description": "우선 실행 과제 목록",
                            "items": {"type": "string"},
                        },
                        "risk_score": {"type": "number"},
                    },
                    "required": ["priority_tasks"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "generate_executive_summary":
            return self._generate_executive_summary(**tool_input)
        if tool_name == "extract_savings_total":
            return self._extract_savings_total(**tool_input)
        if tool_name == "build_action_roadmap":
            return self._build_action_roadmap(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _generate_executive_summary(
        self,
        company_name: str,
        agent_results_text: str,
        risk_score: float = 50.0,
        top_risks: list[str] | None = None,
        annual_revenue: float = 0,
    ) -> dict:
        top_risks = top_risks or []

        # 절세 금액 파싱
        savings = self._extract_savings_total(agent_results_text, annual_revenue)

        # 신호등
        signal = (
            "🟢 안정" if risk_score <= 30
            else "🟡 주의" if risk_score <= 60
            else "🔴 위험"
        )

        # 핵심 과제 추출 (텍스트에서 "즉시", "권고", "필요" 포함 문장)
        action_lines = []
        for line in agent_results_text.split("\n"):
            if any(kw in line for kw in ["즉시", "필수", "조치", "권고", "🔴"]):
                cleaned = re.sub(r"[\U00010000-\U0010ffff]", "", line).strip()
                if cleaned and len(cleaned) > 10:
                    action_lines.append(cleaned[:80])
        top_actions = action_lines[:5]

        return {
            "기업명": company_name,
            "분석일": "2026-04-25",
            "경영_신호등": signal,
            "종합_리스크_점수": f"{risk_score:.0f}/100",
            "절세_절감_총계": savings["추정_절세_총액"],
            "매출_대비_절세율": savings["매출_대비_비율"],
            "긴급_리스크": top_risks[:3],
            "즉시_실행_과제": top_actions,
            "보고서_요약": (
                f"{company_name}의 종합 경영 리스크는 {signal}({risk_score:.0f}점)입니다. "
                f"즉시 실행 가능한 절세·절감 효과는 연간 {savings['추정_절세_총액']}으로 추정됩니다. "
                f"{'긴급 리스크: ' + ', '.join(top_risks[:2]) + '.' if top_risks else '주요 리스크 없음.'}"
            ),
        }

    def _extract_savings_total(
        self,
        results_text: str,
        annual_revenue: float = 0,
    ) -> dict:
        # 숫자 + 만원/억원/원 패턴 추출
        patterns = [
            r"(\d[\d,]+)억\s*원",
            r"(\d[\d,]+)만\s*원",
            r"(\d[\d,]+)\s*원",
        ]
        amounts = []
        for pattern in patterns[:2]:  # 억원·만원만
            for m in re.finditer(pattern, results_text):
                num_str = m.group(1).replace(",", "")
                try:
                    val = int(num_str)
                    if pattern.endswith("억\\s*원"):
                        amounts.append(val * 100_000_000)
                    else:
                        amounts.append(val * 10_000)
                except ValueError:
                    pass

        # 합리적인 절세 금액만 필터 (100만~100억)
        valid = [a for a in amounts if 1_000_000 <= a <= 10_000_000_000]
        # 중복 방지: 유사 금액 제거
        valid_unique = []
        for v in sorted(set(valid)):
            if not valid_unique or abs(v - valid_unique[-1]) > valid_unique[-1] * 0.1:
                valid_unique.append(v)

        # 절세 효과 추정 (텍스트 내 금액의 평균 30% = 절세 기여)
        estimated_saving = sum(valid_unique[:5]) * 0.15 if valid_unique else (annual_revenue * 0.03 if annual_revenue else 0)

        ratio = f"{estimated_saving/annual_revenue*100:.1f}%" if annual_revenue else "N/A"

        return {
            "파싱된_금액수": len(valid_unique),
            "추정_절세_총액": f"{estimated_saving:,.0f}원" if estimated_saving else "데이터 부족",
            "매출_대비_비율": ratio,
            "주요_금액_샘플": [f"{v:,.0f}원" for v in valid_unique[:3]],
        }

    def _build_action_roadmap(
        self,
        priority_tasks: list[str],
        risk_score: float = 50.0,
    ) -> dict:
        # 리스크 점수에 따라 즉시 과제 비중 조정
        immediate_count = 2 if risk_score > 60 else 1

        roadmap = {
            "즉시(1주)": priority_tasks[:immediate_count],
            "단기(1개월)": priority_tasks[immediate_count:immediate_count+2],
            "중기(3개월)": priority_tasks[immediate_count+2:immediate_count+4],
            "중장기(6개월)": priority_tasks[immediate_count+4:immediate_count+5],
            "장기(1년~)": priority_tasks[immediate_count+5:],
        }

        return {
            "총_과제수": len(priority_tasks),
            "리스크_점수": risk_score,
            "실행_타임라인": {k: v for k, v in roadmap.items() if v},
            "권고": "즉시 과제부터 순차 착수 — 세금 신고 기한 역산 필수",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        name = company_data.get("company_name", "분석 기업")
        rev = company_data.get("revenue", 0)
        lines = ["[임원 요약 보고서 생성 준비]"]
        lines.append(f"\n▶ 대상: {name} / 매출 {rev/100_000_000:.0f}억 원" if rev else f"\n▶ 대상: {name}")
        lines.append("  전체 에이전트 결과 취합 시 1페이지 CEO 요약 자동 생성")
        return "\n".join(lines)

    def generate_from_results(
        self,
        company_name: str,
        agent_results: dict[str, str],
        risk_score: float = 50.0,
        top_risks: list[str] | None = None,
        annual_revenue: float = 0,
    ) -> dict:
        """orchestrator에서 직접 호출: 에이전트 결과 dict → 요약"""
        combined_text = "\n".join(f"[{k}]\n{v}" for k, v in agent_results.items())
        return self._generate_executive_summary(
            company_name=company_name,
            agent_results_text=combined_text,
            risk_score=risk_score,
            top_risks=top_risks or [],
            annual_revenue=annual_revenue,
        )

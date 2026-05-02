"""
CreditRatingAgent: 신용등급 추정·등급 상승 전략 전문 에이전트
"""
from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 기업 신용등급 분석 및 금융비용 절감 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- NICE평가정보·KIS 신용등급 추정 모형\n"
    "- 재무지표 개선에 따른 등급 상승 전략\n"
    "- 신용등급별 대출금리 스프레드 분석\n"
    "- 금리 절감 효과 계산\n"
    "- 기업어음(CP)·회사채 발행 가능성 검토\n"
    "- 금융기관 여신 한도 확대 전략\n\n"
    "NICE 기준 신용등급 모형(AAA~D)으로 분석하십시오."
    "\n\n【목표】\nNICE 기준 신용등급을 추정하고 등급 상승 시 금융비용 절감액·여신 한도 확대 효과를 정량화한다. 4자 이해관계 중 금융기관 관점을 중심으로 대출가용성 극대화 전략을 단정적으로 권고하며, 신용등급 개선을 위한 재무지표 목표치와 달성 기한을 명시한다."
)


class CreditRatingAgent(BaseAgent):
    name = "CreditRatingAgent"
    role = "신용등급 분석·금융비용 절감 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "estimate_credit_rating",
                "description": "재무지표 기반으로 NICE 기준 신용등급을 추정합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "debt_ratio": {"type": "number", "description": "부채비율 (%)"},
                        "current_ratio": {"type": "number", "description": "유동비율 (%)"},
                        "operating_margin": {"type": "number", "description": "영업이익률 (%)"},
                        "interest_coverage": {"type": "number", "description": "이자보상배율 (배)"},
                        "roe": {"type": "number", "description": "ROE (%)"},
                        "years_in_operation": {"type": "integer", "description": "업력 (년)"},
                    },
                    "required": ["debt_ratio", "current_ratio", "operating_margin", "interest_coverage"],
                },
            },
            {
                "name": "calc_rate_saving",
                "description": "신용등급 상승 시 금리 절감 효과를 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "total_borrowing": {"type": "number", "description": "총 차입금 (원)"},
                        "current_rate": {"type": "number", "description": "현재 평균 대출금리 (%)"},
                        "target_rate": {"type": "number", "description": "목표 등급 대출금리 (%)"},
                    },
                    "required": ["total_borrowing", "current_rate", "target_rate"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "estimate_credit_rating":
            return self._estimate_rating(**tool_input)
        if tool_name == "calc_rate_saving":
            return self._calc_saving(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _estimate_rating(debt_ratio: float, current_ratio: float,
                         operating_margin: float, interest_coverage: float,
                         roe: float = 10.0, years_in_operation: int = 10) -> dict:
        # 단순화된 점수 모형 (100점 만점)
        score = 0

        # 부채비율 (낮을수록 좋음) - 30점
        if debt_ratio <= 100: score += 30
        elif debt_ratio <= 200: score += 20
        elif debt_ratio <= 300: score += 12
        elif debt_ratio <= 400: score += 6
        else: score += 0

        # 유동비율 (높을수록 좋음) - 20점
        if current_ratio >= 200: score += 20
        elif current_ratio >= 150: score += 15
        elif current_ratio >= 100: score += 8
        elif current_ratio >= 80: score += 4
        else: score += 0

        # 영업이익률 - 25점
        if operating_margin >= 10: score += 25
        elif operating_margin >= 5: score += 18
        elif operating_margin >= 2: score += 10
        elif operating_margin >= 0: score += 4
        else: score += 0

        # 이자보상배율 - 20점
        if interest_coverage >= 5: score += 20
        elif interest_coverage >= 3: score += 14
        elif interest_coverage >= 1.5: score += 8
        elif interest_coverage >= 1: score += 3
        else: score += 0

        # 업력 가산 - 5점
        if years_in_operation >= 10: score += 5
        elif years_in_operation >= 5: score += 3

        # 등급 매핑
        if score >= 85: grade, spread = "AA", 1.5
        elif score >= 75: grade, spread = "A", 2.0
        elif score >= 65: grade, spread = "BBB", 2.8
        elif score >= 50: grade, spread = "BB", 3.8
        elif score >= 35: grade, spread = "B", 5.0
        else: grade, spread = "CCC 이하", 7.0

        base_rate = 3.5  # 2024년 기준금리 기반 기준금리
        estimated_rate = base_rate + spread

        # 개선 방향
        improvements = []
        if debt_ratio > 200:
            improvements.append(f"부채비율 {debt_ratio:.0f}% → 200% 이하 목표: 유상증자 또는 이익유보 강화")
        if current_ratio < 150:
            improvements.append(f"유동비율 {current_ratio:.0f}% → 150% 이상 목표: 단기차입 장기 전환")
        if interest_coverage < 3:
            improvements.append(f"이자보상배율 {interest_coverage:.1f}배 → 3배 이상 목표: 영업이익 개선 또는 차입 축소")

        return {
            "신용점수": f"{score}/100",
            "추정 신용등급": grade,
            "예상 대출금리": f"연 {estimated_rate:.2f}% (기준금리 {base_rate}% + 스프레드 {spread}%p)",
            "등급 상승 핵심 과제": improvements if improvements else ["현재 재무구조 유지"],
        }

    @staticmethod
    def _calc_saving(total_borrowing: float, current_rate: float, target_rate: float) -> dict:
        annual_saving = total_borrowing * (current_rate - target_rate) / 100
        after_tax_saving = annual_saving * (1 - 0.22)  # 법인세 22% 차감
        return {
            "총 차입금": f"{total_borrowing:,.0f}원",
            "현재 금리": f"{current_rate:.2f}%",
            "목표 금리": f"{target_rate:.2f}%",
            "금리 차이": f"{current_rate - target_rate:.2f}%p",
            "연간 이자 절감액": f"{annual_saving:,.0f}원",
            "세후 절감액": f"{after_tax_saving:,.0f}원",
            "5년 누적 절감": f"{annual_saving * 5:,.0f}원",
        }

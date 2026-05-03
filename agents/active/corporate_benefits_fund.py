"""사내근로복지기금 설계 에이전트 (근로복지기본법 §50~75)"""
from __future__ import annotations
import re


class CorporateBenefitsFundAgent:
    """출연 시나리오 3종 + 과세관청 부인 위험 + 운영 설계"""

    # 법인세법 §24: 지정기부금 한도 = 소득의 10%
    DEDUCTION_LIMIT_PCT = 0.10

    def analyze(self, company_data: dict) -> dict:
        net_income = company_data.get("net_income", 0)
        taxable    = company_data.get("taxable_income", 0)

        # 손금 한도
        deduction_limit = taxable * self.DEDUCTION_LIMIT_PCT

        scenarios = [
            {"name": "보수적",   "contribution": min(net_income * 0.02, deduction_limit), "note": "순이익 2%, 손금 인정"},
            {"name": "표준",     "contribution": min(net_income * 0.05, deduction_limit), "note": "순이익 5%, 손금 최적"},
            {"name": "적극적",   "contribution": deduction_limit, "note": "한도 최대 활용"},
        ]

        return {
            "agent": "CorporateBenefitsFundAgent",
            "text": (
                f"법인 측면: 사내근로복지기금 출연은 지정기부금(법§24) 한도 {deduction_limit:,.0f}원 내에서 손금 산입.\n"
                f"주주(오너) 관점: 법인 현금 유출 → 직원 복지 개선으로 인재 유지 효과.\n"
                f"과세관청 관점: 근로복지기본법 §50 설립 요건 준수 필수 (상시근로자 수 등).\n"
                f"금융기관 관점: 부채비율 영향 없음 — 신용등급 중립.\n"
                f"출연 시나리오 3종: {[s['name'] for s in scenarios]}"
            ),
            "scenarios": scenarios,
            "deduction_limit": deduction_limit,
            "require_full_4_perspective": True,
        }

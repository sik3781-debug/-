"""
PolicyFundingAgent: 중진공·기보 정책자금·바우처·인증 전문 에이전트
"""
from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 정책자금·정부지원사업·기업인증 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 중소기업진흥공단(중진공) 정책자금 (시설자금·운전자금·혁신성장)\n"
    "- 기술보증기금(기보)·신용보증기금(신보) 보증 상품\n"
    "- 스마트제조혁신·ESG 경영 바우처\n"
    "- 벤처기업·이노비즈·메인비즈·소재부품전문기업 인증 혜택\n"
    "- 일자리안정자금, 고용유지지원금\n"
    "- 연구개발특구·규제자유특구·창업보육센터 지원\n\n"
    "자격 요건·신청 일정·한도·금리를 구체적으로 제시하십시오."
)


class PolicyFundingAgent(BaseAgent):
    name = "PolicyFundingAgent"
    role = "정책자금·정부지원사업 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "check_policy_eligibility",
                "description": "기업 현황에 따른 정책자금 신청 적격성을 평가합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employees": {"type": "integer", "description": "상시 근로자 수"},
                        "annual_revenue": {"type": "number", "description": "연매출 (원)"},
                        "debt_ratio": {"type": "number", "description": "부채비율 (%)"},
                        "industry": {"type": "string", "description": "업종"},
                        "has_overdue": {"type": "boolean", "description": "금융기관 연체 여부"},
                    },
                    "required": ["employees", "annual_revenue", "debt_ratio"],
                },
            },
            {
                "name": "calc_funding_interest_saving",
                "description": "정책자금 vs 시중은행 금리 차이로 절감 이자를 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "loan_amount": {"type": "number", "description": "대출금액 (원)"},
                        "policy_rate": {"type": "number", "description": "정책자금 금리 (%, 연)"},
                        "market_rate": {"type": "number", "description": "시중은행 금리 (%, 연)"},
                        "loan_years": {"type": "integer", "description": "대출 기간 (년)"},
                    },
                    "required": ["loan_amount", "policy_rate", "market_rate", "loan_years"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "check_policy_eligibility":
            return self._check_eligibility(**tool_input)
        if tool_name == "calc_funding_interest_saving":
            return self._calc_saving(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _check_eligibility(employees: int, annual_revenue: float, debt_ratio: float,
                           industry: str = "제조업", has_overdue: bool = False) -> dict:
        results = []
        warnings = []

        # 중진공 정책자금: 중소기업 기본법상 중소기업
        is_sme = annual_revenue <= 130_000_000_000 and employees <= 300
        if is_sme:
            results.append("중진공 정책자금 신청 가능 (시설자금 최대 60억, 금리 연 2.9~3.5%)")
        else:
            warnings.append("중소기업 기준 초과 — 중진공 대신 중견기업 전용 상품 검토")

        # 부채비율 기준
        if debt_ratio > 500:
            warnings.append(f"부채비율 {debt_ratio:.0f}% — 중진공 심사 불이익 가능 (기준: 500% 이하 권고)")
        elif debt_ratio > 300:
            warnings.append(f"부채비율 {debt_ratio:.0f}% — 추가 담보 또는 보증 요구 가능")
        else:
            results.append(f"부채비율 {debt_ratio:.0f}% — 재무구조 양호, 우대금리 가능")

        # 연체
        if has_overdue:
            warnings.append("금융기관 연체 이력 — 정책자금 신청 불가 (연체 해소 후 6개월 경과 필요)")
        else:
            results.append("연체 없음 — 정책자금 신청 적격")

        # 업종 제외
        excluded = ["유흥", "부동산투기", "소비성서비스"]
        if any(e in industry for e in excluded):
            warnings.append(f"제외 업종 해당 ({industry}) — 정책자금 신청 불가")

        # 인증 추천
        certs = []
        if employees >= 10:
            certs.append("이노비즈(기술혁신형) 인증 — 금리 0.3~0.5% 우대")
        if employees >= 5:
            certs.append("벤처기업 인증 — 법인세 50% 감면 (조특법 제6조), 투자유치 용이")
        certs.append("메인비즈(경영혁신형) 인증 — 신보 우대 보증·정책자금 연계")

        return {
            "신청 가능 상품": results,
            "주의 사항": warnings,
            "추천 인증": certs,
            "즉시 신청 권고": "중진공 온라인(sbiz.or.kr) 또는 관할 지역본부",
        }

    @staticmethod
    def _calc_saving(loan_amount: float, policy_rate: float,
                     market_rate: float, loan_years: int) -> dict:
        annual_saving = loan_amount * (market_rate - policy_rate) / 100
        total_saving = annual_saving * loan_years
        return {
            "대출금액": f"{loan_amount:,.0f}원",
            "정책자금 금리": f"{policy_rate:.2f}%",
            "시중은행 금리": f"{market_rate:.2f}%",
            "금리 차이": f"{market_rate - policy_rate:.2f}%p",
            "연간 이자 절감액": f"{annual_saving:,.0f}원",
            "대출 기간 합계 절감": f"{total_saving:,.0f}원",
        }

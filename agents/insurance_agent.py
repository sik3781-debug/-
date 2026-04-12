"""
InsuranceAgent: CEO 유고·퇴직금 재원 보험·D&O 보험 전문 에이전트
"""
from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 법인 보험 설계 및 세무 처리 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- CEO 유고 리스크 헷지 (키맨보험·사망보험)\n"
    "- 임원 퇴직금 재원 보험 구조 (저축성보험 법인 납입)\n"
    "- D&O 보험 (임원 배상책임보험)\n"
    "- 법인 납입 보험료 손금산입 요건 (법인세법 기본통칙 19-19-4)\n"
    "- 단체보험·단체퇴직보험 4대보험 절감\n"
    "- 보험금 수령 시 세무 처리\n\n"
    "법인세법·소득세법 기준 손금 인정 요건을 반드시 명시하십시오."
)


class InsuranceAgent(BaseAgent):
    name = "InsuranceAgent"
    role = "법인 보험 설계·세무 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_insurance_deductibility",
                "description": "법인 납입 보험료 손금산입 가능 여부 및 절세 효과를 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "insurance_type": {"type": "string",
                                          "description": "보험 유형 (순수보장형/만기환급형/저축성)"},
                        "annual_premium": {"type": "number", "description": "연간 보험료 (원)"},
                        "beneficiary": {"type": "string",
                                       "description": "수익자 (법인/임원/유족)"},
                        "is_ceo": {"type": "boolean", "description": "피보험자가 대표이사 여부"},
                    },
                    "required": ["insurance_type", "annual_premium", "beneficiary"],
                },
            },
            {
                "name": "design_retirement_insurance",
                "description": "임원 퇴직금 재원 보험 설계안을 제시합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_retirement_fund": {"type": "number",
                                                  "description": "목표 퇴직금 재원 (원)"},
                        "years_to_retirement": {"type": "integer",
                                               "description": "퇴직까지 잔여 연수"},
                        "annual_deductible_premium": {"type": "number",
                                                     "description": "연간 손금산입 가능 보험료 한도 (원)"},
                    },
                    "required": ["target_retirement_fund", "years_to_retirement"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_insurance_deductibility":
            return self._calc_deductibility(**tool_input)
        if tool_name == "design_retirement_insurance":
            return self._design_retirement(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _calc_deductibility(insurance_type: str, annual_premium: float,
                            beneficiary: str, is_ceo: bool = True) -> dict:
        # 법인세법 기본통칙 19-19-4 기준
        if "순수보장" in insurance_type:
            if beneficiary == "법인":
                deductible = annual_premium
                deductible_ratio = "100%"
                note = "법인이 수익자인 순수보장형 — 전액 손금 (보험금 수령 시 익금 산입)"
            else:
                deductible = annual_premium
                deductible_ratio = "100%"
                note = "임원·유족 수익자 순수보장형 — 전액 손금 (단, 급여로 처리 = 근로소득 과세)"
        elif "만기환급" in insurance_type or "저축" in insurance_type:
            deductible = 0
            deductible_ratio = "0%"
            note = "만기환급형·저축성 보험 — 손금 불산입 (자산 계상), 해약 환급금 수령 시 익금"
        else:
            deductible = annual_premium * 0.5
            deductible_ratio = "50%"
            note = "혼합형 추정 — 보장성 부분만 손금 (정확한 분류 필요)"

        tax_saving = deductible * 0.22  # 법인세 22%
        return {
            "보험 유형": insurance_type,
            "연간 보험료": f"{annual_premium:,.0f}원",
            "손금산입 가능": deductible_ratio,
            "손금산입액": f"{deductible:,.0f}원",
            "절세 효과(법인세 22%)": f"{tax_saving:,.0f}원/년",
            "세무 처리 주의": note,
        }

    @staticmethod
    def _design_retirement(target_retirement_fund: float, years_to_retirement: int,
                           annual_deductible_premium: float = 0) -> dict:
        # 단순 복리 계산 (가정: 연 3% 적립이율)
        rate = 0.03
        required_annual = target_retirement_fund / (
            ((1 + rate) ** years_to_retirement - 1) / rate * (1 + rate)
        )

        if annual_deductible_premium > 0:
            deductible_coverage = min(required_annual, annual_deductible_premium)
            non_deductible = max(0, required_annual - annual_deductible_premium)
        else:
            deductible_coverage = required_annual
            non_deductible = 0

        tax_benefit = deductible_coverage * years_to_retirement * 0.22

        return {
            "목표 퇴직금 재원": f"{target_retirement_fund:,.0f}원",
            "잔여 기간": f"{years_to_retirement}년",
            "필요 연간 납입액": f"{required_annual:,.0f}원",
            "손금산입 납입": f"{deductible_coverage:,.0f}원/년",
            "손금 초과(비용 처리 불가)": f"{non_deductible:,.0f}원/년",
            "기간 합계 절세액": f"{tax_benefit:,.0f}원",
            "추천 구조": "순수보장형 정기보험(법인 수익자) + DC형 퇴직연금 병행",
        }

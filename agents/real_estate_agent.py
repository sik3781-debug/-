"""
RealEstateAgent: 법인 vs 개인 부동산·공장 매각 전문 에이전트
"""
from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 법인·개인 부동산 세무 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 법인 vs 개인 부동산 취득·보유·양도세 비교\n"
    "- 공장 매각 최적화 (매각가·타이밍·절세 구조)\n"
    "- 부동산 임대차 리스크 (상가건물임대차보호법)\n"
    "- 취득세·재산세·종합부동산세 계산\n"
    "- 양도소득세 vs 법인세 비교\n"
    "- 부동산 과다법인 주식 평가 할증 리스크\n\n"
    "법령: 지방세법, 소득세법, 법인세법, 부동산 거래신고법"
    "\n\n【목표】\n법인 vs 개인 취득·보유·양도 세금 비교 시뮬레이션으로 부동산 거래 최적 구조를 결정한다. 비상장주식 평가 시 부동산 과다법인 할증 리스크(부동산 80%↑ → 순자산가치 100% 적용)를 수치로 경고하고 해소 방안을 제시한다. 지방세법·소득세법·법인세법 교차 적용으로 최소 세부담 구조를 단정적으로 권고한다."
)


class RealEstateAgent(BaseAgent):
    name = "RealEstateAgent"
    role = "법인·개인 부동산 세무 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "compare_acquisition",
                "description": "법인·개인 부동산 취득 시 세금 부담을 비교합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "acquisition_price": {"type": "number", "description": "취득가액 (원)"},
                        "property_type": {"type": "string", "description": "부동산 유형 (공장/사무실/주택/토지)"},
                        "is_corporation": {"type": "boolean", "description": "법인 취득 여부"},
                        "annual_rental_income": {"type": "number", "description": "연간 임대수익 (원, 없으면 0)"},
                    },
                    "required": ["acquisition_price", "property_type"],
                },
            },
            {
                "name": "calc_transfer_tax",
                "description": "부동산 양도 시 법인·개인 세금을 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "acquisition_price": {"type": "number", "description": "취득가액 (원)"},
                        "transfer_price": {"type": "number", "description": "양도가액 (원)"},
                        "holding_years": {"type": "number", "description": "보유 기간 (년)"},
                        "is_corporation": {"type": "boolean", "description": "법인 보유 여부"},
                        "is_factory": {"type": "boolean", "description": "공장(사업용 자산) 여부"},
                    },
                    "required": ["acquisition_price", "transfer_price", "holding_years"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "compare_acquisition":
            return self._compare(**tool_input)
        if tool_name == "calc_transfer_tax":
            return self._calc_transfer(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _compare(acquisition_price: float, property_type: str,
                 is_corporation: bool = True, annual_rental_income: float = 0) -> dict:
        # 취득세율 (2024년)
        corp_rate = 0.04 if "공장" in property_type or "사무" in property_type else 0.04
        ind_rate = 0.01 if "주택" in property_type else 0.04

        corp_tax = acquisition_price * corp_rate
        ind_tax = acquisition_price * ind_rate

        # 보유세 (재산세 기준 단순화)
        annual_property_tax = acquisition_price * 0.002  # 0.2% 단순 가정

        result = {
            "취득 방법": "법인" if is_corporation else "개인",
            "법인 취득세": f"{corp_tax:,.0f}원 ({corp_rate*100:.1f}%)",
            "개인 취득세": f"{ind_tax:,.0f}원 ({ind_rate*100:.1f}%)",
            "연간 재산세(추정)": f"{annual_property_tax:,.0f}원",
        }

        if annual_rental_income > 0:
            # 법인: 임대수익 법인세(19%), 개인: 종합소득세(최대 45%)
            corp_income_tax = annual_rental_income * 0.19
            ind_income_tax = annual_rental_income * 0.38  # 중간 세율 가정
            result["임대수익 세금(법인)"] = f"{corp_income_tax:,.0f}원/년 (19% 적용)"
            result["임대수익 세금(개인)"] = f"{ind_income_tax:,.0f}원/년 (38% 가정)"
            result["법인 보유 유리 여부"] = "법인 유리" if corp_income_tax < ind_income_tax else "개인 검토"

        result["권고"] = (
            "공장(사업용 자산): 법인 취득이 세무·회계상 유리. "
            "단, 부동산 과다법인 판정(총자산 50% 이상) 시 비상장주식 평가 할증 주의"
        )
        return result

    @staticmethod
    def _calc_transfer(acquisition_price: float, transfer_price: float,
                       holding_years: float, is_corporation: bool = True,
                       is_factory: bool = True) -> dict:
        gain = transfer_price - acquisition_price

        if is_corporation:
            # 법인: 양도차익이 법인 과세표준에 합산 → 법인세(19%) + 법인세 추가세(10%)
            corp_tax = gain * 0.19
            local_tax = corp_tax * 0.1
            total_corp = corp_tax + local_tax
            result = {
                "양도차익": f"{gain:,.0f}원",
                "법인세(19%)": f"{corp_tax:,.0f}원",
                "지방소득세(10%)": f"{local_tax:,.0f}원",
                "법인 총 세금": f"{total_corp:,.0f}원",
                "실효세율": f"{total_corp/gain*100:.1f}%" if gain > 0 else "N/A",
            }
        else:
            # 개인: 양도소득세 (장기보유특별공제 적용)
            if is_factory and holding_years >= 3:
                ltcg_rate = min(0.30, holding_years * 0.02)  # 연 2%, 최대 30%
            else:
                ltcg_rate = 0.0
            taxable_gain = gain * (1 - ltcg_rate)
            # 누진세율 단순 적용
            if taxable_gain <= 12_000_000: rate = 0.06
            elif taxable_gain <= 46_000_000: rate = 0.15
            elif taxable_gain <= 88_000_000: rate = 0.24
            elif taxable_gain <= 150_000_000: rate = 0.35
            elif taxable_gain <= 300_000_000: rate = 0.38
            elif taxable_gain <= 500_000_000: rate = 0.40
            else: rate = 0.45
            ind_tax = taxable_gain * rate
            local_tax = ind_tax * 0.1
            total_ind = ind_tax + local_tax
            result = {
                "양도차익": f"{gain:,.0f}원",
                "장기보유특별공제": f"{ltcg_rate*100:.0f}% (보유 {holding_years:.0f}년)",
                "과세표준": f"{taxable_gain:,.0f}원",
                "양도소득세": f"{ind_tax:,.0f}원",
                "지방소득세": f"{local_tax:,.0f}원",
                "개인 총 세금": f"{total_ind:,.0f}원",
                "실효세율": f"{total_ind/gain*100:.1f}%" if gain > 0 else "N/A",
            }

        return result

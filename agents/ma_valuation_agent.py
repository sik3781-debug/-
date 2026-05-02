"""
MAValuationAgent: DCF·PER·EV/EBITDA 기업가치 산출 전문 에이전트
"""
from __future__ import annotations
import math
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 기업가치평가(Valuation) 및 M&A 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- DCF(현금흐름할인) 기업가치 산출\n"
    "- PER(주가수익비율) 비교평가\n"
    "- EV/EBITDA 배수 평가\n"
    "- 외부 매각·투자유치·IPO 기초 검토\n"
    "- 경영권 프리미엄, 소수주주 할인율\n"
    "- 주식매수청구권·풋옵션 설계\n\n"
    "세 가지 방법론(DCF·PER·EV/EBITDA) 병행으로 가치 범위를 산출하십시오."
    "\n\n【목표】\nDCF·PER·EV/EBITDA 3방법론을 병행 적용하여 기업가치 범위를 산출하고, 매각·투자유치·IPO 시 최적 딜 구조와 경영권 프리미엄·소수주주 할인율을 수치 기반으로 제시한다. 법인·주주(오너) 이익 최대화 관점에서 Exit 전략과 주주가치 보전 방안을 권고한다."
)


class MAValuationAgent(BaseAgent):
    name = "MAValuationAgent"
    role = "기업가치평가·M&A 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_dcf_value",
                "description": "DCF 방법으로 기업가치를 산출합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "fcf": {"type": "number", "description": "현재 연간 잉여현금흐름 (원)"},
                        "growth_rate_5y": {"type": "number", "description": "5년간 성장률 (%, 연)"},
                        "terminal_growth": {"type": "number", "description": "영구 성장률 (%, 기본 2.5)"},
                        "wacc": {"type": "number", "description": "가중평균자본비용 (%, 기본 10)"},
                        "net_debt": {"type": "number", "description": "순부채 (원)"},
                    },
                    "required": ["fcf", "growth_rate_5y"],
                },
            },
            {
                "name": "calc_per_value",
                "description": "PER 비교법으로 기업가치를 산출합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "net_income": {"type": "number", "description": "당기순이익 (원)"},
                        "industry_per": {"type": "number", "description": "동종업계 평균 PER (배)"},
                        "discount_rate": {"type": "number", "description": "비상장 할인율 (%, 기본 30)"},
                        "shares_outstanding": {"type": "integer", "description": "발행주식 수"},
                    },
                    "required": ["net_income", "industry_per"],
                },
            },
            {
                "name": "calc_ebitda_value",
                "description": "EV/EBITDA 배수로 기업가치를 산출합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ebitda": {"type": "number", "description": "EBITDA (원)"},
                        "industry_multiple": {"type": "number", "description": "동종업계 EV/EBITDA 배수"},
                        "net_debt": {"type": "number", "description": "순부채 (원)"},
                    },
                    "required": ["ebitda", "industry_multiple"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_dcf_value":
            return self._dcf(**tool_input)
        if tool_name == "calc_per_value":
            return self._per(**tool_input)
        if tool_name == "calc_ebitda_value":
            return self._ebitda(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _dcf(fcf: float, growth_rate_5y: float, terminal_growth: float = 2.5,
             wacc: float = 10.0, net_debt: float = 0) -> dict:
        g = growth_rate_5y / 100
        r = wacc / 100
        tg = terminal_growth / 100

        pv_fcfs = []
        cf = fcf
        total_pv = 0.0
        for yr in range(1, 6):
            cf *= (1 + g)
            pv = cf / (1 + r) ** yr
            pv_fcfs.append(f"{yr}년: FCF {cf:,.0f}원 → PV {pv:,.0f}원")
            total_pv += pv

        # 터미널 가치
        terminal_fcf = cf * (1 + tg)
        terminal_value = terminal_fcf / (r - tg) if r > tg else fcf * 20
        pv_terminal = terminal_value / (1 + r) ** 5

        enterprise_value = total_pv + pv_terminal
        equity_value = enterprise_value - net_debt

        return {
            "DCF 세부 계산": pv_fcfs,
            "5년 FCF PV 합계": f"{total_pv:,.0f}원",
            "터미널 가치 PV": f"{pv_terminal:,.0f}원",
            "기업가치(EV)": f"{enterprise_value:,.0f}원",
            "순부채 차감": f"{net_debt:,.0f}원",
            "주주가치(Equity Value)": f"{equity_value:,.0f}원",
            "WACC": f"{wacc:.1f}%",
        }

    @staticmethod
    def _per(net_income: float, industry_per: float,
             discount_rate: float = 30.0, shares_outstanding: int = 100_000) -> dict:
        market_cap_listed = net_income * industry_per
        discount = discount_rate / 100
        equity_value = market_cap_listed * (1 - discount)
        per_share = equity_value / shares_outstanding if shares_outstanding > 0 else 0
        return {
            "당기순이익": f"{net_income:,.0f}원",
            "업종 평균 PER": f"{industry_per:.1f}배",
            "상장 동종 기준 시가총액": f"{market_cap_listed:,.0f}원",
            "비상장 할인율": f"{discount_rate:.0f}%",
            "적용 주주가치": f"{equity_value:,.0f}원",
            "1주당 가치": f"{per_share:,.0f}원",
        }

    @staticmethod
    def _ebitda(ebitda: float, industry_multiple: float, net_debt: float = 0) -> dict:
        enterprise_value = ebitda * industry_multiple
        equity_value = enterprise_value - net_debt
        return {
            "EBITDA": f"{ebitda:,.0f}원",
            "업종 EV/EBITDA 배수": f"{industry_multiple:.1f}배",
            "기업가치(EV)": f"{enterprise_value:,.0f}원",
            "순부채": f"{net_debt:,.0f}원",
            "주주가치(Equity Value)": f"{equity_value:,.0f}원",
        }

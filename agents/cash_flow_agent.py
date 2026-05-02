"""
CashFlowAgent: 월별 현금흐름 12개월 예측·흑자도산 경보 에이전트
"""
from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 기업 현금흐름 관리 및 유동성 위기 진단 전문가입니다.\n\n"
    "【전문 분야】\n"
    "- 월별 현금흐름 12개월 예측 시뮬레이션\n"
    "- 흑자도산 조기 경보 (Cash Burn Rate, Runway 계산)\n"
    "- 운전자본(Working Capital) 최적화\n"
    "- 매출채권 회전일수·재고 회전일수 개선\n"
    "- 자금조달 Mix 최적화 (단기차입·장기차입·자본)\n"
    "- 기한이익 상실(Cross Default) 조항 리스크\n\n"
    "계산 툴을 활용하여 수치 기반 분석을 제공하십시오."
    "\n\n【목표】\n12개월 월별 현금흐름 예측으로 흑자도산 조기 경보를 발령하고, 운전자본 최적화·자금조달 믹스 조정 방안을 수치 기반으로 제시한다. Cash Burn Rate·Runway 계산으로 유동성 위기 임계점을 단정적으로 경고하며, 4자 이해관계 중 금융기관·법인 관점을 중심으로 즉시 실행 가능한 자금 대책을 권고한다."
)


class CashFlowAgent(BaseAgent):
    name = "CashFlowAgent"
    role = "현금흐름 예측·유동성 관리 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "simulate_cashflow_12m",
                "description": "12개월 월별 현금흐름을 시뮬레이션합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "monthly_revenue": {"type": "number", "description": "월 평균 매출 (원)"},
                        "monthly_cogs_ratio": {"type": "number", "description": "매출원가율 (0~1)"},
                        "monthly_opex": {"type": "number", "description": "월 고정 운영비 (원)"},
                        "monthly_interest": {"type": "number", "description": "월 이자비용 (원)"},
                        "current_cash": {"type": "number", "description": "현재 현금 보유액 (원)"},
                        "large_payment_month": {"type": "integer", "description": "대규모 지출 발생 월 (없으면 0)"},
                        "large_payment_amount": {"type": "number", "description": "대규모 지출 금액 (원)"},
                    },
                    "required": ["monthly_revenue", "monthly_cogs_ratio", "monthly_opex",
                                 "monthly_interest", "current_cash"],
                },
            },
            {
                "name": "calc_working_capital",
                "description": "운전자본 현황 및 개선 여력을 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "receivables": {"type": "number", "description": "매출채권 (원)"},
                        "inventory": {"type": "number", "description": "재고자산 (원)"},
                        "payables": {"type": "number", "description": "매입채무 (원)"},
                        "annual_revenue": {"type": "number", "description": "연매출 (원)"},
                        "annual_cogs": {"type": "number", "description": "연 매출원가 (원)"},
                    },
                    "required": ["receivables", "inventory", "payables", "annual_revenue", "annual_cogs"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "simulate_cashflow_12m":
            return self._simulate_cashflow(**tool_input)
        if tool_name == "calc_working_capital":
            return self._calc_wc(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _simulate_cashflow(
        monthly_revenue: float, monthly_cogs_ratio: float,
        monthly_opex: float, monthly_interest: float,
        current_cash: float,
        large_payment_month: int = 0, large_payment_amount: float = 0
    ) -> dict:
        monthly_cf = monthly_revenue * (1 - monthly_cogs_ratio) - monthly_opex - monthly_interest
        balance = current_cash
        months = []
        warning_months = []
        danger_months = []

        for m in range(1, 13):
            cf = monthly_cf
            if large_payment_month == m:
                cf -= large_payment_amount
            balance += cf
            status = "정상"
            if balance < 0:
                status = "위험-현금부족"
                danger_months.append(m)
            elif balance < monthly_opex * 2:
                status = "경고"
                warning_months.append(m)
            months.append({
                "월": f"{m}월",
                "현금흐름": f"{cf:,.0f}",
                "누적잔액": f"{balance:,.0f}",
                "상태": status,
            })

        runway = current_cash / abs(monthly_cf) if monthly_cf < 0 else 99
        return {
            "월별 현금흐름 (12개월)": months,
            "월 순현금흐름": f"{monthly_cf:,.0f}원",
            "런웨이": f"{runway:.1f}개월" if runway < 99 else "흑자 구조 (위기 없음)",
            "위험 월": danger_months if danger_months else "없음",
            "경고 월": warning_months if warning_months else "없음",
            "12개월 후 잔액": f"{balance:,.0f}원",
        }

    @staticmethod
    def _calc_wc(receivables: float, inventory: float, payables: float,
                 annual_revenue: float, annual_cogs: float) -> dict:
        dso = receivables / (annual_revenue / 365)   # 매출채권 회전일수
        dio = inventory / (annual_cogs / 365)         # 재고 회전일수
        dpo = payables / (annual_cogs / 365)          # 매입채무 지급일수
        ccc = dso + dio - dpo                          # 현금전환주기

        # 업종 평균 CCC 제조업 약 60일
        benchmark_ccc = 60
        improvement_potential = max(0, ccc - benchmark_ccc) * (annual_cogs / 365)

        return {
            "매출채권 회전일수(DSO)": f"{dso:.1f}일",
            "재고 회전일수(DIO)": f"{dio:.1f}일",
            "매입채무 지급일수(DPO)": f"{dpo:.1f}일",
            "현금전환주기(CCC)": f"{ccc:.1f}일",
            "업종 평균 CCC(제조)": f"{benchmark_ccc}일",
            "운전자본 개선 가능액": f"{improvement_potential:,.0f}원",
            "권고": "DSO 단축(선결제 할인), DPO 연장(협상), 재고 최소화로 CCC 개선",
        }

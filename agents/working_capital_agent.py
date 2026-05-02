"""
WorkingCapitalAgent: 운전자본 관리 전담 에이전트

근거 제도:
  - 기업은행·신한·국민 등 외상매출채권담보대출 (네고 팩토링)
  - 중소기업진흥공단 구매론·매출채권보험
  - 신용보증기금 유동화회사보증 (ABS)
  - 부가가치세법 §32 (세금계산서 발행 = 매출채권 성립)

주요 기능:
  - 운전자본 사이클(Cash Conversion Cycle) 계산
  - 매출채권·재고·매입채무 회전일수 분석
  - 운전자본 자금 조달 최적화 (팩토링·매출채권담보대출)
  - 재고 최적화 (EOQ·ABC 분석 방법론)
  - 계절성 매출 기업 월별 운전자본 수요 시뮬레이션
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 운전자본 관리 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- CCC(Cash Conversion Cycle) 분석 및 단축 전략\n"
    "- 매출채권·재고·매입채무 회전일수 최적화\n"
    "- 운전자본 금융: 팩토링·외상매출채권담보대출·구매론 비교\n"
    "- 재고 최적화: EOQ(경제적주문량)·안전재고·ABC 분류\n"
    "- 계절성 사업 월별 현금흐름 계획\n\n"
    "【분석 관점】\n"
    "- 법인: 현금흐름 안정 / 단기 금융비용 최소화\n"
    "- 오너: 흑자도산 방지 / 배당 재원 확보\n"
    "- 금융기관: 매출채권 담보 가치 / 신용한도 활용\n"
    "- 과세관청: 가공 매출채권 여부 / 대손충당금 적정성\n\n"
    "【목표】\n"
    "운전자본 사이클을 최소화하여 현금 창출력을 극대화하고,\n"
    "최저 비용의 운전자본 금융 구조를 설계한다."
)


class WorkingCapitalAgent(BaseAgent):
    name = "WorkingCapitalAgent"
    role = "운전자본 관리 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_ccc",
                "description": (
                    "현금전환주기(CCC) 계산 및 단축 전략.\n"
                    "매출채권회전일수·재고회전일수·매입채무회전일수를\n"
                    "계산하고 개선 시나리오를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "annual_revenue": {"type": "number", "description": "연 매출액 (원)"},
                        "cogs": {"type": "number", "description": "연 매출원가 (원)"},
                        "avg_receivables": {"type": "number", "description": "평균 매출채권 (원)"},
                        "avg_inventory": {"type": "number", "description": "평균 재고자산 (원)"},
                        "avg_payables": {"type": "number", "description": "평균 매입채무 (원)"},
                        "industry": {"type": "string", "description": "업종 (벤치마크용)"},
                    },
                    "required": ["annual_revenue", "cogs", "avg_receivables", "avg_inventory", "avg_payables"],
                },
            },
            {
                "name": "optimize_ar_financing",
                "description": (
                    "매출채권 금융 최적화.\n"
                    "팩토링·외상매출채권담보대출·기업어음 방식별\n"
                    "비용·속도·신용 영향을 비교하여 최적안을 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "receivables_amount": {"type": "number", "description": "매출채권 잔액 (원)"},
                        "avg_collection_days": {"type": "integer", "description": "평균 회수 기간 (일)"},
                        "credit_rating": {"type": "string", "description": "기업 신용등급 (예: BBB)"},
                        "buyer_credit_rating": {"type": "string", "description": "매출처 신용등급 (예: A)"},
                    },
                    "required": ["receivables_amount", "avg_collection_days"],
                },
            },
            {
                "name": "calc_eoq",
                "description": (
                    "경제적주문량(EOQ) 및 안전재고 계산.\n"
                    "연간 수요·주문비용·보관비용을 기반으로\n"
                    "최적 주문량과 재주문점(ROP)을 산출한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "annual_demand": {"type": "number", "description": "연간 수요량 (단위)"},
                        "order_cost": {"type": "number", "description": "1회 주문비용 (원)"},
                        "unit_cost": {"type": "number", "description": "단위당 원가 (원)"},
                        "holding_cost_rate": {
                            "type": "number",
                            "description": "연간 보관비용율 (재고원가 대비, 예: 0.20)",
                        },
                        "lead_time_days": {"type": "integer", "description": "조달 리드타임 (일)"},
                        "safety_stock_days": {
                            "type": "integer",
                            "description": "안전재고 일수 (예: 7)",
                        },
                    },
                    "required": ["annual_demand", "order_cost", "unit_cost", "holding_cost_rate"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_ccc":
            return self._calc_ccc(**tool_input)
        if tool_name == "optimize_ar_financing":
            return self._optimize_ar_financing(**tool_input)
        if tool_name == "calc_eoq":
            return self._calc_eoq(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _calc_ccc(
        self,
        annual_revenue: float,
        cogs: float,
        avg_receivables: float,
        avg_inventory: float,
        avg_payables: float,
        industry: str = "제조업",
    ) -> dict:
        dso = avg_receivables / annual_revenue * 365  # 매출채권회전일수
        dio = avg_inventory / cogs * 365 if cogs else 0  # 재고회전일수
        dpo = avg_payables / cogs * 365 if cogs else 0   # 매입채무회전일수
        ccc = dso + dio - dpo

        # 업종 평균 벤치마크 (단순화)
        bench = {"제조업": 60, "도소매업": 30, "건설업": 90, "서비스업": 20, "기타": 50}
        bench_ccc = bench.get(industry, 50)
        gap = ccc - bench_ccc

        # 개선 시나리오
        target_dso = dso * 0.85
        target_dio = dio * 0.80
        target_dpo = dpo * 1.10
        target_ccc = target_dso + target_dio - target_dpo
        ccc_saving_days = ccc - target_ccc
        ccc_saving_cash = annual_revenue / 365 * ccc_saving_days

        return {
            "매출채권회전일수(DSO)": round(dso, 1),
            "재고회전일수(DIO)": round(dio, 1),
            "매입채무회전일수(DPO)": round(dpo, 1),
            "현금전환주기(CCC)": round(ccc, 1),
            f"업종평균_CCC({industry})": bench_ccc,
            "업종대비_초과(일)": round(gap, 1),
            "개선_목표_CCC": round(target_ccc, 1),
            "개선시_현금_창출": round(ccc_saving_cash),
            "개선_전략": [
                f"DSO {dso:.0f}→{target_dso:.0f}일: 조기 입금 할인(2/10 net 30) 도입",
                f"DIO {dio:.0f}→{target_dio:.0f}일: 재고 ABC 분류 후 C등급 주문 축소",
                f"DPO {dpo:.0f}→{target_dpo:.0f}일: 주요 매입처 결제 조건 연장 협상",
            ],
        }

    def _optimize_ar_financing(
        self,
        receivables_amount: float,
        avg_collection_days: int,
        credit_rating: str = "BBB",
        buyer_credit_rating: str = "A",
    ) -> dict:
        options = []

        # 팩토링 (매출채권 매각)
        factoring_rate = 0.030 if buyer_credit_rating >= "A" else 0.045
        factoring_cost = receivables_amount * factoring_rate * avg_collection_days / 365
        options.append({
            "방식": "팩토링 (매출채권 매각)",
            "비용": round(factoring_cost),
            "연환산금리": f"{factoring_rate*100:.1f}%",
            "장점": "재무제표에서 채권 제거 / 즉시 현금화",
            "단점": "비용 상대적으로 높음",
            "적합": buyer_credit_rating >= "BBB",
        })

        # 외상매출채권담보대출
        loan_rate = 0.040 if credit_rating >= "BBB" else 0.055
        loan_amount = receivables_amount * 0.80  # 80% 담보
        loan_cost = loan_amount * loan_rate * avg_collection_days / 365
        options.append({
            "방식": "외상매출채권담보대출",
            "한도": round(loan_amount),
            "비용": round(loan_cost),
            "연환산금리": f"{loan_rate*100:.1f}%",
            "장점": "채권 유지하며 유동성 확보",
            "단점": "신용한도 소진",
            "적합": credit_rating >= "BB",
        })

        # 구매론 (매입처 활용)
        options.append({
            "방식": "구매론 (매입처 네트워크)",
            "비용": round(receivables_amount * 0.025 * avg_collection_days / 365),
            "연환산금리": "2.5%",
            "장점": "최저 금리 / 매입처 관계 강화",
            "단점": "매입처 참여 필요",
            "적합": True,
        })

        best = min(options, key=lambda x: x["비용"])
        return {
            "매출채권_잔액": round(receivables_amount),
            "평균_회수기간": f"{avg_collection_days}일",
            "방식별_비교": options,
            "추천_방식": best["방식"],
            "추천_이유": f"비용 {best['비용']:,.0f}원으로 최저",
        }

    def _calc_eoq(
        self,
        annual_demand: float,
        order_cost: float,
        unit_cost: float,
        holding_cost_rate: float,
        lead_time_days: int = 7,
        safety_stock_days: int = 7,
    ) -> dict:
        import math
        holding_cost_per_unit = unit_cost * holding_cost_rate
        eoq = math.sqrt(2 * annual_demand * order_cost / holding_cost_per_unit)
        daily_demand = annual_demand / 365
        rop = daily_demand * lead_time_days + daily_demand * safety_stock_days  # 재주문점
        orders_per_year = annual_demand / eoq
        avg_inventory_units = eoq / 2 + daily_demand * safety_stock_days
        avg_inventory_cost = avg_inventory_units * unit_cost

        return {
            "연간_수요": round(annual_demand),
            "경제적_주문량(EOQ)": round(eoq),
            "연간_주문횟수": round(orders_per_year, 1),
            "재주문점(ROP)": round(rop),
            "안전재고": round(daily_demand * safety_stock_days),
            "평균_재고금액": round(avg_inventory_cost),
            "연간_보관비용": round(avg_inventory_cost * holding_cost_rate),
            "연간_주문비용": round(orders_per_year * order_cost),
            "권고": f"EOQ {eoq:.0f}단위씩 연 {orders_per_year:.1f}회 주문 / 재고 {rop:.0f}단위 시 발주",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        rev = company_data.get("revenue", 0)
        cogs = company_data.get("cogs", rev * 0.65)
        ar = company_data.get("avg_receivables", 0)
        inv = company_data.get("avg_inventory", 0)
        ap = company_data.get("avg_payables", 0)
        ind = company_data.get("industry", "제조업")
        lines = ["[운전자본 관리 분석 결과]"]
        if rev and ar:
            ccc = self._calc_ccc(rev, cogs, ar, inv, ap, ind)
            lines.append(f"\n▶ 현금전환주기(CCC): {ccc['현금전환주기(CCC)']}일 (업종평균 {ccc[f'업종평균_CCC({ind})']}일)")
            lines.append(f"  개선 시 현금 창출: {ccc['개선시_현금_창출']:,.0f}원")
        else:
            lines.append("  매출채권·재고 데이터 필요")
        return "\n".join(lines)

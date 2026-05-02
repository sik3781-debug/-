"""
CostAnalysisAgent: 원가분석·관리회계 전담 에이전트

주요 기능:
  - 제품/서비스별 원가 구조 분해 (직접재료비·직접노무비·제조간접비)
  - 손익분기점(BEP) 계산 및 목표이익 달성 매출액 역산
  - 변동원가(Variable Cost) vs. 고정원가(Fixed Cost) 분리
  - 공헌이익률(Contribution Margin Ratio) 분석
  - 원가절감 시뮬레이션 (자재비·인건비·외주비 항목별)
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 원가분석 및 관리회계 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 제품·서비스별 원가 구조 분해 및 원가요소 분류\n"
    "- 손익분기점(BEP: Break-Even Point) 계산 및 안전한계 분석\n"
    "- 변동원가·고정원가 분리를 통한 공헌이익률(CMR) 분석\n"
    "- 목표이익 달성을 위한 매출액·수량 역산\n"
    "- 원가절감 시나리오: 자재비·인건비·외주비·감가상각비별 효과\n"
    "- 표준원가 vs. 실제원가 차이분석 (Price / Efficiency Variance)\n\n"
    "【분석 관점】\n"
    "- 법인: 원가율 최소화 / 손금 항목 최대화 / 재무구조 건전성\n"
    "- 오너: 제품별 수익성 파악 / 수익 집중 전략\n"
    "- 금융기관: 원가경쟁력 / 안전한계율 / 이자보상배율\n"
    "- 과세관청: 원가 귀속 적정성 / 자가소비 여부\n\n"
    "【목표】\n"
    "숫자 한 줄로 '어디서 돈을 벌고 어디서 새는지'를 오너가 즉시 파악하게 한다."
)


class CostAnalysisAgent(BaseAgent):
    name = "CostAnalysisAgent"
    role = "원가분석·관리회계 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_bep",
                "description": (
                    "손익분기점(BEP) 및 목표이익 달성 매출 계산.\n"
                    "고정비·변동비율·현재매출을 입력받아 BEP, 안전한계, 공헌이익률을 반환한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "fixed_cost": {"type": "number", "description": "연간 고정비 합계 (원)"},
                        "variable_cost_ratio": {
                            "type": "number",
                            "description": "변동비율 (매출 대비, 0~1, 예: 0.60)",
                        },
                        "current_revenue": {"type": "number", "description": "현재 연간 매출액 (원)"},
                        "target_profit": {
                            "type": "number",
                            "description": "목표 영업이익 (원, 선택). 미입력 시 BEP만 계산",
                        },
                    },
                    "required": ["fixed_cost", "variable_cost_ratio", "current_revenue"],
                },
            },
            {
                "name": "cost_breakdown",
                "description": "원가 구조 분해. 직접재료비·직접노무비·제조간접비·판관비 비율과 절감 여력을 분석한다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "revenue": {"type": "number", "description": "매출액 (원)"},
                        "direct_material": {"type": "number", "description": "직접재료비 (원)"},
                        "direct_labor": {"type": "number", "description": "직접노무비 (원)"},
                        "mfg_overhead": {"type": "number", "description": "제조간접비 (원)"},
                        "sga": {"type": "number", "description": "판매관리비 (원)"},
                        "industry_cogs_ratio": {
                            "type": "number",
                            "description": "업종 평균 매출원가율 (벤치마크용, 0~1)",
                        },
                    },
                    "required": ["revenue", "direct_material", "direct_labor", "mfg_overhead", "sga"],
                },
            },
            {
                "name": "cost_reduction_sim",
                "description": "원가절감 시나리오 시뮬레이션. 각 원가 항목 절감률별 영업이익 개선 효과를 계산한다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "base_revenue": {"type": "number", "description": "기준 매출액 (원)"},
                        "cost_items": {
                            "type": "object",
                            "description": "원가 항목별 현재 금액 {항목명: 금액}",
                        },
                        "reduction_rates": {
                            "type": "object",
                            "description": "항목별 절감률 시나리오 {항목명: 절감율(0~1)}",
                        },
                    },
                    "required": ["base_revenue", "cost_items", "reduction_rates"],
                },
            },
        ]

    # ── 툴 구현 ────────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_bep":
            return self._calc_bep(**tool_input)
        if tool_name == "cost_breakdown":
            return self._cost_breakdown(**tool_input)
        if tool_name == "cost_reduction_sim":
            return self._cost_reduction_sim(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _calc_bep(
        self,
        fixed_cost: float,
        variable_cost_ratio: float,
        current_revenue: float,
        target_profit: float | None = None,
    ) -> dict:
        cmr = 1 - variable_cost_ratio  # 공헌이익률
        bep = fixed_cost / cmr if cmr else 0  # 손익분기점 매출액
        safety_margin = current_revenue - bep
        safety_margin_ratio = safety_margin / current_revenue if current_revenue else 0
        current_op_income = current_revenue * cmr - fixed_cost

        result: dict[str, Any] = {
            "공헌이익률(CMR)": f"{cmr * 100:.2f}%",
            "손익분기점_매출액": round(bep),
            "현재_매출액": round(current_revenue),
            "안전한계액": round(safety_margin),
            "안전한계율(%)": round(safety_margin_ratio * 100, 2),
            "현재_영업이익": round(current_op_income),
        }

        if target_profit is not None:
            target_revenue = (fixed_cost + target_profit) / cmr if cmr else 0
            result["목표이익"] = round(target_profit)
            result["목표달성_필요매출"] = round(target_revenue)
            result["추가필요매출"] = round(max(0, target_revenue - current_revenue))

        result["평가"] = (
            "우수 (안전한계율 25% 초과)" if safety_margin_ratio > 0.25
            else "주의 (안전한계율 10~25%)" if safety_margin_ratio > 0.10
            else "위험 (안전한계율 10% 이하)"
        )
        return result

    def _cost_breakdown(
        self,
        revenue: float,
        direct_material: float,
        direct_labor: float,
        mfg_overhead: float,
        sga: float,
        industry_cogs_ratio: float = 0.65,
    ) -> dict:
        cogs = direct_material + direct_labor + mfg_overhead
        total_cost = cogs + sga
        op_income = revenue - total_cost

        items = [
            ("직접재료비", direct_material),
            ("직접노무비", direct_labor),
            ("제조간접비", mfg_overhead),
            ("판매관리비", sga),
        ]
        breakdown = [
            {
                "항목": name,
                "금액": round(amt),
                "매출대비(%)": round(amt / revenue * 100, 2) if revenue else 0,
            }
            for name, amt in items
        ]

        bench_cogs = revenue * industry_cogs_ratio
        cogs_gap = cogs - bench_cogs

        return {
            "매출액": round(revenue),
            "매출원가_합계": round(cogs),
            "원가율(%)": round(cogs / revenue * 100, 2) if revenue else 0,
            "업종평균_원가율(%)": round(industry_cogs_ratio * 100, 2),
            "원가율_업종대비(pp)": round((cogs - bench_cogs) / revenue * 100, 2) if revenue else 0,
            "영업이익": round(op_income),
            "영업이익률(%)": round(op_income / revenue * 100, 2) if revenue else 0,
            "원가_상세": breakdown,
            "절감_여력_추정": round(max(0, cogs_gap)),
            "메모": "원가율이 업종 평균 초과 시 자재비·외주비 협상 우선 검토",
        }

    def _cost_reduction_sim(
        self,
        base_revenue: float,
        cost_items: dict[str, float],
        reduction_rates: dict[str, float],
    ) -> dict:
        current_total = sum(cost_items.values())
        current_op = base_revenue - current_total

        scenarios = []
        for item, rate in reduction_rates.items():
            if item not in cost_items:
                continue
            reduction_amt = cost_items[item] * rate
            new_total = current_total - reduction_amt
            new_op = base_revenue - new_total
            op_change = new_op - current_op

            scenarios.append({
                "절감항목": item,
                "절감율(%)": round(rate * 100, 1),
                "절감금액": round(reduction_amt),
                "개선후_영업이익": round(new_op),
                "영업이익_개선액": round(op_change),
                "영업이익률_개선(pp)": round(op_change / base_revenue * 100, 2) if base_revenue else 0,
            })

        # 전체 동시 절감 시나리오
        total_reduction = sum(
            cost_items[item] * rate
            for item, rate in reduction_rates.items()
            if item in cost_items
        )
        combined_op = base_revenue - (current_total - total_reduction)

        return {
            "기준_매출액": round(base_revenue),
            "기준_영업이익": round(current_op),
            "기준_영업이익률(%)": round(current_op / base_revenue * 100, 2) if base_revenue else 0,
            "항목별_단독_절감효과": scenarios,
            "전체동시절감_영업이익": round(combined_op),
            "전체동시절감_개선액": round(total_reduction),
        }

    # ── analyze() 인터페이스 ───────────────────────────────────────────────

    def analyze(self, company_data: dict[str, Any]) -> str:
        revenue = company_data.get("revenue", 0)
        fixed_cost = company_data.get("fixed_cost", 0)
        variable_ratio = company_data.get("variable_cost_ratio", 0.60)
        op_income = company_data.get("operating_income", 0)

        lines = ["[원가분석 결과]"]

        if revenue and fixed_cost:
            bep = self._calc_bep(fixed_cost, variable_ratio, revenue)
            lines.append(f"\n▶ 손익분기점 분석")
            lines.append(f"  공헌이익률: {bep['공헌이익률(CMR)']} / BEP: {bep['손익분기점_매출액']:,.0f}원")
            lines.append(f"  안전한계율: {bep['안전한계율(%)']:.1f}% → {bep['평가']}")

        if not lines[1:]:
            lines.append("  원가 데이터 부족 — 고정비·변동비율 입력 필요")

        return "\n".join(lines)

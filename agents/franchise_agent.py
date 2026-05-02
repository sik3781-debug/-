"""
FranchiseAgent: 프랜차이즈 전략 전담 에이전트

근거 법령:
  - 가맹사업거래의 공정화에 관한 법률 (가맹사업법)
  - 가맹사업법 제7조 (정보공개서 등록·제공 의무)
  - 가맹사업법 제9조 (허위·과장 정보 제공 금지)
  - 가맹사업법 제12조 (가맹점사업자 거래 제한 행위)
  - 공정거래위원회 가맹사업 표준계약서
  - 부가가치세법 (가맹점 매출세금계산서 수수)

주요 기능:
  - 가맹 사업 시작 적격성 진단 (본부 요건·수익성·법적 준비)
  - 가맹비·로열티·인테리어비 수익 구조 최적화
  - 정보공개서 필수 기재 항목 체크리스트
  - 가맹점 수익 시뮬레이션 (가맹점주 입장 손익)
  - 가맹사업법 위반 리스크 진단 (허위표시·부당 광고분담금)
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 프랜차이즈 사업화 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 가맹사업 시작 적격성: 직영점 운영 1년 이상 / 상표권 등록 여부\n"
    "- 정보공개서 작성 및 공정위 등록 (의무 / 미등록 시 영업정지)\n"
    "- 가맹비·로열티·물류마진·인테리어비 수익 구조 설계\n"
    "- 가맹점주 손익 시뮬레이션 (적정 가맹비·수익률 설득력)\n"
    "- 가맹사업법 위반 리스크: 허위표시·불공정 계약 조건\n\n"
    "【분석 관점】\n"
    "- 본부(법인): 가맹비·로열티 수익 극대화 / 세무 처리 적정성\n"
    "- 가맹점사업자: 투자 회수 기간 / 실수익률\n"
    "- 과세관청: 가맹비 과세(VAT) / 로열티 소득 구분\n"
    "- 공정위: 정보공개서 적정성 / 불공정 계약 여부\n\n"
    "【목표】\n"
    "가맹사업법 100% 준수를 전제로 본부·가맹점 상생 수익 구조를 설계하고,\n"
    "가맹점 확장을 통한 법인 가치를 극대화한다."
)

# 가맹사업 시작 법적 요건
FRANCHISE_REQUIREMENTS = {
    "직영점_운영": "1년 이상 (가맹사업법 §6의2)",
    "정보공개서_등록": "공정위 등록 후 14일 이후 가맹계약 체결 가능",
    "상표권": "특허청 등록 완료 필수",
    "가맹계약서": "공정위 표준계약서 준용 권장",
}

# 프랜차이즈 수익 구조 유형
REVENUE_TYPES = {
    "가맹비(입점비)": "계약 체결 시 1회 수취 / VAT 과세",
    "로열티": "월 매출의 일정 비율 / VAT 과세",
    "물류마진": "원재료·부재료 공급 마진 / 과세",
    "인테리어비": "시공비 중 본부 마진 / 별도 세금계산서",
    "광고분담금": "월 정액 또는 매출 비율 / 실제 광고집행 필수",
}


class FranchiseAgent(BaseAgent):
    name = "FranchiseAgent"
    role = "프랜차이즈 전략 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "diagnose_franchise_readiness",
                "description": (
                    "가맹사업 시작 적격성 진단.\n"
                    "직영점 운영·상표권·정보공개서 등 법적 요건과\n"
                    "수익성 요건을 동시에 점검한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "direct_store_years": {
                            "type": "number",
                            "description": "직영점 운영 기간 (년)",
                        },
                        "has_trademark": {"type": "boolean", "description": "상표권 등록 여부"},
                        "has_disclosure_doc": {"type": "boolean", "description": "정보공개서 공정위 등록 여부"},
                        "direct_store_operating_margin": {
                            "type": "number",
                            "description": "직영점 영업이익률 (0~1)",
                        },
                        "num_direct_stores": {"type": "integer", "description": "직영점 수"},
                    },
                    "required": ["direct_store_years", "has_trademark", "direct_store_operating_margin"],
                },
            },
            {
                "name": "design_revenue_structure",
                "description": (
                    "가맹사업 수익 구조 설계.\n"
                    "가맹비·로열티·물류마진·인테리어비 조합으로\n"
                    "본부 수익과 가맹점 매력도를 동시에 최적화한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "avg_monthly_store_revenue": {
                            "type": "number",
                            "description": "가맹점 월평균 예상 매출 (원)",
                        },
                        "initial_franchise_fee": {
                            "type": "number",
                            "description": "가맹비(입점비) 설정 금액 (원)",
                        },
                        "royalty_rate": {
                            "type": "number",
                            "description": "로열티율 (매출 대비, 0~0.10)",
                        },
                        "supply_margin_rate": {
                            "type": "number",
                            "description": "물류 공급 마진율 (공급가 대비, 0~0.30)",
                        },
                        "avg_supply_ratio": {
                            "type": "number",
                            "description": "가맹점 매출 중 본부 원재료 구매 비율 (0~1)",
                        },
                        "target_stores_3y": {
                            "type": "integer",
                            "description": "3년 목표 가맹점 수",
                        },
                    },
                    "required": ["avg_monthly_store_revenue", "royalty_rate", "target_stores_3y"],
                },
            },
            {
                "name": "simulate_franchisee_profit",
                "description": (
                    "가맹점주 손익 시뮬레이션.\n"
                    "투자비·매출·원가·로열티 차감 후 가맹점주 실수익과\n"
                    "투자 회수 기간(PBP)을 계산한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "monthly_revenue": {"type": "number", "description": "월 예상 매출 (원)"},
                        "cogs_ratio": {"type": "number", "description": "원가율 (0~1)"},
                        "labor_cost": {"type": "number", "description": "월 인건비 (원)"},
                        "rent": {"type": "number", "description": "월 임대료 (원)"},
                        "royalty_rate": {"type": "number", "description": "로열티율 (매출 대비)"},
                        "initial_investment": {
                            "type": "number",
                            "description": "초기 투자비 합계 (가맹비+인테리어+집기, 원)",
                        },
                    },
                    "required": ["monthly_revenue", "cogs_ratio", "labor_cost", "rent", "royalty_rate", "initial_investment"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "diagnose_franchise_readiness":
            return self._diagnose_franchise_readiness(**tool_input)
        if tool_name == "design_revenue_structure":
            return self._design_revenue_structure(**tool_input)
        if tool_name == "simulate_franchisee_profit":
            return self._simulate_franchisee_profit(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _diagnose_franchise_readiness(
        self,
        direct_store_years: float,
        has_trademark: bool,
        direct_store_operating_margin: float,
        has_disclosure_doc: bool = False,
        num_direct_stores: int = 1,
    ) -> dict:
        issues = []
        score = 0

        if direct_store_years >= 1.0:
            score += 30
        else:
            issues.append(f"직영점 운영 {direct_store_years:.1f}년 — 1년 이상 필수 (가맹사업법 §6의2)")

        if has_trademark:
            score += 25
        else:
            issues.append("상표권 미등록 — 특허청 등록 먼저 완료 (6개월 소요)")

        if has_disclosure_doc:
            score += 20
        else:
            issues.append("정보공개서 미등록 — 공정위 등록 후 14일 이후 가맹계약 체결 가능")

        if direct_store_operating_margin >= 0.15:
            score += 15
        elif direct_store_operating_margin >= 0.10:
            score += 8
            issues.append(f"직영점 수익률 {direct_store_operating_margin*100:.0f}% — 가맹점 수익성 설득력 낮음")
        else:
            issues.append(f"직영점 수익률 {direct_store_operating_margin*100:.0f}% — 가맹점 모집 전 수익성 개선 필수")

        if num_direct_stores >= 2:
            score += 10

        verdict = (
            "🟢 즉시 가맹사업 시작 가능" if score >= 80 and not issues
            else "🟡 1~6개월 준비 후 시작" if score >= 50
            else "🔴 법적 요건 미충족 — 시작 불가"
        )

        return {
            "준비_점수": f"{score}/100",
            "진단결과": verdict,
            "미비_항목": issues,
            "법적_요건": FRANCHISE_REQUIREMENTS,
            "즉시_조치": issues[:2] if issues else ["정보공개서 공정위 등록 → 가맹점 모집 시작"],
        }

    def _design_revenue_structure(
        self,
        avg_monthly_store_revenue: float,
        royalty_rate: float,
        target_stores_3y: int,
        initial_franchise_fee: float = 10_000_000,
        supply_margin_rate: float = 0.15,
        avg_supply_ratio: float = 0.40,
    ) -> dict:
        monthly_royalty_per_store = avg_monthly_store_revenue * royalty_rate
        monthly_supply_margin = avg_monthly_store_revenue * avg_supply_ratio * supply_margin_rate

        # 가맹점 수 단계별 성장 (1년차 30% / 2년차 60% / 3년차 100%)
        store_ramp = [int(target_stores_3y * r) for r in [0.30, 0.60, 1.00]]
        annual_revenues = []
        for yr, stores in enumerate(store_ramp, 1):
            franchise_fee_income = initial_franchise_fee * max(0, stores - (store_ramp[yr-2] if yr > 1 else 0))
            royalty_income = monthly_royalty_per_store * stores * 12
            supply_income = monthly_supply_margin * stores * 12
            total = franchise_fee_income + royalty_income + supply_income
            annual_revenues.append({
                "연도": f"{yr}년차",
                "가맹점수": stores,
                "가맹비수입": round(franchise_fee_income),
                "로열티수입": round(royalty_income),
                "물류마진수입": round(supply_income),
                "합계": round(total),
            })

        return {
            "수익_구조": REVENUE_TYPES,
            "단위_수익_구조": {
                "점당_월_로열티": round(monthly_royalty_per_store),
                "점당_월_물류마진": round(monthly_supply_margin),
                "점당_월_합계": round(monthly_royalty_per_store + monthly_supply_margin),
            },
            "3개년_수익_예측": annual_revenues,
            "3년차_연간_본부수익": annual_revenues[-1]["합계"],
            "주의사항": "광고분담금은 실제 광고비에만 집행 — 미집행 시 가맹사업법 위반",
        }

    def _simulate_franchisee_profit(
        self,
        monthly_revenue: float,
        cogs_ratio: float,
        labor_cost: float,
        rent: float,
        royalty_rate: float,
        initial_investment: float,
    ) -> dict:
        cogs = monthly_revenue * cogs_ratio
        royalty = monthly_revenue * royalty_rate
        other_costs = monthly_revenue * 0.05  # 기타 운영비 5% 추정
        total_cost = cogs + labor_cost + rent + royalty + other_costs
        monthly_profit = monthly_revenue - total_cost
        annual_profit = monthly_profit * 12
        pbp = initial_investment / annual_profit if annual_profit > 0 else 99
        op_margin = monthly_profit / monthly_revenue if monthly_revenue else 0

        return {
            "월_매출": round(monthly_revenue),
            "원가": round(cogs),
            "인건비": round(labor_cost),
            "임대료": round(rent),
            "로열티": round(royalty),
            "기타운영비": round(other_costs),
            "월_순이익": round(monthly_profit),
            "연_순이익": round(annual_profit),
            "영업이익률(%)": round(op_margin * 100, 1),
            "초기_투자비": round(initial_investment),
            "투자회수기간(년)": round(pbp, 1),
            "평가": (
                "🟢 우수 (PBP 3년 이하)" if pbp <= 3
                else "🟡 보통 (PBP 3~5년)" if pbp <= 5
                else "🔴 재검토 (PBP 5년 초과)"
            ),
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        direct_yrs = company_data.get("direct_store_years", 0)
        has_tm = company_data.get("has_trademark", False)
        margin = company_data.get("direct_store_margin", 0.12)

        lines = ["[프랜차이즈 전략 분석 결과]"]
        diag = self._diagnose_franchise_readiness(direct_yrs, has_tm, margin)
        lines.append(f"\n▶ 가맹사업 적격성: {diag['진단결과']}")
        lines.append(f"  준비 점수: {diag['준비_점수']}")
        if diag["미비_항목"]:
            lines.append(f"  미비 사항: {' / '.join(diag['미비_항목'][:2])}")
        return "\n".join(lines)

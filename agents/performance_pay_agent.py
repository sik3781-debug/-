"""
PerformancePayAgent: 성과급·인센티브 설계 전담 에이전트

근거 법령:
  - 근로기준법 제43조 (임금 지급), 제56조 (연장·야간·휴일 가산)
  - 소득세법 제20조 (근로소득), 제47조의2 (근로소득 세액공제)
  - 법인세법 제26조 (인건비 손금산입), 제29조 (퇴직급여충당금)
  - 조세특례제한법 제29조의4 (고용증대세액공제)
  - 조세특례제한법 제29조의5 (정규직 전환 세액공제)

주요 기능:
  - KPI 연동 성과급 구조 설계 (이익연동·매출연동·절감액연동)
  - 성과급 지급 시 소득세·4대보험 부담 시뮬레이션
  - 주식매수선택권(스톡옵션) vs. 현금 성과급 비교
  - 임원성과급 손금산입 요건 검토 (정관·주총결의 구비 여부)
  - 고용증대세액공제(조특법 §29의4) 적격성 및 공제액 계산
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 성과급·인센티브 설계 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- KPI 연동 성과급 구조 설계 및 지급 기준 문서화\n"
    "- 성과급 지급 시 소득세·4대보험 부담 계산\n"
    "- 임원성과급 손금산입 요건: 정관 또는 주주총회 결의 필수 (법인세법 §26)\n"
    "- 주식매수선택권(Stock Option) vs. 현금 성과급 세부담 비교\n"
    "- 고용증대세액공제 (조특법 §29의4): 청년 1인당 최대 1,550만 원\n"
    "- 정규직 전환 세액공제 (조특법 §29의5): 1인당 최대 1,300만 원\n\n"
    "【분석 관점】\n"
    "- 법인: 인건비 손금 최대화 / 세액공제 수혜 / 인재 유지\n"
    "- 오너: 핵심 인재 이탈 방지 / 성과 동기부여 / 지분 희석 최소화\n"
    "- 과세관청: 성과급의 실질 근로소득 해당 여부 / 손금산입 적정성\n"
    "- 금융기관: 인건비 증가에 따른 현금흐름 영향\n\n"
    "【목표】\n"
    "핵심 인재를 법적·세무적으로 안전하게 보상하고,\n"
    "법인의 절세 효과까지 극대화하는 인센티브 구조를 설계한다."
)

# 고용증대세액공제 (조특법 §29의4 / 2026년 귀속)
EMPLOYMENT_CREDIT = {
    "청년_수도권": 4_500_000,     # 청년·장애인·60세이상 수도권
    "청년_비수도권": 5_500_000,   # 청년·장애인·60세이상 비수도권
    "일반_수도권": 7_000_000,     # 일반 정규직 수도권 (중소)
    "일반_비수도권": 7_700_000,   # 일반 정규직 비수도권 (중소)
}
# 정규직 전환 세액공제 (조특법 §29의5)
REGULAR_CONVERT_CREDIT = 13_000_000   # 1인당 (중소기업)


class PerformancePayAgent(BaseAgent):
    name = "PerformancePayAgent"
    role = "성과급·인센티브 설계 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "design_kpi_bonus",
                "description": (
                    "KPI 연동 성과급 구조 설계.\n"
                    "이익·매출·절감액 등 KPI 지표와 연동하여\n"
                    "지급 구간별 성과급 금액 테이블을 생성한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bonus_pool": {"type": "number", "description": "연간 성과급 재원 (원)"},
                        "kpi_type": {
                            "type": "string",
                            "description": "KPI 유형",
                            "enum": ["영업이익", "매출액", "원가절감액", "고객만족도"],
                        },
                        "target_value": {"type": "number", "description": "KPI 목표값 (원 또는 점수)"},
                        "tiers": {
                            "type": "array",
                            "description": "성과 구간 [{달성율: 0.8, 지급율: 0.5}, ...]",
                            "items": {"type": "object"},
                        },
                    },
                    "required": ["bonus_pool", "kpi_type", "target_value"],
                },
            },
            {
                "name": "calc_bonus_tax",
                "description": (
                    "성과급 지급 시 개인·법인 세금·4대보험 부담 계산.\n"
                    "기본급 + 성과급 합산 소득세, 4대보험 정산 효과를 포함한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "annual_base_salary": {"type": "number", "description": "연간 기본급 (원)"},
                        "bonus_amount": {"type": "number", "description": "성과급 지급액 (원)"},
                        "marginal_tax_rate": {"type": "number", "description": "한계소득세율 (0~0.45)"},
                        "is_executive": {
                            "type": "boolean",
                            "description": "임원 여부 (손금산입 요건 달라짐)",
                        },
                    },
                    "required": ["annual_base_salary", "bonus_amount", "marginal_tax_rate"],
                },
            },
            {
                "name": "calc_employment_credit",
                "description": (
                    "고용증대세액공제(조특법 §29의4) 및\n"
                    "정규직 전환 세액공제(조특법 §29의5) 예상 공제액 계산."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "new_youth_employees": {
                            "type": "integer",
                            "description": "신규 채용 청년 인원 (15~34세)",
                        },
                        "new_general_employees": {
                            "type": "integer",
                            "description": "신규 채용 일반 정규직 인원",
                        },
                        "converted_to_regular": {
                            "type": "integer",
                            "description": "정규직 전환 인원 (기간제→정규직)",
                        },
                        "is_metropolitan": {
                            "type": "boolean",
                            "description": "수도권 소재 여부",
                        },
                    },
                    "required": ["new_youth_employees", "new_general_employees", "converted_to_regular"],
                },
            },
        ]

    # ── 툴 구현 ────────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "design_kpi_bonus":
            return self._design_kpi_bonus(**tool_input)
        if tool_name == "calc_bonus_tax":
            return self._calc_bonus_tax(**tool_input)
        if tool_name == "calc_employment_credit":
            return self._calc_employment_credit(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _design_kpi_bonus(
        self,
        bonus_pool: float,
        kpi_type: str,
        target_value: float,
        tiers: list[dict] | None = None,
    ) -> dict:
        if tiers is None:
            tiers = [
                {"달성율": 0.80, "지급율": 0.50},
                {"달성율": 0.90, "지급율": 0.75},
                {"달성율": 1.00, "지급율": 1.00},
                {"달성율": 1.10, "지급율": 1.20},
                {"달성율": 1.20, "지급율": 1.50},
            ]

        table = []
        for tier in tiers:
            rate = tier.get("달성율", 1.0)
            pay_rate = tier.get("지급율", 1.0)
            kpi_val = target_value * rate
            pay_amt = bonus_pool * pay_rate
            table.append({
                f"KPI달성율(%)": round(rate * 100),
                f"{kpi_type}_달성값": round(kpi_val),
                "성과급_지급율(%)": round(pay_rate * 100),
                "성과급_지급액": round(pay_amt),
            })

        return {
            "KPI유형": kpi_type,
            "목표값": round(target_value),
            "성과급_재원": round(bonus_pool),
            "지급_테이블": table,
            "손금산입_요건": (
                "임원성과급: 정관 규정 또는 주주총회 결의 필수 (법인세법 §26)\n"
                "직원성과급: 취업규칙·단체협약 명시 권장"
            ),
            "법령근거": "법인세법 §26, 근로기준법 §43",
        }

    def _calc_bonus_tax(
        self,
        annual_base_salary: float,
        bonus_amount: float,
        marginal_tax_rate: float,
        is_executive: bool = False,
    ) -> dict:
        total_income = annual_base_salary + bonus_amount
        # 근로소득세 (한계세율 적용 — 단순화)
        base_tax = annual_base_salary * marginal_tax_rate
        bonus_tax = bonus_amount * marginal_tax_rate
        local_tax_rate = 0.10  # 지방소득세
        bonus_tax_total = bonus_tax * (1 + local_tax_rate)

        # 4대보험 정산 (연간 보수 증가 시 건보료 정산 발생)
        # 건강보험 추가 정산 추정 (보수총액 신고 기준)
        hi_rate_total = 0.0709
        hi_extra = bonus_amount * hi_rate_total / 2  # 근로자 부담분

        net_bonus = bonus_amount - bonus_tax_total - hi_extra
        corp_saving = bonus_amount * 0.20  # 법인세 절감 (20% 세율 가정)

        result = {
            "성과급_총액": round(bonus_amount),
            "개인_소득세(근사치)": round(bonus_tax_total),
            "개인_건보료_정산": round(hi_extra),
            "개인_실수령액": round(net_bonus),
            "법인세_절감효과": round(corp_saving),
            "법인_순부담": round(bonus_amount - corp_saving),
        }

        if is_executive:
            result["임원_주의사항"] = (
                "임원성과급은 정관 규정 또는 주주총회에서 지급 한도를 결의해야\n"
                "법인세법 §26에 따른 손금산입 인정. 미결의 시 전액 손금 불산입 위험."
            )
        return result

    def _calc_employment_credit(
        self,
        new_youth_employees: int,
        new_general_employees: int,
        converted_to_regular: int,
        is_metropolitan: bool = False,
    ) -> dict:
        if is_metropolitan:
            youth_unit = EMPLOYMENT_CREDIT["청년_수도권"]
            general_unit = EMPLOYMENT_CREDIT["일반_수도권"]
        else:
            youth_unit = EMPLOYMENT_CREDIT["청년_비수도권"]
            general_unit = EMPLOYMENT_CREDIT["일반_비수도권"]

        youth_credit = new_youth_employees * youth_unit
        general_credit = new_general_employees * general_unit
        convert_credit = converted_to_regular * REGULAR_CONVERT_CREDIT
        total = youth_credit + general_credit + convert_credit

        return {
            "청년_신규채용_인원": new_youth_employees,
            "청년_고용증대공제": round(youth_credit),
            "일반_신규채용_인원": new_general_employees,
            "일반_고용증대공제": round(general_credit),
            "정규직전환_인원": converted_to_regular,
            "정규직전환공제": round(convert_credit),
            "세액공제_합계": round(total),
            "지역구분": "수도권" if is_metropolitan else "비수도권",
            "법령근거": "조세특례제한법 §29의4, §29의5",
            "주의사항": (
                "고용증대세액공제는 공제 연도 및 이후 2년간 상시 근로자 수 유지 필요.\n"
                "감소 시 추징 발생 (조특법 §29의4 제7항)"
            ),
        }

    # ── analyze() 인터페이스 ───────────────────────────────────────────────

    def analyze(self, company_data: dict[str, Any]) -> str:
        bonus_pool = company_data.get("bonus_pool", 0)
        new_youth = company_data.get("new_youth_employees", 0)
        new_general = company_data.get("new_general_employees", 0)
        converted = company_data.get("converted_to_regular", 0)
        is_metro = company_data.get("is_metropolitan", False)

        lines = ["[성과급·인센티브 설계 분석 결과]"]

        if new_youth or new_general or converted:
            credit = self._calc_employment_credit(new_youth, new_general, converted, is_metro)
            lines.append(f"\n▶ 고용 관련 세액공제 합계: {credit['세액공제_합계']:,.0f}원")
            lines.append(f"  청년채용공제: {credit['청년_고용증대공제']:,.0f}원 / 정규직전환공제: {credit['정규직전환공제']:,.0f}원")

        if bonus_pool:
            tbl = self._design_kpi_bonus(bonus_pool, "영업이익", bonus_pool * 5)
            lines.append(f"\n▶ 성과급 재원 {bonus_pool:,.0f}원 기준 KPI 지급 구조 설계 완료")
            lines.append(f"  목표달성(100%) 시 지급액: {bonus_pool:,.0f}원 / 120% 달성 시 {bonus_pool*1.5:,.0f}원")

        if len(lines) == 1:
            lines.append("  인원·성과급 재원 데이터 부족 — 입력 필요")

        return "\n".join(lines)

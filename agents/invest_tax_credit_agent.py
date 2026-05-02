"""
InvestTaxCreditAgent: 통합투자세액공제 전담 에이전트

근거 법령:
  - 조세특례제한법 §24 (통합투자세액공제)
  - 조세특례제한법 §132 (최저한세)

공제 구조 (2026년 귀속 기준):
  기본공제:
    - 일반자산: 중소기업 10% / 중견기업 3% / 대기업 1%
    - 신성장·원천기술: 중소기업 12% / 중견기업 6% / 대기업 3%
    - 국가전략기술: 중소기업 25% / 중견기업 15% / 대기업 15%

  추가공제 (직전 3년 평균 투자액 초과분):
    - 일반자산: 3%
    - 신성장·원천기술: 4%
    - 국가전략기술: 4%

이월공제: 10년 (미공제 시 이월 가능)
"""

from __future__ import annotations
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 조세특례제한법 통합투자세액공제 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 통합투자세액공제 기본공제·추가공제 정밀 계산 (조특법 §24)\n"
    "- 국가전략기술 투자 우대 공제율 적용 (반도체·배터리·바이오·디스플레이)\n"
    "- 신성장·원천기술 투자 공제율 적용\n"
    "- 최저한세 충돌 분석 및 이월공제 10년 관리\n"
    "- 설비투자 시점 최적화 (공제 극대화 시뮬레이션)\n"
    "- 구 설비투자세액공제와의 유불리 비교\n\n"
    "【분석 기준】\n"
    "- 법인 투자 의사결정 / 과세관청 적법성 / 재무구조 영향 교차 분석\n"
    "- 최저한세 초과분 이월 전략 포함\n"
    "- 단정적 전문가 언어, 면책 문구 생략\n\n"
    "【목표】\n"
    "법인의 설비투자에 대한 세액공제를 법적 최대한으로 확보하고,\n"
    "이월공제 관리로 공제 손실을 방지하며 투자 ROI를 극대화한다."
)

# 통합투자세액공제율 (조특법 §24 / 2026년 귀속)
CREDIT_RATES = {
    "일반자산": {
        "기본": {"중소기업": 0.10, "중견기업": 0.03, "대기업": 0.01},
        "추가": 0.03,
    },
    "신성장원천기술": {
        "기본": {"중소기업": 0.12, "중견기업": 0.06, "대기업": 0.03},
        "추가": 0.04,
    },
    "국가전략기술": {
        "기본": {"중소기업": 0.25, "중견기업": 0.15, "대기업": 0.15},
        "추가": 0.04,
    },
}

# 최저한세율
MIN_TAX_RATES = {"중소기업": 0.07, "중견기업": 0.10, "대기업": 0.17}


class InvestTaxCreditAgent(BaseAgent):
    name = "InvestTaxCreditAgent"
    role = "통합투자세액공제 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_investment_credit",
                "description": (
                    "통합투자세액공제(기본+추가)를 정밀 계산합니다. "
                    "최저한세 충돌 및 이월공제를 함께 분석합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "investment_amount":   {"type": "number",
                                               "description": "당기 투자금액 (원)"},
                        "prior_3yr_avg":       {"type": "number",
                                               "description": "직전 3년 평균 투자금액 (원, 없으면 0)"},
                        "asset_type":          {"type": "string",
                                               "enum": ["일반자산", "신성장원천기술", "국가전략기술"],
                                               "description": "투자 자산 유형"},
                        "company_type":        {"type": "string",
                                               "enum": ["중소기업", "중견기업", "대기업"]},
                        "taxable_income":      {"type": "number",
                                               "description": "과세표준 (원)"},
                        "carryover_credit":    {"type": "number",
                                               "description": "전기 이월 세액공제 (원, 없으면 0)"},
                    },
                    "required": ["investment_amount", "asset_type", "company_type", "taxable_income"],
                },
            },
            {
                "name": "compare_investment_scenarios",
                "description": (
                    "투자 시점·금액·자산유형별 시나리오를 비교하여 "
                    "최적 투자 계획을 수립합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_type":   {"type": "string", "enum": ["중소기업", "중견기업", "대기업"]},
                        "taxable_income": {"type": "number"},
                        "prior_3yr_avg":  {"type": "number"},
                        "scenarios": {
                            "type": "array",
                            "description": "투자 시나리오 목록",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label":             {"type": "string"},
                                    "investment_amount": {"type": "number"},
                                    "asset_type":        {"type": "string",
                                                         "enum": ["일반자산", "신성장원천기술", "국가전략기술"]},
                                },
                                "required": ["label", "investment_amount", "asset_type"],
                            },
                        },
                    },
                    "required": ["company_type", "taxable_income", "scenarios"],
                },
            },
            {
                "name": "plan_carryover_management",
                "description": (
                    "미사용 이월공제 현황을 분석하고 향후 10년 이월공제 "
                    "소진 계획을 수립합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "carryover_credits": {
                            "type": "array",
                            "description": "연도별 이월공제 내역",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "year":   {"type": "integer"},
                                    "amount": {"type": "number"},
                                    "expiry": {"type": "integer",
                                              "description": "소멸 예정 연도"},
                                },
                                "required": ["year", "amount", "expiry"],
                            },
                        },
                        "company_type":         {"type": "string", "enum": ["중소기업", "중견기업", "대기업"]},
                        "annual_taxable_income":{"type": "number",
                                                "description": "향후 연평균 과세표준 예상 (원)"},
                    },
                    "required": ["carryover_credits", "company_type", "annual_taxable_income"],
                },
            },
        ]

    # ── 툴 핸들러 ──────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "calc_investment_credit":
            return self._calc_investment_credit(**tool_input)
        if tool_name == "compare_investment_scenarios":
            return self._compare_investment_scenarios(**tool_input)
        if tool_name == "plan_carryover_management":
            return self._plan_carryover_management(**tool_input)
        return {"error": f"알 수 없는 툴: {tool_name}"}

    # ── 법인세 산출 ────────────────────────────────────────────────────────

    @staticmethod
    def _corp_tax(ti: float) -> float:
        if ti <= 0:       return 0.0
        elif ti <= 2e8:   return ti * 0.10
        elif ti <= 2e10:  return 2e7 + (ti - 2e8) * 0.20
        elif ti <= 3e11:  return 3.98e9 + (ti - 2e10) * 0.22
        else:             return 6.958e10 + (ti - 3e11) * 0.25

    # ── 핵심 계산 로직 ────────────────────────────────────────────────────

    def _calc_investment_credit(
        self,
        investment_amount: float,
        asset_type: str,
        company_type: str,
        taxable_income: float,
        prior_3yr_avg: float = 0,
        carryover_credit: float = 0,
    ) -> dict:
        """통합투자세액공제 정밀 계산."""
        rates      = CREDIT_RATES[asset_type]
        base_rate  = rates["기본"][company_type]
        extra_rate = rates["추가"]

        # 기본공제
        basic_credit = investment_amount * base_rate

        # 추가공제 (직전 3년 평균 초과분)
        excess       = max(investment_amount - prior_3yr_avg, 0)
        extra_credit = excess * extra_rate

        total_credit  = basic_credit + extra_credit
        gross_tax     = self._corp_tax(taxable_income)

        # 최저한세 검토
        min_tax_rate   = MIN_TAX_RATES.get(company_type, 0.17)
        min_tax        = taxable_income * min_tax_rate
        max_credit_ok  = max(gross_tax - min_tax, 0)

        total_with_co  = total_credit + carryover_credit
        applied_credit = min(total_with_co, max_credit_ok)
        new_carryover  = max(total_with_co - applied_credit, 0)
        tax_after      = max(gross_tax - applied_credit, min_tax)

        return {
            "투자금액(원)":              round(investment_amount),
            "자산_유형":                 asset_type,
            "기업_규모":                 company_type,
            "기본_공제율":               f"{base_rate*100:.0f}%",
            "추가_공제율":               f"{extra_rate*100:.0f}%",
            "기본공제액(원)":            round(basic_credit),
            "직전3년평균_초과분(원)":    round(excess),
            "추가공제액(원)":            round(extra_credit),
            "당기_산출공제액(원)":       round(total_credit),
            "전기_이월공제(원)":         round(carryover_credit),
            "법인세_산출세액(원)":       round(gross_tax),
            "최저한세(원)":              round(min_tax),
            "최대_적용가능_공제(원)":    round(max_credit_ok),
            "실_적용_공제액(원)":        round(applied_credit),
            "차기_이월공제(원)":         round(new_carryover),
            "이월가능_기간":             "10년 (이월 미사용 시 소멸)",
            "공제_후_법인세(원)":        round(tax_after),
            "절세_효과(원)":             round(gross_tax - tax_after),
            "투자_실질비용(원)":         round(investment_amount - (gross_tax - tax_after)),
            "투자ROI_절세기준(%)":       round((gross_tax - tax_after) / investment_amount * 100, 2) if investment_amount else 0,
            "근거_법령":                 "조세특례제한법 §24(통합투자세액공제) / §132(최저한세)",
        }

    def _compare_investment_scenarios(
        self,
        company_type: str,
        taxable_income: float,
        scenarios: list[dict],
        prior_3yr_avg: float = 0,
    ) -> dict:
        """투자 시나리오 비교."""
        results = []
        for s in scenarios:
            r = self._calc_investment_credit(
                investment_amount=s["investment_amount"],
                asset_type=s["asset_type"],
                company_type=company_type,
                taxable_income=taxable_income,
                prior_3yr_avg=prior_3yr_avg,
            )
            results.append({
                "시나리오":       s["label"],
                "투자금액(원)":   round(s["investment_amount"]),
                "자산유형":      s["asset_type"],
                "공제액(원)":    r["실_적용_공제액(원)"],
                "절세효과(원)":  r["절세_효과(원)"],
                "이월공제(원)":  r["차기_이월공제(원)"],
                "실질투자비(원)": r["투자_실질비용(원)"],
                "투자ROI(%)":   r["투자ROI_절세기준(%)"],
            })

        best = max(results, key=lambda x: x["절세효과(원)"])
        return {
            "기업_규모":      company_type,
            "과세표준(원)":   round(taxable_income),
            "시나리오_비교":  results,
            "최적_시나리오":  best["시나리오"],
            "최대_절세효과(원)": best["절세효과(원)"],
            "전략_요약": (
                f"'{best['시나리오']}'이 절세효과 {best['절세효과(원)']:,.0f}원으로 최대. "
                f"국가전략기술 자산 투자 시 기본공제율이 가장 높음."
            ),
        }

    def _plan_carryover_management(
        self,
        carryover_credits: list[dict],
        company_type: str,
        annual_taxable_income: float,
    ) -> dict:
        """이월공제 소진 계획."""
        gross_tax    = self._corp_tax(annual_taxable_income)
        min_tax_rate = MIN_TAX_RATES.get(company_type, 0.17)
        min_tax      = annual_taxable_income * min_tax_rate
        annual_cap   = max(gross_tax - min_tax, 0)

        import datetime
        current_year = datetime.date.today().year

        plan = []
        remaining_pool = sorted(carryover_credits, key=lambda x: x["expiry"])

        annual_remaining = annual_cap
        for item in remaining_pool:
            yrs_left = item["expiry"] - current_year
            use_amt  = min(item["amount"], annual_remaining)
            at_risk  = item["amount"] - use_amt  # 소멸 위험

            plan.append({
                "발생연도":     item["year"],
                "잔액(원)":    round(item["amount"]),
                "소멸예정연도": item["expiry"],
                "잔여기간(년)": yrs_left,
                "당기_사용가능(원)": round(use_amt),
                "소멸위험(원)": round(at_risk),
                "위험도":       "HIGH" if yrs_left <= 2 else ("MEDIUM" if yrs_left <= 5 else "LOW"),
            })
            annual_remaining = max(annual_remaining - use_amt, 0)

        total_carryover = sum(c["amount"] for c in carryover_credits)
        total_at_risk   = sum(p["소멸위험(원)"] for p in plan)

        return {
            "이월공제_총액(원)":    round(total_carryover),
            "연간_소진가능_한도(원)": round(annual_cap),
            "소멸_위험액(원)":      round(total_at_risk),
            "연도별_소진_계획":     plan,
            "전략_제언": (
                f"총 이월공제 {total_carryover:,.0f}원 중 소멸 위험 {total_at_risk:,.0f}원. "
                "향후 투자 확대 또는 절세 구조 조정으로 조기 소진 권장."
                if total_at_risk > 0 else
                f"총 이월공제 {total_carryover:,.0f}원 — 연간 한도 내 정상 소진 가능."
            ),
            "근거_법령": "조세특례제한법 §24⑥ (이월공제 10년)",
        }

    # ── 공개 인터페이스 ────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        n   = company_data.get("company_name", "대상법인")
        ti  = company_data.get("taxable_income", 0)
        rev = company_data.get("revenue", 0)
        ta  = company_data.get("total_assets", 0)
        rd  = company_data.get("rd_expense", 0)

        company_type = "중소기업" if rev <= 12_000_000_000 else ("중견기업" if rev <= 400_000_000_000 else "대기업")

        query = (
            f"[분석 대상] {n} | {company_type} | 매출 {rev:,.0f}원 | 총자산 {ta:,.0f}원\n"
            f"[투자·세무] 과세표준: {ti:,.0f}원 | R&D: {rd:,.0f}원\n\n"
            f"① 통합투자세액공제 기본+추가 공제 계산 (일반·신성장·국가전략기술 3유형)\n"
            f"② 최저한세 충돌 여부 및 이월공제 활용 계획\n"
            f"③ 설비투자 시점 분산 vs 집중 투자 세액공제 최적화 시나리오\n"
            f"④ 국가전략기술 자산 투자 시 추가 공제율 적용 가능성 검토\n"
            f"⑤ 투자 ROI(절세 기준) 및 실질 투자비용 분석"
        )
        return self.run(query, reset=True)

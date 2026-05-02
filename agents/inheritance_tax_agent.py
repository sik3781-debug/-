"""
InheritanceTaxAgent: 상속세 시뮬레이션 전담 에이전트

근거 법령:
  - 상속세및증여세법 §18 (기초공제·그 밖의 인적공제)
  - 상속세및증여세법 §18의2 (가업상속공제: 최대 600억)
  - 상속세및증여세법 §19 (배우자 상속공제)
  - 상속세및증여세법 §21 (일괄공제 5억)
  - 상속세및증여세법 §13 (사전증여 합산: 상속인 10년, 비상속인 5년)
  - 상속세및증여세법 §56 (세율)

주요 기능:
  - 상속세 정밀 계산 (공제 자동 적용)
  - 가업상속공제 요건 검토 및 한도 산출
  - 사전증여 차감·합산 시뮬레이션
  - 배우자 상속분 최적화
  - 유산취득세 전환 대비 시뮬레이션
"""

from __future__ import annotations
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 상속세및증여세법 전문 세무 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 상속세 정밀 계산 (상증세법 §18~§26)\n"
    "- 가업상속공제 요건·한도 (§18의2: 최대 600억)\n"
    "- 배우자 상속공제 최적화 (§19: 최대 30억 한도 내 실제 상속분)\n"
    "- 사전증여재산 합산 (§13: 상속인 10년, 비상속인 5년)\n"
    "- 유산취득세 전환 대비 시나리오\n"
    "- 상속세 분할납부·연부연납 설계\n\n"
    "【분석 기준】\n"
    "- 법인(가업자산 평가) / 주주(오너) / 과세관청 3자 교차 분석\n"
    "- 최신 개정 세법 반영 (2026년 귀속 기준)\n"
    "- 단정적 전문가 언어, 면책 문구 생략\n\n"
    "【목표】\n"
    "오너 사망 시 가족의 상속세 부담을 법적 범위 내 최소화하고,\n"
    "가업승계 연속성을 확보하는 최적 상속 구조를 설계한다."
)


class InheritanceTaxAgent(BaseAgent):
    name = "InheritanceTaxAgent"
    role = "상속세 시뮬레이션 전담 전문가"
    system_prompt = _SYS

    # ── 상속세율표 (상증세법 §56) ─────────────────────────────────────────
    @staticmethod
    def _calc_inheritance_tax(taxable: float) -> float:
        """과세표준 → 산출세액."""
        if taxable <= 0:
            return 0.0
        elif taxable <= 100_000_000:
            return taxable * 0.10
        elif taxable <= 500_000_000:
            return taxable * 0.20 - 10_000_000
        elif taxable <= 1_000_000_000:
            return taxable * 0.30 - 60_000_000
        elif taxable <= 3_000_000_000:
            return taxable * 0.40 - 160_000_000
        else:
            return taxable * 0.50 - 460_000_000

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_inheritance_tax",
                "description": (
                    "상속세를 정밀 계산합니다. "
                    "가업상속공제·배우자공제·일괄공제 자동 적용."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "gross_estate": {
                            "type": "number",
                            "description": "총 상속재산 (원) — 부동산+금융+주식+기타",
                        },
                        "debts": {
                            "type": "number",
                            "description": "피상속인 채무·장례비용 (원, 없으면 0)",
                        },
                        "prior_gifts_heir_10yr": {
                            "type": "number",
                            "description": "상속인에게 10년 내 사전증여액 합계 (원, 없으면 0)",
                        },
                        "prior_gifts_non_heir_5yr": {
                            "type": "number",
                            "description": "비상속인에게 5년 내 사전증여액 합계 (원, 없으면 0)",
                        },
                        "apply_family_business": {
                            "type": "boolean",
                            "description": "가업상속공제 적용 여부",
                        },
                        "family_business_asset": {
                            "type": "number",
                            "description": "가업자산 가액 (원) — 가업상속공제 적용 시 필수",
                        },
                        "ceo_years": {
                            "type": "integer",
                            "description": "피상속인 가업 경영 기간 (년) — 10년↑300억 / 20년↑500억 / 30년↑600억",
                        },
                        "spouse_actual_share": {
                            "type": "number",
                            "description": "배우자 실제 상속금액 (원, 0이면 법정지분 자동 적용)",
                        },
                        "heirs_count": {
                            "type": "integer",
                            "description": "상속인 수 (배우자 포함)",
                        },
                        "has_spouse": {
                            "type": "boolean",
                            "description": "배우자 생존 여부",
                        },
                        "minor_heirs": {
                            "type": "integer",
                            "description": "미성년 상속인 수 (0이면 없음)",
                        },
                        "disabled_heirs": {
                            "type": "integer",
                            "description": "장애인 상속인 수 (0이면 없음)",
                        },
                    },
                    "required": ["gross_estate", "heirs_count"],
                },
            },
            {
                "name": "check_family_business_eligibility",
                "description": "가업상속공제 요건 충족 여부와 공제 한도를 산출합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ceo_years": {
                            "type": "integer",
                            "description": "피상속인 경영 기간 (년)",
                        },
                        "heir_works_years": {
                            "type": "integer",
                            "description": "상속인의 가업 종사 기간 (년)",
                        },
                        "company_revenue": {
                            "type": "number",
                            "description": "직전 3년 평균 매출 (원) — 중견기업 4천억 이하 요건 확인",
                        },
                        "family_business_asset": {
                            "type": "number",
                            "description": "가업자산 가액 (원)",
                        },
                        "owner_share_pct": {
                            "type": "number",
                            "description": "피상속인 지분율 (%)",
                        },
                    },
                    "required": ["ceo_years", "heir_works_years", "family_business_asset"],
                },
            },
            {
                "name": "simulate_pre_gift_effect",
                "description": "사전증여 규모 변경 시 상속세·증여세 합산 부담 변화를 시뮬레이션합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "gross_estate":       {"type": "number", "description": "현재 총 상속재산 (원)"},
                        "pre_gift_scenarios": {
                            "type": "array",
                            "description": "사전증여 시나리오 목록",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label":      {"type": "string"},
                                    "gift_amount":{"type": "number"},
                                    "donee_type": {"type": "string",
                                                   "enum": ["직계존비속_성년", "직계존비속_미성년",
                                                            "배우자", "기타친족"]},
                                },
                                "required": ["label", "gift_amount", "donee_type"],
                            },
                        },
                        "has_spouse":   {"type": "boolean"},
                        "heirs_count":  {"type": "integer"},
                    },
                    "required": ["gross_estate", "pre_gift_scenarios"],
                },
            },
        ]

    # ── 툴 핸들러 ──────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "calc_inheritance_tax":
            return self._calc_inheritance_tax_tool(**tool_input)
        if tool_name == "check_family_business_eligibility":
            return self._check_family_business(**tool_input)
        if tool_name == "simulate_pre_gift_effect":
            return self._simulate_pre_gift(**tool_input)
        return {"error": f"알 수 없는 툴: {tool_name}"}

    # ── 핵심 계산 로직 ────────────────────────────────────────────────────

    def _family_business_limit(self, ceo_years: int) -> int:
        """가업상속공제 한도 (상증세법 §18의2)."""
        if ceo_years >= 30:
            return 60_000_000_000    # 600억
        elif ceo_years >= 20:
            return 50_000_000_000    # 500억
        elif ceo_years >= 10:
            return 30_000_000_000    # 300억
        return 0

    def _calc_inheritance_tax_tool(
        self,
        gross_estate: float,
        heirs_count: int,
        debts: float = 0,
        prior_gifts_heir_10yr: float = 0,
        prior_gifts_non_heir_5yr: float = 0,
        apply_family_business: bool = False,
        family_business_asset: float = 0,
        ceo_years: int = 10,
        spouse_actual_share: float = 0,
        has_spouse: bool = True,
        minor_heirs: int = 0,
        disabled_heirs: int = 0,
    ) -> dict:
        """상속세 정밀 계산."""

        # 1. 과세가액 산정
        net_estate = gross_estate - debts
        taxable_estate = net_estate + prior_gifts_heir_10yr + prior_gifts_non_heir_5yr

        # 2. 공제 적용
        # 기초공제 2억
        basic_deduction = 200_000_000

        # 그 밖의 인적공제
        minor_deduction    = minor_heirs * 10_000_000 * max(19, 0)  # 19세까지 1천만×잔여연수 (단순화)
        disabled_deduction = disabled_heirs * 10_000_000             # 단순화 (실제는 기대여명 반영)
        other_deductions   = minor_deduction + disabled_deduction

        # 일괄공제 (기초공제+인적공제 vs 5억 중 큰 금액)
        lump_deduction = max(basic_deduction + other_deductions, 500_000_000)

        # 가업상속공제
        fb_deduction = 0
        fb_limit     = 0
        if apply_family_business and family_business_asset > 0:
            fb_limit     = self._family_business_limit(ceo_years)
            fb_deduction = min(family_business_asset, fb_limit)

        # 배우자 공제 (상증세법 §19: 법정상속분 vs 실상속분 중 작은 금액, 최소 5억~최대 30억)
        spouse_deduction = 0
        if has_spouse:
            legal_share_rate = (1.5 / (heirs_count - 1 + 1.5)) if heirs_count > 1 else 1.0
            legal_share_val  = net_estate * legal_share_rate
            if spouse_actual_share > 0:
                spouse_deduction = min(spouse_actual_share, legal_share_val, 30_000_000_000)
            else:
                spouse_deduction = min(legal_share_val, 30_000_000_000)
            spouse_deduction = max(spouse_deduction, 500_000_000)  # 최소 5억

        total_deduction = lump_deduction + fb_deduction + spouse_deduction
        taxable = max(taxable_estate - total_deduction, 0)

        gross_tax     = self._calc_inheritance_tax(taxable)
        filing_credit = gross_tax * 0.03   # 신고세액공제 3%
        final_tax     = gross_tax - filing_credit

        # 사전증여분 세액공제 (합산된 증여세 차감)
        gift_tax_credit = self._calc_gift_tax_approx(prior_gifts_heir_10yr, "직계존비속_성년")
        net_tax = max(final_tax - gift_tax_credit, 0)

        return {
            "총_상속재산(원)":        round(gross_estate),
            "채무_공제(원)":          round(debts),
            "사전증여_합산(원)":       round(prior_gifts_heir_10yr + prior_gifts_non_heir_5yr),
            "과세가액(원)":           round(taxable_estate),
            "일괄공제(원)":           round(lump_deduction),
            "가업상속공제(원)":        round(fb_deduction),
            "가업상속공제_한도(원)":   round(fb_limit),
            "배우자공제(원)":          round(spouse_deduction),
            "총_공제액(원)":           round(total_deduction),
            "과세표준(원)":            round(taxable),
            "산출세액(원)":            round(gross_tax),
            "신고세액공제_3%(원)":     round(filing_credit),
            "증여세_기납부공제(원)":   round(gift_tax_credit),
            "최종_납부세액(원)":       round(net_tax),
            "실효세율(%)":             round(net_tax / gross_estate * 100, 2) if gross_estate else 0,
            "근거_법령": (
                "상증세법 §18(기초공제) §18의2(가업상속공제) §19(배우자공제) "
                "§21(일괄공제) §13(사전증여합산) §56(세율)"
            ),
        }

    @staticmethod
    def _calc_gift_tax_approx(gift_amount: float, donee_type: str) -> float:
        """사전증여세 추정 (기납부세액공제용 단순계산)."""
        deduction = {"배우자": 600_000_000, "직계존비속_성년": 50_000_000,
                     "직계존비속_미성년": 20_000_000, "기타친족": 10_000_000}.get(donee_type, 10_000_000)
        taxable = max(gift_amount - deduction, 0)
        if taxable <= 0:
            return 0.0
        elif taxable <= 100_000_000:
            return taxable * 0.10
        elif taxable <= 500_000_000:
            return taxable * 0.20 - 10_000_000
        elif taxable <= 1_000_000_000:
            return taxable * 0.30 - 60_000_000
        elif taxable <= 3_000_000_000:
            return taxable * 0.40 - 160_000_000
        else:
            return taxable * 0.50 - 460_000_000

    def _check_family_business(
        self,
        ceo_years: int,
        heir_works_years: int,
        family_business_asset: float,
        company_revenue: float = 0,
        owner_share_pct: float = 50.0,
    ) -> dict:
        """가업상속공제 적격성 판단."""
        limit = self._family_business_limit(ceo_years)

        # 요건 점검
        req_ceo_years     = ceo_years >= 10
        req_heir_works    = heir_works_years >= 2   # 상속 전 2년 이상 종사
        req_revenue       = company_revenue <= 400_000_000_000 if company_revenue else True  # 4천억 이하
        req_owner_share   = owner_share_pct >= 40   # 최대주주 + 특수관계인 합산 40%↑

        all_qualified = all([req_ceo_years, req_heir_works, req_revenue, req_owner_share])

        return {
            "가업상속공제_적격": all_qualified,
            "요건_점검": {
                "피상속인_10년이상_경영":   {"충족": req_ceo_years,   "실제": f"{ceo_years}년"},
                "상속인_2년이상_가업종사":  {"충족": req_heir_works,  "실제": f"{heir_works_years}년"},
                "중견기업_매출4천억이하":   {"충족": req_revenue,     "실제": f"{company_revenue/100_000_000:.0f}억" if company_revenue else "미입력"},
                "최대주주_지분율_40%이상":  {"충족": req_owner_share, "실제": f"{owner_share_pct}%"},
            },
            "공제_한도(원)":      limit,
            "공제_한도_억원":     limit // 100_000_000,
            "가업자산_가액(원)":  round(family_business_asset),
            "적용_공제액(원)":    round(min(family_business_asset, limit)) if all_qualified else 0,
            "사후_의무이행_요건": (
                "①가업 종사 유지 7년 ②지분 유지 ③고용 유지(5년 내 정규직 80%↑) — "
                "위반 시 공제액 추징"
            ),
            "근거_법령": "상증세법 §18의2 (2026년 귀속 기준)",
        }

    def _simulate_pre_gift(
        self,
        gross_estate: float,
        pre_gift_scenarios: list[dict],
        has_spouse: bool = True,
        heirs_count: int = 3,
    ) -> dict:
        """사전증여 효과 시뮬레이션."""
        deduction_map = {
            "배우자": 600_000_000,
            "직계존비속_성년": 50_000_000,
            "직계존비속_미성년": 20_000_000,
            "기타친족": 10_000_000,
        }

        # 기준: 사전증여 없음
        base = self._calc_inheritance_tax_tool(
            gross_estate=gross_estate,
            heirs_count=heirs_count,
            has_spouse=has_spouse,
        )
        base_tax = base["최종_납부세액(원)"]

        results = [{"시나리오": "사전증여 없음 (기준)", "사전증여액(원)": 0,
                    "상속세(원)": base_tax, "증여세(원)": 0, "합산세부담(원)": base_tax,
                    "절세효과(원)": 0}]

        for s in pre_gift_scenarios:
            ga    = s.get("gift_amount", 0)
            dtype = s.get("donee_type", "직계존비속_성년")
            ded   = deduction_map.get(dtype, 10_000_000)
            g_taxable = max(ga - ded, 0)
            gift_tax  = self._calc_gift_tax_approx(ga, dtype)

            # 사전증여 후 잔여 상속재산
            remain_estate = max(gross_estate - ga, 0)
            inh = self._calc_inheritance_tax_tool(
                gross_estate=remain_estate,
                heirs_count=heirs_count,
                has_spouse=has_spouse,
                prior_gifts_heir_10yr=ga,
            )
            inh_tax   = inh["최종_납부세액(원)"]
            total_tax = gift_tax + inh_tax
            saving    = base_tax - total_tax

            results.append({
                "시나리오":       s.get("label", f"사전증여 {ga/100_000_000:.0f}억"),
                "사전증여액(원)":  round(ga),
                "증여세(원)":     round(gift_tax),
                "상속세(원)":     round(inh_tax),
                "합산세부담(원)": round(total_tax),
                "절세효과(원)":   round(saving),
            })

        best = max(results[1:], key=lambda x: x["절세효과(원)"], default=results[0])
        return {
            "기준_상속세(원)":  base_tax,
            "시나리오_비교":    results,
            "최적_시나리오":    best.get("시나리오"),
            "최대_절세효과(원)": best.get("절세효과(원)", 0),
            "주의사항": (
                "사전증여액은 10년(상속인) / 5년(비상속인) 합산 과세 대상. "
                "증여 후 자산가치 상승분은 상속재산에서 제외되므로 주가·부동산 저평가 시점 증여가 유리."
            ),
        }

    # ── 공개 인터페이스 ────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        n        = company_data.get("company_name", "대상법인")
        ceo_age  = company_data.get("ceo_age", 55)
        bv       = company_data.get("business_value", 0)
        te       = company_data.get("total_equity", 0)
        ta       = company_data.get("total_assets", 0)
        yrs      = company_data.get("years_in_operation", 0)
        children = company_data.get("children_count", 2)

        query = (
            f"[분석 대상] {n} | 대표 {ceo_age}세 | 업력 {yrs}년 | 자녀 {children}명\n"
            f"[자산 현황] 기업가치 {bv:,.0f}원 | 자기자본 {te:,.0f}원 | 총자산 {ta:,.0f}원\n\n"
            f"① 현재 시점 상속 발생 시 상속세 정밀 계산 (배우자·일괄공제 최적 적용)\n"
            f"② 가업상속공제 요건 점검 및 적용 시 절세 효과 (업력 {yrs}년 기준)\n"
            f"③ 사전증여 0원·5억·10억·20억 4가지 시나리오 상속세+증여세 합산 비교\n"
            f"④ 배우자 상속분 최적화 전략 (배우자공제 한도 내 최대 활용)\n"
            f"⑤ 상속세 연부연납(최대 10년) 활용 시 현금흐름 영향 분석"
        )
        return self.run(query, reset=True)

"""
VATAgent: 부가가치세 절세 전담 에이전트

근거 법령:
  - 부가가치세법 §40~§43 (간이과세)
  - 부가가치세법 §42 (의제매입세액공제)
  - 부가가치세법 §29 (과세표준)
  - 조세특례제한법 §108 (의제매입세액공제 한도)

주요 기능:
  - 일반과세·간이과세 유불리 판단
  - 의제매입세액공제 계산 (음식·제조업 업종별 공제율)
  - 면세·과세 겸업 시 공통매입세액 안분 계산
  - 세금계산서 불부합 리스크 진단
  - VAT 환급 타이밍 최적화
"""

from __future__ import annotations
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 부가가치세법 전문 세무 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 일반과세 vs 간이과세 유불리 비교 (매출액 8천만 기준)\n"
    "- 의제매입세액공제 최적화 (업종별 공제율 적용)\n"
    "- 면세·과세 겸업 공통매입세액 안분 계산\n"
    "- 세금계산서 발행·수취 오류 리스크 진단\n"
    "- VAT 조기환급 신청 전략\n"
    "- 영세율·면세 구분 및 절세 활용\n\n"
    "【분석 기준】\n"
    "- 법인 재무 영향 / 과세관청 적법성 / 실행 가능성 교차 분석\n"
    "- 최신 개정 세법 반영 (2026년 귀속 기준)\n"
    "- 단정적 전문가 언어, 면책 문구 생략\n\n"
    "【목표】\n"
    "법인의 부가가치세 부담을 적법하게 최소화하고,\n"
    "세금계산서 불부합 등 세무조사 리스크를 사전 제거한다."
)

# 의제매입세액공제율 (부가가치세법 §42, 조특법 §108)
DEEMED_INPUT_RATES = {
    "음식점업_법인":      2 / 102,   # 2/102
    "음식점업_개인":      8 / 108,   # 8/108
    "제조업_중소기업":    4 / 104,   # 4/104
    "제조업_일반":        2 / 102,   # 2/102
    "과자점_도소매":      2 / 102,   # 2/102
    "농축수산물_판매":    2 / 102,
}

# 간이과세 업종별 부가가치율
SIMPLIFIED_VAT_RATES = {
    "전기가스수도업":     0.05,
    "소매업":            0.15,
    "재생용재료수집판매": 0.15,
    "음식점업":          0.25,
    "건설업":            0.30,
    "숙박업":            0.25,
    "운수통신업":        0.30,
    "기타서비스":        0.30,
    "제조업":            0.20,
}


class VATAgent(BaseAgent):
    name = "VATAgent"
    role = "부가가치세 절세 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "compare_vat_type",
                "description": (
                    "일반과세·간이과세 유불리를 비교하고 최적 과세 유형을 추천합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "annual_revenue": {
                            "type": "number",
                            "description": "연간 매출액 (원, 부가세 제외)",
                        },
                        "annual_input_tax": {
                            "type": "number",
                            "description": "연간 매입세액 합계 (원)",
                        },
                        "industry": {
                            "type": "string",
                            "description": "업종 (소매업/음식점업/제조업/서비스업 등)",
                        },
                        "is_corporation": {
                            "type": "boolean",
                            "description": "법인 여부 (True=법인, False=개인)",
                        },
                    },
                    "required": ["annual_revenue", "annual_input_tax", "industry"],
                },
            },
            {
                "name": "calc_deemed_input_credit",
                "description": (
                    "의제매입세액공제액을 계산합니다. "
                    "음식점업·제조업 등 면세 농축수산물 사용 업종에 적용."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "exempt_purchase": {
                            "type": "number",
                            "description": "면세 원재료(농축수산물 등) 매입액 (원)",
                        },
                        "industry_type": {
                            "type": "string",
                            "enum": list(DEEMED_INPUT_RATES.keys()),
                            "description": "업종 구분",
                        },
                        "taxable_revenue": {
                            "type": "number",
                            "description": "과세 매출액 (원) — 공제 한도 계산용",
                        },
                        "is_corporation": {
                            "type": "boolean",
                            "description": "법인 여부",
                        },
                    },
                    "required": ["exempt_purchase", "industry_type", "taxable_revenue"],
                },
            },
            {
                "name": "calc_common_input_allocation",
                "description": (
                    "면세·과세 겸업 법인의 공통매입세액 안분 계산과 "
                    "정산 방법을 제시합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "total_input_tax": {
                            "type": "number",
                            "description": "당기 총 매입세액 (원)",
                        },
                        "taxable_revenue": {
                            "type": "number",
                            "description": "과세 매출액 (원)",
                        },
                        "exempt_revenue": {
                            "type": "number",
                            "description": "면세 매출액 (원)",
                        },
                        "directly_taxable_input": {
                            "type": "number",
                            "description": "과세사업에만 사용된 매입세액 (직접 귀속, 원)",
                        },
                        "directly_exempt_input": {
                            "type": "number",
                            "description": "면세사업에만 사용된 매입세액 (직접 귀속, 원)",
                        },
                    },
                    "required": ["total_input_tax", "taxable_revenue", "exempt_revenue"],
                },
            },
        ]

    # ── 툴 핸들러 ──────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "compare_vat_type":
            return self._compare_vat_type(**tool_input)
        if tool_name == "calc_deemed_input_credit":
            return self._calc_deemed_input_credit(**tool_input)
        if tool_name == "calc_common_input_allocation":
            return self._calc_common_input_allocation(**tool_input)
        return {"error": f"알 수 없는 툴: {tool_name}"}

    # ── 핵심 계산 로직 ────────────────────────────────────────────────────

    def _compare_vat_type(
        self,
        annual_revenue: float,
        annual_input_tax: float,
        industry: str,
        is_corporation: bool = True,
    ) -> dict:
        """일반과세 vs 간이과세 납부세액 비교."""
        # 법인은 간이과세 불가 (부가가치세법 §61)
        if is_corporation:
            general_vat = annual_revenue * 0.10 - annual_input_tax
            return {
                "과세_유형_비교":        "법인은 간이과세 불가 — 일반과세만 적용",
                "일반과세_납부세액(원)":  round(max(general_vat, 0)),
                "환급세액(원)":          round(abs(min(general_vat, 0))),
                "연간_VAT_부담(원)":     round(max(general_vat, 0)),
                "절세_전략":            "매입세액 최대화 (적격 세금계산서 수취 철저), 조기환급 적극 활용",
                "근거":                 "부가가치세법 §61 (법인 간이과세 적용 제외)",
            }

        # 개인사업자 비교
        SIMPLIFIED_THRESHOLD = 80_000_000  # 8천만 미만 간이과세

        # 일반과세
        general_vat = max(annual_revenue * 0.10 - annual_input_tax, 0)

        # 간이과세
        vat_rate = SIMPLIFIED_VAT_RATES.get(industry, 0.30)
        simplified_vat = annual_revenue * 0.10 * vat_rate  # 간이과세 납부의무

        can_simplified = annual_revenue < SIMPLIFIED_THRESHOLD

        return {
            "연간_매출액(원)":           round(annual_revenue),
            "간이과세_적용가능":          can_simplified,
            "간이과세_기준_매출(원)":     80_000_000,
            "일반과세_납부세액(원)":      round(general_vat),
            "간이과세_납부세액(원)":      round(simplified_vat) if can_simplified else "적용불가",
            "유리한_과세유형":            (
                "간이과세" if (can_simplified and simplified_vat < general_vat) else "일반과세"
            ),
            "절세_금액(원)":             round(
                abs(general_vat - simplified_vat) if can_simplified else 0
            ),
            "주의사항": (
                "간이과세자는 매입세액 환급 불가. 매입세액이 많은 업종(투자 집중)은 "
                "일반과세가 유리할 수 있음."
            ),
            "근거": "부가가치세법 §40(간이과세) / 업종별 부가가치율 고시",
        }

    def _calc_deemed_input_credit(
        self,
        exempt_purchase: float,
        industry_type: str,
        taxable_revenue: float,
        is_corporation: bool = True,
    ) -> dict:
        """의제매입세액공제 계산."""
        rate = DEEMED_INPUT_RATES.get(industry_type, 2 / 102)

        # 공제액 = 면세매입액 × 공제율
        credit = exempt_purchase * rate

        # 공제 한도: 과세매출액 × 업종별 한도율
        # 음식점업 법인: 매출의 40%, 음식점 개인: 60%, 제조업: 50%
        limit_rate_map = {
            "음식점업_법인":      0.40,
            "음식점업_개인":      0.60,
            "제조업_중소기업":    0.50,
            "제조업_일반":        0.50,
            "과자점_도소매":      0.40,
            "농축수산물_판매":    0.40,
        }
        limit_rate = limit_rate_map.get(industry_type, 0.40)
        credit_limit = taxable_revenue * 0.10 * limit_rate

        applicable_credit = min(credit, credit_limit)

        return {
            "면세원재료_매입액(원)":   round(exempt_purchase),
            "업종_구분":              industry_type,
            "의제매입공제율":          f"{rate * 100:.4f}% ({int(rate * 100 * 102 / 100)}/{int(102)})",
            "산출_의제매입세액공제(원)": round(credit),
            "공제_한도율":             f"과세매출의 {limit_rate*100:.0f}%",
            "공제_한도액(원)":         round(credit_limit),
            "실_적용_공제액(원)":      round(applicable_credit),
            "절세_효과(원)":           round(applicable_credit),
            "한도_초과여부":           credit > credit_limit,
            "근거":                   "부가가치세법 §42 / 조세특례제한법 §108",
        }

    def _calc_common_input_allocation(
        self,
        total_input_tax: float,
        taxable_revenue: float,
        exempt_revenue: float,
        directly_taxable_input: float = 0,
        directly_exempt_input: float = 0,
    ) -> dict:
        """공통매입세액 안분 계산 (부가가치세법 §40)."""
        total_revenue = taxable_revenue + exempt_revenue

        # 공통매입세액 = 총매입세액 - 직접귀속분
        common_input = total_input_tax - directly_taxable_input - directly_exempt_input

        # 과세비율 = 과세매출 / 총매출
        taxable_ratio = taxable_revenue / total_revenue if total_revenue else 0

        # 공통매입세액 중 과세분
        common_taxable = common_input * taxable_ratio
        common_exempt  = common_input * (1 - taxable_ratio)

        # 총 공제 가능 매입세액
        deductible = directly_taxable_input + common_taxable
        non_deductible = directly_exempt_input + common_exempt

        return {
            "총_매입세액(원)":           round(total_input_tax),
            "과세매출(원)":              round(taxable_revenue),
            "면세매출(원)":              round(exempt_revenue),
            "과세_비율(%)":              round(taxable_ratio * 100, 2),
            "공통매입세액(원)":          round(common_input),
            "공제_가능_매입세액(원)": {
                "직접귀속_과세분(원)":     round(directly_taxable_input),
                "공통매입_과세안분(원)":   round(common_taxable),
                "합계(원)":               round(deductible),
            },
            "불공제_매입세액(원)": {
                "직접귀속_면세분(원)":     round(directly_exempt_input),
                "공통매입_면세안분(원)":   round(common_exempt),
                "합계(원)":               round(non_deductible),
            },
            "절세_전략": (
                f"과세비율 {taxable_ratio*100:.1f}% 유지 시 {deductible:,.0f}원 공제 가능. "
                "면세사업 비중 축소 또는 과세사업 확대 시 공제율 개선."
            ),
            "근거": "부가가치세법 §40 (공통매입세액 안분계산)",
        }

    # ── 공개 인터페이스 ────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        n        = company_data.get("company_name", "대상법인")
        rev      = company_data.get("revenue", 0)
        ind      = company_data.get("industry", "제조업")
        rd       = company_data.get("rd_expense", 0)
        ni       = company_data.get("net_income", 0)

        query = (
            f"[분석 대상] {n} | 업종: {ind} | 연매출: {rev:,.0f}원\n"
            f"[재무 현황] R&D 지출: {rd:,.0f}원 | 순이익: {ni:,.0f}원\n\n"
            f"① 부가가치세 신고 현황 진단 및 절세 포인트 3가지 제시\n"
            f"② {ind} 업종 의제매입세액공제 적용 여부 및 예상 공제액 산출\n"
            f"③ 세금계산서 불부합 리스크 항목과 예방 체크리스트\n"
            f"④ VAT 조기환급 신청 가능 조건 및 예상 환급액\n"
            f"⑤ 매입세액 공제 최대화를 위한 실무 개선 방안"
        )
        return self.run(query, reset=True)

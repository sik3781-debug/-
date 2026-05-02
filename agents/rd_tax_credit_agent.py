"""
RDTaxCreditAgent: R&D 세액공제 전담 에이전트

근거 법령:
  - 조세특례제한법 §10 (연구·인력개발비 세액공제)
  - 조세특례제한법 §10의2 (신성장·원천기술 R&D 세액공제)
  - 조세특례제한법 §132 (최저한세)

공제율 체계 (2026년 귀속 기준):
  ① 일반 R&D — 중소기업: Max(증가분 25%, 당기분 25%)
               중견기업: Max(증가분 40%, 당기분 8%)
               대기업:   Max(증가분 40%, 당기분 2%)
  ② 신성장·원천기술 — 중소 40% / 중견 20% / 대기업 20%
  ③ 국가전략기술 — 중소 50% / 중견 40% / 대기업 40%

최저한세: 중소기업 7% / 일반 법인 17%
"""

from __future__ import annotations
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 조세특례제한법 R&D 세액공제 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 일반 R&D 세액공제 (조특법 §10): 증가분·당기분 방식 비교\n"
    "- 신성장·원천기술 세액공제 (§10의2)\n"
    "- 국가전략기술 R&D 공제 (반도체·배터리·바이오 등)\n"
    "- 인력개발비 공제 (직무발명보상금·산학협력 포함)\n"
    "- 최저한세 충돌 분석 (§132)\n"
    "- R&D 적격비용 분류 및 증빙 체계 구축\n\n"
    "【분석 기준】\n"
    "- 법인 절세 극대화 / 과세관청 적법성 교차 분석\n"
    "- 최저한세 초과 공제액 이월 관리\n"
    "- 단정적 전문가 언어, 면책 문구 생략\n\n"
    "【목표】\n"
    "법인의 R&D 투자에 대한 세액공제를 법적 최대한으로 확보하고,\n"
    "최저한세 충돌 시 이월 전략으로 공제 손실을 방지한다."
)

# 공제율 테이블 (조특법 §10 / 2026년 귀속)
CREDIT_RATES = {
    "일반": {
        "중소기업": {"당기분": 0.25, "증가분": 0.25},
        "중견기업": {"당기분": 0.08, "증가분": 0.40},
        "대기업":   {"당기분": 0.02, "증가분": 0.40},
    },
    "신성장원천": {
        "중소기업": 0.40,
        "중견기업": 0.20,
        "대기업":   0.20,
    },
    "국가전략기술": {
        "중소기업": 0.50,
        "중견기업": 0.40,
        "대기업":   0.40,
    },
}

# 최저한세율
MIN_TAX_RATES = {"중소기업": 0.07, "중견기업": 0.10, "대기업": 0.17}


class RDTaxCreditAgent(BaseAgent):
    name = "RDTaxCreditAgent"
    role = "R&D 세액공제 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_rd_credit",
                "description": (
                    "R&D 세액공제액을 정밀 계산합니다. "
                    "일반·신성장·국가전략기술 3트랙과 최저한세 충돌을 함께 검토합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "current_rd":       {"type": "number", "description": "당기 R&D 비용 (원)"},
                        "prior_rd_avg":     {"type": "number", "description": "직전 4년 평균 R&D 비용 (원, 없으면 0)"},
                        "company_type":     {"type": "string", "enum": ["중소기업", "중견기업", "대기업"],
                                            "description": "기업 규모"},
                        "rd_type":          {"type": "string", "enum": ["일반", "신성장원천", "국가전략기술"],
                                            "description": "R&D 유형"},
                        "taxable_income":   {"type": "number", "description": "과세표준 (원)"},
                        "carryover_credit": {"type": "number", "description": "전기 이월 세액공제 (원, 없으면 0)"},
                    },
                    "required": ["current_rd", "company_type", "rd_type", "taxable_income"],
                },
            },
            {
                "name": "compare_rd_tracks",
                "description": (
                    "일반·신성장·국가전략기술 3가지 트랙의 공제액을 비교하고 "
                    "최적 트랙을 추천합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "current_rd":     {"type": "number"},
                        "prior_rd_avg":   {"type": "number"},
                        "company_type":   {"type": "string", "enum": ["중소기업", "중견기업", "대기업"]},
                        "taxable_income": {"type": "number"},
                        "eligible_tracks":{"type": "array", "items": {"type": "string"},
                                          "description": "적용 가능한 트랙 목록 (모두 가능하면 전부 포함)"},
                    },
                    "required": ["current_rd", "company_type", "taxable_income"],
                },
            },
            {
                "name": "plan_rd_investment",
                "description": (
                    "목표 절세액 달성을 위한 R&D 투자 규모를 역산하고, "
                    "세액공제 대비 실질 투자 비용을 분석합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_tax_saving": {"type": "number", "description": "목표 절세액 (원)"},
                        "company_type":      {"type": "string", "enum": ["중소기업", "중견기업", "대기업"]},
                        "rd_type":           {"type": "string", "enum": ["일반", "신성장원천", "국가전략기술"]},
                        "current_rd":        {"type": "number", "description": "현재 R&D 지출 (원)"},
                        "taxable_income":    {"type": "number"},
                    },
                    "required": ["target_tax_saving", "company_type", "rd_type", "taxable_income"],
                },
            },
        ]

    # ── 툴 핸들러 ──────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "calc_rd_credit":
            return self._calc_rd_credit(**tool_input)
        if tool_name == "compare_rd_tracks":
            return self._compare_rd_tracks(**tool_input)
        if tool_name == "plan_rd_investment":
            return self._plan_rd_investment(**tool_input)
        return {"error": f"알 수 없는 툴: {tool_name}"}

    # ── 법인세 산출 ────────────────────────────────────────────────────────

    @staticmethod
    def _corp_tax(ti: float) -> float:
        """법인세법 §55 (2026년 귀속)."""
        if ti <= 0:            return 0.0
        elif ti <= 2e8:        return ti * 0.10
        elif ti <= 2e10:       return 2e7 + (ti - 2e8) * 0.20
        elif ti <= 3e11:       return 3.98e9 + (ti - 2e10) * 0.22
        else:                  return 6.958e10 + (ti - 3e11) * 0.25

    # ── 핵심 계산 로직 ────────────────────────────────────────────────────

    def _calc_rd_credit(
        self,
        current_rd: float,
        company_type: str,
        rd_type: str,
        taxable_income: float,
        prior_rd_avg: float = 0,
        carryover_credit: float = 0,
    ) -> dict:
        """R&D 세액공제 정밀 계산."""
        gross_tax = self._corp_tax(taxable_income)

        if rd_type == "일반":
            rates = CREDIT_RATES["일반"][company_type]
            # 당기분 방식
            credit_current = current_rd * rates["당기분"]
            # 증가분 방식
            increase = max(current_rd - prior_rd_avg, 0)
            credit_increase = increase * rates["증가분"]
            # 유리한 방식 선택
            credit_gross = max(credit_current, credit_increase)
            method = "당기분" if credit_current >= credit_increase else "증가분"
        else:
            rate = CREDIT_RATES[rd_type][company_type]
            credit_gross = current_rd * rate
            method = rd_type

        # 최저한세 검토
        min_tax_rate = MIN_TAX_RATES.get(company_type, 0.17)
        min_tax = taxable_income * min_tax_rate
        max_credit_allowed = max(gross_tax - min_tax, 0)

        credit_applied   = min(credit_gross + carryover_credit, max_credit_allowed)
        credit_carryover = max(credit_gross - credit_applied, 0)  # 미사용 이월
        tax_after_credit = max(gross_tax - credit_applied, min_tax)

        return {
            "당기_R&D_비용(원)":          round(current_rd),
            "R&D_유형":                  rd_type,
            "기업_규모":                  company_type,
            "적용_방식":                  method,
            "산출_공제액(원)":            round(credit_gross),
            "전기_이월_공제(원)":          round(carryover_credit),
            "법인세_산출세액(원)":         round(gross_tax),
            "최저한세(원)":               round(min_tax),
            "최대_적용가능_공제(원)":      round(max_credit_allowed),
            "실_적용_공제액(원)":          round(credit_applied),
            "이월_미사용_공제(원)":        round(credit_carryover),
            "공제_후_법인세(원)":          round(tax_after_credit),
            "절세_효과(원)":              round(gross_tax - tax_after_credit),
            "R&D_실질_비용(원)":          round(current_rd - credit_applied),
            "근거_법령":                  f"조세특례제한법 §10({'§10의2' if rd_type != '일반' else ''}) / §132(최저한세)",
        }

    def _compare_rd_tracks(
        self,
        current_rd: float,
        company_type: str,
        taxable_income: float,
        prior_rd_avg: float = 0,
        eligible_tracks: list | None = None,
    ) -> dict:
        """3트랙 공제액 비교."""
        if eligible_tracks is None:
            eligible_tracks = ["일반", "신성장원천", "국가전략기술"]

        results = {}
        for track in eligible_tracks:
            r = self._calc_rd_credit(
                current_rd=current_rd,
                company_type=company_type,
                rd_type=track,
                taxable_income=taxable_income,
                prior_rd_avg=prior_rd_avg,
            )
            results[track] = {
                "공제액(원)":    r["실_적용_공제액(원)"],
                "이월공제(원)":  r["이월_미사용_공제(원)"],
                "절세효과(원)":  r["절세_효과(원)"],
                "적용방식":     r["적용_방식"],
            }

        best_track = max(results, key=lambda k: results[k]["공제액(원)"])
        return {
            "R&D비용(원)":    round(current_rd),
            "기업_규모":      company_type,
            "트랙별_비교":    results,
            "최적_트랙":      best_track,
            "최대_공제액(원)": results[best_track]["공제액(원)"],
            "추천_근거":      (
                f"{best_track} 트랙이 공제액 {results[best_track]['공제액(원)']:,.0f}원으로 최대. "
                "국가전략기술·신성장 트랙은 별도 기술 인증 필요."
            ),
        }

    def _plan_rd_investment(
        self,
        target_tax_saving: float,
        company_type: str,
        rd_type: str,
        taxable_income: float,
        current_rd: float = 0,
    ) -> dict:
        """목표 절세액 달성을 위한 R&D 투자 역산."""
        gross_tax    = self._corp_tax(taxable_income)
        min_tax_rate = MIN_TAX_RATES.get(company_type, 0.17)
        min_tax      = taxable_income * min_tax_rate
        max_saving   = max(gross_tax - min_tax, 0)

        # 유효 목표 절세액 (최저한세 초과분 불가)
        effective_target = min(target_tax_saving, max_saving)

        # 필요 R&D 비용 역산
        if rd_type == "일반":
            rate = CREDIT_RATES["일반"][company_type]["당기분"]
        else:
            rate = CREDIT_RATES[rd_type][company_type]

        required_rd = effective_target / rate if rate else 0
        additional_rd = max(required_rd - current_rd, 0)

        # 실질 비용 (R&D 추가 투자 - 절세)
        net_cost = additional_rd - effective_target

        return {
            "목표_절세액(원)":          round(target_tax_saving),
            "최저한세_제한_후_가능절세(원)": round(effective_target),
            "필요_총_R&D비용(원)":      round(required_rd),
            "현재_R&D비용(원)":         round(current_rd),
            "추가_투자_필요(원)":       round(additional_rd),
            "실질_투자비용(원)":         round(net_cost),
            "R&D_투자_ROI(%)":         round((effective_target / additional_rd * 100), 1) if additional_rd else 999,
            "최저한세_제한_여부":       target_tax_saving > max_saving,
            "전략_제언": (
                f"R&D {additional_rd:,.0f}원 추가 투자 시 절세 {effective_target:,.0f}원 달성. "
                f"실질 비용 {net_cost:,.0f}원 — R&D 투자 대비 절세 ROI {effective_target/additional_rd*100:.1f}%."
                if additional_rd > 0 else "현재 R&D 비용으로 목표 절세 달성 가능."
            ),
            "근거_법령": f"조세특례제한법 §10 ({company_type} {rd_type}) / §132(최저한세)",
        }

    # ── 공개 인터페이스 ────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        n   = company_data.get("company_name", "대상법인")
        rd  = company_data.get("rd_expense", 0)
        rev = company_data.get("revenue", 0)
        ti  = company_data.get("taxable_income", 0)
        emp = company_data.get("employees", 0)
        pat = company_data.get("patents", 0)

        # 기업 규모 자동 판단 (단순화)
        company_type = "중소기업" if rev <= 12_000_000_000 else ("중견기업" if rev <= 400_000_000_000 else "대기업")

        query = (
            f"[분석 대상] {n} | {company_type} | 매출 {rev:,.0f}원 | 임직원 {emp}명 | 특허 {pat}건\n"
            f"[R&D 현황] R&D 비용: {rd:,.0f}원 ({rd/rev*100:.1f}%) | 과세표준: {ti:,.0f}원\n\n"
            f"① 일반·신성장·국가전략기술 3트랙 공제액 비교 및 최적 트랙 선택\n"
            f"② 증가분 vs 당기분 방식 유불리 분석\n"
            f"③ 최저한세 충돌 여부 및 이월공제 관리 방안\n"
            f"④ R&D 적격비용 분류 기준과 증빙 체계 구축 방법\n"
            f"⑤ 추가 R&D 투자 시 절세 효과 시뮬레이션 (투자 ROI 포함)"
        )
        return self.run(query, reset=True)

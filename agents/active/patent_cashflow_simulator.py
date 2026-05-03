"""특허 통합 NPV 시뮬레이터 (조특§10·12 + 소§12③마목 + 발명진흥법)"""
from __future__ import annotations


class PatentCashflowSimulator:
    """
    직무발명 보상 + 자본화 + 자체개발 50% 감면 + R&D 세액공제 통합 NPV.
    """
    RD_CREDIT_SME = 0.25       # 중소기업 R&D 세액공제 25%
    IP_TRANSFER_DISCOUNT = 0.50  # 조특§12: 기술이전 소득 50% 감면
    DISCOUNT_RATE = 0.08         # DCF 할인율 8%

    def analyze(self, company_data: dict) -> dict:
        rd_expense   = company_data.get("rd_expense", 0)
        patent_value = company_data.get("patent_value", 0)
        royalty_annual = company_data.get("royalty_annual", 0)
        years          = company_data.get("patent_years_left", 10)
        tax_rate       = company_data.get("tax_rate", 0.20)

        # R&D 세액공제
        rd_credit = rd_expense * self.RD_CREDIT_SME

        # 직무발명 보상 손금 산입
        inventor_reward = company_data.get("inventor_reward", 0)

        # 기술이전 NPV (조특§12 50% 감면)
        royalty_tax = royalty_annual * tax_rate * (1 - self.IP_TRANSFER_DISCOUNT)
        royalty_npv = sum(
            royalty_annual / (1 + self.DISCOUNT_RATE) ** y
            for y in range(1, years + 1)
        )
        royalty_npv_after_tax = royalty_npv * (1 - tax_rate * (1 - self.IP_TRANSFER_DISCOUNT))

        # 자체 개발 자본화 vs 비용처리 비교
        capitalize_benefit = patent_value * 0.05  # 상각 기간 20년 기준 연 5%
        expense_benefit    = patent_value * tax_rate  # 즉시 비용처리 시 절세

        return {
            "agent": "PatentCashflowSimulator",
            "text": (
                f"법인 측면: R&D 세액공제 {rd_credit:,.0f}원 (조특§10 중소기업 25%).\n"
                f"주주(오너) 관점: 기술이전 소득 {royalty_annual:,.0f}원 × 50% 감면 (조특§12) → 실효세율 {tax_rate*(1-0.5):.0%}.\n"
                f"과세관청 관점: 특허 자본화 vs 비용처리 선택 영향 — 자본화 시 내용연수 20년 적용.\n"
                f"금융기관 관점: 특허 IP 담보 대출 활용 — 가치 {patent_value:,.0f}원 기준.\n"
                f"통합 NPV: {royalty_npv_after_tax:,.0f}원 (10년, 세후)"
            ),
            "rd_credit": rd_credit,
            "royalty_npv_after_tax": royalty_npv_after_tax,
            "capitalize_benefit": capitalize_benefit,
            "expense_benefit": expense_benefit,
            "require_full_4_perspective": True,
        }

"""상속·증여세 통합 에이전트 v2 (자기주식 옵션 + 신탁 협력)"""
from __future__ import annotations


TAX_BRACKETS = [
    (100_000_000,    0.10, 0),
    (500_000_000,    0.20, 10_000_000),
    (1_000_000_000,  0.30, 60_000_000),
    (3_000_000_000,  0.40, 160_000_000),
    (float('inf'),   0.50, 460_000_000),
]


def _calc_gift_tax(taxable: int) -> int:
    for limit, rate, deduction in TAX_BRACKETS:
        if taxable <= limit:
            return int(taxable * rate - deduction)
    return int(taxable * 0.50 - 460_000_000)


class InheritanceTaxAgent:
    """상속·증여세 통합 + v2: 자기주식 옵션 + 민사신탁 협력"""

    DEDUCTIONS = {"spouse": 600_000_000, "adult_child": 50_000_000,
                  "minor_child": 20_000_000, "other": 10_000_000}
    MARRIAGE_BIRTH_EXTRA = 100_000_000

    def analyze(self, company_data: dict) -> dict:
        gift_amount   = company_data.get("gift_amount", 0)
        recipient     = company_data.get("recipient_type", "adult_child")
        marriage_gift = company_data.get("marriage_gift", False)

        deduction = self.DEDUCTIONS.get(recipient, 0)
        if marriage_gift:
            deduction += self.MARRIAGE_BIRTH_EXTRA
        taxable = max(0, gift_amount - deduction)
        gift_tax = _calc_gift_tax(taxable)

        # v2: 자기주식 활용 시나리오
        stock_price  = company_data.get("share_price", 10_000)
        shares_to_gift = company_data.get("shares_to_gift", 0)
        stock_gift_val = shares_to_gift * stock_price
        stock_gift_tax = _calc_gift_tax(max(0, stock_gift_val - deduction))

        # v2: 신탁 통한 단계적 증여
        staged_gift = gift_amount / 10  # 10년 분할
        staged_tax  = _calc_gift_tax(max(0, staged_gift - deduction)) * 10

        strategies = [
            {"name": "일시 현금 증여", "tax": gift_tax, "after": gift_amount - gift_tax},
            {"name": "주식 증여 (저평가 시점)", "tax": stock_gift_tax, "after": stock_gift_val - stock_gift_tax},
            {"name": "10년 분할 증여 (신탁 활용)", "tax": staged_tax, "after": gift_amount - staged_tax},
        ]
        best = min(strategies, key=lambda s: s["tax"])

        return {
            "agent": "InheritanceTaxAgent",
            "text": (
                f"주주(오너) 관점: 증여세 최소화 전략 — {best['name']} (세부담 {best['tax']:,.0f}원).\n"
                f"법인 측면: 주식 증여 시 보충적 평가액 기준 적용 (상증§54).\n"
                f"과세관청 관점: 10년 합산 (상증§47②) — 이전 증여 이력 반드시 합산.\n"
                f"금융기관 관점: 증여 후 지분 변동 → 주거래은행 통보 의무 확인.\n"
                f"v2 신설: 자기주식 증여 + 신탁 분할 증여 옵션 포함."
            ),
            "base_gift_tax": gift_tax,
            "strategies": strategies,
            "recommended": best["name"],
            "require_full_4_perspective": True,
        }

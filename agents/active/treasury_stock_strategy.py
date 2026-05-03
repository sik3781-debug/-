"""자기주식 5종 통합 전략 에이전트"""
from __future__ import annotations


class TreasuryStockStrategyAgent:
    """
    자기주식 5종 전략:
    1. 취득→양도 (배당 대체 33% 양도세)
    2. 이익소각 (의제배당 회피 설계)
    3. 가지급금 상환 활용
    4. 차등배당 지원
    5. ⭐ 주가 유동화 → 상속·증여 절세
    """

    def analyze(self, company_data: dict) -> dict:
        retained     = company_data.get("retained_earnings", 0)
        stock_price  = company_data.get("share_price", 10_000)
        shares_total = company_data.get("shares_total", 100_000)
        owner_pct    = company_data.get("owner_share_pct", 0.70)
        prov_payment = company_data.get("provisional_payment", 0)
        tax_rate     = company_data.get("owner_marginal_rate", 0.45)

        buyback_shares = int(shares_total * 0.10)  # 10% 매입 가정
        buyback_cost   = buyback_shares * stock_price

        strategies = [
            {
                "no": 1,
                "name": "취득→양도 (배당 대체)",
                "tax_rate": 0.33,
                "after_tax": buyback_cost * (1 - 0.33),
                "vs_dividend": buyback_cost * (1 - min(tax_rate + 0.044, 0.495)),
                "saving": buyback_cost * (min(tax_rate + 0.044, 0.495) - 0.33),
            },
            {
                "no": 2,
                "name": "이익소각 (의제배당 최소화)",
                "note": "취득단가 ≥ 소각가액 설계 시 의제배당 0원",
                "condition": "취득단가 = 소각가액",
            },
            {
                "no": 3,
                "name": "가지급금 상환",
                "available": min(prov_payment, buyback_cost),
                "note": f"가지급금 {prov_payment:,.0f}원 중 {min(prov_payment, buyback_cost):,.0f}원 상환 가능",
            },
            {
                "no": 4,
                "name": "차등배당 지원",
                "note": "비대주주 배당 집중 → 대주주 세부담 이연",
            },
            {
                "no": 5,
                "name": "⭐ 주가 유동화 → 상속·증여",
                "note": "자기주식 매입 → 주당 가치 상승 → 낮은 가격에 사전 증여 완료 후 소각",
                "tax_strategy": "증여 시점 주가 낮을 때 이전 → 이후 가치 상승분 비과세",
            },
        ]
        best = strategies[0]  # 배당 대체가 가장 명확한 절세

        return {
            "agent": "TreasuryStockStrategyAgent",
            "text": (
                f"주주(오너) 관점: 자기주식 취득→양도로 배당 대비 세율 {best['tax_rate']:.0%} vs {min(tax_rate+0.044,0.495):.0%} — 절세 {best['saving']:,.0f}원.\n"
                f"법인 측면: 자기주식 취득 시 발행주식 수 감소 → 1주당 가치 상승.\n"
                f"과세관청 관점: 소각 시 의제배당(소§17②4호) + 이익소각 vs 자본감소 구분 주의.\n"
                f"금융기관 관점: 자기주식 취득 시 자기자본 감소 — 부채비율 상승 주의.\n"
                f"⭐ 5종 전략 중 핵심: 주가 유동화→상속·증여 절세 설계."
            ),
            "strategies": strategies,
            "recommended_primary": best["name"],
            "buyback_shares": buyback_shares,
            "buyback_cost": buyback_cost,
            "require_full_4_perspective": True,
        }

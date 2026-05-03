"""미처분이익잉여금 처리 4방안 + 자기주식 5종 연동"""
from __future__ import annotations


class RetainedEarningsManagementAgent:
    """
    미처분이익잉여금 처리 방안:
    ① 배당 (종합소득세 최대 49.5%)
    ② 자기주식 취득→양도 (양도세 33% 또는 기본세율)
    ③ 자본전입 (의제배당 과세)
    ④ 이익소각 (의제배당 회피 설계 시)
    """
    # 세율 기준 (2026년)
    MAX_DIVIDEND_RATE = 0.495   # 배당소득세 최고 (종합과세 + 지방세)
    BUYBACK_RATE      = 0.33    # 자기주식 양도세 (대주주 10% 지분 이상)
    CAPITAL_SURPLUS_EXEMPTION = True  # 자본전입 중 자본잉여금 부분 비과세

    def analyze(self, company_data: dict) -> dict:
        retained = company_data.get("retained_earnings", 0)
        owner_pct = company_data.get("owner_share_pct", 0.70)
        tax_rate_personal = company_data.get("owner_marginal_rate", 0.45)

        # ① 배당
        div_tax = retained * owner_pct * min(tax_rate_personal + 0.044, self.MAX_DIVIDEND_RATE)
        div_after = retained * owner_pct - div_tax

        # ② 자기주식 취득→양도 (양도세 33%)
        buyback_tax = retained * owner_pct * self.BUYBACK_RATE
        buyback_after = retained * owner_pct - buyback_tax

        # ③ 자본전입 (의제배당)
        capital_transfer_tax = retained * owner_pct * min(tax_rate_personal + 0.044, self.MAX_DIVIDEND_RATE)

        # ④ 이익소각 (자기주식 소각)
        cancellation_tax = retained * owner_pct * self.BUYBACK_RATE  # 의제배당 but 자기주식 매입단가 차감

        methods = [
            {"method": "① 배당",          "tax": div_tax,            "after": div_after,     "effective_rate": f"{div_tax/retained:.1%}"},
            {"method": "② 자기주식 취득→양도", "tax": buyback_tax,      "after": buyback_after, "effective_rate": f"{buyback_tax/retained:.1%}"},
            {"method": "③ 자본전입",       "tax": capital_transfer_tax, "after": 0,            "effective_rate": f"{capital_transfer_tax/retained:.1%}"},
            {"method": "④ 이익소각",       "tax": cancellation_tax,  "after": 0,              "effective_rate": f"{cancellation_tax/retained:.1%}"},
        ]
        best = min(methods, key=lambda m: m["tax"])

        return {
            "agent": "RetainedEarningsManagementAgent",
            "text": (
                f"주주(오너) 관점: 미처분이익잉여금 {retained:,.0f}원 처리 — 최적 방안: {best['method']} (실효세율 {best['effective_rate']}).\n"
                f"법인 측면: 자기주식 취득 시 발행주식 수 감소 → 1주당 가치 상승.\n"
                f"과세관청 관점: 자기주식 소각 시 의제배당 과세 (소§17②4호) 주의.\n"
                f"금융기관 관점: 배당 시 현금 유출 → 신용등급 일시 하락 가능.\n"
                f"4방안 비교 완료. 자기주식 5종 연동 활용 권장."
            ),
            "retained_earnings": retained,
            "methods": methods,
            "recommended": best["method"],
            "require_full_4_perspective": True,
        }

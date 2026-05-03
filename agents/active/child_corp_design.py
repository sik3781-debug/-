"""자녀법인 설계 에이전트 (일감몰아주기 §45의3 적정선)"""
from __future__ import annotations


class ChildCorpDesignAgent:
    """
    자녀법인 설립 시 일감몰아주기 증여 의제 회피 설계.
    상증§45의3: 특수관계법인 거래비율 30% 초과 + 주주 지분 3% 이상 시 과세.
    """

    TRANSACTION_SAFE_HARBOR = 0.30  # 30% 이하 시 과세 없음
    SHAREHOLDER_THRESHOLD   = 0.03  # 3% 이상 주주 대상

    def analyze(self, company_data: dict) -> dict:
        child_revenue = company_data.get("child_corp_revenue", 0)
        parent_supply = company_data.get("supply_from_parent", 0)
        child_shares  = company_data.get("owner_child_shares_pct", 0.50)

        ratio = parent_supply / child_revenue if child_revenue else 0
        safe  = ratio <= self.TRANSACTION_SAFE_HARBOR or child_shares < self.SHAREHOLDER_THRESHOLD
        tax_base = max(0, ratio - self.TRANSACTION_SAFE_HARBOR) * child_revenue * child_shares

        scenarios = [
            {"name": "안전항 이하", "supply_pct": 0.25, "gift_tax": 0, "note": "거래비율 25% — 과세 없음"},
            {"name": "임계점",      "supply_pct": 0.30, "gift_tax": 0, "note": "30% 기준선"},
            {"name": "초과",        "supply_pct": 0.50, "gift_tax": int(tax_base * 0.40 * 0.10), "note": "40% 초과분 의제증여"},
        ]

        return {
            "agent": "ChildCorpDesignAgent",
            "text": (
                f"주주(오너) 관점: 자녀법인 설립 후 일감몰아주기 거래비율 {ratio:.0%} — {'과세 없음' if safe else '증여 의제 과세 위험'}.\n"
                f"법인 측면: 자녀법인 매출 중 모법인 공급 비율 30% 이하 유지 필수.\n"
                f"과세관청 관점: 상증§45의3 — 거래비율 30% 초과 + 지분 3% 이상 시 의제증여 과세.\n"
                f"금융기관 관점: 자녀법인 독립 신용 구축으로 모법인 연대보증 최소화.\n"
                f"안전 설계 권고: 거래비율 25% 이하 유지."
            ),
            "current_ratio": ratio,
            "is_safe": safe,
            "scenarios": scenarios,
            "require_full_4_perspective": True,
        }

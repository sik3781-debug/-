"""상증§45의5 특수관계법인 거래 회피 설계 에이전트"""
from __future__ import annotations


CLAUSES = {
    "가목": {"desc": "무상·저가 제공", "risk": "시가와 대가 차액 증여의제", "threshold_pct": 0.30},
    "나목": {"desc": "고가 양도·취득", "risk": "시가 초과금액 증여의제", "threshold_pct": 0.30},
    "다목": {"desc": "채무 면제·인수·변제", "risk": "면제금액 증여의제", "threshold_pct": 0},
    "라목": {"desc": "출자 평가증", "risk": "이익 기여 비율만큼 증여의제", "threshold_pct": 0},
    "마목": {"desc": "합병·분할 이익", "risk": "합병비율 불공정 시 증여의제", "threshold_pct": 0},
}


class SpecialCorpTransactionAgent:
    def analyze(self, company_data: dict) -> dict:
        transaction_type = company_data.get("transaction_type", "가목")
        transaction_amt  = company_data.get("transaction_amount", 0)
        market_price     = company_data.get("market_price", 0)
        clause = CLAUSES.get(transaction_type, CLAUSES["가목"])

        # 가목·나목: 시가 ±30% 안전항
        safe_max = market_price * (1 + clause["threshold_pct"])
        safe_min = market_price * (1 - clause["threshold_pct"]) if clause["threshold_pct"] else market_price
        is_safe  = safe_min <= transaction_amt <= safe_max if clause["threshold_pct"] else True
        deemed_gift = max(0, abs(transaction_amt - market_price) - market_price * clause["threshold_pct"])

        scenarios = [
            {"name": "안전항 이내",  "amount": safe_min, "tax": 0, "note": "시가 ±30% 이내"},
            {"name": "시가 거래",    "amount": market_price, "tax": 0, "note": "시가 정확히 일치"},
            {"name": "안전항 초과",  "amount": transaction_amt, "tax": int(deemed_gift * 0.30), "note": f"초과분 {deemed_gift:,.0f}원 증여세"},
        ]

        return {
            "agent": "SpecialCorpTransactionAgent",
            "text": (
                f"과세관청 관점: 상증§45의5 {transaction_type} ({clause['desc']}) — {clause['risk']}.\n"
                f"법인 측면: 시가 {market_price:,.0f}원 기준 안전항 {clause['threshold_pct']:.0%} 이내 거래 설계.\n"
                f"주주(오너) 관점: 안전항 초과 시 의제증여 {deemed_gift:,.0f}원 — 증여세 약 {deemed_gift*0.30:,.0f}원.\n"
                f"금융기관 관점: 특수관계 거래 공시 의무 — 신용등급 영향 검토.\n"
                f"현재 거래 {'안전' if is_safe else '위험'}: 시나리오 3종 제시."
            ),
            "clause": transaction_type,
            "is_safe": is_safe,
            "deemed_gift": deemed_gift,
            "scenarios": scenarios,
            "require_full_4_perspective": True,
        }

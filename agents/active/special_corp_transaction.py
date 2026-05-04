"""상증§45의5 특수관계법인 거래 회피 설계 에이전트 — 4단계 워크플로우"""
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
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "SpecialCorpTransactionAgent",
            "strategy": strategy,
            "risks":    risks,
            "hedges":   hedges,
            "process":  process,
            "post":     post,
            "matrix_12cells": self._build_4party_3time_matrix(strategy, risks, hedges, process, post),
            "agent": "SpecialCorpTransactionAgent",
            "text": strategy["text"],
            "require_full_4_perspective": True,
        }

    # ── ① 전략생성 ────────────────────────────────────────────

    def generate_strategy(self, case: dict) -> dict:
        transaction_type = case.get("transaction_type", "가목")
        transaction_amt  = case.get("transaction_amount", 0)
        market_price     = case.get("market_price", 0)
        clause = CLAUSES.get(transaction_type, CLAUSES["가목"])

        safe_max = market_price * (1 + clause["threshold_pct"])
        safe_min = market_price * (1 - clause["threshold_pct"]) if clause["threshold_pct"] else market_price
        is_safe  = safe_min <= transaction_amt <= safe_max if clause["threshold_pct"] else True
        deemed_gift = max(0, abs(transaction_amt - market_price) - market_price * clause["threshold_pct"])

        scenarios = [
            {"name": "안전항 이내",  "amount": safe_min, "tax": 0, "note": "시가 ±30% 이내"},
            {"name": "시가 거래",    "amount": market_price, "tax": 0, "note": "시가 정확히 일치"},
            {"name": "안전항 초과",  "amount": transaction_amt, "tax": int(deemed_gift * 0.30), "note": f"초과분 {deemed_gift:,.0f}원 증여세"},
        ]
        text = (
            f"과세관청 관점: 상증§45의5 {transaction_type} ({clause['desc']}) — {clause['risk']}.\n"
            f"법인 측면: 시가 {market_price:,.0f}원 기준 안전항 {clause['threshold_pct']:.0%} 이내 거래 설계.\n"
            f"주주(오너) 관점: 안전항 초과 시 의제증여 {deemed_gift:,.0f}원 — 증여세 약 {deemed_gift*0.30:,.0f}원.\n"
            f"금융기관 관점: 특수관계 거래 공시 의무 — 신용등급 영향 검토.\n"
            f"현재 거래 {'안전' if is_safe else '위험'}: 시나리오 3종 제시."
        )
        return {
            "clause_key": transaction_type,
            "clause":     clause,
            "transaction_amt": transaction_amt,
            "market_price":    market_price,
            "is_safe":         is_safe,
            "deemed_gift":     deemed_gift,
            "scenarios":       scenarios,
            "text":            text,
        }

    # ── ② 5축 리스크 검증 ─────────────────────────────────────

    def validate_risk_5axis(self, strategy: dict) -> dict:
        dg  = strategy["deemed_gift"]
        mp  = strategy["market_price"]
        axes = {
            "DOMAIN": {"pass": mp > 0, "detail": f"시가 {mp:,.0f}원 — 상증§60 시가 원칙 적용"},
            "LEGAL":  {"pass": True,   "detail": f"상증§45의5 {strategy['clause_key']} ({strategy['clause']['desc']}) 법령 인용"},
            "CALC":   {"pass": dg >= 0, "detail": f"증여의제 {dg:,.0f}원 — 안전항 초과분 계산"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) == 3, "detail": "3가지 시나리오 (안전항/시가/초과) 제시"},
            "CROSS":  {"pass": True, "detail": "4자관점(과세관청·법인·주주·금융기관) × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    # ── ② 4단계 헷지 ─────────────────────────────────────────

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        safe = strategy["is_safe"]
        return {
            "1_pre": [
                f"상증§60·§61 시가 산정 — {'안전항 이내 확인' if safe else '시가 조정 필요'}",
                "이사회 결의서 + 계약서 시가 근거 첨부",
                "특수관계 거래 법인세 조정계산서 준비 (법§52 부당행위계산)",
            ],
            "2_now": [
                f"거래가액 {strategy['transaction_amt']:,.0f}원 — 안전항 {'준수' if safe else '위반: 조정 필요'}",
                "대금 실제 이전 + 계약서 보관 (증빙 완비)",
                "법§52 부당행위계산 부인 여부 세무사 사전 검토",
            ],
            "3_post": [
                "증여세 신고 (3개월 이내) — 가산세 회피",
                f"법인세 조정계산서: {strategy['clause_key']} 거래 명세 반영",
                "차기 거래 시 동일 조항 재적용 여부 재점검",
            ],
            "4_worst": [
                f"의제증여 {strategy['deemed_gift']:,.0f}원 발생 시 수혜 법인 지분율 비례 부담",
                "세무조사 시 시가 이의 → 감정평가 vs 국세청 기준 분쟁 대응 준비",
                "다목(채무인수)·라목(출자평가증)은 안전항 없음 — 별도 법률 검토 필수",
            ],
        }

    # ── ③ 과정관리 ────────────────────────────────────────────

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "시가 산정 근거 확보", "law": "상증§60·§61"},
            "step2": {"action": f"거래가액 설계 — {strategy['scenarios'][0]['name']} 적용", "target": strategy["scenarios"][0]["amount"]},
            "step3": {"action": "계약서 작성·대금 이전·이사회 기록"},
            "step4": {"action": "증여세 신고 (해당 시)", "deadline": "3개월 이내"},
            "hedge_applied": hedges["2_now"],
        }

    # ── ④ 사후관리 ────────────────────────────────────────────

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["유사 거래 반복 시 누계 의제금액 합산 여부 점검", "법인세 조정계산서 연도별 추적"],
            "reporting":  {"세무신고": "증여세 (3개월)", "법인세": "법§52 부당행위계산 조정"},
            "next_review": "6개월 후 지분율 변동·동종 거래 추가 여부 재점검",
        }

    # ── 4자×3시점 12셀 ──────────────────────────────────────

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        mp = strategy["market_price"]
        dg = strategy["deemed_gift"]
        return {
            "법인":       {"사전": f"상증§45의5 {strategy['clause_key']} 해당 여부 사전 확인", "현재": f"시가({mp:,.0f}원) 기준 거래 설계·계약 체결", "사후": "법§52 부당행위계산 조정계산서 반영"},
            "주주(오너)": {"사전": "안전항(±30%) 이내 거래가액 계획", "현재": f"의제증여 {'0원 (안전항 이내)' if dg==0 else f'{dg:,.0f}원 발생'}", "사후": "증여세 납부 스케줄 + 10년 합산 관리"},
            "과세관청":   {"사전": "상증§60·§61 시가 산정 근거 확보", "현재": "§45의5 과세 요건(30% 안전항) 적합성 판단", "사후": "세무조사 대비 계약서·대금 이전 증빙 10년 보관"},
            "금융기관":   {"사전": "특수관계 거래 공시 의무 검토", "현재": "거래 실질·대가 수수 — 신용평가 영향 최소화", "사후": "과세 후 현금흐름 변동 대출 약정 재무비율 모니터링"},
        }

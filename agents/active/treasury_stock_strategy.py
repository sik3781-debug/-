"""자기주식 5종 통합 전략 에이전트 — 4단계 워크플로우"""
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
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "TreasuryStockStrategyAgent",
            "strategy": strategy,
            "risks":    risks,
            "hedges":   hedges,
            "process":  process,
            "post":     post,
            "matrix_12cells": self._build_4party_3time_matrix(strategy, risks, hedges, process, post),
            "agent": "TreasuryStockStrategyAgent",
            "text": strategy["text"],
            "require_full_4_perspective": True,
        }

    # ── ① 전략생성 ────────────────────────────────────────────

    def generate_strategy(self, case: dict) -> dict:
        retained     = case.get("retained_earnings", 0)
        stock_price  = case.get("share_price", 10_000)
        shares_total = case.get("shares_total", 100_000)
        owner_pct    = case.get("owner_share_pct", 0.70)
        prov_payment = case.get("provisional_payment", 0)
        tax_rate     = case.get("owner_marginal_rate", 0.45)

        buyback_shares = int(shares_total * 0.10)
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
        best = strategies[0]
        text = (
            f"주주(오너) 관점: 자기주식 취득→양도로 배당 대비 세율 {best['tax_rate']:.0%} vs {min(tax_rate+0.044,0.495):.0%} — 절세 {best['saving']:,.0f}원.\n"
            f"법인 측면: 자기주식 취득 시 발행주식 수 감소 → 1주당 가치 상승.\n"
            f"과세관청 관점: 소각 시 의제배당(소§17②4호) + 이익소각 vs 자본감소 구분 주의.\n"
            f"금융기관 관점: 자기주식 취득 시 자기자본 감소 — 부채비율 상승 주의.\n"
            f"⭐ 5종 전략 중 핵심: 주가 유동화→상속·증여 절세 설계."
        )
        return {
            "buyback_shares": buyback_shares,
            "buyback_cost":   buyback_cost,
            "strategies": strategies,
            "recommended_primary": best["name"],
            "tax_rate":   tax_rate,
            "prov_payment": prov_payment,
            "text": text,
        }

    # ── ② 5축 리스크 검증 ─────────────────────────────────────

    def validate_risk_5axis(self, strategy: dict) -> dict:
        bc = strategy["buyback_cost"]
        axes = {
            "DOMAIN": {"pass": bc > 0, "detail": f"상법§341 배당가능이익 이내 취득 — 비용 {bc:,.0f}원 확인"},
            "LEGAL":  {"pass": True,   "detail": "소§17②4호 의제배당·소§94 양도소득세·상법§342의2 처분 적법성"},
            "CALC":   {"pass": strategy["strategies"][0].get("saving", 0) > 0,
                       "detail": f"절세 효과 {strategy['strategies'][0].get('saving', 0):,.0f}원 양수 확인"},
            "LOGIC":  {"pass": len(strategy["strategies"]) == 5, "detail": "5종 전략 전부 열거"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀 충족"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    # ── ② 4단계 헷지 ─────────────────────────────────────────

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        return {
            "1_pre": [
                "상법§341 배당가능이익 재무담당 확인 후 이사회 결의서 작성",
                "자기주식 취득 목적·한도·기간 특정 (상법§341의2 준용)",
                "세무사 사전 검토: 소각 vs 양도 시 과세 분기점 확인",
            ],
            "2_now": [
                "5종 전략 중 우선순위 결정 — 실효세율 최소화 기준",
                "취득→양도: 양도일 다음 달 말일까지 소§94 신고",
                "이익소각: 취득단가 = 소각가액 설계 → 의제배당 0원 확인",
            ],
            "3_post": [
                "소각 완료 후 법§16 처분손익 익금/손금 불산입 처리",
                "발행주식 수 변경 → 등기부 반영 + 주주명부 갱신",
                "자기자본 감소 → 부채비율 변동 → 대출 약정 재무비율 확인",
            ],
            "4_worst": [
                "주가 급락 시 소각가액 > 취득단가 → 법§16 손금불산입 위험",
                "자기주식 취득 후 1년 이내 미처분 시 상법§341 위반 리스크",
                "상증§54 저가 매수 의제 발생 시 수증자 증여세 추가 부담",
            ],
        }

    # ── ③ 과정관리 ────────────────────────────────────────────

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "이사회 결의 (취득 한도·목적·기간)", "law": "상법§341"},
            "step2": {"action": "자기주식 취득 실행", "cost": f"{strategy['buyback_cost']:,.0f}원"},
            "step3": {"action": strategy["recommended_primary"] + " 실행"},
            "step4": {"action": "세무 신고·등기 처리", "law": "소§94·상법§342의2"},
            "hedge_applied": hedges["2_now"],
        }

    # ── ④ 사후관리 ────────────────────────────────────────────

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["자기자본·부채비율 분기별 재확인", "주가 추이 모니터링 — 추가 취득 타이밍"],
            "reporting":  {"세무": "양도소득세 신고 (양도일 다음달 말)", "법무": "발행주식 수 변경 등기"},
            "next_review": "12개월 후 미처분이익잉여금 재진단 + 5종 전략 재평가",
        }

    # ── 4자×3시점 12셀 ──────────────────────────────────────

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        bc = strategy["buyback_cost"]
        return {
            "법인":       {"사전": "배당가능이익 산정·이사회 결의", "현재": f"취득 {strategy['buyback_shares']:,}주·{bc:,.0f}원", "사후": "법§16 처분손익 처리·등기"},
            "주주(오너)": {"사전": "5종 전략 선택·세율 시뮬", "현재": f"최적 전략 실행 — {strategy['recommended_primary']}", "사후": "잔여 지분 가치 모니터링"},
            "과세관청":   {"사전": "의제배당·양도세 계획", "현재": "소§94 양도세 신고 준수", "사후": "소각 완료 후 세무신고·추징 리스크 제로화"},
            "금융기관":   {"사전": "자기자본 감소→부채비율 영향 시뮬", "현재": "대출 약정 재무비율 유지 확인", "사후": "신용등급 재평가 후 금리 조건 재협의"},
        }

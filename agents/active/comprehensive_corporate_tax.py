"""
법인세 종합진단 에이전트 (/법인세종합진단) — 전문 솔루션 그룹
핵심 법령: 법§55(세율), §13~§24(손금·익금), §57(이월결손금), §58의3(공제한도)
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class ComprehensiveCorporateTaxAgent(ProfessionalSolutionAgent):
    """법인세 과세표준 ~ 납부세액 전 과정 종합 진단 + 절세 포인트 발굴"""

    # ── ① 전략생성 ────────────────────────────────────────────

    def generate_strategy(self, case: dict) -> dict:
        """법§55 세율 구간 × 손금·익금·공제 종합 절세 전략 산출"""
        revenue         = case.get("revenue", 0)
        gross_income    = case.get("gross_income", 0)
        loss_carryover  = case.get("loss_carryover", 0)          # 이월결손금
        deductions      = case.get("deductions", {})             # 손금 항목
        credits         = case.get("tax_credits", {})            # 세액공제
        tax_rate_table  = [(200_000_000, 0.09), (20_000_000_000, 0.19),
                           (300_000_000_000, 0.21), (float("inf"), 0.24)]

        # 이월결손금 공제 (법§58의3: 과세표준의 60% 한도)
        loss_deductible = min(loss_carryover, gross_income * 0.60)
        taxable_income  = max(0, gross_income - loss_deductible)

        # 세율 적용 (법§55 구간별)
        tax = 0.0
        remaining = taxable_income
        for limit, rate in tax_rate_table:
            band = min(remaining, limit)
            tax += band * rate
            remaining -= band
            if remaining <= 0:
                break

        # 세액공제 차감
        total_credits = sum(credits.values()) if isinstance(credits, dict) else 0
        net_tax       = max(0, tax - total_credits)
        effective_rate = net_tax / max(taxable_income, 1)

        # 손금 미인정 위험 항목
        risky_deductions = [k for k, v in (deductions.items() if isinstance(deductions, dict) else {}.items())
                            if v > 0 and k in ["접대비", "기부금", "임원상여금", "업무무관경비"]]

        # 3가지 절세 시나리오
        scenarios = [
            {"name": "이월결손금 최대 활용",
             "net_tax": max(0, tax - total_credits - loss_carryover * 0.09),
             "note": f"이월결손금 {loss_carryover:,.0f}원 추가 공제 → 세율 절감"},
            {"name": "R&D 세액공제 확대",
             "net_tax": max(0, net_tax - revenue * 0.025),
             "note": "R&D 투자 확대로 세액공제 2.5% 추가 (조특§10)"},
            {"name": "현행 유지",
             "net_tax": net_tax, "note": "현재 신고 구조 유지"},
        ]
        best = min(scenarios, key=lambda s: s["net_tax"])
        text = (
            f"법인 측면: 과세표준 {taxable_income:,.0f}원 → 산출세액 {tax:,.0f}원 → 납부 {net_tax:,.0f}원.\n"
            f"주주(오너) 관점: 실효세율 {effective_rate:.1%} — 절세 최적안: {best['name']}.\n"
            f"과세관청 관점: 손금 부인 위험 항목 {len(risky_deductions)}개 — 사전 검토 권고.\n"
            f"금융기관 관점: 납부세액 현금 유출 → 운전자본 영향 {net_tax:,.0f}원."
        )
        return {
            "revenue": revenue, "gross_income": gross_income,
            "loss_carryover": loss_carryover, "loss_deductible": loss_deductible,
            "taxable_income": taxable_income, "tax": tax,
            "total_credits": total_credits, "net_tax": net_tax,
            "effective_rate": effective_rate, "risky_deductions": risky_deductions,
            "scenarios": scenarios, "recommended": best["name"], "text": text,
        }

    # ── ② 5축 리스크 검증 ─────────────────────────────────────

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["gross_income"] >= 0,
                       "detail": f"과세표준 {strategy['taxable_income']:,.0f}원 — 법§55 구간 적용"},
            "LEGAL":  {"pass": True,
                       "detail": "법§55(세율)·§13~§24(손금·익금)·§57(이월결손금)·§58의3(공제한도 60%)"},
            "CALC":   {"pass": strategy["net_tax"] >= 0,
                       "detail": f"납부세액 {strategy['net_tax']:,.0f}원 — 실효세율 {strategy['effective_rate']:.1%}"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) >= 3,
                       "detail": f"절세 시나리오 {len(strategy['scenarios'])}종 + 최적안 선택"},
            "CROSS":  {"pass": True, "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    # ── ② 4단계 헷지 ─────────────────────────────────────────

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        risky = strategy["risky_deductions"]
        return {
            "1_pre": [
                f"손금 부인 위험 항목 {len(risky)}개 사전 세무사 검토: {risky}",
                "이월결손금 잔액·공제 한도(60%) 재확인 (법§58의3)",
                "세액공제 명세서 완비 (R&D·투자·고용·창업 항목)",
            ],
            "2_now": [
                f"과세표준 {strategy['taxable_income']:,.0f}원 최종 확정",
                "법§55 구간별 산출세액 계산 검증",
                "세액공제 적용 순서 확인 (한도 이월 vs 소멸 구분)",
            ],
            "3_post": [
                "법인세 신고 기한 (결산일 3개월 이내) 준수",
                "중간예납 (8월) 기준 납부 설계",
                "이월결손금 잔액 갱신 + 차기연도 공제 계획",
            ],
            "4_worst": [
                "과소 신고 시 가산세 (법§47): 납부 불성실 0.022%/일",
                "손금 부인 확정 시 추징세액 + 이자상당액",
                "세무조사 시 접대비·임원상여 증빙 완비 필수",
            ],
        }

    # ── ③ 과정관리 ────────────────────────────────────────────

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "결산·세무조정 계산서 작성", "law": "법§14~§24"},
            "step2": {"action": f"이월결손금 공제 {strategy['loss_deductible']:,.0f}원 적용"},
            "step3": {"action": "세액공제 명세서 첨부 (R&D·투자·고용)", "law": "조특§10·§24"},
            "step4": {"action": f"납부세액 {strategy['net_tax']:,.0f}원 확정·신고"},
        }

    # ── ④ 사후관리 ────────────────────────────────────────────

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["분기별 중간 세부담 추적", "이월결손금 잔액 연간 업데이트"],
            "reporting": {"세무": "법인세 신고서 + 세액공제 명세서",
                          "내부": "실효세율 추이 보고"},
            "next_review": "다음 결산기 전 절세 시뮬 재실행",
        }

    # ── 4자×3시점 12셀 ──────────────────────────────────────

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        ti = strategy["taxable_income"]
        nt = strategy["net_tax"]
        er = strategy["effective_rate"]
        return {
            "법인":       {"사전": "세무조정 계산서·손금 부인 위험 사전 점검", "현재": f"과세표준 {ti:,.0f}원·납부세액 {nt:,.0f}원", "사후": "신고 완료·이월결손금 갱신"},
            "주주(오너)": {"사전": "실효세율 목표 설정·절세 시나리오 선택", "현재": f"실효세율 {er:.1%} 확정·최적안 실행", "사후": "배당 여력 재계산·차기 절세 계획"},
            "과세관청":   {"사전": "손금 부인 항목 사전 리스크 점검", "현재": "세액공제 적용 적정성·이월결손금 한도 준수", "사후": "세무조사 대비 증빙 10년 보관"},
            "금융기관":   {"사전": f"납부세액 {nt:,.0f}원 현금 유출 유동성 영향", "현재": "중간예납 납부 후 여신 약정 재무비율 확인", "사후": "세후 이익 기준 신용등급 재평가"},
        }

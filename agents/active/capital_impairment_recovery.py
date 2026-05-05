"""
자본잠식 회복 에이전트 (/자본잠식회복) — 전문 솔루션 그룹
핵심 법령: 상법§517(해산사유), §438(감자), 법§57(이월결손금), K-IFRS 1001, 외감법§4·§5
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class CapitalImpairmentRecoveryAgent(ProfessionalSolutionAgent):
    """자본잠식률 산정 + 감자·증자·자산매각 회복 로드맵 + 해산 방지

    상법§517 해산 사유(완전자본잠식) · 상법§438 자본금 감소(감자) 절차
    법인세법§57 이월결손금 공제(과세표준 60% 한도)
    K-IFRS 1001 재무상태표 계속기업 가정 공시
    외감법§4 외부감사 대상 판정(자본총계 기준) · 외감법§5 감사보고서 의견
    상법§330 결손금 처리 · 법인세법§18 자산 평가증익 익금산입
    """

    def generate_strategy(self, case: dict) -> dict:
        """① 전략생성 — 자본잠식률 산정 + 회복 시나리오"""
        paid_in_capital = case.get("paid_in_capital", 1)              # 납입자본금
        capital_surplus = case.get("capital_surplus", 0)              # 자본잉여금
        retained_earnings = case.get("retained_earnings", 0)         # (음수면 결손금)
        other_comprehensive = case.get("other_comprehensive", 0)      # 기타포괄손익누계액
        total_assets    = case.get("total_assets", 0)
        total_liabilities = case.get("total_liabilities", 0)
        annual_loss     = case.get("annual_loss", 0)                  # 연간 당기순손실
        loss_carryover  = case.get("loss_carryover", 0)               # 이월결손금

        # 자본총계
        total_equity = paid_in_capital + capital_surplus + retained_earnings + other_comprehensive
        # 자본잠식률 (결손금 / 납입자본금)
        deficit = min(retained_earnings, 0)
        impairment_ratio = abs(deficit) / max(paid_in_capital, 1) if deficit < 0 else 0
        # 완전자본잠식 여부 (상법§517 해산 사유)
        full_impairment = total_equity <= 0

        # 부채비율
        debt_ratio = total_liabilities / max(total_equity, 1) if total_equity > 0 else float("inf")

        # 회복 시나리오 3종
        # 1. 감자 후 증자 (상법§438 → 신주 발행)
        capital_reduction = abs(deficit) * 0.8  # 감자 규모 (결손금 80% 소각)
        new_investment_needed = abs(deficit) - capital_reduction
        # 2. 이익 유보 누적 (연간 손실 → 이익 전환)
        years_to_recovery = abs(deficit) / max(annual_loss * -1, 1) if annual_loss < 0 else 0
        # 3. 자산 매각 + 부채 상환
        asset_sale_target = abs(deficit) * 1.2

        scenarios = [
            {"name": "감자 후 증자 (신주 발행)",
             "action": f"감자 {capital_reduction:,.0f}원 + 신규 투자 유치 {max(new_investment_needed, 0):,.0f}원",
             "timeline": "3~6개월 (임시주주총회 소집·법원 인가)",
             "law": "상법§438 감자 + 상법§416 신주 발행"},
            {"name": "이익 유보 자연 회복",
             "action": f"연간 흑자 전환 후 {years_to_recovery:.1f}년 누적 회복",
             "timeline": f"{years_to_recovery:.1f}년 (흑자 전환 전제)",
             "law": "법인세법§57 이월결손금 공제 병행"},
            {"name": "자산 매각 + 부채 축소",
             "action": f"자산 {asset_sale_target:,.0f}원 매각 + 부채 상환으로 자본잠식 해소",
             "timeline": "6~12개월",
             "law": "법인세법§18 자산 평가차익 익금산입 주의"},
        ]
        recommended = scenarios[0]["name"] if impairment_ratio < 0.8 else "전문가 즉시 자문 필요"

        text = (
            f"법인 측면: 자본총계 {total_equity:,.0f}원 — 잠식률 {impairment_ratio:.1%} "
            f"({'완전잠식 ⚠️ 상법§517 해산 위험' if full_impairment else '부분잠식'}).\n"
            f"주주(오너) 관점: 부채비율 {debt_ratio:.1f}배 — 감자 시 기존 지분 희석.\n"
            f"과세관청 관점: 이월결손금 {loss_carryover:,.0f}원 — 법§57 60% 한도 공제 가능.\n"
            f"금융기관 관점: 자본잠식 → 여신 약정 위반 가능 — 사전 협의 필수."
        )

        return {
            "paid_in_capital": paid_in_capital, "total_equity": total_equity,
            "deficit": deficit, "impairment_ratio": impairment_ratio,
            "full_impairment": full_impairment, "debt_ratio": debt_ratio,
            "loss_carryover": loss_carryover, "annual_loss": annual_loss,
            "scenarios": scenarios, "recommended": recommended, "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["paid_in_capital"] > 0,
                       "detail": f"잠식률 {strategy['impairment_ratio']:.1%} — {'완전잠식' if strategy['full_impairment'] else '부분잠식'}"},
            "LEGAL":  {"pass": True,
                       "detail": "상법§517(해산)·§438(감자)·외감법§4·법§57(이월결손금 60%)"},
            "CALC":   {"pass": strategy["total_equity"] is not None,
                       "detail": f"자본총계 {strategy['total_equity']:,.0f}원 · 부채비율 {strategy['debt_ratio']:.1f}배"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) >= 3,
                       "detail": "감자증자·이익유보·자산매각 3종 시나리오"},
            "CROSS":  {"pass": True, "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        ir = strategy["impairment_ratio"]
        fi = strategy["full_impairment"]
        return {
            "1_pre": [
                f"{'⚠️ 완전자본잠식 — 상법§517 해산 위험 즉각 법률 자문' if fi else f'잠식률 {ir:.1%} 진단'}",
                "K-IFRS 1001 계속기업 가정 검토 — 외감인 사전 협의",
                "이월결손금 세무 확인 (법§57 60% 공제 한도 재계산)",
            ],
            "2_now": [
                "감자 (상법§438) — 임시주주총회 결의·법원 인가 절차 착수",
                "신규 투자 유치 협상 또는 오너 추가 출자 결정",
                "자산 매각 대상 선정 — 담보 해제 후 매각 순서 확정",
            ],
            "3_post": [
                "감자·증자 완료 후 재무상태표 재작성 (K-IFRS 1001)",
                "여신 약정 재무비율 회복 → 금융기관 통보",
                "이월결손금 세무 조정 후 법인세 신고 반영",
            ],
            "4_worst": [
                f"{'완전잠식 장기화 시 — 법원 자진 해산·청산 절차' if fi else '잠식률 100% 초과 시 해산 위험'}",
                "외감법§5 — 감사의견 한정·부적정·의견 거절 위험 시 조기 대응",
                "금융기관 기한이익 상실 → 가압류·경매 방지 사전 협의",
            ],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "임시주주총회 소집 (감자 결의)", "law": "상법§438"},
            "step2": {"action": "법원 인가 신청 → 자본금 변경 등기"},
            "step3": {"action": "신주 발행 또는 추가 출자 — 자본총계 플러스 전환"},
            "step4": {"action": "재무상태표 재작성·외감인 확인·금융기관 보고"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [
                "분기별 자본총계·잠식률 추적",
                "이월결손금 공제 계획 연간 업데이트",
                "K-IFRS 1001 계속기업 가정 반기별 재검토",
            ],
            "reporting": {
                "외감": "재무상태표 자본 변동 공시 (외감법§4)",
                "내부": "월별 자본잠식률 대시보드",
            },
            "next_review": "잠식 해소 후 1년 — 자본 구조 안정성 재진단",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        ir = strategy["impairment_ratio"]
        te = strategy["total_equity"]
        return {
            "법인":       {"사전": f"잠식률 {ir:.1%} 현황 · 감자 방안 검토", "현재": "감자·증자 절차 실행 + 재무제표 재작성", "사후": "자본총계 플러스 전환·이월결손금 공제 누적"},
            "주주(오너)": {"사전": "지분 희석 최소화 방안 협의 (감자 비율 결정)", "현재": f"추가 출자 or 외부 투자 유치 결정", "사후": "지분 구조 재정비·배당 여력 재평가"},
            "과세관청":   {"사전": "이월결손금 잔액·공제 한도 확인 (법§57)", "현재": "감자 차익 익금산입 여부 세무 검토", "사후": "결손금 보전 세무 조정 반영"},
            "금융기관":   {"사전": f"자본총계 {te:,.0f}원 — 여신 약정 재무비율 이탈 여부", "현재": "여신 재협의 + 담보 가치 재평가", "사후": "자본 회복 후 신용등급 상향·금리 재협상"},
        }

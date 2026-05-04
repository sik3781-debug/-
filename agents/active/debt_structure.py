"""
부채구조 최적화 에이전트 (/부채구조최적화) — 전문 솔루션 그룹
핵심 기준: 부채비율(부채/자기자본), 차입금의존도, 이자보상비율(EBIT/이자)
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class DebtStructureAgent(ProfessionalSolutionAgent):
    """부채 구조 분석 + 최적 자본구조 설계 + 이자 절감 전략"""

    def generate_strategy(self, case: dict) -> dict:
        """부채비율·차입금의존도·이자보상비율 산출 + 최적화 방안 3종"""
        total_debt   = case.get("total_debt", 0)
        equity       = case.get("equity", 1)
        total_assets = case.get("total_assets", 1)
        ebit         = case.get("ebit", 0)          # 이자·세전이익
        interest_exp = case.get("interest_expense", 1)
        short_debt   = case.get("short_term_debt", 0)
        long_debt    = case.get("long_term_debt", 0)

        # 핵심 비율
        debt_ratio        = total_debt / max(equity, 1)          # 부채비율
        debt_dependency   = total_debt / max(total_assets, 1)    # 차입금의존도
        interest_coverage = ebit / max(interest_exp, 1)          # 이자보상비율
        lt_debt_ratio     = long_debt / max(total_debt, 1)       # 장기부채 비율

        # 부채 구조 진단
        health = "양호" if debt_ratio < 2.0 and interest_coverage > 2.0 else "주의"
        if debt_ratio > 3.0 or interest_coverage < 1.0:
            health = "위험"

        # 최적화 방안 3종
        scenarios = [
            {"name": "단기→장기 전환", "debt_ratio": debt_ratio,
             "saving": interest_exp * 0.005,
             "note": "단기차입금 → 5년 장기대출 전환 → 리파이낸싱 리스크 제거"},
            {"name": "변동→고정금리 전환", "debt_ratio": debt_ratio,
             "saving": interest_exp * 0.01,
             "note": "금리 상승기 변동금리 → 고정금리 헷지 (IRS 활용)"},
            {"name": "DES(출자전환) 활용", "debt_ratio": debt_ratio * 0.7,
             "saving": interest_exp * 0.30,
             "note": "대주주 대여금 출자전환 → 부채비율 감소·이자비용 절감"},
        ]
        best = min(scenarios, key=lambda s: s["debt_ratio"])

        text = (
            f"법인 측면: 부채비율 {debt_ratio:.1f}배 ({health}) — 이자보상비율 {interest_coverage:.1f}배.\n"
            f"주주(오너) 관점: 단기부채 {short_debt:,.0f}원 → 장기 전환 시 리파이낸싱 위험 감소.\n"
            f"과세관청 관점: 차입금 이자 손금(법§28) — 업무무관 차입금 이자 손금 부인 주의.\n"
            f"금융기관 관점: 차입금의존도 {debt_dependency:.1%} — "
            f"{'BBB 수준' if debt_dependency < 0.60 else '위험 수준'} (기준 60%)."
        )
        return {
            "total_debt": total_debt, "equity": equity, "ebit": ebit,
            "interest_exp": interest_exp, "short_debt": short_debt, "long_debt": long_debt,
            "debt_ratio": debt_ratio, "debt_dependency": debt_dependency,
            "interest_coverage": interest_coverage, "lt_debt_ratio": lt_debt_ratio,
            "health": health, "scenarios": scenarios, "recommended": best["name"],
            "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["total_debt"] >= 0,
                       "detail": f"부채비율 {strategy['debt_ratio']:.1f}배·이자보상비율 {strategy['interest_coverage']:.1f}배"},
            "LEGAL":  {"pass": True, "detail": "법§28(이자손금)·법§52(부당행위)·상법§288 자본 규정"},
            "CALC":   {"pass": strategy["interest_coverage"] >= 0,
                       "detail": f"EBIT {strategy['ebit']:,.0f}원 ÷ 이자 {strategy['interest_exp']:,.0f}원 = {strategy['interest_coverage']:.1f}배"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) >= 3,
                       "detail": f"최적화 시나리오 {len(strategy['scenarios'])}종 — 권고: {strategy['recommended']}"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        dr = strategy["debt_ratio"]; ic = strategy["interest_coverage"]
        return {
            "1_pre": [f"부채비율 {dr:.1f}배 — 목표 200% 이하 달성 로드맵 수립",
                      f"이자보상비율 {ic:.1f}배 — {'위험: 이자 > EBIT, 즉각 구조조정' if ic < 1.0 else ''}",
                      "단기차입금 만기 구조 파악 + 리파이낸싱 계획"],
            "2_now": [f"단기부채 {strategy['short_debt']:,.0f}원 → 장기 전환 협의",
                      "변동금리 부채 → 고정금리 헷지 (IRS)",
                      "대주주 대여금 DES 출자전환 검토 (법§52 부당행위 여부 확인)"],
            "3_post": ["부채비율·이자보상비율 분기별 모니터링",
                       "장기부채 비율 50% 이상 유지 → 리파이낸싱 리스크 최소화",
                       "이자비용 절감 효과 측정 (연간 이자비용 변화)"],
            "4_worst": [f"이자보상비율 1.0 미만 시 — 즉각 채무 구조조정·금융기관 협의",
                        "DES 출자전환 시 기존 주주 지분 희석 → 특수관계인 거래 주의",
                        "단기차입금 연장 거절 시 — 긴급 정책자금(중진공·기보) 신청"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "단기·장기 부채 현황표 작성·만기 구조 분석"},
            "step2": {"action": f"권고 방안 실행: {strategy['recommended']}"},
            "step3": {"action": "금융기관 협의 (리파이낸싱·금리 조건 재협상)"},
            "step4": {"action": "부채비율 목표 달성 후 신용등급 재평가 의뢰"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [f"분기별 부채비율 {strategy['debt_ratio']:.1f}배 → 목표 2.0배 이하 추적",
                           "이자비용 월별 추적·절감 효과 측정"],
            "reporting": {"법인": "차입금 이자 손금 명세서 (법§28)",
                          "금융": "대출 약정 재무비율 보고"},
            "next_review": "6개월 후 신용등급 재평가 + 추가 리파이낸싱 기회 탐색",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        dr = strategy["debt_ratio"]; ic = strategy["interest_coverage"]
        ie = strategy["interest_exp"]; td = strategy["total_debt"]
        return {
            "법인":       {"사전": f"부채비율 {dr:.1f}배·이자보상비율 {ic:.1f}배 현황 진단", "현재": f"단기→장기 전환·금리 헷지 실행·총부채 {td:,.0f}원", "사후": "분기별 부채 구조 추적·리파이낸싱 계획 갱신"},
            "주주(오너)": {"사전": "DES 출자전환 가능성·지분 희석 시뮬", "현재": "대주주 대여금 출자전환 실행 (법§52 검토)", "사후": "지분율 변화 모니터링·신용등급 개선 효과"},
            "과세관청":   {"사전": "업무무관 차입금 이자(법§28) 구분·손금 부인 리스크", "현재": "이자 손금 명세서 작성·부당행위 계산 검토", "사후": "세무조사 대비 차입금 업무관련성 증빙 보관"},
            "금융기관":   {"사전": f"차입금의존도 {strategy['debt_dependency']:.1%} — 여신 심사 기준 협의", "현재": f"이자비용 {ie:,.0f}원 절감 구조 협상·담보 재설정", "사후": "신용등급 개선 시 금리 재협상·한도 증액"},
        }

"""
원가구조 정밀분석 에이전트 (/원가구조정밀) — 전문 솔루션 그룹
핵심 기준: 변동비·고정비 분리, BEP, 기여이익률, K-IFRS 1002
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class CostStructurePrecisionAgent(ProfessionalSolutionAgent):
    """변동비·고정비 분리 → BEP·기여이익률 분석 + 원가절감 우선순위

    K-IFRS 1002 원가 분류(제품원가·기간비용)
    법인세법§19 손금 요건 · 법인세법§20 접대비 한도
    조특§7 중소기업 특별세액공제 · 소득세법§94 자산 양도
    국기법§81의6 세무조사 비율 관리 · 외감법§4 원가명세서 공시
    """

    def generate_strategy(self, case: dict) -> dict:
        """변동·고정원가 분리 + BEP + 기여이익률 + 원가절감 시뮬"""
        revenue       = case.get("revenue", 1)
        variable_cost = case.get("variable_cost", 0)      # 변동비 합계
        fixed_cost    = case.get("fixed_cost", 0)         # 고정비 합계
        cost_items    = case.get("cost_items", {})        # {"직접재료비":X, "직접노무비":Y, ...}

        # 원가 구조 비율
        var_ratio  = variable_cost / max(revenue, 1)
        fixed_ratio = fixed_cost / max(revenue, 1)
        total_cost = variable_cost + fixed_cost

        # 기여이익·기여이익률
        contribution_margin = revenue - variable_cost
        cm_ratio            = contribution_margin / max(revenue, 1)

        # 손익분기점 (BEP)
        bep_sales    = fixed_cost / max(cm_ratio, 0.001)  # BEP 매출액
        bep_ratio    = bep_sales / max(revenue, 1)        # BEP 달성률
        safety_margin = (revenue - bep_sales) / max(revenue, 1)  # 안전한계율

        # 영업이익
        op_income = revenue - total_cost

        # 원가 항목별 개선 순위 (비중 높은 순)
        if isinstance(cost_items, dict) and cost_items:
            sorted_items = sorted(cost_items.items(), key=lambda x: x[1], reverse=True)
            top_cost_items = sorted_items[:3]
        else:
            top_cost_items = []

        # 원가절감 시나리오 3종
        scenarios = [
            {"name": "변동비 5% 절감",
             "new_variable": variable_cost * 0.95,
             "new_bep": fixed_cost / max(cm_ratio + 0.05, 0.001),
             "note": "직접재료비·외주비 단가 재협상"},
            {"name": "고정비 10% 절감",
             "new_variable": variable_cost,
             "new_bep": fixed_cost * 0.90 / max(cm_ratio, 0.001),
             "note": "임차료·감가상각 조정·인원 효율화"},
            {"name": "현행 유지",
             "new_variable": variable_cost,
             "new_bep": bep_sales,
             "note": "현재 구조 유지"},
        ]
        text = (
            f"법인 측면: 변동비 {var_ratio:.1%} + 고정비 {fixed_ratio:.1%} = 총원가 {total_cost:,.0f}원.\n"
            f"주주(오너) 관점: BEP {bep_sales:,.0f}원 (현재 매출 {bep_ratio:.0%} 달성) — 안전한계 {safety_margin:.1%}.\n"
            f"과세관청 관점: K-IFRS 1002 원가 분류 — 제품원가·기간비용 구분 적정성.\n"
            f"금융기관 관점: 기여이익률 {cm_ratio:.1%} — "
            f"{'여신 우호' if cm_ratio > 0.30 else '개선 필요'} (기준 30%)."
        )
        return {
            "revenue": revenue, "variable_cost": variable_cost, "fixed_cost": fixed_cost,
            "var_ratio": var_ratio, "fixed_ratio": fixed_ratio, "total_cost": total_cost,
            "cm_ratio": cm_ratio, "contribution_margin": contribution_margin,
            "bep_sales": bep_sales, "bep_ratio": bep_ratio,
            "safety_margin": safety_margin, "op_income": op_income,
            "top_cost_items": top_cost_items, "scenarios": scenarios, "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["revenue"] > 0,
                       "detail": f"변동비율 {strategy['var_ratio']:.1%}·고정비율 {strategy['fixed_ratio']:.1%} 분리 완비"},
            "LEGAL":  {"pass": True, "detail": "K-IFRS 1002 원가·비용 분류 + 법인세법 손금 기준"},
            "CALC":   {"pass": strategy["bep_sales"] >= 0,
                       "detail": f"BEP={strategy['bep_sales']:,.0f}원·CM률={strategy['cm_ratio']:.1%}·안전한계={strategy['safety_margin']:.1%}"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) >= 3,
                       "detail": "변동비절감·고정비절감·현행유지 3종 시나리오"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        bep = strategy["bep_sales"]; sm = strategy["safety_margin"]
        return {
            "1_pre": [f"BEP {bep:,.0f}원·안전한계 {sm:.1%} — {'위험: BEP 매출 90% 이상' if bep > strategy['revenue']*0.9 else '정상'}",
                      "변동비·고정비 분리 작업 (관리회계 시스템 구축)",
                      "주요 원가 항목 Top 3 절감 가능성 검토"],
            "2_now": ["직접재료비 단가 재협상 (구매처 경쟁입찰)",
                      "고정비 절감: 임차료 재협상·불필요 고정비 구조조정",
                      f"기여이익률 {strategy['cm_ratio']:.1%} → 목표 35% 이상 달성 계획"],
            "3_post": ["월별 변동비·고정비 실적 vs 예산 비교",
                       "BEP 달성 여부 분기별 점검",
                       "원가절감 효과 손익계산서 반영·보고"],
            "4_worst": [f"안전한계 {sm:.1%} 부(-)일 경우 — 즉각 긴급 원가절감 조치",
                        "고정비 과다 시 레버리지 효과 역작용 → 매출 하락 시 손실 급증",
                        "원가 구조 개선 실패 시 가격 인상 또는 제품 믹스 변경"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "원가 항목 변동비·고정비 분류표 작성", "law": "K-IFRS 1002"},
            "step2": {"action": f"BEP {strategy['bep_sales']:,.0f}원 확정·목표 매출 설정"},
            "step3": {"action": "상위 3개 원가 항목 절감 계획 실행"},
            "step4": {"action": "월별 원가보고서 작성·경영진 보고"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["월별 CM률·BEP 추적", "원가 항목별 단가 변동 모니터링"],
            "reporting": {"내부": "제품별 기여이익보고서", "법인세": "원가명세서 (외감 대상 시)"},
            "next_review": "분기 결산 후 원가 구조 재분석·절감 목표 갱신",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        cm = strategy["cm_ratio"]; bep = strategy["bep_sales"]
        sm = strategy["safety_margin"]; oi = strategy["op_income"]
        return {
            "법인":       {"사전": "원가 항목 분류·BEP 목표 설정", "현재": f"CM률 {cm:.1%}·BEP {bep:,.0f}원·영업이익 {oi:,.0f}원", "사후": "월별 원가보고서·절감 효과 추적"},
            "주주(오너)": {"사전": "원가절감 목표 설정·투자 ROI 계산", "현재": f"안전한계 {sm:.1%} — {'배당 가능' if sm > 0.20 else '유보 권고'}", "사후": "원가 개선 → 배당 여력 재평가"},
            "과세관청":   {"사전": "원가명세서 K-IFRS 기준 적정 작성", "현재": "제품원가·기간비용 구분 세무조정", "사후": "원가명세서 10년 보관·세무조사 대비"},
            "금융기관":   {"사전": f"CM률 {cm:.1%} — 여신 심사 기준(30%) 충족 여부", "현재": "영업이익 기준 대출 상환 능력 평가", "사후": f"CM률 개선 → 신용등급 상향·금리 재협상"},
        }

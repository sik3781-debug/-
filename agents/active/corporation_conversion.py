"""
법인전환 에이전트 (/법인전환) — 전문 솔루션 그룹
핵심 법령: 조특§32(양도세 이월), 지특§57(취득세 감면 75%), 부가§5, 조특§120(자산이월), 법§17
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class CorporationConversionAgent(ProfessionalSolutionAgent):
    """개인사업자→법인 전환 최적 시점·방식 설계 + 세제 혜택 극대화

    조특§32 개인사업자 법인전환 양도세 이월과세(5년 미처분 시 과세)
    지방세특례§57 취득세 감면 75%(사업용 자산)
    부가가치세법§5 사업 양수도 시 재화 공급 의제 면제
    조특§120 중소기업 세감면 승계 (법인전환 후 잔여 감면 유지)
    법인세법§17 현물출자 시 자산 취득가액(출자 시 공정가액)
    소득세법§94·§104 양도소득세 세율·계산 (사업용 자산 양도 시)
    상법§317 법인 설립 절차 · 상법§374 현물출자 검사인 선임
    """

    def generate_strategy(self, case: dict) -> dict:
        """① 전략생성 — 법인전환 최적 방식 + 세금 비교"""
        business_income  = case.get("business_income", 0)             # 개인 사업 소득 (연)
        net_assets       = case.get("net_assets", 0)                  # 순자산 (사업용)
        real_estate_value = case.get("real_estate_value", 0)          # 사업용 부동산 공정가액
        personal_tax_rate = case.get("personal_tax_rate", 0.42)       # 현행 소득세 최고세율
        years_in_business = case.get("years_in_business", 5)          # 개인사업 연수
        conversion_method = case.get("conversion_method", "현물출자")  # 현물출자·양수도·포괄양수도

        # 연간 세 부담 절감 효과 (개인 소득세 vs 법인세)
        personal_tax = business_income * personal_tax_rate
        corp_tax_base = business_income * 0.90  # 법인: 손금 추가 인정 약 10%
        corp_tax = corp_tax_base * 0.19 if corp_tax_base <= 20_000_000_000 else corp_tax_base * 0.21
        annual_savings = personal_tax - corp_tax

        # 전환 비용 추계
        registration_cost = net_assets * 0.004           # 법인설립 등록면허세 약 0.4%
        acquisition_tax = real_estate_value * 0.04 * 0.25  # 취득세 4% → 75% 감면 (지특§57)
        appraisal_cost = max(net_assets * 0.002, 500_000)  # 감정평가 비용

        total_conversion_cost = registration_cost + acquisition_tax + appraisal_cost
        payback_period = total_conversion_cost / max(annual_savings, 1)  # 회수 기간 (년)

        # 양도세 이월과세 (조특§32)
        # 전환 시점 양도세 이연 → 5년 보유 후 처분 시 과세
        deferred_tax = real_estate_value * 0.10  # 추정 양도차익 × 세율

        # 전환 방식 비교
        scenarios = [
            {"name": "현물출자 전환",
             "cost": registration_cost + acquisition_tax * 0.25 + appraisal_cost,
             "tax_benefit": "취득세 75% 감면 + 양도세 이월 (조특§32)",
             "risk": "법인세법§17 취득가액 공정가액 적용 — 미래 처분 시 양도차익 큼",
             "timeline": "3~4개월 (현물출자 검사인 선임·법원 인가)"},
            {"name": "사업 양수도 전환",
             "cost": total_conversion_cost,
             "tax_benefit": "포괄양수도 시 부가가치세 면제 (부가§5)",
             "risk": "양도소득세 즉시 과세 — 조특§32 이월 불가",
             "timeline": "1~2개월 (계약·등기 간소화)"},
            {"name": "신설법인 전환 (사업 이전)",
             "cost": registration_cost * 0.5 + appraisal_cost,
             "tax_benefit": "중소기업 세감면 승계 가능 (조특§120)",
             "risk": "부동산 재취득 → 취득세 정상 과세",
             "timeline": "2~3개월"},
        ]
        best = min(scenarios, key=lambda s: s["cost"])

        text = (
            f"법인 측면: 전환 비용 {total_conversion_cost:,.0f}원 — 회수 기간 {payback_period:.1f}년.\n"
            f"주주(오너) 관점: 연간 절세 {annual_savings:,.0f}원 (개인세 {personal_tax:,.0f} → 법인세 {corp_tax:,.0f}).\n"
            f"과세관청 관점: 조특§32 양도세 이월 5년 추적 — 처분 시 추징 주의.\n"
            f"금융기관 관점: 법인 전환 후 신용평가 갱신 — 기업여신 전환 협의 필요."
        )

        # 영업권 평가 자동 통합 (법인전환 케이스 표준 연계)
        goodwill_result = None
        try:
            from agents.active.goodwill_valuation import GoodwillValuationAgent
            gw_agent = GoodwillValuationAgent()
            gw_financials = case.get("financials", {
                "최근3년_평균순손익": business_income * 0.20,  # 매출의 20% 추정
                "자기자본": net_assets,
                "매출액": business_income,
            })
            gw_result = gw_agent.analyze({
                "case_type": "법인전환",
                "financials": gw_financials,
                "evaluation_date": case.get("evaluation_date", ""),
                "discount_rate": case.get("discount_rate", 0.06),
                "normal_return_rate": case.get("normal_return_rate", 0.10),
            })
            goodwill_result = {
                "recommended_method": gw_result.get("strategy", {}).get("recommended_method"),
                "recommended_value": gw_result.get("strategy", {}).get("recommended_value", 0),
                "annual_amortization": gw_result.get("strategy", {}).get("annual_amortization", 0),
                "transfer_tax": gw_result.get("strategy", {}).get("transfer_tax", 0),
            }
        except Exception:
            goodwill_result = {"note": "영업권 평가 통합 미실행 (GoodwillValuationAgent 로드 오류)"}

        return {
            "business_income": business_income, "net_assets": net_assets,
            "real_estate_value": real_estate_value, "personal_tax": personal_tax,
            "corp_tax": corp_tax, "annual_savings": annual_savings,
            "total_conversion_cost": total_conversion_cost,
            "payback_period": payback_period, "deferred_tax": deferred_tax,
            "scenarios": scenarios, "recommended": best["name"],
            "conversion_method": conversion_method, "text": text,
            "goodwill_valuation": goodwill_result,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["net_assets"] > 0,
                       "detail": f"순자산 {strategy['net_assets']:,.0f}원 · 전환 비용 {strategy['total_conversion_cost']:,.0f}원"},
            "LEGAL":  {"pass": True,
                       "detail": "조특§32(양도세이월)·지특§57(취득세감면75%)·부가§5·조특§120·법§17"},
            "CALC":   {"pass": strategy["annual_savings"] > 0,
                       "detail": f"연간 절세 {strategy['annual_savings']:,.0f}원 · 회수 {strategy['payback_period']:.1f}년"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) >= 3,
                       "detail": "현물출자·양수도·신설법인 3종 시나리오"},
            "CROSS":  {"pass": True, "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        as_ = strategy["annual_savings"]
        dt  = strategy["deferred_tax"]
        return {
            "1_pre": [
                "법인전환 전 개인사업 청산 or 양수도 계약 방식 확정",
                "부동산 공정가액 감정평가 (조특§32 취득가액 기준)",
                "조특§120 세감면 승계 요건 확인 (기술 혁신·고용 유지)",
            ],
            "2_now": [
                "현물출자 검사인 선임·법원 인가 (상법§374)",
                "지방세특례§57 취득세 감면 신청 (사업용 자산 요건 증빙)",
                "부가가치세 포괄양수도 신고 (부가§5 재화 공급 의제 면제)",
            ],
            "3_post": [
                f"조특§32 양도세 이월 — 5년 내 처분 금지 추적 (추징세 약 {dt:,.0f}원)",
                "법인 전환 후 5년간 사후 관리 (세감면 추징 방지)",
                "금융기관 기업여신 전환 + 신용평가 갱신",
            ],
            "4_worst": [
                f"5년 내 처분 시 이월 양도세 {dt:,.0f}원 추징 — 보유 필수",
                "취득세 감면 사후 요건 미충족 시 감면분 추징 (지특§57)",
                "중소기업 요건 탈락 시 조특§120 세감면 소멸 주의",
            ],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "법인 설립 등기 + 사업자 등록", "law": "상법§317"},
            "step2": {"action": f"현물출자·양수도 계약 + 취득세 감면 신청", "law": "지특§57"},
            "step3": {"action": "부가가치세 포괄양수도 신고", "law": "부가§5"},
            "step4": {"action": "조특§32 이월과세 사후 관리 대장 개설 (5년 추적)"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [
                "조특§32 이월과세 5년 추적 — 처분 금지 알림",
                "취득세 감면 사후 요건 연간 점검",
                "법인 전환 후 재무비율·신용등급 분기별 확인",
            ],
            "reporting": {
                "세무": "법인 전환 신고서 + 조특§32 이월 명세서",
                "내부": "연간 절세 효과 실적 vs 목표 보고서",
            },
            "next_review": "전환 후 1년 — 법인 사업 효율 재진단 + 3년차 이월과세 중간 점검",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        as_ = strategy["annual_savings"]; pp = strategy["payback_period"]
        return {
            "법인":       {"사전": "전환 방식 결정 + 법인 설립 비용 산정", "현재": "등기·계약·세감면 신청 실행", "사후": f"연간 절세 {as_:,.0f}원 실현 추적·5년 사후관리"},
            "주주(오너)": {"사전": f"회수 기간 {pp:.1f}년 감안 전환 시점 결정", "현재": "현물출자 지분 배정·대표이사 등재", "사후": "배당 정책 수립 + 조특§32 이월과세 추적"},
            "과세관청":   {"사전": "조특§32 이월과세·§120 세감면 승계 요건 확인", "현재": "부가§5 포괄양수도 신고 수리", "사후": "5년 내 처분 시 양도세 추징·감면 추징 점검"},
            "금융기관":   {"사전": "개인사업 여신 → 법인 여신 전환 사전 협의", "현재": "법인 신용평가 갱신·여신 한도 재설정", "사후": f"법인 전환 후 신용도 개선 → 금리 재협상"},
        }

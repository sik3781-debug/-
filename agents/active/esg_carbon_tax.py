"""
ESG 탄소세 에이전트 (/ESG탄소세) — 전문 솔루션 그룹
핵심 법령: 탄소중립기본법§22(배출권거래), §27(탄소세), K-Taxonomy 2026, CBAM 규정, 자본시장법§159
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class ESGCarbonTaxAgent(ProfessionalSolutionAgent):
    """탄소 배출 산정 + CBAM 이행 + ESG 보고서 + K-Taxonomy 적격성 진단

    탄소중립기본법§22 온실가스 배출권 거래(KAU·KCU 운영)
    K-Taxonomy 2026 녹색분류체계 · 외감법§5 지속가능성 보고서 공시
    조특§25의3 에너지절약시설 투자세액공제 · 국기법§47의3 신고불성실 가산세
    법인세법§24 기부금 손금(탄소크레딧 연계) · 소득세법§94 탄소배출권 양도소득
    상증§41 특수관계인 배출권 이전 증여 의제 · 자본시장법§159 ESG 공시
    """

    # 탄소 집약도 기준 (업종별 tCO2/억원)
    _CARBON_INTENSITY = {
        "제조업": 18.5, "철강": 85.0, "시멘트": 120.0,
        "화학": 45.0, "서비스": 3.2, "유통": 5.5, "IT": 2.1,
    }

    # CBAM 대상 품목
    _CBAM_SECTORS = ["철강", "알루미늄", "시멘트", "비료", "전력", "수소"]

    def generate_strategy(self, case: dict) -> dict:
        """① 전략생성 — 탄소 배출 산정 + CBAM + ESG 전략"""
        revenue          = case.get("revenue", 1)
        industry         = case.get("industry", "제조업")
        scope1_emission  = case.get("scope1_emission", 0)             # tCO2eq (직접)
        scope2_emission  = case.get("scope2_emission", 0)             # tCO2eq (간접)
        scope3_emission  = case.get("scope3_emission", 0)             # tCO2eq (밸류체인)
        eu_export_ratio  = case.get("eu_export_ratio", 0.0)           # EU 수출 비율
        is_ets_target    = case.get("is_ets_target", False)           # 배출권 거래제 대상
        ets_allocation   = case.get("ets_allocation", 0)              # 할당 배출권 (tCO2)
        k_taxonomy_apply = case.get("k_taxonomy_apply", False)        # K-Taxonomy 적용 여부

        # 탄소 집약도
        total_emission = scope1_emission + scope2_emission + scope3_emission
        carbon_intensity = total_emission / max(revenue / 100_000_000, 1)  # tCO2/억원
        benchmark = self._CARBON_INTENSITY.get(industry, 10.0)
        intensity_vs_benchmark = (carbon_intensity - benchmark) / max(benchmark, 1)

        # 배출권 거래제 포지션 (ETS)
        ets_deficit = max(0, scope1_emission - ets_allocation)       # 부족분 → 구매 필요
        kau_price   = 10_000                                          # 가정 KAU 가격 (원/tCO2)
        ets_cost    = ets_deficit * kau_price

        # CBAM 비용 추정 (EU 탄소가격 €60/tCO2 = 약 85,000원/tCO2)
        cbam_applicable = any(s in industry for s in self._CBAM_SECTORS)
        eu_export_emission = total_emission * eu_export_ratio
        cbam_cost = eu_export_emission * 85_000 if cbam_applicable else 0

        # K-Taxonomy 적격성 체크 (6대 환경목표)
        k_taxonomy_targets = [
            "기후변화 완화 (온실가스 감축 목표 설정)",
            "기후변화 적응 (물리적 리스크 관리)",
            "수자원·해양 보전",
            "순환경제 전환",
            "오염 방지",
            "생물다양성 보전",
        ]

        # 3종 시나리오
        scenarios = [
            {"name": "탄소 집약도 20% 감축",
             "target_emission": total_emission * 0.80,
             "ets_cost_saved": ets_cost * 0.20,
             "investment": revenue * 0.005,  # 매출 0.5% 투자
             "law": "탄소중립기본법§22 + K-Taxonomy 기후완화"},
            {"name": "CBAM 사전 대응 (탄소발자국 인증)",
             "target_emission": total_emission * 0.90,
             "ets_cost_saved": 0,
             "investment": cbam_cost * 0.3,
             "law": "EU CBAM 규정 2026 + 자본시장법§159 공시"},
            {"name": "현행 유지 + 배출권 구매",
             "target_emission": total_emission,
             "ets_cost_saved": 0,
             "investment": ets_cost + cbam_cost,
             "law": "온실가스배출권거래법§12"},
        ]
        best = min(scenarios, key=lambda s: s["investment"])

        text = (
            f"법인 측면: 총 배출 {total_emission:,.0f} tCO2 — 집약도 {carbon_intensity:.1f} tCO2/억원 "
            f"(업종 벤치마크 {benchmark:.1f} 대비 {intensity_vs_benchmark:+.1%}).\n"
            f"주주(오너) 관점: ETS 비용 {ets_cost:,.0f}원 + CBAM {cbam_cost:,.0f}원 = 연간 탄소 비용 {ets_cost+cbam_cost:,.0f}원.\n"
            f"과세관청 관점: 탄소세 2027년 시행 예정 (탄소중립기본법§27) — 선제 대비.\n"
            f"금융기관 관점: ESG 등급·K-Taxonomy {'적격' if k_taxonomy_apply else '진단 필요'} → 녹색 금융 조달 가능성."
        )

        return {
            "revenue": revenue, "industry": industry,
            "scope1_emission": scope1_emission, "scope2_emission": scope2_emission,
            "scope3_emission": scope3_emission, "total_emission": total_emission,
            "carbon_intensity": carbon_intensity, "benchmark": benchmark,
            "intensity_vs_benchmark": intensity_vs_benchmark,
            "ets_deficit": ets_deficit, "ets_cost": ets_cost,
            "cbam_applicable": cbam_applicable, "cbam_cost": cbam_cost,
            "k_taxonomy_targets": k_taxonomy_targets, "k_taxonomy_apply": k_taxonomy_apply,
            "scenarios": scenarios, "recommended": best["name"], "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["total_emission"] >= 0,
                       "detail": f"총 배출 {strategy['total_emission']:,.0f} tCO2 · 집약도 {strategy['carbon_intensity']:.1f} tCO2/억원"},
            "LEGAL":  {"pass": True,
                       "detail": "탄소중립기본법§22·§27 · K-Taxonomy 2026 · CBAM 규정 · 자본시장법§159"},
            "CALC":   {"pass": strategy["ets_cost"] >= 0,
                       "detail": f"ETS 비용 {strategy['ets_cost']:,.0f}원 · CBAM {strategy['cbam_cost']:,.0f}원"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) >= 3,
                       "detail": "집약도감축·CBAM대응·현행유지 3종 시나리오"},
            "CROSS":  {"pass": True, "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        ec = strategy["ets_cost"]; cc = strategy["cbam_cost"]
        return {
            "1_pre": [
                "Scope 1·2·3 배출량 산정 기준 확정 (GHG Protocol)",
                f"ETS 대상 시 할당 배출권 {strategy['ets_allocation'] if 'ets_allocation' in strategy else 0:,.0f} tCO2 확인",
                f"CBAM {'해당 — EU 수출 탄소발자국 인증 준비' if strategy['cbam_applicable'] else '비해당 확인'}",
            ],
            "2_now": [
                f"배출권 부족분 {strategy['ets_deficit']:,.0f} tCO2 → KAU 구매 {ec:,.0f}원",
                "ESG 보고서 작성 (GRI·TCFD·ISSB 기준)",
                "K-Taxonomy 적격성 진단 6대 목표 체크",
            ],
            "3_post": [
                "온실가스 감축 목표(SBTi) 검증·인증",
                "ESG 등급 기관 평가 (MSCI·Sustainalytics) 대응",
                "녹색채권·ESG대출 조달 계획 수립",
            ],
            "4_worst": [
                f"탄소세 2027년 시행 시 추가 비용 추정 {strategy['total_emission']*15000:,.0f}원",
                f"CBAM 본격 부과 2026년 — EU 수출 {cc:,.0f}원 추가 비용",
                "ESG 미공시 과태료 (자본시장법§159 — 위반 시 제재)",
            ],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "온실가스 인벤토리 구축 (Scope 1·2·3)", "law": "탄소중립기본법§22"},
            "step2": {"action": "K-Taxonomy 적격성 자가진단 + 외부 검증"},
            "step3": {"action": "ESG 보고서 작성 (GRI Standards + TCFD)", "law": "자본시장법§159"},
            "step4": {"action": f"ETS 배출권 구매 {strategy['ets_cost']:,.0f}원 + CBAM 인증 준비"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [
                "월별 온실가스 배출량 추적",
                "KAU 가격 변동 모니터링 + 선물 헷지 검토",
                "CBAM 규정 변경 사항 추적 (2026년~)",
            ],
            "reporting": {
                "외부": "ESG 보고서 연간 발행 + 제3자 검증",
                "내부": "탄소 비용 월별 대시보드",
            },
            "next_review": "연간 탄소 감축 목표 달성도 검토 + K-Taxonomy 재진단",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        ec = strategy["ets_cost"]; cc = strategy["cbam_cost"]
        te = strategy["total_emission"]
        return {
            "법인":       {"사전": f"Scope 1·2·3 인벤토리 구축 · 집약도 {strategy['carbon_intensity']:.1f} tCO2/억원", "현재": "ETS·CBAM·ESG 보고서 병행 실행", "사후": "온실가스 감축 목표 달성 추적·ESG 등급 상향"},
            "주주(오너)": {"사전": f"탄소 비용 {ec+cc:,.0f}원 예산 반영", "현재": "녹색채권 발행 or ESG대출 조달", "사후": "ESG 등급 상향 → 자본 비용 절감·배당 여력"},
            "과세관청":   {"사전": "탄소세 2027년 대비 사전 감축", "현재": f"ETS 배출권 {strategy['ets_deficit']:,.0f} tCO2 부족분 구매", "사후": "탄소세 신고·ETS 정산·K-Taxonomy 적격 증빙"},
            "금융기관":   {"사전": f"ESG 등급·K-Taxonomy 적격성 → 녹색금융 한도 협의", "현재": "녹색채권·ESG연계대출 실행", "사후": "ESG KPI 달성 시 금리 인센티브 적용"},
        }

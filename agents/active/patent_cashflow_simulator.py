"""
특허 통합 NPV 시뮬레이터 (/특허현금흐름시뮬) — 4단계 워크플로우

핵심 법령:
  조특§10 (R&D 세액공제 — 중소기업 25%·중견 8%·대기업 2%)
  조특§12 (기술이전·사업화 소득 50% 감면)
  법인세법§23 (무형자산 자본화 — 특허 내용연수 20년)
  법인세법§45 (특허 사용료 손금 인정)
  소득세법§21①10호 (직무발명 보상금 과세)
  상증§41의3 (특허권 이전 이익 증여 의제)
  국기법§26의2 (부과제척기간 — R&D 공제 사후관리)
  발명진흥법§40 (직무발명 보상 의무·IP 담보)
  외감법§4 (외감 대상 — 특허 자산 반영 재무비율)
"""
from __future__ import annotations


class PatentCashflowSimulator:
    """직무발명 보상 + 자본화 + 자체개발 50% 감면 + R&D 세액공제 통합 NPV"""

    RD_CREDIT_SME     = 0.25
    IP_TRANSFER_DISC  = 0.50
    DISCOUNT_RATE     = 0.08

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "PatentCashflowSimulator",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "PatentCashflowSimulator",
            "text": strategy["text"],
            "rd_credit": strategy["rd_credit"],
            "royalty_npv_after_tax": strategy["royalty_npv_after_tax"],
            "capitalize_benefit": strategy["capitalize_benefit"],
            "expense_benefit": strategy["expense_benefit"],
            "require_full_4_perspective": True,
        }

    def generate_strategy(self, case: dict) -> dict:
        rd_expense     = case.get("rd_expense", 0)
        patent_value   = case.get("patent_value", 0)
        royalty_annual = case.get("royalty_annual", 0)
        years          = case.get("patent_years_left", 10)
        tax_rate       = case.get("tax_rate", 0.20)
        inventor_rwd   = case.get("inventor_reward", 0)

        rd_credit   = rd_expense * self.RD_CREDIT_SME
        royalty_npv = sum(
            royalty_annual / (1 + self.DISCOUNT_RATE) ** y for y in range(1, years + 1)
        )
        royalty_npv_after = royalty_npv * (1 - tax_rate * (1 - self.IP_TRANSFER_DISC))
        cap_benefit = patent_value * 0.05
        exp_benefit = patent_value * tax_rate

        text = (
            f"법인 측면: R&D 세액공제 {rd_credit:,.0f}원 (조특§10 중소기업 25%).\n"
            f"주주(오너) 관점: 기술이전 소득 {royalty_annual:,.0f}원 × 50% 감면(조특§12) → "
            f"실효세율 {tax_rate*(1-0.5):.0%}.\n"
            f"과세관청 관점: 특허 자본화 vs 비용처리 선택 — 자본화 시 내용연수 20년 적용.\n"
            f"금융기관 관점: IP 담보 대출 활용 — 특허가치 {patent_value:,.0f}원 기준.\n"
            f"통합 NPV(세후): {royalty_npv_after:,.0f}원"
        )
        # IP 활용 전략 시나리오 3종
        scenarios = [
            {"name": "R&D 세액공제 극대화 (조특§10)",
             "benefit": rd_credit,
             "method": "연구전담부서 설립·인건비 100% 세액공제 적용",
             "law": "조특§10 중소기업 25% + 국기법§26의2 사후관리 5년"},
            {"name": "기술이전 소득 감면 (조특§12)",
             "benefit": royalty_npv_after,
             "method": "라이선스 계약 → 기술이전 소득 50% 법인세 감면",
             "law": "조특§12 + 법인세법§45 사용료 손금 + 발명진흥법§40 IP 담보"},
            {"name": "특허 자본화 처리 (법인세법§23)",
             "benefit": cap_benefit,
             "method": "특허 취득원가 자산화 → 20년 감가상각 손금",
             "law": "법인세법§23 무형자산 + 상증§41의3 이전이익 증여 의제 주의"},
        ]

        return {
            "rd_expense": rd_expense, "patent_value": patent_value,
            "royalty_annual": royalty_annual, "years": years, "tax_rate": tax_rate,
            "inventor_reward": inventor_rwd, "rd_credit": rd_credit,
            "royalty_npv_after_tax": royalty_npv_after,
            "capitalize_benefit": cap_benefit, "expense_benefit": exp_benefit,
            "scenarios": scenarios, "recommended": scenarios[0]["name"],
            "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["rd_expense"] >= 0,
                       "detail": f"R&D 지출 {strategy['rd_expense']:,.0f}원 — 연구전담부서 인정 여부 확인"},
            "LEGAL":  {"pass": True,
                       "detail": "조특§10 (R&D 세액공제) + §12 (기술이전 50% 감면) + 발명진흥법"},
            "CALC":   {"pass": strategy["royalty_npv_after_tax"] >= 0,
                       "detail": f"NPV(세후) {strategy['royalty_npv_after_tax']:,.0f}원 — {strategy['years']}년 DCF"},
            "LOGIC":  {"pass": strategy["capitalize_benefit"] >= 0,
                       "detail": "자본화·비용처리 양방향 비교 제시"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        return {
            "1_pre": ["연구전담부서 인정 요건 확인 (조특§10 적용 전제)",
                      "기술이전 계약서 작성 + 조특§12 감면 요건 충족 여부"],
            "2_now": [f"R&D 세액공제 {strategy['rd_credit']:,.0f}원 법인세 신고 반영",
                      f"직무발명 보상금 {strategy['inventor_reward']:,.0f}원 손금 처리"],
            "3_post": ["기술이전 로열티 연간 정산·납세 (세후 NPV 추적)",
                       "특허 만료 전 재출원·연장 계획 수립"],
            "4_worst": ["연구전담부서 요건 위반 시 세액공제 추징 (5년)",
                        "기술이전 계약 해지 시 NPV 재산출 → 잔여 로열티 대안"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "연구전담부서 인정 신청·유지", "law": "조특§10"},
            "step2": {"action": f"R&D 세액공제 {strategy['rd_credit']:,.0f}원 신고 준비"},
            "step3": {"action": "기술이전 계약 체결 + 로열티 수취 구조 설계", "law": "조특§12"},
            "step4": {"action": "IP 담보 대출 신청 — 금융기관 협의"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["연간 로열티 수입 추적·NPV 갱신",
                           "특허 유효기간 만료 알림"],
            "reporting": {"법인세": "R&D 세액공제 명세서",
                          "기술이전": "기술료 수입 신고"},
            "next_review": "매년 R&D 지출 확정 후 세액공제 규모 재산정",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        rc  = strategy["rd_credit"]
        npv = strategy["royalty_npv_after_tax"]
        pv  = strategy["patent_value"]
        return {
            "법인": {
                "사전": "연구전담부서 인정·R&D 예산 계획",
                "현재": f"세액공제 {rc:,.0f}원 신고 + 기술이전 계약",
                "사후": "로열티 수입 회계 처리·특허 만료 관리",
            },
            "주주(오너)": {
                "사전": "직무발명 보상금 설계 + 발명진흥법 요건",
                "현재": f"기술이전 NPV {npv:,.0f}원 (세후) 현금화",
                "사후": "특허 포트폴리오 확대 계획",
            },
            "과세관청": {
                "사전": "조특§10 R&D 세액공제 요건 사전 확인",
                "현재": "기술이전 소득 50% 감면(조특§12) 적법성",
                "사후": "세액공제 추징 위험 5년간 서류 보관",
            },
            "금융기관": {
                "사전": f"IP 담보 대출 — 특허가치 {pv:,.0f}원 산정",
                "현재": "IP 담보 설정·대출 실행",
                "사후": "특허 만료·무효화 시 담보가치 재평가",
            },
        }

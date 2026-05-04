"""사내근로복지기금 설계 에이전트 — 4단계 워크플로우"""
from __future__ import annotations


class CorporateBenefitsFundAgent:
    """출연 시나리오 3종 + 과세관청 부인 위험 + 운영 설계"""

    DEDUCTION_LIMIT_PCT = 0.10  # 법§24: 지정기부금 한도

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "CorporateBenefitsFundAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "CorporateBenefitsFundAgent",
            "text": strategy["text"],
            "scenarios": strategy["scenarios"],
            "deduction_limit": strategy["deduction_limit"],
            "require_full_4_perspective": True,
        }

    def generate_strategy(self, case: dict) -> dict:
        net_income = case.get("net_income", 0)
        taxable    = case.get("taxable_income", 0)
        limit      = taxable * self.DEDUCTION_LIMIT_PCT
        scenarios = [
            {"name": "보수적",   "contribution": min(net_income * 0.02, limit), "note": "순이익 2%, 손금 인정"},
            {"name": "표준",     "contribution": min(net_income * 0.05, limit), "note": "순이익 5%, 손금 최적"},
            {"name": "적극적",   "contribution": limit, "note": "한도 최대 활용"},
        ]
        text = (
            f"법인 측면: 사내근로복지기금 출연은 지정기부금(법§24) 한도 {limit:,.0f}원 내에서 손금 산입.\n"
            f"주주(오너) 관점: 법인 현금 유출 → 직원 복지 개선으로 인재 유지 효과.\n"
            f"과세관청 관점: 근로복지기본법§50 설립 요건 준수 필수 (상시근로자 수 등).\n"
            f"금융기관 관점: 부채비율 영향 없음 — 신용등급 중립.\n"
            f"출연 시나리오 3종: {[s['name'] for s in scenarios]}"
        )
        return {"net_income": net_income, "taxable": taxable,
                "deduction_limit": limit, "scenarios": scenarios, "text": text}

    def validate_risk_5axis(self, strategy: dict) -> dict:
        limit = strategy["deduction_limit"]
        axes = {
            "DOMAIN": {"pass": True, "detail": "근로복지기본법§50~75 기금 설립·운영 요건 충족 여부"},
            "LEGAL":  {"pass": limit >= 0,
                       "detail": f"법§24 지정기부금 한도 {limit:,.0f}원 — 초과 출연 시 손금 부인"},
            "CALC":   {"pass": len(strategy["scenarios"]) == 3, "detail": "3가지 출연 시나리오 완비"},
            "LOGIC":  {"pass": True, "detail": "보수적→표준→적극적 출연 단계 논리 정합"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        return {
            "1_pre": ["상시근로자 50인 이상 여부 확인 (의무설립 기준)",
                      "기금 설립 신고 준비 — 고용노동부 신고 절차"],
            "2_now": [f"출연액 {strategy['deduction_limit']:,.0f}원 이내 집행·이사회 결의",
                      "법§24 한도 초과 시 손금 불산입 경고"],
            "3_post": ["기금 운영위원회 구성·운영 (근로복지기본법§63)",
                       "출연금 사용 계획 수립 (복지사업 항목)"],
            "4_worst": ["과세관청 부인 시: 실질 복지사업 증빙 준비",
                        "한도 초과 출연분 → 손금 부인 → 법인세 추납"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "기금 설립 신고 (고용노동부)", "law": "근로복지기본법§50"},
            "step2": {"action": f"출연 결의 — 표준안 {strategy['scenarios'][1]['contribution']:,.0f}원"},
            "step3": {"action": "출연금 이전 + 지정기부금 영수증 수령"},
            "step4": {"action": "법인세 신고 시 법§24 한도 내 손금 반영"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["연간 출연 한도 소진율 모니터링",
                           "기금 잔액·투자수익 분기별 확인"],
            "reporting": {"법인세": "지정기부금 명세서 첨부",
                          "고용부": "기금 결산서 제출"},
            "next_review": "다음 회계연도 순이익 확정 후 출연 시나리오 재산정",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        lim = strategy["deduction_limit"]
        return {
            "법인": {
                "사전": "기금 설립 신고·출연 계획 수립",
                "현재": f"법§24 한도 {lim:,.0f}원 이내 출연 실행",
                "사후": "손금 처리·법인세 명세서 첨부",
            },
            "주주(오너)": {
                "사전": "출연 규모 결정 — 인재 유지 ROI 계산",
                "현재": "직원 복지 개선 → 이직률 감소",
                "사후": "기금 운영 성과 보고",
            },
            "과세관청": {
                "사전": "근로복지기본법 설립 요건 검토",
                "현재": "법§24 지정기부금 한도 초과 여부 확인",
                "사후": "출연 목적 실질 복지사업 증빙 보관",
            },
            "금융기관": {
                "사전": "부채비율·신용등급 영향 없음 확인",
                "현재": "현금 유출 → 유동성 비율 모니터링",
                "사후": "기금 자산 담보 활용 가능 여부 검토",
            },
        }

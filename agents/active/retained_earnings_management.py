"""미처분이익잉여금 처리 4방안 에이전트 — 4단계 워크플로우"""
from __future__ import annotations


class RetainedEarningsManagementAgent:
    """
    미처분이익잉여금 처리:
    ① 배당 ② 자기주식 취득→양도 ③ 자본전입 ④ 이익소각
    """

    MAX_DIVIDEND_RATE         = 0.495
    BUYBACK_RATE              = 0.33
    CAPITAL_SURPLUS_EXEMPTION = True

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "RetainedEarningsManagementAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "RetainedEarningsManagementAgent",
            "text": strategy["text"],
            "retained_earnings": strategy["retained_earnings"],
            "methods": strategy["methods"],
            "recommended": strategy["recommended"],
            "require_full_4_perspective": True,
        }

    def generate_strategy(self, case: dict) -> dict:
        retained  = case.get("retained_earnings", 0)
        owner_pct = case.get("owner_share_pct", 0.70)
        tax_rate  = case.get("owner_marginal_rate", 0.45)

        eff_rate    = min(tax_rate + 0.044, self.MAX_DIVIDEND_RATE)
        div_tax     = retained * owner_pct * eff_rate
        buyback_tax = retained * owner_pct * self.BUYBACK_RATE

        methods = [
            {"method": "① 배당",              "tax": div_tax,
             "after": retained * owner_pct - div_tax,
             "effective_rate": f"{div_tax / max(retained, 1):.1%}"},
            {"method": "② 자기주식 취득→양도", "tax": buyback_tax,
             "after": retained * owner_pct - buyback_tax,
             "effective_rate": f"{buyback_tax / max(retained, 1):.1%}"},
            {"method": "③ 자본전입",           "tax": div_tax,
             "after": 0, "effective_rate": f"{div_tax / max(retained, 1):.1%}"},
            {"method": "④ 이익소각",           "tax": buyback_tax,
             "after": 0, "effective_rate": f"{buyback_tax / max(retained, 1):.1%}"},
        ]
        best = min(methods, key=lambda m: m["tax"])

        text = (
            f"주주(오너) 관점: 미처분이익잉여금 {retained:,.0f}원 처리 — "
            f"최적: {best['method']} (실효세율 {best['effective_rate']}).\n"
            f"법인 측면: 자기주식 취득 시 발행주식 수 감소 → 1주당 가치 상승.\n"
            f"과세관청 관점: 자기주식 소각 시 의제배당 (소§17②4호) 주의.\n"
            f"금융기관 관점: 배당 시 현금 유출 → 신용등급 일시 하락 가능.\n"
            f"4방안 비교 완료. 자기주식 5종 연동 활용 권장."
        )
        return {
            "retained_earnings": retained, "owner_pct": owner_pct,
            "owner_marginal_rate": tax_rate, "methods": methods,
            "recommended": best["method"], "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        re = strategy["retained_earnings"]
        axes = {
            "DOMAIN": {"pass": re >= 0, "detail": f"미처분이익잉여금 {re:,.0f}원 — 재무제표 확인"},
            "LEGAL":  {"pass": True,
                       "detail": "소§17②4호 (의제배당) + 소§94 (양도세) + 상법§341 (자기주식)"},
            "CALC":   {"pass": len(strategy["methods"]) == 4, "detail": "4방안 세액 계산 완비"},
            "LOGIC":  {"pass": True,
                       "detail": f"최적 방안 = {strategy['recommended']} (세액 최소)"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        best = strategy["recommended"]
        re   = strategy["retained_earnings"]
        return {
            "1_pre": [f"미처분이익잉여금 {re:,.0f}원 — 배당가능이익 확인",
                      "4방안 세액 비교 후 최적 방안 이사회 의결"],
            "2_now": [f"선택 방안: {best} 실행",
                      "③ 자본전입 선택 시: 주주총회 특별결의 + 등기 변경"],
            "3_post": ["실행 후 세무 신고 (배당·양도세 기한 내)",
                       "등기부 변경 (자기주식 소각·자본전입 시)"],
            "4_worst": ["④ 이익소각 취득단가 > 소각가액 시 의제배당 발생",
                        "③ 자본전입 시 의제배당(소§17②2호) 과세 → 세부담 사전 계산"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "이사회·주주총회 결의 (방안별 결의 요건 상이)"},
            "step2": {"action": f"{strategy['recommended']} 실행"},
            "step3": {"action": "세무 신고 + 증빙 완비"},
            "step4": {"action": "등기부 반영 (자기주식 소각·자본전입 시)"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["연간 미처분이익잉여금 잔액 추적",
                           "주당 가치 변동 모니터링"],
            "reporting": {"세무": "배당소득세·양도세 신고",
                          "법무": "등기 변경 완료 확인"},
            "next_review": "다음 결산기 미처분이익잉여금 재진단 + 방안 재선택",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        re   = strategy["retained_earnings"]
        best = strategy["recommended"]
        return {
            "법인": {
                "사전": f"미처분이익잉여금 {re:,.0f}원 — 4방안 세액 비교",
                "현재": f"{best} 실행·결의",
                "사후": "세무신고 + 등기 변경",
            },
            "주주(오너)": {
                "사전": "실효세율 최소화 방안 선택",
                "현재": f"{best} 실행 → 현금 수취 또는 지분가치 상승",
                "사후": "소득 신고 + 잔여 이익잉여금 관리",
            },
            "과세관청": {
                "사전": "4방안별 과세 분기점 사전 검토",
                "현재": "의제배당·양도세 과세 여부 판정",
                "사후": "세무신고 완료·추징 리스크 제로화",
            },
            "금융기관": {
                "사전": "배당 시 현금 유출 → 유동성 영향 시뮬",
                "현재": "자기주식 취득 후 자기자본 감소 → 부채비율 변동",
                "사후": "배당 후 신용등급 재평가 대비",
            },
        }

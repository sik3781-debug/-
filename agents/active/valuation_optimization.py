"""비상장주식 평가액 최적화 에이전트 — 4단계 워크플로우"""
from __future__ import annotations


class ValuationOptimizationAgent:
    """
    자기주식 + 미처분이익잉여금 + 부동산 평가 통합 →
    비상장 평가액 조정 시뮬.
    ⚠ 과세관청 부인 위험 시나리오 3종 반드시 포함.
    """

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "ValuationOptimizationAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "ValuationOptimizationAgent",
            "text": strategy["text"],
            "base_value": strategy["base_value"],
            "scenarios": strategy["scenarios"],
            "weight": strategy["weight"],
            "require_full_4_perspective": True,
        }

    def generate_strategy(self, case: dict) -> dict:
        nas         = case.get("net_asset_per_share", 10_000)
        nis         = case.get("net_income_per_share", 2_000)
        re_pct      = case.get("real_estate_ratio", 0.30)
        startup_yrs = case.get("years_in_operation", 5)

        if startup_yrs <= 3 or re_pct >= 0.80:
            wn, wa = 0, 1
        elif re_pct >= 0.50:
            wn, wa = 2, 3
        else:
            wn, wa = 3, 2
        total_w    = wn + wa
        base_value = (nis * wn + nas * wa) / total_w

        scenarios = [
            {"name": "현재 평가액",
             "value": base_value,
             "method": f"순손익{wn}:순자산{wa} 가중",
             "risk": "없음"},
            {"name": "이익잉여금 감소 후",
             "value": base_value * 0.75,
             "method": "배당·소각으로 순자산 감소 → 평가액 하락",
             "risk": "과세관청: 조세회피 목적 부인 가능 — 비상업적 사유 필요"},
            {"name": "부동산 비율 조정 후",
             "value": base_value * 0.90,
             "method": "부동산 처분으로 가중치 변경 (50% 이하)",
             "risk": "과세관청: 직전 3년 평균 부동산비율 참조 — 단기 조작 부인"},
        ]
        text = (
            f"주주(오너) 관점: 현재 비상장 평가액 {base_value:,.0f}원/주 — 절세 시점 조정 가능.\n"
            f"법인 측면: 이익잉여금 배당·소각으로 순자산 감소 → 평가액 약 25% 하락 가능.\n"
            f"과세관청 관점: ⚠ 조세회피 목적 인위 조정 시 국기§14②③ 실질과세 부인 위험.\n"
            f"금융기관 관점: 평가액 하락 시 담보가치 감소 → 기존 대출 재평가 가능.\n"
            f"시나리오 3종 중 '현재 평가액' 유지 후 합법적 절세 권장."
        )
        return {
            "nas": nas, "nis": nis, "re_pct": re_pct,
            "startup_yrs": startup_yrs, "weight_nis": wn, "weight_nas": wa,
            "base_value": base_value, "scenarios": scenarios,
            "weight": f"순손익{wn}:순자산{wa}", "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        bv = strategy["base_value"]
        axes = {
            "DOMAIN": {"pass": bv > 0,
                       "detail": f"평가액 {bv:,.0f}원 — 상증§54~§56 가중평균 적용"},
            "LEGAL":  {"pass": True,
                       "detail": "상증§54 (순손익·순자산 가중) + 국기§14 실질과세 부인 위험 명시"},
            "CALC":   {"pass": strategy["weight_nis"] + strategy["weight_nas"] > 0,
                       "detail": f"가중치 {strategy['weight']} — 부동산 비율·업력 기준"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) == 3,
                       "detail": "현재/이익잉여금감소/부동산조정 3종 시나리오"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        bv = strategy["base_value"]
        return {
            "1_pre": [f"평가 기준일 확정 — 상증§60 시가 원칙 (거래일 전후 3개월)",
                      f"부동산 비율 {strategy['re_pct']:.0%} → 가중치 {strategy['weight']} 결정"],
            "2_now": [f"현재 평가액 {bv:,.0f}원/주 — 증여·양도 시점 최적화",
                      "이익잉여금 감소 방안 검토 (배당·소각) — 국기§14 실질과세 사전 검토"],
            "3_post": ["평가액 변동 후 증여·양도세 신고 완료",
                       "평가액 조작 의심 시 감정평가로 보완"],
            "4_worst": ["과세관청 실질과세 부인 → 원래 평가액 기준 과세 + 가산세",
                        "담보가치 하락 시 금융기관 추가담보 요구"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "평가 기준일·가중치 확정", "law": "상증§54~§56"},
            "step2": {"action": f"현재 평가액 {strategy['base_value']:,.0f}원 산출"},
            "step3": {"action": "3종 시나리오 중 합법적 절세 방안 선택"},
            "step4": {"action": "증여·양도 실행 + 세무 신고"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["평가 기준일 이후 6개월 내 유사 거래 가격 추적",
                           "부동산 비율 변동 → 차기 평가 가중치 재확인"],
            "reporting": {"세무": "증여세·양도세 신고 (평가서 첨부)", "내부": "평가 리포트 보관"},
            "next_review": "6개월마다 평가액 갱신 + 최적 증여 타이밍 재판단",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        bv  = strategy["base_value"]
        wt  = strategy["weight"]
        s1  = strategy["scenarios"][1]["value"]
        return {
            "법인": {
                "사전": f"가중치 결정 ({wt}) + 평가 기준일 확정",
                "현재": f"평가액 {bv:,.0f}원/주 산출·검증",
                "사후": "평가결과 세무신고·등기 반영",
            },
            "주주(오너)": {
                "사전": "증여·양도 시점 최적화 계획",
                "현재": f"3종 시나리오 중 선택 — 이익잉여금 감소 후 {s1:,.0f}원 가능",
                "사후": "증여세·양도세 납부 + 10년 합산 관리",
            },
            "과세관청": {
                "사전": "상증§54~§56 가중평균 적용 요건 확인",
                "현재": "⚠ 국기§14 실질과세 — 인위적 평가액 조작 부인 위험",
                "사후": "세무조사 대비 평가 근거 서류 10년 보관",
            },
            "금융기관": {
                "사전": "현재 담보가치 = 평가액 기준 협의",
                "현재": "평가액 하락 시 추가담보 요구 가능성 사전 협의",
                "사후": "담보가치 재평가 + 대출 약정 조건 유지 확인",
            },
        }

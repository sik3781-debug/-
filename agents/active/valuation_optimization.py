"""비상장주식 평가액 최적화 메타 에이전트 (Opus 권장)"""
from __future__ import annotations


class ValuationOptimizationAgent:
    """
    자기주식 + 미처분이익잉여금 + 부동산 평가 통합 →
    비상장 평가액 인위적 조정 시뮬.
    ⚠ 과세관청 부인 위험 시나리오 3종 반드시 포함.
    """

    def analyze(self, company_data: dict) -> dict:
        nas     = company_data.get("net_asset_per_share", 10_000)
        nis     = company_data.get("net_income_per_share", 2_000)
        re_pct  = company_data.get("real_estate_ratio", 0.30)
        startup_yrs = company_data.get("years_in_operation", 5)

        # 가중치 결정 (상증§54~56)
        if startup_yrs <= 3 or re_pct >= 0.80:
            weight_nis, weight_nas = 0, 1
        elif re_pct >= 0.50:
            weight_nis, weight_nas = 2, 3
        else:
            weight_nis, weight_nas = 3, 2
        total_w = weight_nis + weight_nas
        base_value = (nis * weight_nis + nas * weight_nas) / total_w

        # 평가액 조정 시나리오 3종
        scenarios = [
            {
                "name": "현재 평가액",
                "value": base_value,
                "method": f"순손익{weight_nis}:순자산{weight_nas} 가중",
                "risk": "없음",
            },
            {
                "name": "이익잉여금 감소 후",
                "value": base_value * 0.75,
                "method": "배당·소각으로 순자산 감소 → 평가액 하락",
                "risk": "과세관청: 조세회피 목적 부인 가능 — 비상업적 사유 필요",
            },
            {
                "name": "부동산 비율 조정 후",
                "value": base_value * 0.90,
                "method": "부동산 처분으로 가중치 변경 (50% 이하)",
                "risk": "과세관청: 직전 3년 평균 부동산비율 참조 — 단기 조작 부인",
            },
        ]

        return {
            "agent": "ValuationOptimizationAgent",
            "text": (
                f"주주(오너) 관점: 현재 비상장 평가액 {base_value:,.0f}원/주 — 절세 시점 조정 가능.\n"
                f"법인 측면: 이익잉여금 배당·소각으로 순자산 감소 → 평가액 약 25% 하락 가능.\n"
                f"과세관청 관점: ⚠ 조세회피 목적 평가액 인위 조정 시 국세기본법§14②③ 실질과세 부인 위험.\n"
                f"금융기관 관점: 평가액 하락 시 담보가치 감소 → 기존 대출 재평가 가능.\n"
                f"시나리오 3종 중 '현재 평가액' 유지 후 합법적 절세 권장."
            ),
            "base_value": base_value,
            "scenarios": scenarios,
            "weight": f"순손익{weight_nis}:순자산{weight_nas}",
            "require_full_4_perspective": True,
        }

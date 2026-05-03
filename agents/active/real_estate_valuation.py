"""부동산 정식 평가 4종 에이전트"""
from __future__ import annotations


EVAL_METHODS = {
    "공시지가": {"base": 0.70, "note": "취득세·재산세 기준, 시세의 약 70%"},
    "기준시가": {"base": 0.80, "note": "양도세·증여세 기준, 국세청 고시"},
    "감정평가": {"base": 1.00, "note": "시장가치 기준 공인감정사 평가"},
    "매매사례": {"base": 0.98, "note": "인근 실거래 사례 기준"},
}


class RealEstateValuationAgent:
    def analyze(self, company_data: dict) -> dict:
        market_value = company_data.get("real_estate", {}).get("value", 0)
        re_type      = company_data.get("real_estate", {}).get("type", "공장")

        valuations = {
            method: {"value": int(market_value * info["base"]), "note": info["note"]}
            for method, info in EVAL_METHODS.items()
        }
        # 세금 목적별 권장 평가
        tax_purpose = {
            "취득세·재산세": "공시지가",
            "양도소득세":    "기준시가 (or 실거래가 더 높으면 실거래가)",
            "증여·상속":     "기준시가 (or 감정평가 병행)",
            "담보 대출":     "감정평가",
            "매각 협상":     "매매사례",
        }

        return {
            "agent": "RealEstateValuationAgent",
            "text": (
                f"법인 측면: {re_type} 시장가치 {market_value:,.0f}원 — 4종 평가 비교.\n"
                f"주주(오너) 관점: 매각 시 감정평가 활용 → 양도세 기준가액 극대화.\n"
                f"과세관청 관점: 증여·상속세 기준 = 기준시가 (감정평가 없을 경우).\n"
                f"금융기관 관점: 담보 설정 시 감정평가액 기준 — 시세의 약 100%.\n"
                f"평가액 범위: {min(v['value'] for v in valuations.values()):,.0f} ~ {max(v['value'] for v in valuations.values()):,.0f}원"
            ),
            "valuations": valuations,
            "tax_purpose_guide": tax_purpose,
            "require_full_4_perspective": True,
        }

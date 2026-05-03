"""부동산 탁상감정 에이전트 (즉시 약식 평가, 30초 목표)"""
from __future__ import annotations


REGION_MULTIPLIER = {
    "서울": 1.5, "경기": 1.2, "부산": 1.1, "인천": 1.1,
    "대구": 1.0, "광주": 0.9, "대전": 0.9, "경남": 0.85,
    "경북": 0.8, "전남": 0.75, "전북": 0.75, "충남": 0.8, "기타": 0.8,
}
USAGE_MULTIPLIER = {
    "공장": 0.7, "오피스": 1.2, "상가": 1.0, "주거": 1.1,
    "토지": 0.6, "창고": 0.65,
}


class RealEstateDesktopAppraisalAgent:
    BASE_PRICE_PER_SQM = 1_000_000  # 1백만원/㎡ 기준

    def analyze(self, company_data: dict) -> dict:
        re = company_data.get("real_estate", {})
        region  = re.get("region", "기타")
        usage   = re.get("type", "공장")
        area_m2 = re.get("area_m2", 0)
        floors  = re.get("floors", 1)

        region_mult = REGION_MULTIPLIER.get(region, 0.8)
        usage_mult  = USAGE_MULTIPLIER.get(usage, 0.8)
        estimated   = area_m2 * floors * self.BASE_PRICE_PER_SQM * region_mult * usage_mult

        confidence  = "중" if area_m2 > 0 else "낮음"
        formal_needed = estimated > 500_000_000  # 5억 초과 시 정식 감정 권장

        return {
            "agent": "RealEstateDesktopAppraisalAgent",
            "text": (
                f"법인 측면: {region} {usage} {area_m2}㎡ × {floors}층 탁상감정 = 약 {estimated:,.0f}원.\n"
                f"주주(오너) 관점: 신뢰구간 ±20% — 실제 거래 전 정식 감정{'(권장)' if formal_needed else '(선택)'}.\n"
                f"과세관청 관점: 탁상감정은 세무 목적 인정 불가 — 반드시 공인감정 병행.\n"
                f"금융기관 관점: 담보 설정은 공인감정평가서 필수.\n"
                f"신뢰도: {confidence} / 정식 감정 권장: {'예' if formal_needed else '선택'}"
            ),
            "estimated_value": estimated,
            "confidence_level": confidence,
            "formal_appraisal_recommended": formal_needed,
            "require_full_4_perspective": True,
        }

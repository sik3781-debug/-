"""민사신탁 4유형 설계 에이전트 (신탁법 + 상증§4의3)"""
from __future__ import annotations


TRUST_TYPES = {
    "유언대용신탁": {
        "법령": "신탁법 §59",
        "장점": "사망 시 신탁재산 즉시 수익자에게 이전 (상속 절차 불필요)",
        "절세": "상속세 과세가액 포함되나 유류분 분쟁 방지",
        "주의": "타인자본 조달 시 신탁재산 담보 활용 가능",
    },
    "증여신탁": {
        "법령": "신탁법 §2 + 상증§4의3",
        "장점": "단계적 증여 + 10년 합산 공제 활용",
        "절세": "증여시점 평가액 기준 과세 → 저평가 시점 활용",
        "주의": "증여 의제(§4의3) 주의 — 수익자 변경 시 추가 과세",
    },
    "자익신탁": {
        "법령": "신탁법 §2",
        "장점": "위탁자 = 수익자 → 재산 보전·관리 목적",
        "절세": "기업 운영 중 비상장 주식 신탁 → 평가 시점 조절 가능",
        "주의": "소득세 과세 지점 주의",
    },
    "타익신탁": {
        "법령": "신탁법 §2 + 상증§4의3",
        "장점": "위탁자 ≠ 수익자 → 가업승계·차명주식 우회 활용",
        "절세": "수익자 지정 시점 증여세 과세 (분할 납부 가능)",
        "주의": "차명주식 해소 목적 활용 시 §45의2 적용 여부 검토",
    },
}


class CivilTrustAgent:
    def analyze(self, company_data: dict) -> dict:
        purpose = company_data.get("trust_purpose", "가업승계")
        trust_info = TRUST_TYPES.get(purpose, TRUST_TYPES["타익신탁"])

        return {
            "agent": "CivilTrustAgent",
            "text": (
                f"주주(오너) 관점: {purpose} 신탁 — {trust_info['장점']}.\n"
                f"법인 측면: {trust_info['절세']}.\n"
                f"과세관청 관점: {trust_info['법령']} 기준 적법성 확보 필수. {trust_info['주의']}.\n"
                f"금융기관 관점: 신탁재산을 담보로 활용 가능 여부 협의 필요.\n"
                f"4유형 전체: {list(TRUST_TYPES.keys())}"
            ),
            "trust_types": TRUST_TYPES,
            "recommended": purpose,
            "require_full_4_perspective": True,
        }

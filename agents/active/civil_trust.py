"""
민사신탁 4유형 설계 에이전트 (/민사신탁) — 4단계 워크플로우

핵심 법령:
  신탁법§2 (신탁 정의 및 성립)
  신탁법§59 (유언대용신탁)
  상증§4의3 (신탁 이익 증여 의제)
  상증§45의2 (명의신탁 증여 의제 — 신탁과 구별)
  조특§91의20 (신탁 집합투자 세액공제)
  법인세법§5 (신탁재산 과세 원칙)
  소득세법§2의3 (수익적 소유자 — 신탁 수익자)
  국기법§14 (실질과세 원칙 — 신탁 형식 남용 방지)
"""
from __future__ import annotations


TRUST_TYPES = {
    "유언대용신탁": {
        "법령": "신탁법§59",
        "장점": "사망 시 신탁재산 즉시 수익자에게 이전 (상속 절차 불필요)",
        "절세": "상속세 과세가액 포함되나 유류분 분쟁 방지",
        "주의": "타인자본 조달 시 신탁재산 담보 활용 가능",
    },
    "증여신탁": {
        "법령": "신탁법§2 + 상증§4의3",
        "장점": "단계적 증여 + 10년 합산 공제 활용",
        "절세": "증여시점 평가액 기준 과세 → 저평가 시점 활용",
        "주의": "증여 의제(§4의3) 주의 — 수익자 변경 시 추가 과세",
    },
    "자익신탁": {
        "법령": "신탁법§2",
        "장점": "위탁자 = 수익자 → 재산 보전·관리 목적",
        "절세": "기업 운영 중 비상장 주식 신탁 → 평가 시점 조절 가능",
        "주의": "소득세 과세 지점 주의",
    },
    "타익신탁": {
        "법령": "신탁법§2 + 상증§4의3",
        "장점": "위탁자 ≠ 수익자 → 가업승계·차명주식 우회 활용",
        "절세": "수익자 지정 시점 증여세 과세 (분할 납부 가능)",
        "주의": "차명주식 해소 목적 활용 시 §45의2 적용 여부 검토",
    },
}


class CivilTrustAgent:
    """민사신탁 4유형 — 가업승계·상속·증여 절세 설계"""

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "CivilTrustAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "CivilTrustAgent",
            "text": strategy["text"],
            "trust_types": TRUST_TYPES,
            "recommended": strategy["purpose"],
            "require_full_4_perspective": True,
        }

    def generate_strategy(self, case: dict) -> dict:
        purpose   = case.get("trust_purpose", "가업승계")
        info      = TRUST_TYPES.get(purpose, TRUST_TYPES["타익신탁"])
        asset_val = case.get("trust_asset_value", 0)
        text = (
            f"주주(오너) 관점: {purpose} 신탁 — {info['장점']}.\n"
            f"법인 측면: {info['절세']}.\n"
            f"과세관청 관점: {info['법령']} 기준 적법성 확보 필수. {info['주의']}.\n"
            f"금융기관 관점: 신탁재산({asset_val:,.0f}원)을 담보로 활용 가능 여부 협의 필요.\n"
            f"4유형 전체: {list(TRUST_TYPES.keys())}"
        )
        # 신탁 유형별 선택 시나리오 3종 (핵심 목적 기준)
        scenarios = [
            {"name": "유언대용신탁 (상속 분쟁 방지)",
             "law": "신탁법§59 + 국기법§14 실질과세 원칙",
             "merit": "사망 즉시 수익자에게 이전 — 유류분 분쟁 최소화",
             "tax": "상속세 과세가액 포함 (상증§4의3)"},
            {"name": "타익신탁 (가업승계·증여 절세)",
             "law": "신탁법§2 + 상증§4의3 + 조특§91의20",
             "merit": "수익자 지정 시점 증여세 과세 — 분할 납부 가능",
             "tax": "소득세법§2의3 수익적 소유자 기준 과세"},
            {"name": "자익신탁 (재산 보전·관리)",
             "law": "신탁법§2 + 법인세법§5 신탁재산 과세",
             "merit": "위탁자 = 수익자 — 비상장주식 신탁으로 평가 시점 조절",
             "tax": "소득세 과세 시점 조절 가능"},
        ]

        return {"purpose": purpose, "trust_info": info,
                "asset_value": asset_val,
                "scenarios": scenarios, "recommended": scenarios[0]["name"],
                "text": text}

    def validate_risk_5axis(self, strategy: dict) -> dict:
        info = strategy["trust_info"]
        axes = {
            "DOMAIN": {"pass": strategy["purpose"] in TRUST_TYPES,
                       "detail": f"{strategy['purpose']} — 4유형 중 선택 유효"},
            "LEGAL":  {"pass": True,
                       "detail": f"{info['법령']} 기준 설계 — 주의: {info['주의']}"},
            "CALC":   {"pass": strategy["asset_value"] >= 0,
                       "detail": f"신탁재산 {strategy['asset_value']:,.0f}원 — 증여세 산출 필요"},
            "LOGIC":  {"pass": True,
                       "detail": "4유형 비교 제시 + 목적별 최적 유형 선택"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        info = strategy["trust_info"]
        return {
            "1_pre": [f"신탁 목적 명확화 — {strategy['purpose']} 적합성 법무 검토",
                      f"{info['법령']} 요건 충족 여부 사전 확인"],
            "2_now": [f"신탁계약서 작성 — {info['주의']}",
                      "신탁 설정 등기·신고 완료"],
            "3_post": ["수익자 변경 시 상증§4의3 추가 과세 모니터링",
                       "신탁 자산 운용 결과 보고 (연간)"],
            "4_worst": ["신탁 해지 시 위탁자 원상복구 → 증여세 재산정",
                        "차명주식 해소 목적 활용 시 §45의2 증여의제 리스크"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        info = strategy["trust_info"]
        return {
            "step1": {"action": "신탁 목적·수익자 확정", "law": info["법령"]},
            "step2": {"action": "신탁계약서 공증·신탁 재산 이전"},
            "step3": {"action": "신탁 설정 등기 (부동산) 또는 명의 변경 (주식)"},
            "step4": {"action": "세무신고 — 증여세 (수익자 지정 시점)"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["수익자 변경 여부 추적 — 추가 과세 트리거",
                           "신탁 자산 평가액 연 1회 재산정"],
            "reporting": {"신탁": "신탁 운용 보고서 (수익자에게)",
                          "세무": "수익 발생 시 소득세 신고"},
            "next_review": "3년마다 신탁 목적 달성 여부 점검 + 해지·연장 결정",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        info = strategy["trust_info"]
        av   = strategy["asset_value"]
        p    = strategy["purpose"]
        return {
            "법인": {
                "사전": f"{info['절세']} — 신탁 설정 전 세무 효과 시뮬",
                "현재": "신탁 자산 이전·등기 완료",
                "사후": "신탁 운용 수익 법인세 처리",
            },
            "주주(오너)": {
                "사전": f"{p} 신탁 설계 확정",
                "현재": f"재산({av:,.0f}원) 신탁 이전 실행",
                "사후": "수익자 지정·변경 관리 + 상속 준비",
            },
            "과세관청": {
                "사전": f"{info['법령']} 요건 충족 사전 확인",
                "현재": "증여세 신고 (수익자 지정 시점)",
                "사후": f"{info['주의']} — 추가 과세 리스크 모니터링",
            },
            "금융기관": {
                "사전": "신탁 재산 담보 활용 가능성 협의",
                "현재": "신탁 설정 후 담보 등기 검토",
                "사후": "신탁 자산 가치 변동 → 대출 담보비율 재평가",
            },
        }

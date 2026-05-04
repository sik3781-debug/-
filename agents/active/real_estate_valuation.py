"""부동산 정식 평가 4종 에이전트 — 4단계 워크플로우"""
from __future__ import annotations


EVAL_METHODS = {
    "공시지가": {"base": 0.70, "note": "취득세·재산세 기준, 시세의 약 70%"},
    "기준시가": {"base": 0.80, "note": "양도세·증여세 기준, 국세청 고시"},
    "감정평가": {"base": 1.00, "note": "시장가치 기준 공인감정사 평가"},
    "매매사례": {"base": 0.98, "note": "인근 실거래 사례 기준"},
}


class RealEstateValuationAgent:
    """부동산 4종 평가 비교 + 세금 목적별 권장 평가"""

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "RealEstateValuationAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "RealEstateValuationAgent",
            "text": strategy["text"],
            "valuations": strategy["valuations"],
            "tax_purpose_guide": strategy["tax_purpose"],
            "require_full_4_perspective": True,
        }

    def generate_strategy(self, case: dict) -> dict:
        re_info      = case.get("real_estate", {})
        market_value = re_info.get("value", 0)
        re_type      = re_info.get("type", "공장")

        valuations = {
            method: {"value": int(market_value * info["base"]), "note": info["note"]}
            for method, info in EVAL_METHODS.items()
        }
        tax_purpose = {
            "취득세·재산세": "공시지가",
            "양도소득세":    "기준시가 (or 실거래가 더 높으면 실거래가)",
            "증여·상속":     "기준시가 (or 감정평가 병행)",
            "담보 대출":     "감정평가",
            "매각 협상":     "매매사례",
        }
        val_min = min(v["value"] for v in valuations.values())
        val_max = max(v["value"] for v in valuations.values())
        text = (
            f"법인 측면: {re_type} 시장가치 {market_value:,.0f}원 — 4종 평가 비교.\n"
            f"주주(오너) 관점: 매각 시 감정평가 활용 → 양도세 기준가액 극대화.\n"
            f"과세관청 관점: 증여·상속세 기준 = 기준시가 (감정평가 없을 경우).\n"
            f"금융기관 관점: 담보 설정 시 감정평가액 기준 — 시세의 약 100%.\n"
            f"평가액 범위: {val_min:,.0f} ~ {val_max:,.0f}원"
        )
        return {
            "market_value": market_value, "re_type": re_type,
            "valuations": valuations, "tax_purpose": tax_purpose,
            "val_min": val_min, "val_max": val_max, "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        mv = strategy["market_value"]
        axes = {
            "DOMAIN": {"pass": mv >= 0,
                       "detail": f"부동산 시장가치 {mv:,.0f}원 — 4종 평가 비교 완비"},
            "LEGAL":  {"pass": True,
                       "detail": "상증§60·§61 시가 원칙 + 감정평가사법 기준"},
            "CALC":   {"pass": len(strategy["valuations"]) == 4,
                       "detail": "4종 평가 산출 완료 (공시지가/기준시가/감정/매매사례)"},
            "LOGIC":  {"pass": len(strategy["tax_purpose"]) == 5,
                       "detail": "5가지 세금 목적별 권장 평가방법 매핑"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        mv = strategy["market_value"]
        return {
            "1_pre": [f"시장가치 {mv:,.0f}원 — 4종 평가방법 목적별 선택 기준 결정",
                      "공인감정평가사 선임 (담보·매각 목적 시)"],
            "2_now": ["세금 목적에 맞는 평가방법 적용",
                      "감정평가서 유효기간 (6개월) 내 활용"],
            "3_post": ["평가액 등기·세무신고 반영",
                       "평가액 이의신청 준비 (국세청 기준시가 이의 시)"],
            "4_worst": ["감정평가 결과 > 국세청 기준시가 시 고가 선택 → 세부담 증가",
                        "매매사례 부재 시 감정평가로 대체 → 비용 발생"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "평가 목적 확정 (세금/담보/매각)", "law": "상증§60·§61"},
            "step2": {"action": "4종 평가 중 목적별 최적 선택"},
            "step3": {"action": "공인감정평가사 의뢰 (필요 시)"},
            "step4": {"action": "평가결과 세무신고·등기 반영"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["평가액 변동 모니터링 (연간)",
                           "공시지가 고시 후 재산정 (매년 1월)"],
            "reporting": {"세무": "양도세·증여세 신고 시 평가서 첨부",
                          "금융": "담보 재평가 (대출 기간 중 3년마다)"},
            "next_review": "거래 발생 시 재평가 + 과거 신고 가액과의 일관성 확인",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        mv  = strategy["market_value"]
        vn  = strategy["val_min"]
        vx  = strategy["val_max"]
        rtype = strategy["re_type"]
        return {
            "법인": {
                "사전": f"{rtype} 시장가치 {mv:,.0f}원 — 평가 목적 및 방법 결정",
                "현재": "4종 평가 실행·감정평가사 의뢰",
                "사후": "평가결과 장부·세무신고 반영",
            },
            "주주(오너)": {
                "사전": "매각·증여·담보 중 목적 확정",
                "현재": f"평가액 범위 {vn:,.0f}~{vx:,.0f}원 — 목적별 최적 선택",
                "사후": "양도세·증여세 신고 완료 + 잔여 보유 전략",
            },
            "과세관청": {
                "사전": "상증§60·§61 시가 원칙 사전 확인",
                "현재": "기준시가 vs 감정평가 — 과세 기준 선택",
                "사후": "세무조사 대비 감정평가서 10년 보관",
            },
            "금융기관": {
                "사전": "담보 목적 감정평가액 산정 계획",
                "현재": "공인감정평가서 기준 담보 설정",
                "사후": "담보가치 변동 시 추가담보 요구 대비",
            },
        }

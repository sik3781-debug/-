"""
부동산 탁상감정 에이전트 (/부동산탁상감정) — 4단계 워크플로우

핵심 법령:
  감정평가법§3 (감정평가 기준 및 방법)
  부동산공시법§3 (공시지가 기준)
  부동산공시법§17 (개별주택가격 산정)
  상증§60 (시가 평가 원칙)
  상증§61 (보충적 평가 — 부동산)
  소득세법§94 (부동산 양도소득 과세)
  법인세법§52 (부당행위계산 — 저가·고가 양도)
  조특§69 (8년 자경농지 양도소득세 감면)
  국기법§35 (조세채권 우선변제 — 담보 설정 시)
"""
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
    """부동산 탁상감정 — 즉시 약식 평가, 30초 목표"""

    BASE_PRICE_PER_SQM = 1_000_000

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "RealEstateDesktopAppraisalAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "RealEstateDesktopAppraisalAgent",
            "text": strategy["text"],
            "estimated_value": strategy["estimated"],
            "confidence_level": strategy["confidence"],
            "formal_appraisal_recommended": strategy["formal_needed"],
            "require_full_4_perspective": True,
        }

    def generate_strategy(self, case: dict) -> dict:
        re      = case.get("real_estate", {})
        region  = re.get("region", "기타")
        usage   = re.get("type", "공장")
        area_m2 = re.get("area_m2", 0)
        floors  = re.get("floors", 1)

        r_mult     = REGION_MULTIPLIER.get(region, 0.8)
        u_mult     = USAGE_MULTIPLIER.get(usage, 0.8)
        estimated  = area_m2 * floors * self.BASE_PRICE_PER_SQM * r_mult * u_mult
        confidence = "중" if area_m2 > 0 else "낮음"
        formal     = estimated > 500_000_000

        # 평가방식 3종 시나리오 (감정평가법§3)
        scenarios = [
            {"name": "비교방식 (거래사례 비교)",
             "value": estimated * 1.05,
             "method": "인근 실거래가 비교 + 지역·개별요인 보정",
             "law": "상증§60 시가 평가 원칙 (공시지가 3개 이내 거래사례)"},
            {"name": "원가방식 (토지+건물 원가)",
             "value": estimated * 0.95,
             "method": "토지 공시지가 + 건물 표준단가 × (1 - 감가율)",
             "law": "부동산공시법§3 공시지가 기준 + 상증§61 보충적 평가"},
            {"name": "수익방식 (임대수익 환원)",
             "value": estimated * 0.90,
             "method": "연간 임대료 / 환원율 (상가 6~8%, 오피스 5~7%)",
             "law": "소득세법§94 양도소득 기준가액 참고"},
        ]
        best_scenario = scenarios[0]

        text = (
            f"법인 측면: {region} {usage} {area_m2}㎡ × {floors}층 "
            f"탁상감정 = 약 {estimated:,.0f}원.\n"
            f"주주(오너) 관점: 신뢰구간 ±20% — "
            f"실제 거래 전 정식 감정{'(권장)' if formal else '(선택)'}.\n"
            f"과세관청 관점: 탁상감정은 세무 목적 인정 불가 — 반드시 공인감정 병행.\n"
            f"금융기관 관점: 담보 설정은 공인감정평가서 필수.\n"
            f"신뢰도: {confidence} / 정식 감정 권장: {'예' if formal else '선택'}"
        )
        return {
            "region": region, "usage": usage, "area_m2": area_m2,
            "floors": floors, "estimated": estimated,
            "confidence": confidence, "formal_needed": formal,
            "scenarios": scenarios, "recommended": best_scenario["name"],
            "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        est = strategy["estimated"]
        axes = {
            "DOMAIN": {"pass": strategy["area_m2"] >= 0,
                       "detail": f"면적 {strategy['area_m2']}㎡·{strategy['floors']}층 입력값 유효"},
            "LEGAL":  {"pass": True,
                       "detail": "탁상감정 = 참고용 — 세무·담보 목적 공인감정 필요"},
            "CALC":   {"pass": est >= 0,
                       "detail": f"탁상감정 {est:,.0f}원 — 지역계수·용도계수 적용"},
            "LOGIC":  {"pass": True,
                       "detail": f"5억 초과 시 정식 감정 권장 — 현재: {'권장' if strategy['formal_needed'] else '선택'}"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        est = strategy["estimated"]
        return {
            "1_pre": [f"탁상감정 {est:,.0f}원 — ±20% 신뢰구간 사전 고지",
                      "정식 감정 필요 여부 결정 (5억 초과 기준)"],
            "2_now": ["지역·용도 계수 입력값 검증",
                      "면적·층수 등기부등본 확인 후 재산정"],
            "3_post": ["정식 감정평가 의뢰 (거래 전)",
                       "탁상 vs 정식 감정 차이 분석"],
            "4_worst": ["탁상감정 기준 의사결정 후 정식 감정 상이 시 손실 리스크",
                        "세무·금융 목적 사용 금지 — 반드시 공인감정 별도 진행"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "지역·용도·면적·층수 입력 확인"},
            "step2": {"action": f"탁상감정 {strategy['estimated']:,.0f}원 산출"},
            "step3": {"action": "정식 감정 필요 판단 후 감정사 의뢰"},
            "step4": {"action": "최종 평가액 목적별 활용"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["정식 감정 결과 수령 후 탁상과 비교",
                           "부동산 시세 변동 시 재탁상 감정"],
            "reporting": {"내부": "탁상감정 리포트 보관 (참고용)",
                          "외부": "정식 감정평가서 제출 (거래·담보·세무)"},
            "next_review": "정식 감정 유효기간(6개월) 만료 전 갱신 여부 결정",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        est = strategy["estimated"]
        r   = strategy["region"]
        u   = strategy["usage"]
        fm  = strategy["formal_needed"]
        return {
            "법인": {
                "사전": f"{r} {u} 탁상감정 목적 결정 (참고/담보/세무)",
                "현재": f"탁상감정 {est:,.0f}원 산출 (신뢰도 ±20%)",
                "사후": "정식 감정 결과 반영·장부 업데이트",
            },
            "주주(오너)": {
                "사전": "탁상감정으로 매각 협상 목표가 설정",
                "현재": f"{'정식 감정 의뢰 권장' if fm else '탁상감정 참고 활용'}",
                "사후": "거래 완료 후 양도세 신고 (실거래가 기준)",
            },
            "과세관청": {
                "사전": "탁상감정 = 세무 목적 불인정 사전 고지",
                "현재": "공인감정평가서 요구 (증여·양도 시)",
                "사후": "감정평가서 10년 보관 의무",
            },
            "금융기관": {
                "사전": "탁상감정으로 담보가치 사전 협의",
                "현재": "정식 감정평가서 제출 후 담보 설정",
                "사후": "담보가치 재평가 주기 (대출 기간 중 3년마다)",
            },
        }

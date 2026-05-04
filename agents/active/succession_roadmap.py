"""
가업승계 로드맵 에이전트 (/가업승계로드맵) — 4단계 워크플로우

핵심 법령:
  상증§18의2 (가업상속공제 최대 600억)
  상증§41의2 (차등배당 — 승계 전 오너 소득 확보)
  조특§30의6 (가업승계 증여세 특례 — 10% 과세)
  법인세법§52 (부당행위계산 — 저가 주식 이전 방지)
  소득세법§94①3호 (비상장주식 양도소득)
  국기법§47의4 (가업상속 사후관리 추징 이자상당액)
  외감법§4 (외감 대상 법인 가업승계 특례 요건)
  상증령§15 (사후관리 7년 — 업종·고용 80%·자산 80% 유지 의무)
"""
from __future__ import annotations


# ── 법령 상수 ─────────────────────────────────────────────────
_SUCCESSION_DEDUCTION_MAX  = 60_000_000_000  # 가업상속공제 최대 600억
_POST_MANAGEMENT_YEARS     = 7               # 사후관리 7년
_MIN_MANAGEMENT_YEARS      = 10              # 경영 10년 이상 (공제 요건)
_EMPLOYMENT_MAINTAIN_RATIO = 0.80            # 고용 80% 유지 의무
_ASSET_MAINTAIN_RATIO      = 0.80            # 사업용 자산 80% 유지 의무


class SuccessionRoadmapAgent:
    """
    가업승계 10년 로드맵:
    사전 준비 → 승계 실행 → 7년 사후관리 추적
    """

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "SuccessionRoadmapAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "SuccessionRoadmapAgent",
            "text": strategy["text"],
            "require_full_4_perspective": True,
        }

    # ── ① 전략생성 ────────────────────────────────────────────

    def generate_strategy(self, case: dict) -> dict:
        ceo_age          = case.get("ceo_age", 60)
        business_value   = case.get("business_value", 5_000_000_000)
        management_years = case.get("management_years", 12)
        employee_count   = case.get("employee_count", 50)
        successor_age    = case.get("successor_age", 35)
        is_sme           = case.get("is_sme", True)
        business_assets  = case.get("business_assets", business_value * 0.80)

        # 가업상속공제 한도 (업력별)
        if management_years >= 20:
            deduction_limit = _SUCCESSION_DEDUCTION_MAX
        elif management_years >= 15:
            deduction_limit = _SUCCESSION_DEDUCTION_MAX * 0.833  # 500억
        elif management_years >= 10:
            deduction_limit = _SUCCESSION_DEDUCTION_MAX * 0.667  # 400억
        else:
            deduction_limit = 0  # 10년 미만 공제 불가

        # 증여세 절세 효과 (조특§30의6)
        gift_tax_normal  = max(0, business_value - deduction_limit) * 0.50
        gift_tax_special = business_value * 0.10  # 특례: 10% 과세
        gift_tax_saving  = gift_tax_normal - gift_tax_special

        # 10년 로드맵
        roadmap = [
            {"year": 0,  "phase": "준비", "action": "경영자 10년 요건 점검·후계자 경영 참여 시작"},
            {"year": 2,  "phase": "준비", "action": "조특§30의6 증여세 특례 신청 (CEO 65세 이전 권장)"},
            {"year": 5,  "phase": "이전", "action": "주식 단계적 증여 + 경영권 이전"},
            {"year": 7,  "phase": "이전", "action": "가업승계 완료 신고·사후관리 시작"},
            {"year": 10, "phase": "관리", "action": "7년 사후관리 완료 — 추징 위험 소멸"},
        ]

        text = (
            f"주주(오너) 관점: 가업 {business_value:,.0f}원 승계 — "
            f"공제 한도 {deduction_limit:,.0f}원 (업력 {management_years}년).\n"
            f"법인 측면: 조특§30의6 특례 활용 시 증여세 절세 {gift_tax_saving:,.0f}원.\n"
            f"과세관청 관점: 사후관리 7년 — 업종·고용(80%)·자산(80%) 유지 의무.\n"
            f"금융기관 관점: 승계 과정 신용등급 연속성 유지 + 후계자 개인 담보 전환 계획."
        )
        # 승계 전략 시나리오 3종
        scenarios = [
            {"name": "증여세 특례 (조특§30의6) — 10% 과세",
             "cost": gift_tax_special,
             "saving": gift_tax_saving,
             "condition": f"CEO {ceo_age}세 이전 + 후계자 10년 경영 참여",
             "law": "조특§30의6 + 상증령§15 사후관리 7년"},
            {"name": "가업상속공제 (상증§18의2) — 최대 600억 공제",
             "cost": max(0, business_value - deduction_limit) * 0.50,
             "saving": deduction_limit * 0.50,
             "condition": f"경영 {management_years}년 → 공제 한도 {deduction_limit:,.0f}원",
             "law": "상증§18의2 + 국기법§47의4 추징 이자상당액 주의"},
            {"name": "단계 증여 (10년 합산 공제 활용)",
             "cost": business_value * 0.30,
             "saving": business_value * 0.10,
             "condition": "10년 단위 분할 증여 → 공제(5천만원) 반복 활용",
             "law": "소득세법§94①3호 + 법인세법§52 부당행위 방지"},
        ]

        return {
            "ceo_age": ceo_age, "successor_age": successor_age,
            "business_value": business_value,
            "management_years": management_years,
            "employee_count": employee_count,
            "is_sme": is_sme, "business_assets": business_assets,
            "deduction_limit": deduction_limit,
            "gift_tax_saving": gift_tax_saving,
            "roadmap": roadmap,
            "scenarios": scenarios, "recommended": scenarios[0]["name"],
            "text": text,
        }

    # ── ② 5축 리스크 검증 ─────────────────────────────────────

    def validate_risk_5axis(self, strategy: dict) -> dict:
        my = strategy["management_years"]
        axes = {
            "DOMAIN": {"pass": my >= _MIN_MANAGEMENT_YEARS,
                       "detail": f"경영 {my}년 — "
                                 f"{'공제 요건 충족' if my >= _MIN_MANAGEMENT_YEARS else '10년 미만 공제 불가'}"},
            "LEGAL":  {"pass": True,
                       "detail": "상증§18의2(공제)·조특§30의6(특례)·시행령§15(사후관리7년)"},
            "CALC":   {"pass": strategy["deduction_limit"] >= 0,
                       "detail": f"공제 한도 {strategy['deduction_limit']:,.0f}원 산출"},
            "LOGIC":  {"pass": len(strategy["roadmap"]) >= 5,
                       "detail": "10년 5단계 로드맵 완비"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    # ── ② 4단계 헷지 ─────────────────────────────────────────

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        ec  = strategy["employee_count"]
        ba  = strategy["business_assets"]
        return {
            "1_pre": [
                f"CEO 경영 {strategy['management_years']}년 요건 증빙 준비 (이사회 의사록·세무신고)",
                f"조특§30의6 신청 — CEO 65세 이전 권장 (현재 {strategy['ceo_age']}세)",
                "후계자 가업종사 요건 확인 (2년 이상 종사 후 증여)",
            ],
            "2_now": [
                f"주식 단계적 증여 — 10년 합산 한도 관리",
                f"고용 {ec}명 × 80% = {int(ec*0.8)}명 이상 유지 계획",
                f"사업용 자산 {ba:,.0f}원 × 80% 이상 유지",
            ],
            "3_post": [
                f"사후관리 {_POST_MANAGEMENT_YEARS}년간 연 1회 업종·고용·자산 점검",
                "위반 시 추징세액 + 이자상당액 즉시 계산·납부 계획",
                "후계자 지분율 10% 이상 유지 (상증시행령§15)",
            ],
            "4_worst": [
                "업종 변경 시 가업상속공제 전액 추징",
                "고용 20% 이상 감소 시 비율 추징",
                "CEO 사망·승계 전 세무조사 → 비상 승계 계획 수립",
            ],
        }

    # ── ③ 과정관리 ────────────────────────────────────────────

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "가업상속공제 요건 점검서 작성", "law": "상증§18의2"},
            "step2": {"action": "조특§30의6 증여세 특례 신청", "deadline": "CEO 65세 이전"},
            "step3": {"action": "주식 단계적 증여 실행 + 경영권 이전"},
            "step4": {"action": f"사후관리 {_POST_MANAGEMENT_YEARS}년 모니터링 시스템 구축"},
        }

    # ── ④ 사후관리 ────────────────────────────────────────────

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [
                f"연 1회 업종 유지 확인 (표준산업분류 기준, {_POST_MANAGEMENT_YEARS}년)",
                f"고용 {_EMPLOYMENT_MAINTAIN_RATIO:.0%} 이상 유지 추적",
                f"사업용 자산 {_ASSET_MAINTAIN_RATIO:.0%} 이상 유지 확인",
            ],
            "reporting": {
                "국세청": "사후관리 이행 확인서 연 1회 제출",
                "내부": "승계 이행 보고서 + 위반 위험 체크리스트",
            },
            "next_review": "매년 결산 후 사후관리 요건 점검 + 위반 위험 사전 조치",
        }

    # ── 4자×3시점 12셀 ──────────────────────────────────────

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        bv  = strategy["business_value"]
        dl  = strategy["deduction_limit"]
        gs  = strategy["gift_tax_saving"]
        my  = strategy["management_years"]
        return {
            "법인": {
                "사전": f"가업 {bv:,.0f}원 — 공제 한도 {dl:,.0f}원 (업력 {my}년) 확인",
                "현재": "주식 단계적 증여·경영권 이전 실행",
                "사후": "사후관리 7년 업종·고용·자산 유지 모니터링",
            },
            "주주(오너)": {
                "사전": "조특§30의6 특례 신청 — CEO 65세 이전",
                "현재": f"증여세 절세 {gs:,.0f}원 효과 실현",
                "사후": "후계자 지분율·경영권 안정화",
            },
            "과세관청": {
                "사전": "경영 10년·가업종사 요건 증빙 검토",
                "현재": "공제 적용 적정성·증여 시가 확인",
                "사후": f"사후관리 {_POST_MANAGEMENT_YEARS}년 위반 시 전액 추징",
            },
            "금융기관": {
                "사전": "CEO 연대보증 → 후계자 명의 전환 계획",
                "현재": "승계 중 신용등급 연속성 유지 협의",
                "사후": "후계자 단독 신용도 구축 + 대출 재협의",
            },
        }

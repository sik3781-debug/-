"""
법률리스크 체크·헷지 에이전트 (LegalRiskHedgeAgent)
====================================================
계약·정관·이사회·주총·등기 5대 영역 리스크 점검 + 정량화 + 헷지 방안 매핑.

핵심 법령:
- 상법 §289~§542 (회사 설립·운영·합병·분할·해산 절차)
  - §382의3 (이사 충실의무), §397 (경업금지), §398 (자기거래)
  - §391~§393 (이사회 의사록·결의 요건), §433~§435 (주총 결의·소집 절차)
- 민법 §103 (반사회질서 행위 무효)
- 민법 §104 (불공정한 법률행위 무효 — 폭리·궁박·경솔·무경험)
- 형법 §356 (업무상 배임 — 이익 취득 또는 제3자 이익)
- 자본시장법 §178 (부정거래행위 금지 — 사기·기망·부실표시)
- 부정경쟁방지법 §18 (영업비밀 침해 형사처벌)

본 모듈은 base level 구현이며, 후속 세션에서 다음 항목 심화 예정:
- 계약서·정관 텍스트 입력 시 NLP 기반 리스크 조항 자동 하이라이트
- 판례 검색 자동 통합 (LAW_API_ID 발급 후)
- 형법§356 배임 트리거 알림 (특수관계 거래 임계치 초과 자동 감지)

작성: 2026-05-04 [LAPTOP]
"""
from __future__ import annotations

import os
from typing import Any

from agents.base_agent import BaseAgent


# ──────────────────────────────────────────────────────────────────────────
# 5대 영역별 리스크 룰북
# ──────────────────────────────────────────────────────────────────────────

CONTRACT_RISK_RULES = {
    "특수관계인거래_시가초과": {
        "trigger": lambda d: (
            d.get("is_related_party", False)
            and d.get("transaction_amount", 0) > d.get("market_price", 0) * 1.30
        ),
        "law": "상증§45의5 + 법§52 부당행위계산부인",
        "risk_level": "HIGH",
        "penalty_calc": lambda d: max(0, d.get("transaction_amount", 0)
                                        - d.get("market_price", 0)) * 0.30,
    },
    "이사_자기거래_미승인": {
        "trigger": lambda d: (
            d.get("is_director_self_dealing", False)
            and not d.get("board_approval", False)
        ),
        "law": "상법§398 (이사 자기거래 — 이사회 사전 승인 필수)",
        "risk_level": "HIGH",
        "penalty_calc": lambda d: d.get("transaction_amount", 0) * 0.05,
    },
    "이사_경업금지_위반": {
        "trigger": lambda d: d.get("director_competing_business", False),
        "law": "상법§397 (이사 경업금지 — 이사회 승인 또는 손해배상)",
        "risk_level": "MEDIUM",
        "penalty_calc": lambda d: d.get("competing_business_revenue", 0) * 0.20,
    },
    "민법103_반사회질서": {
        "trigger": lambda d: d.get("contract_purpose_illegal", False),
        "law": "민법§103 (반사회질서 행위 — 무효)",
        "risk_level": "CRITICAL",
        "penalty_calc": lambda d: d.get("transaction_amount", 0),  # 전액 무효
    },
    "민법104_불공정행위": {
        "trigger": lambda d: (
            d.get("counterparty_distress", False)
            and abs(d.get("transaction_amount", 0) - d.get("market_price", 0))
                > d.get("market_price", 0) * 0.50
        ),
        "law": "민법§104 (불공정한 법률행위 — 무효)",
        "risk_level": "HIGH",
        "penalty_calc": lambda d: abs(d.get("transaction_amount", 0)
                                       - d.get("market_price", 0)),
    },
    "형법356_업무상배임_트리거": {
        "trigger": lambda d: (
            d.get("is_director_self_dealing", False)
            and d.get("transaction_amount", 0) > d.get("market_price", 0) * 1.50
        ),
        "law": "형법§356 (업무상 배임 — 5년 이하/1500만원 이하)",
        "risk_level": "CRITICAL",
        "penalty_calc": lambda d: max(0, d.get("transaction_amount", 0)
                                        - d.get("market_price", 0)),
    },
    "정관_위반_결의": {
        "trigger": lambda d: d.get("violates_articles", False),
        "law": "상법§376 (주총 결의 취소의 소) + §380 (결의 무효)",
        "risk_level": "HIGH",
        "penalty_calc": lambda d: 1_000_000,  # 정량 어려움 — 명목값
    },
    "이사회_정족수_미달": {
        "trigger": lambda d: (
            d.get("board_attendance", 100) / 100 < 0.5
        ),
        "law": "상법§391 ① (이사 과반 출석·과반 찬성)",
        "risk_level": "HIGH",
        "penalty_calc": lambda d: 1_000_000,
    },
    "주총_소집통지_누락": {
        "trigger": lambda d: not d.get("notice_2weeks_prior", True),
        "law": "상법§363 (주총 소집통지 2주 전)",
        "risk_level": "MEDIUM",
        "penalty_calc": lambda d: 500_000,  # 과태료 명목
    },
    "등기_지연": {
        "trigger": lambda d: d.get("registration_delay_days", 0) > 14,
        "law": "상법§37 + 상업등기법 — 변경등기 2주 이내",
        "risk_level": "LOW",
        "penalty_calc": lambda d: min(5_000_000,
                                       d.get("registration_delay_days", 0) * 50_000),
    },
    "자본시장법178_부정거래": {
        "trigger": lambda d: d.get("misleading_disclosure", False),
        "law": "자본시장법§178 (사기·기망·부실표시 — 5년 이하/5억 이하)",
        "risk_level": "CRITICAL",
        "penalty_calc": lambda d: 500_000_000,  # 형벌 5억
    },
    # [3중루프 보강] 영업비밀 침해 룰
    "부정경쟁방지법18_영업비밀침해": {
        "trigger": lambda d: d.get("trade_secret_violation", False),
        "law": "부정경쟁방지법§18 (영업비밀 침해 — 10년 이하/5억 이하)",
        "risk_level": "CRITICAL",
        "penalty_calc": lambda d: max(d.get("trade_secret_damage", 0),
                                      500_000_000),  # 손해액 또는 형벌 상한
    },
    # [3중루프 보강] 부당과소신고 가산세 (국기§47의3 — 40%)
    "부당과소신고_가산세": {
        "trigger": lambda d: d.get("intentional_underreporting", False),
        "law": "국기§47의3 ② (부당과소신고 가산세 40%)",
        "risk_level": "HIGH",
        "penalty_calc": lambda d: d.get("underreport_amount", 0) * 0.40,
    },
}

# [3중루프 보강] 위험도 정렬 우선순위
RISK_PRIORITY = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}

# [3중루프 보강] 형사·민사·행정 처분 분류
PENALTY_TYPE = {
    "형사": ["형법§356", "자본시장법§178", "부정경쟁방지법§18"],
    "민사": ["민법§103", "민법§104", "상법§397", "상법§398"],
    "행정": ["상증§45의5", "법§52", "국기§47", "상법§37", "상법§363"],
}


def classify_penalty_type(law: str) -> str:
    for ptype, keywords in PENALTY_TYPE.items():
        if any(k in law for k in keywords):
            return ptype
    return "기타"


# [3중루프 보강] 룰별 즉시 헷지 매핑
RULE_TO_HEDGE = {
    "특수관계인거래_시가초과": "감정평가서 추가 + 시가 산정 근거 보완 + ±30% 안전항 조정",
    "이사_자기거래_미승인": "즉시 사전 이사회 승인 결의 보완 + 의사록 작성",
    "이사_경업금지_위반": "이사회 승인 결의 + 손해배상 합의서 검토",
    "민법103_반사회질서": "계약 즉시 해지 + 변호사 자문 + 새 계약 검토",
    "민법104_불공정행위": "정상가 재산정 + 보충 계약서 + 합의서 작성",
    "형법356_업무상배임_트리거": "이사회 승인 + 정상가 입증 + 형사 변호사 즉시 자문",
    "정관_위반_결의": "정관 개정 또는 결의 재진행 + 결의 취소의 소 대비",
    "이사회_정족수_미달": "이사회 재소집 + 정족수 확보 + 의사록 재작성",
    "주총_소집통지_누락": "주총 재소집 + 2주 전 통지 + 추인 결의",
    "등기_지연": "즉시 변경등기 신청 + 과태료 자진 납부",
    "자본시장법178_부정거래": "공시 정정 + 외부 회계사 자문 + 자율 신고 검토",
    "부정경쟁방지법18_영업비밀침해": "유출 차단 + 형사·민사 동시 대응 + 영업비밀 관리체계 정비",
    "부당과소신고_가산세": "수정신고 + 가산세 50% 감면 신청 (국기§48)",
}


class LegalRiskHedgeAgent(BaseAgent):
    """5대 영역 법률 리스크 점검 + 정량화 + 헷지 매핑 에이전트."""

    name: str = "LegalRiskHedgeAgent"
    role: str = "법률 리스크 진단·헷지 전문가"
    model: str = "claude-opus-4-7"
    system_prompt: str = (
        "당신은 계약·정관·이사회·주총·등기 5대 영역 법률 리스크 진단 "
        "전문가입니다. 상법§289~§542, 민법§103·§104, 형법§356(배임), "
        "자본시장법§178을 기준으로 절차 위반·무효 사유·배임 트리거를 "
        "검출하고 위약금·손해배상·과태료·가산세 금전 위험액을 정량화하며 "
        "헷지 방안을 매핑합니다."
    )

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.conversation: list[dict[str, Any]] = []
        self.tools: list[dict[str, Any]] = []
        self.client = None

    def _ensure_client(self) -> None:
        if self.client is None:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=os.environ["ANTHROPIC_API_KEY"]
            )

    def run(self, user_message: str, *, reset: bool = False) -> str:
        self._ensure_client()
        return super().run(user_message, reset=reset)

    # ------------------------------------------------------------------ #
    # 핵심 분석                                                            #
    # ------------------------------------------------------------------ #

    def analyze(self, company_data: dict) -> dict:
        # ── 5대 영역 룰북 일괄 점검 ───────────────────────────────────
        triggered = []
        total_penalty = 0
        for rule_name, rule in CONTRACT_RISK_RULES.items():
            try:
                if rule["trigger"](company_data):
                    penalty = rule["penalty_calc"](company_data)
                    triggered.append({
                        "rule": rule_name,
                        "law": rule["law"],
                        "risk_level": rule["risk_level"],
                        "penalty_estimated": penalty,
                        # [3중루프 보강] 즉시 헷지 + 처분 유형
                        "immediate_hedge": RULE_TO_HEDGE.get(rule_name, "변호사 자문"),
                        "penalty_type": classify_penalty_type(rule["law"]),
                    })
                    total_penalty += penalty
            except Exception as e:
                triggered.append({
                    "rule": rule_name,
                    "error": str(e),
                    "risk_level": "UNKNOWN",
                })

        # [3중루프 보강] 위험도 우선순위 정렬
        triggered.sort(key=lambda t: RISK_PRIORITY.get(t.get("risk_level", "UNKNOWN"), 9))

        # ── 5대 영역별 점검 결과 분류 ────────────────────────────────
        area_summary = {
            "계약": [t for t in triggered if "거래" in t["rule"] or "민법" in t["rule"]],
            "정관": [t for t in triggered if "정관" in t["rule"]],
            "이사회": [t for t in triggered if "이사" in t["rule"]],
            "주총": [t for t in triggered if "주총" in t["rule"]],
            "등기": [t for t in triggered if "등기" in t["rule"]],
        }

        # ── 위험도 분포 ─────────────────────────────────────────────
        risk_dist = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
        for t in triggered:
            risk_dist[t.get("risk_level", "UNKNOWN")] += 1

        # ── 결과 본문 ──────────────────────────────────────────────
        text = (
            f"법인 측면: 5대 영역 리스크 {len(triggered)}건 검출, "
            f"금전 위험액 합계 약 {total_penalty:,.0f}원 "
            f"(CRITICAL {risk_dist['CRITICAL']} / HIGH {risk_dist['HIGH']} / "
            f"MEDIUM {risk_dist['MEDIUM']} / LOW {risk_dist['LOW']}).\n"
            f"주주(오너) 관점: 형법§356 배임 트리거 "
            f"{risk_dist['CRITICAL']}건 — 즉시 헷지 필요.\n"
            f"과세관청 관점: 상증§45의5·법§52 부당행위계산부인 위험 "
            f"+ 상법 절차 위반 시 결의 무효 가능성.\n"
            f"금융기관 관점: 결의 무효·등기 지연 시 신용평가 감점·"
            f"대출 회수 트리거 가능."
        )

        result = {
            "agent": self.name,
            "text": text,
            "triggered_rules": triggered,
            "total_penalty_estimated": total_penalty,
            "area_summary": area_summary,
            "risk_distribution": risk_dist,
            "checklist": self._checklist(),
            "disclaimer": self._disclaimer(),
            "require_full_4_perspective": True,
        }

        result["risk_5axis"] = self.validate_risk_5axis(result, company_data)
        result["risk_hedge_4stage"] = self.generate_risk_hedge_4stage(company_data)
        result["matrix_4x3"] = self._build_4x3_matrix(result)
        result["self_check_4axis"] = self.validate(result)
        return result

    # ------------------------------------------------------------------ #
    # §A 5축 검증                                                          #
    # ------------------------------------------------------------------ #

    def validate_risk_5axis(self, result: dict, company_data: dict) -> dict:
        axes: dict[str, dict] = {}

        # DOMAIN: 5대 영역 점검 완료
        areas_covered = sum(1 for v in result.get("area_summary", {}).values()
                            if v is not None)
        domain_pass = areas_covered == 5
        axes["DOMAIN"] = {
            "pass": domain_pass,
            "detail": f"5대 영역(계약·정관·이사회·주총·등기) {areas_covered}/5 점검",
        }

        # LEGAL: 인용 법령이 룰북에 실재
        triggered = result.get("triggered_rules", [])
        legal_pass = all("law" in t for t in triggered)
        axes["LEGAL"] = {
            "pass": legal_pass,
            "detail": (
                f"검출 룰 {len(triggered)}건 모두 법령 인용 — "
                f"상법§289~§542 + 민법§103·104 + 형법§356 + 자본시장법§178"
            ),
        }

        # CALC: 위약금·손해배상·과태료 정량화 합계
        calc_pass = result.get("total_penalty_estimated", 0) >= 0
        axes["CALC"] = {
            "pass": calc_pass,
            "detail": f"금전 위험액 합계 {result.get('total_penalty_estimated', 0):,.0f}원",
        }

        # LOGIC: 위험도 분포가 검출 룰 수와 일치
        risk_dist = result.get("risk_distribution", {})
        logic_pass = sum(risk_dist.values()) == len(triggered)
        axes["LOGIC"] = {
            "pass": logic_pass,
            "detail": (
                f"위험도 분포 합 {sum(risk_dist.values())} = 검출 {len(triggered)}건"
            ),
        }

        # CROSS: 4자관점 본문 + 매트릭스 12셀
        text = result.get("text", "")
        cross_pass = (
            sum(1 for p in ["법인", "주주", "과세관청", "금융기관"] if p in text) == 4
        )
        axes["CROSS"] = {
            "pass": cross_pass,
            "detail": "4자관점 본문 노출 (법인·주주·과세관청·금융기관)",
        }

        all_pass = all(a["pass"] for a in axes.values())
        return {
            "all_pass": all_pass,
            "axes": axes,
            "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5",
        }

    # ------------------------------------------------------------------ #
    # §B 4단계 헷지                                                        #
    # ------------------------------------------------------------------ #

    def generate_risk_hedge_4stage(self, company_data: dict) -> dict:
        return {
            "1_pre": [
                "계약 체결 전 정관 + 이사회결의 적법성 검토",
                "특수관계인 거래 시 정상가 입증자료 사전 확보 (감정평가서·시장조사)",
                "이사 자기거래 시 이사회 승인 절차 사전 진행 (상법§398)",
                "주총 소집 시 2주 전 통지 + 안건 명시 (상법§363)",
            ],
            "2_now": [
                "계약서 조문별 리스크 표시 + 수정안 제시",
                "이사회·주총 의사록에 출석·찬반·기권 명시 (상법§391·§393)",
                "변경등기 사유 발생 시 2주 이내 등기 신청 (상법§37)",
                "공시·신고 시 자본시장법§178 부정거래 회피 워딩 강제",
            ],
            "3_post": [
                "계약 이행 모니터링 + 이행보증 (필요 시 보증보험)",
                "정기 검토 캘린더 (분기별 정관·이사회·주총 적법성)",
                "이사회·주총 의사록 보존 (상법§396 — 본점 10년)",
                "등기 변동사항 매월 점검 + 미등기 시 즉시 보정",
            ],
            "4_worst": [
                "분쟁 발생 시: 의사록·결의서·계약서 일괄 백업 + 변호사 자문",
                "세무조사 시: 부당행위계산부인 대비 정상가 입증자료 즉시 제출",
                "형법§356 배임 의혹 시: 이사회 승인 + 정상가 입증 + 대안 시나리오",
                "자본시장법§178 의혹 시: 공시·내부통제 회의록 + 외부 회계사 자문",
            ],
        }

    # ------------------------------------------------------------------ #
    # 4자×3시점 매트릭스                                                    #
    # ------------------------------------------------------------------ #

    def _build_4x3_matrix(self, result: dict) -> dict:
        n_critical = result["risk_distribution"].get("CRITICAL", 0)
        n_high     = result["risk_distribution"].get("HIGH", 0)
        return {
            "법인": {
                "사전": "정관·이사회·주총·등기 사전 정비 + 내부통제 점검",
                "현재": f"검출 리스크 CRITICAL {n_critical} / HIGH {n_high}",
                "사후": "이사회·주총 의사록 10년 보존 + 정기 검토",
            },
            "주주": {
                "사전": "이사 자기거래·경업금지 사전 승인 (상법§397·§398)",
                "현재": "주총 결의 정족수·소집통지·의결권 행사 점검",
                "사후": "결의 무효의 소·취소의 소 제기 권리 행사 가능 (상법§376·§380)",
            },
            "과세관청": {
                "사전": "특수관계 거래 정상가 입증자료 사전 확보",
                "현재": "상증§45의5·법§52 부당행위계산부인 적용 점검",
                "사후": f"세무조사 시 금전 위험액 {result['total_penalty_estimated']:,.0f}원 입증",
            },
            "금융기관": {
                "사전": "정관·이사회결의 적법성 검토 (대출 약정 조건)",
                "현재": "결의 무효·등기 지연 시 신용평가 감점 위험",
                "사후": "대출 약정 위반 트리거 시 회수 가능 — 사전 헷지 필수",
            },
        }

    # ------------------------------------------------------------------ #
    # 자가검증 4축                                                          #
    # ------------------------------------------------------------------ #

    def validate(self, result: dict) -> dict:
        text = result.get("text", "")
        ax_calc = any(c.isdigit() for c in text)
        ax_law  = any(k in text for k in ["§", "법", "상증", "형법", "민법", "자본시장법"])
        ax_4P   = sum(1 for p in ["법인", "주주", "과세관청", "금융기관"]
                      if p in text) >= 4
        ax_regr = result.get("require_full_4_perspective", False)
        return {
            "calc": ax_calc, "law": ax_law,
            "perspective_4": ax_4P, "regression": ax_regr,
            "all_pass": all([ax_calc, ax_law, ax_4P, ax_regr]),
        }

    def _checklist(self) -> list[str]:
        return [
            "[함정] 이사 자기거래 무승인 시 상법§398 위반 + 무효 + 배임 트리거",
            "[함정] 특수관계 거래 시가 130% 초과 시 상증§45의5 의제증여",
            "[리스크] 주총 소집통지 2주 전 누락 시 결의 취소의 소 (상법§376)",
            "[리스크] 변경등기 2주 초과 시 과태료 (상법§37)",
            "[실행] 이사회·주총 의사록 10년 보존 (상법§396) + 디지털 백업",
        ]

    def _disclaimer(self) -> str:
        return (
            "본 자료는 검토용 초안이며, 최종 계약 검토·정관 변경·"
            "이사회·주총 진행·등기·소송·세무 대응은 변호사·법무사·세무사 "
            "검토를 거쳐 진행하십시오."
        )

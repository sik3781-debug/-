"""
사업계획서 에이전트 (BusinessPlanAgent — 정식 통합본)
=====================================================
정책자금·가업승계 사후관리·기업인증·IPO 대비 5년 사업계획서 자동 생성.

본 파일은 PART6 신설 (Pro 접미사) → PART7 통합 (Pro 제거) 정식 단일화 결과물.
구 agents/business_plan_agent.py (LLM 기반 BusinessPlanAgent)는 deprecation
re-export로 대체되어 본 모듈로 자동 라우팅됨 (v1.1.0 / 2026-11-04 자동 삭제).

핵심 법령:
- 중소기업기본법 §2 (중소기업 적격성 — 매출·자산 기준)
- 벤처기업법 §2의2 (벤처기업 인증 요건)
- 조특§6 (창업중소기업 세액감면 5년 50~100%)
- 조특§7 (중소기업 특별세액감면 5~30%)
- 자본시장법 §178 (부정거래·과장 금지) — 추정치 면책 워딩 강제
- 신용보증기금·기술보증기금·중진공 신용평가 기준

본 모듈은 base level 구현이며, 후속 세션에서 다음 항목 심화 예정:
- DART 동종업종 비교 자동 호출 (DART_API_KEY 발급 후)
- 정책자금 신·기보·중진공·KIBO 자동 매칭 (현재는 적격성 분류만)
- 추정재무제표 → pptx + xlsx 산출물 자동 생성

작성: 2026-05-04 [LAPTOP]
"""
from __future__ import annotations

import os
from typing import Any

from agents.base_agent import BaseAgent


# ──────────────────────────────────────────────────────────────────────────
# 법령 상수
# ──────────────────────────────────────────────────────────────────────────

# 중소기업기본법§2 + 시행령 별표1 — 업종별 평균매출 상한 (단순화)
SME_REVENUE_CEILING = {
    "제조업": 150_000_000_000,   # 1,500억
    "건설업": 100_000_000_000,   # 1,000억
    "도소매": 100_000_000_000,
    "정보통신": 80_000_000_000,
    "기타":  40_000_000_000,
}

# 조특§6 창업중소기업 세액감면 (수도권 외 청년창업 100% / 일반 50%)
STARTUP_TAX_RELIEF = {
    "수도권외_청년": 1.00,    # 100% 감면 (5년)
    "수도권외_일반": 0.50,    # 50%
    "수도권_청년":  0.50,
    "수도권_일반":  0.00,
}

# 정책자금 적격성 키워드 매핑
POLICY_FUND_MATCH = {
    "신용보증기금":   {"min_yrs": 1,  "max_debt_ratio": 500, "purpose": "운전·시설"},
    "기술보증기금":   {"min_yrs": 1,  "max_debt_ratio": 500, "purpose": "기술·R&D"},
    "중소벤처기업진흥공단": {"min_yrs": 0, "max_debt_ratio": 300, "purpose": "정책자금"},
    "IBK기업은행":   {"min_yrs": 1,  "max_debt_ratio": 400, "purpose": "운전·시설"},
}


class BusinessPlanAgent(BaseAgent):
    """정책자금·가업승계·인증·IPO 대비 5년 사업계획서 작성 에이전트.

    PART6→PART7 통합본. 구 agents/business_plan_agent.py:BusinessPlanAgent
    (LLM 기반 본문 생성)는 deprecation 처리되었으며, 본 클래스가 정식.
    LLM 기반 본문 생성 능력은 후속 세션에서 narrative 메서드로 보강 예정.
    """

    name: str = "BusinessPlanAgent"
    role: str = "정책자금·가업승계 사업계획서 전문가"
    model: str = "claude-opus-4-7"
    system_prompt: str = (
        "당신은 정책자금 신청·가업승계 사후관리·기업인증용 사업계획서 "
        "작성 전문가입니다. 중소기업기본법§2 적격성, 조특§6·§7 세액감면, "
        "자본시장법§178 부정거래 금지를 기준으로 5년 추정재무제표·BEP·"
        "민감도 3시나리오(낙관·중립·비관)·정책자금 매칭·SWOT을 작성합니다. "
        "추정치는 자본시장법§178 회피를 위해 가정·근거를 명시하고 면책 "
        "워딩을 자동 삽입합니다."
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
        n        = company_data.get("company_name", "대상법인")
        ind      = company_data.get("industry", "제조업")
        rev      = company_data.get("current_revenue", 0)
        gr       = company_data.get("growth_rate_assumption", 0.10)
        capex    = company_data.get("capex_plan", 0)
        debt     = company_data.get("total_debt", 0)
        equity   = company_data.get("total_equity", 1)
        op_margin = company_data.get("operating_margin", 0.08)
        purpose  = company_data.get("purpose", "정책자금")
        yrs      = company_data.get("years_in_operation", 5)
        is_youth = company_data.get("ceo_under_34", False)
        in_seoul = company_data.get("location_seoul_metro", True)

        # ── 1. 중소기업기본법§2 적격성 ───────────────────────────────
        sme_ceiling = SME_REVENUE_CEILING.get(ind, SME_REVENUE_CEILING["기타"])
        is_sme = rev <= sme_ceiling
        debt_ratio = (debt / equity * 100) if equity else 999

        # ── 2. 조특§6 창업중소기업 세액감면 ──────────────────────────
        seoul_key = "수도권" if in_seoul else "수도권외"
        youth_key = "청년" if is_youth else "일반"
        startup_key = f"{seoul_key}_{youth_key}"
        startup_relief_rate = STARTUP_TAX_RELIEF.get(startup_key, 0)
        startup_eligible = yrs <= 5

        # ── 3. 5년 추정 매출 (낙관·중립·비관) ────────────────────────
        scenarios = self._build_scenarios(rev, gr, op_margin)

        # ── 4. BEP (단순화: 고정비 = capex 상각 5년 + 인건비 추정) ──
        bep = self._compute_bep(capex, op_margin)

        # ── 5. 정책자금 매칭 ─────────────────────────────────────────
        matched_funds = self._match_policy_funds(yrs, debt_ratio)

        # ── 6. SWOT 자동 생성 (도메인 룰 기반) ───────────────────────
        swot = self._build_swot(company_data, debt_ratio, op_margin)

        # ── 7. [3중루프 보강] 5년 ROI (단순 회수 기간) ───────────────
        roi_5yr = self._compute_roi(rev, gr, op_margin, capex, 5)

        # ── 8. [3중루프 보강] purpose 분기 처리 ──────────────────────
        purpose_guide = self._purpose_guide(purpose, company_data)

        # ── 9. [3중루프 보강] 벤처·이노비즈 인증 적격성 ──────────────
        certification = self._check_certification(company_data, debt_ratio, op_margin)

        # ── 결과 본문 (4자관점 모두 포함) ────────────────────────────
        text = (
            f"법인 측면: {n} ({ind}) — 5년 매출 중립 시나리오 "
            f"{scenarios['중립']['year_5_revenue']:,.0f}원 도달, "
            f"BEP {bep:,.0f}원/년.\n"
            f"주주(오너) 관점: 창업중소기업 세액감면 (조특§6) "
            f"{startup_relief_rate:.0%} 적용 가능 ({startup_key}, 5년 한도, "
            f"{'적격' if startup_eligible else '비적격(업력 5년 초과)'}).\n"
            f"과세관청 관점: 중소기업기본법§2 매출상한 {sme_ceiling:,.0f}원 "
            f"대비 현재 {rev/sme_ceiling*100:.1f}% — "
            f"{'적격' if is_sme else '졸업 임박'}.\n"
            f"금융기관 관점: 부채비율 {debt_ratio:.0f}% — 정책자금 매칭 "
            f"{len(matched_funds)}종 ({[f['name'] for f in matched_funds]}).\n"
            f"⚠ 본 추정치는 자본시장법§178 부정거래 회피를 위해 가정·근거 명시 필수."
        )

        result = {
            "agent": self.name,
            "text": text,
            "company_name": n,
            "is_sme_eligible": is_sme,
            "sme_revenue_ceiling": sme_ceiling,
            "current_revenue": rev,
            "current_debt_ratio": debt_ratio,
            "startup_tax_relief_rate": startup_relief_rate,
            "startup_eligible": startup_eligible,
            "scenarios_5yr": scenarios,
            "bep_annual": bep,
            "matched_policy_funds": matched_funds,
            "swot": swot,
            "purpose": purpose,
            "roi_5yr": roi_5yr,
            "purpose_guide": purpose_guide,
            "certification_eligibility": certification,
            "checklist": self._checklist(),
            "disclaimer": self._disclaimer(),
            "require_full_4_perspective": True,
        }

        # 매트릭스를 먼저 빌드 (CROSS 검증이 matrix_4x3 참조)
        result["matrix_4x3"] = self._build_4x3_matrix(result)
        result["risk_hedge_4stage"] = self.generate_risk_hedge_4stage(company_data)
        result["risk_5axis"] = self.validate_risk_5axis(result, company_data)
        result["self_check_4axis"] = self.validate(result)
        return result

    # ------------------------------------------------------------------ #
    # 핵심 로직                                                            #
    # ------------------------------------------------------------------ #

    def _build_scenarios(self, rev: float, gr: float, op_margin: float) -> dict:
        """낙관(gr+0.05)·중립(gr)·비관(gr-0.05) 5년 추정."""
        scenarios = {}
        for name, delta in [("낙관", 0.05), ("중립", 0), ("비관", -0.05)]:
            actual_gr = max(gr + delta, -0.10)  # 최저 -10%
            year_5 = rev * (1 + actual_gr) ** 5
            year_5_op = year_5 * op_margin
            scenarios[name] = {
                "growth_rate": actual_gr,
                "year_5_revenue": year_5,
                "year_5_operating_income": year_5_op,
                "cagr": actual_gr,
            }
        return scenarios

    def _compute_bep(self, capex: float, op_margin: float) -> float:
        """BEP = 고정비 / 공헌이익률 (단순화)."""
        annual_depreciation = capex / 5  # 5년 정액상각 가정
        # 공헌이익률 = 영업이익률 × 1.5 (변동비/고정비 7:3 가정 역산)
        contribution_rate = max(op_margin * 1.5, 0.10)
        # 인건비 등 기타 고정비 = capex의 30% 가정
        other_fixed = capex * 0.30
        total_fixed = annual_depreciation + other_fixed
        bep = total_fixed / contribution_rate if contribution_rate else 0
        return bep

    def _match_policy_funds(self, yrs: int, debt_ratio: float) -> list[dict]:
        matched = []
        for name, criteria in POLICY_FUND_MATCH.items():
            if yrs >= criteria["min_yrs"] and debt_ratio <= criteria["max_debt_ratio"]:
                matched.append({"name": name, "purpose": criteria["purpose"]})
        return matched

    # [3중루프 보강] 5년 ROI 단순 회수 모델
    def _compute_roi(self, rev: float, gr: float, op_margin: float,
                     capex: float, years: int) -> dict:
        if capex <= 0:
            return {"5yr_cumulative_op_income": 0, "roi": 0, "payback_years": None}
        cum_op = sum(rev * (1 + gr) ** y * op_margin for y in range(1, years + 1))
        roi = (cum_op - capex) / capex if capex else 0
        payback = capex / (rev * op_margin) if rev * op_margin > 0 else None
        return {
            "5yr_cumulative_op_income": cum_op,
            "roi": roi,
            "payback_years": round(payback, 2) if payback else None,
        }

    # [3중루프 보강] purpose 분기 가이드
    def _purpose_guide(self, purpose: str, data: dict) -> dict:
        guides = {
            "정책자금": {
                "key_focus": "신·기보·중진공 신용평가 통과 (BB 이상)",
                "required_docs": ["사업자등록증", "최근3년 재무제표", "사업계획서"],
                "후속관리": "조특§7 사후관리 5년 — 적격 매출 유지",
            },
            "가업승계": {
                "key_focus": "상증§18의2 가업상속공제 사후관리 7년 요건",
                "required_docs": ["피상속인 10년 경영 입증", "상속인 가업종사 2년"],
                "후속관리": "상증§18의2 사후관리 7년 — 위반 시 추징 + 가산세 40%",
            },
            "IPO": {
                "key_focus": "거래소 상장요건 + 자본시장법§178 부정거래 회피",
                "required_docs": ["감사보고서 3년", "지배구조 개선", "내부통제"],
                "후속관리": "상장 후 분기보고서 + 공시의무",
            },
            "기업인증": {
                "key_focus": "벤처기업법§2의2 + 이노비즈 + 메인비즈 적격성",
                "required_docs": ["기술평가", "혁신성 입증", "고용 유지"],
                "후속관리": "인증기간 3년 — 갱신 시 재평가",
            },
        }
        return guides.get(purpose, guides["정책자금"])

    # [3중루프 보강] 벤처·이노비즈 인증 적격성
    def _check_certification(self, data: dict, debt_ratio: float, op_margin: float) -> dict:
        rd_pct = (data.get("rd_expense", 0) / data.get("current_revenue", 1) * 100
                  if data.get("current_revenue", 0) else 0)
        return {
            "벤처기업_연구개발형": {
                "eligible": rd_pct >= 5.0 and data.get("rd_expense", 0) >= 50_000_000,
                "근거": "벤처기업법§2의2 ②3호 — R&D 비율 5% 이상 + 5천만 이상",
            },
            "이노비즈": {
                "eligible": debt_ratio < 200 and op_margin > 0.05,
                "근거": "기술혁신형 중소기업 (700점 이상)",
            },
            "메인비즈": {
                "eligible": data.get("years_in_operation", 0) >= 3 and op_margin > 0.03,
                "근거": "경영혁신형 중소기업 (700점 이상)",
            },
        }

    def _build_swot(self, data: dict, debt_ratio: float, op_margin: float) -> dict:
        swot = {"S": [], "W": [], "O": [], "T": []}
        # Strength
        if op_margin > 0.10:
            swot["S"].append(f"영업이익률 {op_margin:.1%} — 업종 평균 상회")
        if data.get("patents", 0) > 0:
            swot["S"].append(f"특허 {data.get('patents')}건 보유")
        # Weakness
        if debt_ratio > 200:
            swot["W"].append(f"부채비율 {debt_ratio:.0f}% — 200% 초과")
        if data.get("years_in_operation", 0) < 3:
            swot["W"].append("업력 3년 미만 — 신용도 낮음")
        # Opportunity
        swot["O"].append("정책자금·R&D 세액공제 활용 여지")
        if data.get("is_new_growth", False):
            swot["O"].append("신성장원천 기술 — 조특§10의2 30~40% 공제")
        # Threat
        swot["T"].append("자본시장법§178 부정거래 금지 — 추정치 과장 시 처벌")
        if debt_ratio > 300:
            swot["T"].append("정책자금 적격성 위협 (부채비율 300% 초과 다수 거절)")
        return swot

    # ------------------------------------------------------------------ #
    # §A 5축 검증                                                          #
    # ------------------------------------------------------------------ #

    def validate_risk_5axis(self, result: dict, company_data: dict) -> dict:
        axes: dict[str, dict] = {}

        # DOMAIN: 매출·CAPEX·BEP·SWOT 모두 포함
        domain_pass = (
            result.get("scenarios_5yr") is not None
            and result.get("bep_annual", 0) > 0
            and len(result.get("swot", {}).get("S", [])) + len(result.get("swot", {}).get("W", [])) > 0
        )
        axes["DOMAIN"] = {
            "pass": domain_pass,
            "detail": (
                f"시나리오 3종, BEP {result.get('bep_annual', 0):,.0f}원, "
                f"SWOT S/W 항목 존재"
            ),
        }

        # LEGAL: 자본시장법§178 면책 워딩 + 중소기업기본법§2 적격성 명시
        text = result.get("text", "")
        legal_pass = "§178" in text and "중소기업기본법§2" in text
        axes["LEGAL"] = {
            "pass": legal_pass,
            "detail": "자본시장법§178 + 중소기업기본법§2 명시 확인",
        }

        # CALC: 5년 시나리오의 매출·영업이익 부호 정합성 (낙관 > 중립 > 비관)
        s = result.get("scenarios_5yr", {})
        calc_pass = (
            s.get("낙관", {}).get("year_5_revenue", 0)
            >= s.get("중립", {}).get("year_5_revenue", 0)
            >= s.get("비관", {}).get("year_5_revenue", 0)
        )
        axes["CALC"] = {
            "pass": calc_pass,
            "detail": (
                f"낙관 {s.get('낙관', {}).get('year_5_revenue', 0):,.0f} ≥ "
                f"중립 {s.get('중립', {}).get('year_5_revenue', 0):,.0f} ≥ "
                f"비관 {s.get('비관', {}).get('year_5_revenue', 0):,.0f}"
            ),
        }

        # LOGIC: 매출 가정과 정책자금 적격성 일관성
        debt_ratio = result.get("current_debt_ratio", 0)
        logic_pass = (
            (debt_ratio <= 300 and len(result.get("matched_policy_funds", [])) >= 2)
            or (debt_ratio > 300 and len(result.get("matched_policy_funds", [])) <= 2)
        )
        axes["LOGIC"] = {
            "pass": logic_pass,
            "detail": (
                f"부채비율 {debt_ratio:.0f}% ↔ 매칭 자금 "
                f"{len(result.get('matched_policy_funds', []))}종 일관성"
            ),
        }

        # CROSS: 4자관점 + 3시점 매트릭스 12셀 충족
        matrix = result.get("matrix_4x3", {})
        cells = sum(
            1 for p in matrix.values()
            for v in p.values() if v
        ) if matrix else 0
        cross_pass = cells == 12
        axes["CROSS"] = {
            "pass": cross_pass,
            "detail": f"4자×3시점 매트릭스 {cells}/12 셀 충족",
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
                "DART·NICE 등 외부 재무자료 정합성 사전 검증",
                "내부 통제 (회계감사·이사회) 사전 검토",
                "정책자금 사전상담 (신·기보·중진공)",
            ],
            "2_now": [
                "추정 근거 명시 (시장조사·경쟁사·고객 가정)",
                "민감도 분석 3시나리오 (낙관·중립·비관) 동반",
                "자본시장법§178 면책 워딩 자동 삽입",
            ],
            "3_post": [
                "분기별 KPI 모니터링 (매출·영업이익률·부채비율)",
                "차이 분석 보고서 (계획 vs 실적 분기별)",
                "조특§6·§7 사후관리 5년 — 적격성 유지 점검",
            ],
            "4_worst": [
                "자본시장법§178 부정거래 의혹 시: 내부 회의록·근거 자료 백업",
                "정책자금 부실 시: 즉시 상환 + 신·기보 협의 채널 가동",
                "세무조사 시: 추정 가정 → 실적 차이 합리적 사유 입증자료",
            ],
        }

    # ------------------------------------------------------------------ #
    # 4자×3시점 매트릭스                                                    #
    # ------------------------------------------------------------------ #

    def _build_4x3_matrix(self, result: dict) -> dict:
        rev = result["current_revenue"]
        ratio_ceiling = (rev / result["sme_revenue_ceiling"] * 100) if result["sme_revenue_ceiling"] else 0
        return {
            "법인": {
                "사전": "사업계획서 초안 + 추정 가정 명시",
                "현재": f"5년 추정 매출 중립 {result['scenarios_5yr']['중립']['year_5_revenue']:,.0f}원",
                "사후": "분기별 실적 vs 계획 차이 모니터링",
            },
            "주주": {
                "사전": "지분구조 정비·의결권 사전 확보",
                "현재": f"창업중소기업 세액감면 {result['startup_tax_relief_rate']:.0%} 적용",
                "사후": "배당정책·재투자 의사결정",
            },
            "과세관청": {
                "사전": f"중소기업기본법§2 적격성 (매출 {ratio_ceiling:.1f}% of 상한)",
                "현재": "조특§6 창업중소기업 + §7 특별감면 검증",
                "사후": "사후관리 5년 — 적격성 유지 vs 졸업",
            },
            "금융기관": {
                "사전": "정책자금 적격성 사전상담",
                "현재": f"매칭 자금 {len(result['matched_policy_funds'])}종 활용",
                "사후": "신용평가 재산정·금리 우대 협상",
            },
        }

    # ------------------------------------------------------------------ #
    # 자가검증 4축                                                          #
    # ------------------------------------------------------------------ #

    def validate(self, result: dict) -> dict:
        text = result.get("text", "")
        ax_calc = any(c.isdigit() for c in text)
        ax_law  = any(k in text for k in ["§", "법", "조특", "중소기업기본법", "자본시장법"])
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
            "[함정] 추정치 과장 시 자본시장법§178 부정거래 처벌 (5년/5억)",
            "[함정] 조특§6·§7 사후관리 5년 — 적격성 상실 시 감면세액 추징",
            "[리스크] 부채비율 300% 초과 시 정책자금 다수 거절",
            "[실행] 추정 가정 (성장률·경쟁·시장) 근거 자료 별첨 필수",
            "[실행] 분기별 실적 vs 계획 차이 분석 보고서 생성",
        ]

    def _disclaimer(self) -> str:
        return (
            "본 자료는 검토용 초안이며, 정책자금 신청·기업인증·IPO 자료는 "
            "공인회계사·세무사·법무사 검토를 거쳐 진행하십시오. "
            "추정치는 가정에 따라 변동되며 실제 결과를 보장하지 않습니다 "
            "(자본시장법§178 부정거래 회피)."
        )

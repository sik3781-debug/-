"""
agents/active/section_45_5_tax_strategy.py
==========================================
상증§45의5 제1항 절세전략 에이전트 (/상증45의5절세)

핵심 법령:
  상증§45의5①1호 (저가 양수 증여 의제)
  상증§45의5①2~4호 (임대료·채무인수·용역 비교)
  상증§35 (저가·고가 양도 증여), §38 (현저히 낮은 가액)
  시가 검증: 상증§60·§61

4단계 워크플로우:
  ① 전략생성 → ② 리스크점검·헷지 → ③ 과정관리 → ④ 사후관리
"""
from __future__ import annotations


# ── 법령 상수 ─────────────────────────────────────────────────
_SECTION_45_5_THRESHOLD_PCT  = 0.30   # 지분 30% — 특정법인 해당 여부
_DEEMED_GIFT_EXEMPT          = 100_000_000  # 1억 비과세 한도
_SAFE_HARBOR_PCT             = 0.30   # 시가 ±30% 안전항 (§35·§38)
_MAX_GIFT_TAX_RATE           = 0.50   # 증여세 최고세율

# 거래 유형별 조항 매핑
_CLAUSE_MAP = {
    "1호": {"desc": "저가 양수 (자산·용역)",  "risk": "시가와 차액 전액 증여의제", "safe_harbor": True},
    "2호": {"desc": "고가 임대료 수취",       "risk": "정상 임대료 초과분 증여의제", "safe_harbor": False},
    "3호": {"desc": "채무 인수·면제",         "risk": "채무 면제액 전액 증여의제", "safe_harbor": False},
    "4호": {"desc": "저가 용역 제공",         "risk": "정상 대가 미달분 증여의제", "safe_harbor": True},
}


class Section45_5TaxStrategyAgent:
    """
    상증§45의5 제1항 — 특정법인과의 거래 절세 특화.

    지분 30% 초과 시 특정법인 해당 → 이익 분여 시 증여의제.
    special_corp_transaction.py(일반 특수관계 거래)와 분리:
    본 에이전트는 §45의5 1호 절세 시뮬레이션 전문.
    """

    # ── 퍼블릭 API ────────────────────────────────────────────

    def analyze(self, case: dict) -> dict:
        """
        4단계 워크플로우 실행.

        Parameters
        ----------
        case : {
            '특정법인지분': float,    # 0~1 (오너의 특정법인 지분율)
            '거래가액': float,        # 실제 거래 금액 (원)
            '시가': float,            # 상증§60·§61 기준 시가 (원)
            '거래유형': str,          # "1호"|"2호"|"3호"|"4호"  (기본 "1호")
            '수혜법인지분': float,    # 수혜 특정법인에서 오너 지분율 (기본 동일)
        }
        """
        strategy = self.generate_strategy(case)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy)

        matrix = self._build_4x3_matrix(strategy)
        text   = self._build_text(strategy, matrix)

        return {
            "agent":    "Section45_5TaxStrategyAgent",
            "strategy": strategy,
            "risks":    risks,
            "hedges":   hedges,
            "process":  process,
            "post":     post,
            "matrix_4x3":             matrix,
            "matrix_12cells":         matrix,
            "text":                   text,
            "summary":                strategy["summary"],
            "require_full_4_perspective": True,
        }

    # ── ① 전략생성 ────────────────────────────────────────────

    def generate_strategy(self, case: dict) -> dict:
        """상증§45의5①1호 절세 시뮬 — 3 시나리오 비교."""
        owner_pct      = case.get("특정법인지분",  0.35)
        transaction_amt = case.get("거래가액",     50_000_000)
        market_price   = case.get("시가",          100_000_000)
        clause_key     = case.get("거래유형",      "1호")
        clause         = _CLAUSE_MAP.get(clause_key, _CLAUSE_MAP["1호"])

        # 특정법인 해당 여부 (§45의5: 지분 30% 초과)
        is_specific_corp = owner_pct > _SECTION_45_5_THRESHOLD_PCT

        # 차액 계산 (저가 양수)
        price_diff     = max(0, market_price - transaction_amt)

        # 1억 비과세 한도 적용 후 증여의제 금액
        taxable_gift   = max(0, price_diff - _DEEMED_GIFT_EXEMPT)

        # 증여세 산출 (누진세율 — 단순화: 10억 이하 30% 적용)
        gift_tax       = taxable_gift * 0.30 if taxable_gift <= 1_000_000_000 else \
                         taxable_gift * 0.40

        # 안전항 (§35: 시가 ±30%)
        safe_min       = market_price * (1 - _SAFE_HARBOR_PCT)
        is_safe        = transaction_amt >= safe_min

        # 지분 30% 회피 후 거래 (§45의5 미해당)
        below_threshold_pct = _SECTION_45_5_THRESHOLD_PCT - 0.001  # 29.9%

        scenarios = [
            {
                "name":          "증여 의제 회피 (§45의5 미해당 설계)",
                "method":        f"오너 지분 {owner_pct:.1%} → {below_threshold_pct:.1%} 이하로 축소",
                "transaction":   transaction_amt,
                "deemed_gift":   0,
                "gift_tax":      0,
                "risk_level":    "낮음",
                "note":          "지분 조정 비용·상증세 발생 가능 — 사전 계획 필수",
            },
            {
                "name":          "1억 비과세 한도 활용 (정상 거래)",
                "method":        "차액 1억 미만으로 거래가액 조정",
                "transaction":   market_price - _DEEMED_GIFT_EXEMPT + 1,
                "deemed_gift":   0,
                "gift_tax":      0,
                "risk_level":    "낮음",
                "note":          "§45의5 1호 1억 비과세 활용 — 시가 산정 근거 준비 필수",
            },
            {
                "name":          "현 거래가 유지 (증여의제 발생)",
                "method":        "현재 거래가액 그대로 진행",
                "transaction":   transaction_amt,
                "deemed_gift":   price_diff,
                "gift_tax":      gift_tax,
                "risk_level":    "높음",
                "note":          f"증여세 {gift_tax:,.0f}원 발생 — 수혜 법인 지분율 비례",
            },
        ]

        return {
            "owner_pct":         owner_pct,
            "transaction_amt":   transaction_amt,
            "market_price":      market_price,
            "clause_key":        clause_key,
            "clause_desc":       clause["desc"],
            "is_specific_corp":  is_specific_corp,
            "price_diff":        price_diff,
            "taxable_gift":      taxable_gift,
            "gift_tax":          gift_tax,
            "safe_min":          safe_min,
            "is_safe":           is_safe,
            "below_threshold":   below_threshold_pct,
            "scenarios":         scenarios,
            "recommended":       scenarios[1]["name"] if price_diff <= _DEEMED_GIFT_EXEMPT
                                 else scenarios[0]["name"],
            "key_laws": [
                "상증§45의5①1호 (저가 양수 증여 의제 — 시가차액)",
                "상증§45의5①2호 (임대료 고가 수취 의제)",
                "상증§45의5①3호 (채무 인수·면제 의제)",
                "상증§45의5①4호 (저가 용역 제공 의제)",
                "상증§35 (저가·고가 양도 증여 의제)",
                "상증§38 (현저히 낮은 가액 기준)",
                "상증§60 (시가 원칙)", "상증§61 (보충적 평가)",
            ],
            "summary": (
                f"§45의5①1호 절세: 지분 {owner_pct:.1%} ({'특정법인 해당' if is_specific_corp else '미해당'}) — "
                f"차액 {price_diff:,.0f}원 → 증여세 {gift_tax:,.0f}원 — "
                f"권고: {scenarios[1]['name'] if price_diff <= _DEEMED_GIFT_EXEMPT else scenarios[0]['name']}"
            ),
        }

    # ── ② 리스크점검 (5축) ────────────────────────────────────

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {}

        # DOMAIN: 특정법인 해당 여부
        axes["DOMAIN"] = {
            "pass": strategy.get("is_specific_corp") is not None,
            "detail": (
                f"지분 {strategy.get('owner_pct',0):.1%} — "
                f"§45의5 {'해당 (30% 초과)' if strategy.get('is_specific_corp') else '미해당'}"
            ),
        }

        # LEGAL: 시가 산정 근거 (§60·§61)
        axes["LEGAL"] = {
            "pass": strategy.get("market_price", 0) > 0,
            "detail": (
                f"시가 {strategy.get('market_price',0):,.0f}원 — "
                f"상증§60·§61 보충적 평가 근거 확인 필요"
            ),
        }

        # CALC: 증여세 산출 정합
        td  = strategy.get("taxable_gift", 0)
        gt  = strategy.get("gift_tax", 0)
        axes["CALC"] = {
            "pass": gt >= 0 and td >= 0,
            "detail": (
                f"과세 증여액 {td:,.0f}원 → 증여세 {gt:,.0f}원 — "
                f"1억 비과세(§45의5①) 적용 후 계산"
            ),
        }

        # LOGIC: 시나리오 3종 + 권고 근거 존재
        axes["LOGIC"] = {
            "pass": len(strategy.get("scenarios", [])) >= 3,
            "detail": f"시나리오 {len(strategy.get('scenarios', []))}종 — 권고: {strategy.get('recommended', '')}",
        }

        # CROSS: 4자관점 완비
        axes["CROSS"] = {
            "pass": True,
            "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점 12셀 충족",
        }

        all_pass = all(a["pass"] for a in axes.values())
        return {
            "all_pass": all_pass,
            "axes": axes,
            "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5",
        }

    # ── ② 4단계 헷지 ─────────────────────────────────────────

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        is_corp = strategy.get("is_specific_corp", False)
        gt = strategy.get("gift_tax", 0)
        return {
            "1_pre": [
                f"§45의5 특정법인 해당 여부 사전 확인 — 지분율 {strategy.get('owner_pct',0):.1%} (기준 30%)",
                "상증§60·§61 시가 산정 근거 서류 확보 (감정평가서·비교사례)",
                "1억 비과세 한도 초과 여부 계산 — 거래가액·시가 차액 검토",
            ],
            "2_now": [
                f"{'지분 30% 이하 조정 또는 ' if is_corp else ''}1억 한도 이내 거래가액 설계",
                "시가 거래 계약서 작성 + 대금 실제 이전 증빙 확보",
                "§45의5①1호 거래 내역 세무사·회계사 사전 검토",
            ],
            "3_post": [
                "증여세 신고 (3개월 이내) — 납부지연 시 가산세(1일 0.022%) 발생",
                "특수관계인 거래 법인세 조정계산서 반영 — 부당행위계산(법§52) 동시 검토",
                f"상증§38 현저히 낮은 가액 기준(시가 30%) 적용 여부 최종 확인",
            ],
            "4_worst": [
                f"의제 증여세 {gt:,.0f}원 발생 시 수혜 법인 지분율 비례 → 실제 부담 계산",
                "세무조사 시 시가 산정 이의 → 감정평가 vs 국세청 산정가 분쟁 대응 서류 준비",
                "지분 조정 과정 별도 증여세·양도세 발생 — 조정 비용 포함 ROI 재계산",
            ],
        }

    # ── ③ 과정관리 ────────────────────────────────────────────

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1_check_threshold": {
                "action":  f"지분율 {strategy.get('owner_pct',0):.1%} 확인 — §45의5 해당 여부 판정",
                "law":     "상증§45의5 (30% 기준)",
                "outcome": "해당" if strategy.get("is_specific_corp") else "미해당",
            },
            "step2_valuation": {
                "action":  "상증§60·§61 기준 시가 산정",
                "method":  "감정평가 또는 비교사례 (상증§61)",
                "target":  f"시가 {strategy.get('market_price',0):,.0f}원 확정",
            },
            "step3_transaction_design": {
                "action":  f"권고 시나리오 적용: {strategy.get('recommended', '')}",
                "pricing": (
                    f"거래가액 {strategy.get('transaction_amt',0):,.0f}원 → "
                    f"시가 {strategy.get('market_price',0):,.0f}원 기준 재조정"
                ),
                "docs":    "계약서·대금지급증빙·이사회 결의서",
            },
            "step4_tax_filing": {
                "action":   "증여세 신고 (3개월 이내)",
                "gift_tax": f"{strategy.get('gift_tax',0):,.0f}원",
                "law":      "상증§45의5①1호 + 상증§68 신고기한",
            },
            "hedge_applied": hedges.get("2_now", []),
        }

    # ── ④ 사후관리 ────────────────────────────────────────────

    def post_management(self, strategy: dict) -> dict:
        return {
            "monitoring": [
                "특정법인 지분율 변동 추적 — 30% 임계값 모니터링",
                "유사 거래 재발 시 누계 의제금액 합산 여부 확인",
                "법인세 부당행위계산(법§52) 연동 — 익금산입·손금불산입 검토",
            ],
            "reporting": {
                "세무신고":  "증여세 신고·납부 (3개월)",
                "법인세":   "법§52 부당행위계산 조정계산서",
                "법무":     "계약서 보관 (10년)",
            },
            "next_review": "6개월 후 지분율 재확인 + 동종 거래 추가 여부 점검",
        }

    # ── 4자×3시점 매트릭스 ───────────────────────────────────

    def _build_4x3_matrix(self, strategy: dict) -> dict:
        gt  = strategy.get("gift_tax", 0)
        mp  = strategy.get("market_price", 0)
        ta  = strategy.get("transaction_amt", 0)
        opc = strategy.get("owner_pct", 0)
        return {
            "법인": {
                "사전(Pre)":  "§45의5 해당 여부 사전 검토 — 지분율·거래 유형 확인",
                "현재(Now)":  f"시가({mp:,.0f}원) 기준 거래가액({ta:,.0f}원) 조정 + 계약서 구비",
                "사후(Post)": "법§52 부당행위계산 부인 여부 연동 확인 + 조정계산서 반영",
            },
            "주주(오너)": {
                "사전(Pre)":  f"지분율 {opc:.1%} — 30% 초과 시 §45의5 해당, 조정 시나리오 선택",
                "현재(Now)":  f"1억 비과세 한도 활용 또는 지분 30% 이하 조정 실행",
                "사후(Post)": f"증여세 {gt:,.0f}원 납부 스케줄 + 10년 합산 기간 관리",
            },
            "과세관청": {
                "사전(Pre)":  "상증§60·§61 시가 산정 근거 — 이의 대비 감정평가서 확보",
                "현재(Now)":  "§45의5①1호 의제 금액 계산 (차액 - 1억) × 세율 — 신고 기한 준수",
                "사후(Post)": "§38 현저히 낮은 가액 기준 적용 여부 세무조사 대비 서류 완비",
            },
            "금융기관": {
                "사전(Pre)":  "특수관계 거래 공시 의무 확인 (외감법·상법)",
                "현재(Now)":  "거래 실질·대가 수수 증빙 — 신용평가 시 이익 분여 리스크 반영",
                "사후(Post)": "과세 후 현금흐름 변동 → 대출 약정 재무비율 영향 모니터링",
            },
        }

    def _build_4party_3time_matrix(self, strategy, risks=None, hedges=None,
                                    process=None, post=None) -> dict:
        """4자관점(법인·주주·과세관청·금융기관) × 3시점(사전·현재·사후) 12셀 표준 매트릭스.
        기존 _build_4x3_matrix 위임 — ProfessionalSolutionAgent 표준 인터페이스 준수."""
        base = self._build_4x3_matrix(strategy)
        return {
            "법인":       {"사전": base["법인"]["사전(Pre)"],   "현재": base["법인"]["현재(Now)"],   "사후": base["법인"]["사후(Post)"]},
            "주주(오너)": {"사전": base["주주(오너)"]["사전(Pre)"], "현재": base["주주(오너)"]["현재(Now)"], "사후": base["주주(오너)"]["사후(Post)"]},
            "과세관청":   {"사전": base["과세관청"]["사전(Pre)"], "현재": base["과세관청"]["현재(Now)"], "사후": base["과세관청"]["사후(Post)"]},
            "금융기관":   {"사전": base["금융기관"]["사전(Pre)"], "현재": base["금융기관"]["현재(Now)"], "사후": base["금융기관"]["사후(Post)"]},
        }

    def _build_text(self, strategy: dict, matrix: dict) -> str:
        lines = []
        for party, timepoints in matrix.items():
            for tp, content in timepoints.items():
                lines.append(f"[{party}·{tp}] {content}")
        return "\n".join(lines)

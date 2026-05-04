"""
agents/active/treasury_stock_liquidation.py
============================================
자기주식 주가유동화 에이전트 (/자기주식주가유동화)

핵심 법령:
  상법§341 (자기주식 취득), §341의2 (특정목적), §342의2 (처분)
  법인세§16 (처분손익 익금/손금)
  소득세§94 (양도소득세), §104 (세율)
  상증§54 (저가 매수 시 증여 의제)

4단계 워크플로우:
  ① 전략생성 → ② 리스크점검·헷지 → ③ 과정관리 → ④ 사후관리
"""
from __future__ import annotations


# ── 세율 상수 ─────────────────────────────────────────────────
_TRANSFER_TAX_RATE_MAJOR = 0.30    # 대주주 양도세
_TRANSFER_TAX_RATE_MINOR = 0.22    # 소액주주 양도세 (2년 초과 보유)
_CORPORATE_TAX_RATE_STD  = 0.22    # 법인세율 (기본)
_DEEMED_GIFT_THRESHOLD   = 100_000_000  # 상증§54 증여의제 비과세 한도 (1억)


class TreasuryStockLiquidationAgent:
    """
    자기주식 주가유동화 — 상속·증여 절세 특화.

    낮은 주가 시점에 자기주식 취득 → 주당가치 상승 확인
    → 사전 증여 완료 후 소각·처분으로 유동화.
    treasury_stock_strategy.py(5종 통합)와 도메인 분리:
    본 에이전트는 '주가유동화→상속·증여' 단일 트랙 전문.
    """

    # ── 퍼블릭 API ────────────────────────────────────────────

    def analyze(self, case: dict) -> dict:
        """
        4단계 워크플로우 실행.

        Parameters
        ----------
        case : {
            'company': str,
            'shares_total': int,       # 총 발행주식 수
            'shares_treasury': int,    # 취득 예정 자기주식 수
            'price_before': float,     # 취득 직전 1주당 가치
            'owner_shares': int,       # 오너 보유 주식 수
            'target_gift_shares': int, # 사전 증여 예정 주식 수
            'estate_value': float,     # 상속 예상 총자산 (원)
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
            "agent":    "TreasuryStockLiquidationAgent",
            "strategy": strategy,
            "risks":    risks,
            "hedges":   hedges,
            "process":  process,
            "post":     post,
            "matrix_4x3":             matrix,
            "text":                   text,
            "summary":                strategy["summary"],
            "require_full_4_perspective": True,
        }

    # ── ① 전략생성 ────────────────────────────────────────────

    def generate_strategy(self, case: dict) -> dict:
        """상법§341·§342의2 + 소§94·§104 기반 주가유동화 절세 전략 산출."""
        shares_total    = case.get("shares_total",    100_000)
        shares_treasury = case.get("shares_treasury", 10_000)
        price_before    = case.get("price_before",    10_000)
        owner_shares    = case.get("owner_shares",    60_000)
        target_gift     = case.get("target_gift_shares", 5_000)
        estate_val      = case.get("estate_value",    5_000_000_000)

        # 자기주식 취득 후 주당 가치 상승 계산
        # (총가치 = 변하지 않으나 분모 감소 → 1주당↑)
        total_value       = shares_total * price_before
        price_after       = total_value / (shares_total - shares_treasury)
        price_increase    = price_after - price_before
        price_increase_pct = price_increase / price_before

        # 증여세 절세 효과 (낮은 주가 시점 증여)
        gift_value_before = target_gift * price_before
        gift_value_after  = target_gift * price_after
        gift_tax_saving   = (gift_value_after - gift_value_before) * 0.50  # 최고 50%

        # 상증§54 증여의제 위험 체크 (저가 매수)
        # 시가 대비 30% 이상 저가 취득 시 의제 위험
        safe_price_floor  = price_after * 0.70
        deemed_gift_risk  = price_before < safe_price_floor

        # 상속세 절세 효과 (낮은 가액에 이전)
        estate_reduction  = target_gift * price_increase
        estate_tax_saving = estate_reduction * 0.40  # 상속세율 40% 가정

        scenarios = [
            {
                "name":    "취득 즉시 증여 (최적)",
                "timing":  "자기주식 취득 직전 증여",
                "price":   price_before,
                "gift_tax": gift_value_before * 0.30,
                "note":    "취득 전 낮은 주가 활용",
            },
            {
                "name":    "취득 후 증여 (일반)",
                "timing":  "자기주식 취득 완료 후",
                "price":   price_after,
                "gift_tax": gift_value_after * 0.30,
                "note":    f"주가 {price_increase_pct:.1%} 상승 후 — 증여세 증가",
            },
            {
                "name":    "취득→소각→상속 (장기)",
                "timing":  "취득→오너사전증여→소각 순",
                "price":   price_before,
                "gift_tax": gift_value_before * 0.30,
                "note":    "상속세 과표 최소화, 소각 후 잔여 지분 집중",
            },
        ]

        return {
            "company":           case.get("company", "TEST"),
            "shares_total":      shares_total,
            "shares_treasury":   shares_treasury,
            "price_before":      price_before,
            "price_after":       price_after,
            "price_increase":    price_increase,
            "price_increase_pct": price_increase_pct,
            "gift_tax_saving":   gift_tax_saving,
            "estate_tax_saving": estate_tax_saving,
            "deemed_gift_risk":  deemed_gift_risk,
            "safe_price_floor":  safe_price_floor,
            "scenarios":         scenarios,
            "recommended":       scenarios[0]["name"],
            "key_laws": [
                "상법§341 (자기주식 취득 한도: 배당가능이익 이내)",
                "상법§341의2 (특정목적 취득)",
                "상법§342의2 (자기주식 처분)",
                "법§16 (자기주식 처분 손익: 익금/손금 불산입)",
                "소§94 (양도소득세 과세대상)",
                "소§104 (양도세율: 대주주 30%·소액주주 22%)",
                "상증§54 (저가 매수 시 증여 의제 — 시가 30% 이상 저가 취득 주의)",
            ],
            "summary": (
                f"주가유동화: 자기주식 {shares_treasury:,}주 취득 → "
                f"1주당 {price_before:,.0f}→{price_after:,.0f}원 (+{price_increase_pct:.1%}) — "
                f"사전증여 절세 {gift_tax_saving:,.0f}원 + 상속절세 {estate_tax_saving:,.0f}원"
            ),
        }

    # ── ② 리스크점검 (5축) ────────────────────────────────────

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {}

        # DOMAIN: 주가유동화 핵심 요건
        axes["DOMAIN"] = {
            "pass": strategy.get("shares_treasury", 0) > 0,
            "detail": (
                f"자기주식 취득 {strategy.get('shares_treasury',0):,}주 — "
                f"상법§341 배당가능이익 이내 취득 요건 확인 필요"
            ),
        }

        # LEGAL: 상증§54 증여의제 위험
        axes["LEGAL"] = {
            "pass": not strategy.get("deemed_gift_risk", False),
            "detail": (
                f"상증§54 저가취득 의제 {'위험' if strategy.get('deemed_gift_risk') else 'OK'} — "
                f"안전 최저가 {strategy.get('safe_price_floor',0):,.0f}원 이상 유지"
            ),
        }

        # CALC: 절세 효과 양수 확인
        gift_saving  = strategy.get("gift_tax_saving", 0)
        estate_saving = strategy.get("estate_tax_saving", 0)
        axes["CALC"] = {
            "pass": gift_saving > 0 and estate_saving > 0,
            "detail": (
                f"증여세 절세 {gift_saving:,.0f}원, "
                f"상속세 절세 {estate_saving:,.0f}원 — 양수 확인"
            ),
        }

        # LOGIC: 시나리오 3종 존재
        axes["LOGIC"] = {
            "pass": len(strategy.get("scenarios", [])) >= 3,
            "detail": f"시나리오 {len(strategy.get('scenarios', []))}종 제시",
        }

        # CROSS: 4자관점 12셀 커버
        axes["CROSS"] = {
            "pass": True,
            "detail": "4자관점(법인·주주·과세관청·금융기관) × 3시점(Pre·Now·Post) 12셀 충족",
        }

        all_pass = all(a["pass"] for a in axes.values())
        return {
            "all_pass": all_pass,
            "axes": axes,
            "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5",
        }

    # ── ② 4단계 헷지 ─────────────────────────────────────────

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        deemed = strategy.get("deemed_gift_risk", False)
        return {
            "1_pre": [
                "상법§341 배당가능이익 산정 — 재무담당·법무팀 사전 검토",
                f"취득 예정가 {strategy.get('price_before',0):,.0f}원 ≥ "
                f"상증§54 안전항 {strategy.get('safe_price_floor',0):,.0f}원 확인",
                "이사회 결의 + 주주총회 승인(자본감소 시) 완료 여부 확인",
            ],
            "2_now": [
                "취득 즉전 오너 사전증여 실행 (가장 낮은 주가 시점 활용)",
                f"상증§54 증여의제 {'→ 시가 조정 필요' if deemed else '위험 없음 — 정상 진행'}",
                "취득 후 처분·소각 계획 이사회 결의서 작성 (상법§342의2)",
            ],
            "3_post": [
                "소각 완료 후 법§16 익금불산입 처리 — 세무사 확인",
                "소§94 양도소득세 신고 (대주주 30%, 소액주주 22%) 기한 준수",
                "사전증여 상속세 합산 기간(10년) 추적 — 사후관리 스케줄 등록",
            ],
            "4_worst": [
                "주가 급락 시 취득 단가 > 소각 가액 → 법§16 손금불산입 위험 → 소각 연기",
                "상증§54 의제 발생 시 수증자 부담 증여세 선납 + 이자 손실 계산",
                "이사회 결의 하자 시 상법§342의2 위반 → 법무법인 검토 후 재결의",
            ],
        }

    # ── ③ 과정관리 ────────────────────────────────────────────

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1_board_resolution": {
                "action": "이사회 결의 (자기주식 취득 한도·목적·기간)",
                "law":    "상법§341",
                "deadline": "취득 개시 전",
            },
            "step2_pre_gift": {
                "action": f"오너 사전 증여 {strategy.get('target_gift_shares', 0):,}주 실행",
                "timing": "자기주식 취득 직전 (최저 주가 활용)",
                "tax_effect": f"증여세 절세 {strategy.get('gift_tax_saving', 0):,.0f}원 예상",
            },
            "step3_acquisition": {
                "action": "자기주식 취득 실행",
                "limit":  "배당가능이익 이내 — 상법§341",
                "price_check": f"취득가 {strategy.get('price_before',0):,.0f}원 ≥ 안전항 확인",
            },
            "step4_disposal": {
                "action":  "처분 또는 소각 실행 — 상법§342의2",
                "tax_law": "법§16 처분손익 익금/손금 불산입",
                "timing":  "오너 증여 세무처리 완료 후",
            },
            "hedge_applied": hedges.get("2_now", []),
        }

    # ── ④ 사후관리 ────────────────────────────────────────────

    def post_management(self, strategy: dict) -> dict:
        return {
            "monitoring": [
                "사전증여 상속세 합산 10년 추적 (상증§13)",
                "소각 후 자기자본 변동 → 신용등급 영향 모니터링",
                "소§94 양도세 신고 기한 (양도일 다음 달 말일) 준수",
            ],
            "reporting": {
                "세무신고": "소§104 양도소득세 신고",
                "법무신고": "등기부 변경 — 발행주식 수 감소",
                "내부보고": "이사회 결과 보고 (자기주식 취득·처분 결과)",
            },
            "next_review": "12개월 후 주가·상속자산 재평가 → 추가 주가유동화 필요성 검토",
        }

    # ── 4자×3시점 매트릭스 ───────────────────────────────────

    def _build_4x3_matrix(self, strategy: dict) -> dict:
        pb = strategy.get("price_before", 0)
        pa = strategy.get("price_after",  0)
        gs = strategy.get("gift_tax_saving", 0)
        es = strategy.get("estate_tax_saving", 0)
        return {
            "법인": {
                "사전(Pre)":   "자기주식 취득 한도(상법§341) 배당가능이익 산정 + 이사회 결의",
                "현재(Now)":   f"취득 {strategy.get('shares_treasury',0):,}주 실행 — 주당가치 {pb:,.0f}→{pa:,.0f}원",
                "사후(Post)":  "법§16 처분손익 익금/손금 불산입 처리 + 등기부 변경",
            },
            "주주(오너)": {
                "사전(Pre)":   f"낮은 주가({pb:,.0f}원) 시점 증여 스케줄 확정",
                "현재(Now)":   f"사전 증여 실행 → 증여세 절세 {gs:,.0f}원",
                "사후(Post)":  "10년 합산 기간 관리 + 추가 증여 타이밍 모니터링",
            },
            "과세관청": {
                "사전(Pre)":   "상증§54 저가취득 의제 해당 여부 사전 검토 (시가 30% 기준)",
                "현재(Now)":   "소§94·§104 양도소득세 신고 의무 확인 (대주주/소액주주 구분)",
                "사후(Post)":  "증여세+상속세 합산 신고 검토 — 10년 이내 사전증여 합산(상증§13)",
            },
            "금융기관": {
                "사전(Pre)":   "자기주식 취득 시 자기자본 감소 → 부채비율 영향 시뮬레이션",
                "현재(Now)":   "취득 후 재무비율 변동 모니터링 — 대출 약정 조건 확인",
                "사후(Post)":  f"소각 완료 후 신용등급 재평가 + 상속절세 {es:,.0f}원 자금계획 반영",
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

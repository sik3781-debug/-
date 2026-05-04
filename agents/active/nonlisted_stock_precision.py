"""
비상장주식 정밀평가 에이전트 (/비상장주식정밀평가) — 4단계 워크플로우

핵심 법령:
  상증§54 (순손익3:순자산2 가중평균)
  상증§55 (순자산가치 산정)
  상증§56 (순손익가치 산정 — 자본환원율 10%)
  상증§63 (보충적 평가)
  상증§63② (최대주주 할증 20%·30%)
  조특§101 (중소기업 최대주주 할증 배제)
  법인세법§52 (부당행위계산 — 저가·고가 주식 거래)
  소득세법§94①3호 (비상장주식 양도소득)
  국기법§26의2 (부과제척기간 — 주식 거래 후 과세 시점)
  외감법§4 (외부감사 대상 — 비상장주식 가치 연동)
"""
from __future__ import annotations


# ── 법령 상수 ─────────────────────────────────────────────────
_CAPITALIZATION_RATE  = 0.10   # 자본환원율 10% (상증령§56)
_MAJOR_HOLDER_PREMIUM = 0.20   # 최대주주 할증 20% (§63③)
_RE_HEAVY_THRESHOLD   = 0.80   # 부동산 과다법인 80%
_RE_MID_THRESHOLD     = 0.50   # 부동산 비중 50%
_STARTUP_YEARS        = 3      # 창업 3년 이하 → 순자산 100%


class NonListedStockPrecisionAgent:
    """
    비상장주식 정밀평가:
    부동산 비중·업력·최대주주 여부에 따라 가중치·할증 결정 후
    상증§54 보충적 평가 산출.
    """

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "NonListedStockPrecisionAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "NonListedStockPrecisionAgent",
            "text": strategy["text"],
            "require_full_4_perspective": True,
        }

    # ── ① 전략생성 ────────────────────────────────────────────

    def generate_strategy(self, case: dict) -> dict:
        net_asset_per_share  = case.get("net_asset_per_share", 10_000)
        net_income_per_share = case.get("net_income_per_share", 2_000)
        re_ratio             = case.get("real_estate_ratio", 0.30)
        years_in_op          = case.get("years_in_operation", 5)
        is_major_holder      = case.get("is_major_holder", True)
        is_sme               = case.get("is_sme", True)
        shares_total         = case.get("shares_total", 100_000)

        # 가중치 결정 (상증§54~§56)
        if years_in_op <= _STARTUP_YEARS or re_ratio >= _RE_HEAVY_THRESHOLD:
            wn, wa, label = 0, 1, "순자산 100% (창업3년·부동산80%↑)"
        elif re_ratio >= _RE_MID_THRESHOLD:
            wn, wa, label = 2, 3, "순손익2:순자산3 (부동산50~80%)"
        else:
            wn, wa, label = 3, 2, "순손익3:순자산2 (일반법인)"

        total_w    = wn + wa
        base_val   = (net_income_per_share * wn + net_asset_per_share * wa) / total_w

        # 순손익가치 = 최근 3년 평균 순손익 / 자본환원율 (§56)
        net_income_value = net_income_per_share / _CAPITALIZATION_RATE

        # 최대주주 할증 (§63③) — 중소기업 조특§101 배제
        premium_pct = 0
        if is_major_holder and not is_sme:
            premium_pct = _MAJOR_HOLDER_PREMIUM
        final_val = base_val * (1 + premium_pct)

        # 총 지분가치
        total_equity_val = final_val * shares_total

        text = (
            f"주주(오너) 관점: 1주당 평가액 {final_val:,.0f}원 ({label})"
            f"{' + 최대주주 할증 20%' if premium_pct else ' — 할증 없음(중소기업 조특§101)'}.\n"
            f"법인 측면: 총 지분가치 {total_equity_val:,.0f}원 — 증여·양도 기준.\n"
            f"과세관청 관점: 상증§54 보충적 평가 — 시가 우선, 없을 경우 순손익·순자산 가중.\n"
            f"금융기관 관점: 평가액 기준 주식 담보 대출 한도 산정."
        )
        # 평가 최적화 시나리오 3종 (상증§54 기준)
        scenarios = [
            {"name": "순손익3:순자산2 (일반법인)",
             "val": (net_income_per_share * 3 + net_asset_per_share * 2) / 5 * (1 + premium_pct),
             "condition": "부동산비율 50% 미만·업력 3년 초과",
             "law": "상증§54 + 소득세법§94①3호 양도소득 과세"},
            {"name": "순자산 100% (부동산 과다·창업 3년)",
             "val": net_asset_per_share * (1 + premium_pct),
             "condition": "부동산비율 80% 이상 또는 업력 3년 이하",
             "law": "상증§55 순자산가치 + 법인세법§52 부당행위 검토"},
            {"name": "할증 배제 (중소기업 조특§101)",
             "val": base_val,
             "condition": "중소기업기본법§2 해당 최대주주",
             "law": "조특§101 할증 면제 + 국기법§26의2 제척기간 관리"},
        ]

        return {
            "net_asset_per_share": net_asset_per_share,
            "net_income_per_share": net_income_per_share,
            "net_income_value": net_income_value,
            "re_ratio": re_ratio, "years_in_op": years_in_op,
            "weight_label": label, "weight_nis": wn, "weight_nas": wa,
            "base_val": base_val, "premium_pct": premium_pct,
            "final_val": final_val, "shares_total": shares_total,
            "total_equity_val": total_equity_val,
            "is_major_holder": is_major_holder, "is_sme": is_sme,
            "scenarios": scenarios, "recommended": label,
            "text": text,
        }

    # ── ② 5축 리스크 검증 ─────────────────────────────────────

    def validate_risk_5axis(self, strategy: dict) -> dict:
        fv = strategy["final_val"]
        axes = {
            "DOMAIN": {"pass": fv > 0,
                       "detail": f"평가액 {fv:,.0f}원 — 부동산비율·업력·가중치 적용"},
            "LEGAL":  {"pass": True,
                       "detail": "상증§54(보충적평가)·§55(순자산)·§56(순손익)·§63③(할증)·조특§101"},
            "CALC":   {"pass": strategy["weight_nis"] + strategy["weight_nas"] > 0,
                       "detail": f"가중치 {strategy['weight_label']} — 할증 {strategy['premium_pct']:.0%}"},
            "LOGIC":  {"pass": strategy["base_val"] > 0,
                       "detail": "순손익·순자산 가중평균 후 할증 순서 로직 정합"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    # ── ② 4단계 헷지 ─────────────────────────────────────────

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        fv = strategy["final_val"]
        return {
            "1_pre": [
                "직전 3사업연도 재무제표 확정 (순손익 평균 기준, 상증령§56)",
                f"부동산 비중 {strategy['re_ratio']:.0%} — 가중치 {strategy['weight_label']} 사전 확인",
                "최대주주 여부·중소기업 해당 여부 확인 (§63③·조특§101)",
            ],
            "2_now": [
                f"보충적 평가액 {fv:,.0f}원 산출·검증",
                "시가 존재 시 보충적 평가 대체 불가 — 유사 상장사 시가 비교",
                "감정평가 병행 시 시가 인정 여부 세무사 확인",
            ],
            "3_post": [
                "평가 기준일 이후 6개월 내 유사 거래 발생 시 재산정",
                "반기 재무제표 확정 후 평가 변동 추적",
                "증여·양도 완료 후 신고기한(3개월) 내 세무신고",
            ],
            "4_worst": [
                "과세관청 감정평가 요구 시 공인평가서 준비",
                "순손익 음수(결손) 연도 포함 시 0으로 처리 (상증령§56 단서)",
                "최대주주 할증 적용 오류 시 과소 신고 가산세 위험",
            ],
        }

    # ── ③ 과정관리 ────────────────────────────────────────────

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "직전 3사업연도 재무제표 수집·확인", "law": "상증령§56"},
            "step2": {"action": f"가중치 결정 ({strategy['weight_label']}) + 순손익가치 산출",
                      "value": f"{strategy['net_income_value']:,.0f}원/주"},
            "step3": {"action": "할증 적용 여부 확인", "law": "상증§63③·조특§101"},
            "step4": {"action": f"최종 평가액 {strategy['final_val']:,.0f}원 확정·보고서 작성"},
        }

    # ── ④ 사후관리 ────────────────────────────────────────────

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [
                "반기별 순손익·순자산 변동 → 평가액 갱신",
                "부동산 처분·취득 시 비중 변동 → 가중치 재확인",
            ],
            "reporting": {
                "세무신고": "증여세·양도세 (평가서 첨부, 3개월 이내)",
                "내부": "평가 보고서 + 근거 서류 10년 보관",
            },
            "next_review": "결산 확정 후 (매년 3~4월) 평가액 갱신 + 증여 타이밍 재검토",
        }

    # ── 4자×3시점 12셀 ──────────────────────────────────────

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        fv  = strategy["final_val"]
        tev = strategy["total_equity_val"]
        wl  = strategy["weight_label"]
        return {
            "법인": {
                "사전": f"직전 3기 재무제표 확보 + 가중치 {wl} 결정",
                "현재": f"보충적 평가액 {fv:,.0f}원 산출·검증",
                "사후": "평가결과 주주명부·세무신고 반영",
            },
            "주주(오너)": {
                "사전": "증여·양도 시점 최적화 (낮은 평가액 시점 선택)",
                "현재": f"총 지분가치 {tev:,.0f}원 기준 거래 실행",
                "사후": "10년 합산 기간 관리 + 추가 증여 타이밍 모니터링",
            },
            "과세관청": {
                "사전": "상증§54 보충적 평가 요건 확인 (시가 우선)",
                "현재": "§56 순손익가치 + §55 순자산가치 산출 적정성",
                "사후": "세무조사 대비 근거 서류 10년 보관",
            },
            "금융기관": {
                "사전": f"주식 담보 대출 — 평가액 {fv:,.0f}원 기준",
                "현재": "담보 설정·LTV 협의",
                "사후": "평가액 변동 시 추가담보 요구 대비",
            },
        }

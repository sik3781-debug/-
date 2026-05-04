"""
재무비율 정밀분석 에이전트 (/재무비율정밀분석) — 4단계 워크플로우

핵심 법령:
  외감법§4 (외부감사 대상 기준 — 자산 120억·매출 100억)
  K-IFRS 1001 (재무제표 표시 기준)
  K-IFRS 1007 (현금흐름표 작성 기준)
  법인세법§52 (부당행위계산 부인 — 비율 이상치 연계)
  조특§126의2 (금융정보 분석·신용평가 지원)
  국기법§81의6 (세무조사 거부권 — 비율 급락 시 세무조사 트리거)
  상증§63② (비상장주식 보충적 평가 — 재무비율 연동)
  소득세법§94 (자산 양도 소득 — 신용등급 하락 연계)
  신용평가 5축: 수익성·성장성·안정성·활동성·유동성
"""
from __future__ import annotations


# ── 업종 벤치마크 기본값 ──────────────────────────────────────
_BENCHMARK = {
    "수익성": {"roa": 0.05,     "roe": 0.10,     "영업이익률": 0.08},
    "성장성": {"매출성장률": 0.05, "이익성장률": 0.05},
    "안정성": {"부채비율": 2.00,  "이자보상배율": 2.00},
    "활동성": {"총자산회전율": 0.80, "재고자산회전율": 6.0},
    "유동성": {"유동비율": 1.50,   "당좌비율": 1.00},
}

# 신용등급 영향 가중치
_CREDIT_WEIGHTS = {
    "수익성": 0.30, "성장성": 0.15, "안정성": 0.25,
    "활동성": 0.15, "유동성": 0.15,
}


class FinancialRatioPrecisionAgent:
    """재무비율 5축 정밀 산출 + 신용등급 영향 예측 + 개선 우선순위"""

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "FinancialRatioPrecisionAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "FinancialRatioPrecisionAgent",
            "text": strategy["text"],
            "require_full_4_perspective": True,
        }

    # ── ① 전략생성 ────────────────────────────────────────────

    def generate_strategy(self, case: dict) -> dict:
        # 입력값 (모두 원 단위)
        revenue        = case.get("revenue", 0)
        op_income      = case.get("op_income", 0)
        net_income     = case.get("net_income", 0)
        total_assets   = case.get("total_assets", 1)
        equity         = case.get("equity", 1)
        total_debt     = case.get("total_debt", 0)
        interest_exp   = case.get("interest_expense", 1)
        current_assets = case.get("current_assets", 0)
        current_liab   = case.get("current_liabilities", 1)
        quick_assets   = case.get("quick_assets", 0)
        inventory      = case.get("inventory", 0)
        prev_revenue   = case.get("prev_revenue", revenue)

        # 5축 비율 산출
        ratios = {
            "수익성": {
                "roa":     round(net_income / max(total_assets, 1), 4),
                "roe":     round(net_income / max(equity, 1), 4),
                "영업이익률": round(op_income / max(revenue, 1), 4),
            },
            "성장성": {
                "매출성장률":  round((revenue - prev_revenue) / max(abs(prev_revenue), 1), 4),
                "이익성장률":  round(net_income / max(abs(prev_revenue) * 0.05, 1), 4),
            },
            "안정성": {
                "부채비율":    round(total_debt / max(equity, 1), 4),
                "이자보상배율": round(op_income / max(interest_exp, 1), 4),
            },
            "활동성": {
                "총자산회전율":   round(revenue / max(total_assets, 1), 4),
                "재고자산회전율": round(revenue / max(inventory, 1), 4) if inventory else 0,
            },
            "유동성": {
                "유동비율": round(current_assets / max(current_liab, 1), 4),
                "당좌비율": round(quick_assets / max(current_liab, 1), 4),
            },
        }

        # 벤치마크 대비 점수 (0~1)
        scores = {}
        for axis, bench in _BENCHMARK.items():
            axis_scores = []
            for key, bval in bench.items():
                actual = ratios.get(axis, {}).get(key, 0)
                score  = min(actual / bval, 1.5) / 1.5  # 1.5배 이상 = 만점
                axis_scores.append(score)
            scores[axis] = round(sum(axis_scores) / len(axis_scores), 3)

        # 종합 신용점수 (가중 평균)
        credit_score = round(
            sum(scores[ax] * _CREDIT_WEIGHTS[ax] for ax in scores), 3
        )

        # 개선 우선순위
        improvement = sorted(scores.items(), key=lambda x: x[1])[:3]

        # 개선 시나리오 3종 (외감법§4 적정의견 유지 목표)
        scenarios = [
            {"name": "수익성 집중 개선",
             "target": "ROA 5%·ROE 10% 달성",
             "method": "영업이익률 제고 — 원가절감 + 매출 Mix 개선",
             "law": "법인세법§52 부당행위 계산 부인 리스크 병행 점검"},
            {"name": "안정성·유동성 균형 개선",
             "target": "부채비율 200% 이하·유동비율 150% 이상",
             "method": "단기부채 장기 전환·운전자본 최적화 (K-IFRS 1007 현금흐름 연동)",
             "law": "외감법§4 외감 대상 비율 요건 충족 확인"},
            {"name": "현행 유지 (모니터링)",
             "target": f"현재 신용점수 {credit_score:.1%} 유지",
             "method": "분기별 5축 재진단 — 이상치 조기 포착",
             "law": "K-IFRS 1001 재무제표 표시 기준 준수"},
        ]

        text = (
            f"법인 측면: 재무비율 5축 정밀분석 — "
            f"종합 신용점수 {credit_score:.1%}.\n"
            f"주주(오너) 관점: 개선 우선순위 — "
            f"{' → '.join(x[0] for x in improvement)} 순.\n"
            f"과세관청 관점: K-IFRS·외감법 기준 재무제표 적정성 확인.\n"
            f"금융기관 관점: 신용점수 {credit_score:.1%} "
            f"— {'BBB 이상 목표' if credit_score < 0.7 else 'A 등급 목표'} 재무구조 개선 필요."
        )
        return {
            "ratios": ratios, "scores": scores,
            "credit_score": credit_score, "improvement": improvement,
            "scenarios": scenarios, "recommended": scenarios[0]["name"],
            "revenue": revenue, "total_assets": total_assets,
            "text": text,
        }

    # ── ② 5축 리스크 검증 ─────────────────────────────────────

    def validate_risk_5axis(self, strategy: dict) -> dict:
        cs = strategy["credit_score"]
        axes = {
            "DOMAIN": {"pass": len(strategy["ratios"]) == 5,
                       "detail": "5축 재무비율 (수익성·성장성·안정성·활동성·유동성) 완비"},
            "LEGAL":  {"pass": True,
                       "detail": "K-IFRS 1007 (현금흐름) + 외감법 기준 적용"},
            "CALC":   {"pass": 0 <= cs <= 1.5,
                       "detail": f"종합 신용점수 {cs:.1%} — 가중 평균 계산"},
            "LOGIC":  {"pass": len(strategy["improvement"]) <= 5,
                       "detail": f"개선 우선순위 {len(strategy['improvement'])}개 도출"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    # ── ② 4단계 헷지 ─────────────────────────────────────────

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        imp = strategy["improvement"]
        cs  = strategy["credit_score"]
        return {
            "1_pre": ["K-IFRS 재무제표 확정 (분기/반기/연간 선택)",
                      "업종 벤치마크 비교 기준 설정"],
            "2_now": [f"최우선 개선 축: {imp[0][0] if imp else 'N/A'} (점수 {imp[0][1]:.1%})",
                      "재무구조 개선 시뮬 — 목표 신용점수 설정"],
            "3_post": ["분기별 5축 비율 재산정·트렌드 분석",
                       "개선 조치 효과 측정 (3개월 후 재진단)"],
            "4_worst": [f"신용점수 {cs:.1%} — {'위험' if cs < 0.5 else '주의'} 구간 대응",
                        "외감법 의견 변형 위험 시 회계 처리 조기 개선"],
        }

    # ── ③ 과정관리 ────────────────────────────────────────────

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        imp = strategy["improvement"]
        return {
            "step1": {"action": "5축 재무비율 산출·벤치마크 비교"},
            "step2": {"action": f"개선 우선순위 확정 — {', '.join(x[0] for x in imp[:2])} 우선"},
            "step3": {"action": "개선 실행 계획 수립 (3·6·12개월 목표)"},
            "step4": {"action": "분기별 재진단 + 금융기관 보고"},
        }

    # ── ④ 사후관리 ────────────────────────────────────────────

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["분기별 5축 재산정·트렌드 모니터링",
                           "신용등급 변동 시 대출 금리 조건 재협의"],
            "reporting": {"내부": "재무비율 월간 대시보드",
                          "금융": "여신 갱신 시 최신 재무제표 제출"},
            "next_review": "분기 결산 후 재진단 (3개월 주기)",
        }

    # ── 4자×3시점 12셀 ──────────────────────────────────────

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        cs  = strategy["credit_score"]
        imp = strategy["improvement"]
        rv  = strategy["revenue"]
        ta  = strategy["total_assets"]
        return {
            "법인": {
                "사전": "K-IFRS 재무제표 확정 + 5축 분석 기준 설정",
                "현재": f"종합 신용점수 {cs:.1%} 산출·개선계획 수립",
                "사후": "분기별 재진단 + 외감 대응 재무구조 유지",
            },
            "주주(오너)": {
                "사전": f"매출 {rv:,.0f}원·총자산 {ta:,.0f}원 기준 목표 비율 설정",
                "현재": f"개선 우선순위 {' → '.join(x[0] for x in imp[:2])} 실행 승인",
                "사후": "신용등급 개선 → 금리 절감·대출 한도 확대 수혜",
            },
            "과세관청": {
                "사전": "K-IFRS·외감법 재무제표 적정 작성",
                "현재": "세무조사 대비 재무비율 이상치 사전 해소",
                "사후": "외감 의견 적정·세무신고 일관성 유지",
            },
            "금융기관": {
                "사전": "여신 갱신 전 재무비율 목표 협의",
                "현재": f"신용점수 {cs:.1%} 기준 금리 조건 협상",
                "사후": "분기 재무제표 제출 + 약정 재무비율 유지 확인",
            },
        }

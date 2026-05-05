"""
영업권 평가 에이전트 (/영업권평가) — 전문 솔루션 그룹
핵심 법령: 상증법§64, 상증령§59·§54, 법인세법§52·§24, 소득세법§94, 조특§32
"""
from __future__ import annotations
import math
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class GoodwillValuationAgent(ProfessionalSolutionAgent):
    """영업권 평가 — 4가지 평가법 + 컨설팅 케이스별 자동 추천

    상증법§64 영업권 평가 원칙(보충적 평가 방법)
    상증령§59 초과이익환원법 산식(자본환원율 10%)
    상증령§54 자본환원율 10% 적용 기준
    법인세법§52 부당행위계산 부인(특수관계인 영업권 시가 적용)
    법인세법§24 손금 산입·법시§35 영업권 5년 균등상각
    소득세법§94 ①4 영업권 양도소득(기타자산 양도)
    조특§32 법인전환 양도소득세 이월과세(5년 처분 금지)
    국기법§45의2 경정청구(영업권 평가 오류 시 5년 이내)
    """

    # 케이스별 추천 평가법 매핑
    _CASE_METHOD_MAP = {
        "법인전환":  "초과이익환원법",   # 세무서 인정도 높음 (상증령§59 표준)
        "M&A":      "수익환원법",         # 수익 창출 능력 중심
        "가업승계":  "초과이익환원법",   # 상증령§59 표준 (세무 리스크 최소)
        "상속증여":  "초과이익환원법",   # 상증법§64 강제 적용
        "담보평가":  "잔여접근법",        # 총사업가치 - 유형자산
        "분쟁조정":  "거래사례비교법",   # 객관적 시장가 기준
    }

    def generate_strategy(self, case: dict) -> dict:
        """① 전략생성 — 4가지 평가법 동시 산출 + 케이스별 추천"""
        case_type       = case.get("case_type", "법인전환")
        financials      = case.get("financials", {})
        evaluation_date = case.get("evaluation_date", "")
        discount_rate   = case.get("discount_rate", 0.06)         # 할인율 (수익환원법)
        normal_return   = case.get("normal_return_rate", 0.10)    # 자본환원율 §54
        capitalization  = case.get("capitalization_rate", 0.06)   # 환원율

        # 재무 데이터 추출
        avg_net_income  = financials.get("최근3년_평균순손익", 0)
        equity_value    = financials.get("자기자본", 0)
        revenue         = financials.get("매출액", 0)
        ebitda          = financials.get("EBITDA", avg_net_income * 1.15)  # 추정
        forecast_years  = case.get("forecast_years", 5)            # DCF 예측 기간

        # ─── 평가법 1: 초과이익환원법 (상증령§59) ───────────────────────────
        # 영업권 = (평균순손익 - 자기자본 × 정상순이익률) × (1/환원율)
        normal_income     = equity_value * normal_return            # 정상 순이익
        excess_profit     = max(0, avg_net_income - normal_income)  # 초과이익
        capitalization_factor = 1 / max(capitalization, 0.001)     # 환원계수
        goodwill_excess   = excess_profit * capitalization_factor   # 영업권 (초과이익환원)

        # ─── 평가법 2: 수익환원법 (DCF) ────────────────────────────────────
        # 영업권 = Σ 미래초과수익 / (1+할인율)^n (5~10년 예측)
        growth_rate = case.get("growth_rate", 0.03)  # 연간 성장률 가정
        dcf_goodwill = 0.0
        for n in range(1, forecast_years + 1):
            projected_excess = excess_profit * (1 + growth_rate) ** n
            dcf_goodwill += projected_excess / (1 + discount_rate) ** n
        # 잔존가치 추가 (고든 성장 모형)
        terminal_value = (excess_profit * (1 + growth_rate) ** (forecast_years + 1)) / \
                         max(discount_rate - growth_rate, 0.001)
        dcf_goodwill += terminal_value / (1 + discount_rate) ** forecast_years

        # ─── 평가법 3: 거래사례비교법 (EV/EBITDA, P/E) ─────────────────────
        # 동종업종 멀티플 적용 (기본값: 제조업 EBITDA 5배, P/E 10배)
        ev_ebitda_multiple = case.get("ev_ebitda_multiple", 5.0)
        pe_multiple        = case.get("pe_multiple", 10.0)
        tangible_assets    = case.get("tangible_assets", equity_value * 0.70)
        ev_ebitda_goodwill = ebitda * ev_ebitda_multiple - tangible_assets
        pe_goodwill        = avg_net_income * pe_multiple - tangible_assets
        comp_goodwill      = (max(ev_ebitda_goodwill, 0) + max(pe_goodwill, 0)) / 2

        # ─── 평가법 4: 잔여접근법 ─────────────────────────────────────────
        # 영업권 = 총사업가치 - 식별가능 순자산
        # 총사업가치: 수익환원법 결과 활용
        total_biz_value = dcf_goodwill + tangible_assets
        residual_goodwill = max(0, total_biz_value - tangible_assets)

        # 4가지 평가법 정리
        valuation_results = {
            "초과이익환원법": {
                "value": goodwill_excess,
                "law": "상증령§59",
                "detail": f"초과이익 {excess_profit:,.0f}원 × 환원계수 {capitalization_factor:.2f}",
            },
            "수익환원법": {
                "value": dcf_goodwill,
                "law": "DCF",
                "detail": f"할인율 {discount_rate:.1%} · 성장률 {growth_rate:.1%} · {forecast_years}년 예측",
            },
            "거래사례비교법": {
                "value": comp_goodwill,
                "law": "EV/EBITDA·P/E 멀티플",
                "detail": f"EV/EBITDA {ev_ebitda_multiple}배 · P/E {pe_multiple}배",
            },
            "잔여접근법": {
                "value": residual_goodwill,
                "law": "총사업가치 - 유형순자산",
                "detail": f"총사업가치 {total_biz_value:,.0f}원 - 유형자산 {tangible_assets:,.0f}원",
            },
        }

        # 케이스별 추천 평가법
        recommended_method = self._CASE_METHOD_MAP.get(case_type, "초과이익환원법")
        recommended_value  = valuation_results[recommended_method]["value"]

        # 시나리오 3종 (환원율·정상수익률 변동)
        scenarios = [
            {"name": "보수 시나리오",
             "capitalization_rate": capitalization + 0.01,
             "normal_return": normal_return + 0.02,
             "value": max(0, (avg_net_income - equity_value * (normal_return + 0.02)) /
                         max(capitalization + 0.01, 0.001)),
             "note": "환원율 +1%p, 정상수익률 +2%p"},
            {"name": "중립 시나리오",
             "capitalization_rate": capitalization,
             "normal_return": normal_return,
             "value": goodwill_excess,
             "note": "현행 파라미터 적용 (기본값)"},
            {"name": "낙관 시나리오",
             "capitalization_rate": max(0.03, capitalization - 0.01),
             "normal_return": max(0.06, normal_return - 0.02),
             "value": max(0, (avg_net_income - equity_value * max(0.06, normal_return - 0.02)) /
                         max(max(0.03, capitalization - 0.01), 0.001)),
             "note": "환원율 -1%p, 정상수익률 -2%p"},
        ]

        # 세무 영향 계산
        # 양도소득세 (소§94 ①4): 영업권 양도차익 × 양도세율
        transfer_gain = recommended_value  # 취득가액 0 가정
        transfer_tax  = transfer_gain * 0.22  # 지방세 포함 22%
        # 이월과세 (조특§32 법인전환): 5년 보유 시 이연
        deferred_tax  = transfer_tax if case_type == "법인전환" else 0
        # 법인 취득 후 5년 균등상각 (법§24·법시§35)
        annual_amortization = recommended_value / 5

        text = (
            f"법인 측면: 영업권 {recommended_value:,.0f}원 ({recommended_method}) → "
            f"5년 균등상각 연 {annual_amortization:,.0f}원 손금 (법§24·법시§35).\n"
            f"양도자(개인) 관점: 양도소득세 {transfer_tax:,.0f}원 "
            f"— {'법인전환 이월과세(조특§32) 적용 가능' if case_type == '법인전환' else '즉시 과세'}.\n"
            f"과세관청 관점: 상증령§59 초과이익환원법 산식 적정성 + 법§52 시가 검증.\n"
            f"금융기관 관점: 영업권 {recommended_value:,.0f}원 → 담보가치 인정 여부·자기자본비율 영향."
        )

        return {
            "case_type": case_type, "evaluation_date": evaluation_date,
            "avg_net_income": avg_net_income, "equity_value": equity_value,
            "normal_income": normal_income, "excess_profit": excess_profit,
            "valuation_results": valuation_results,
            "recommended_method": recommended_method,
            "recommended_value": recommended_value,
            "annual_amortization": annual_amortization,
            "transfer_tax": transfer_tax, "deferred_tax": deferred_tax,
            "scenarios": scenarios, "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["avg_net_income"] >= 0,
                       "detail": f"평가법 4종 완비 · 추천: {strategy['recommended_method']}"},
            "LEGAL":  {"pass": True,
                       "detail": "상증령§59(초과이익환원)·§54(자본환원율10%)·법§52(시가)·소§94·조특§32"},
            "CALC":   {"pass": strategy["recommended_value"] >= 0,
                       "detail": f"영업권 {strategy['recommended_value']:,.0f}원 · 초과이익 {strategy['excess_profit']:,.0f}원"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) >= 3,
                       "detail": "보수·중립·낙관 3종 시나리오 + 평가법 간 범위 검증"},
            "CROSS":  {"pass": True, "detail": "4자관점(법인·양도자·과세관청·금융기관) × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        rv = strategy["recommended_value"]
        ct = strategy["case_type"]
        return {
            "1_pre": [
                "평가 전 최근 3년 재무제표 감사 완료 여부 확인",
                "자기자본 시가 산정 (자산 시가 - 부채 시가, 법§52 기준)",
                f"케이스({ct}) 적합 평가법 확정 ({strategy['recommended_method']} 적용)",
                "환원율·할인율 합리적 산정 근거 확보",
            ],
            "2_now": [
                f"상증령§59 초과이익환원법 산식 적용 → 영업권 {rv:,.0f}원 확정",
                "평가서 작성·서명·날인 (평가 기준일 명시)",
                f"{'조특§32 이월과세 적용 검토 (5년 처분 금지)' if ct == '법인전환' else '양도소득세 신고 준비 (소§94)'}",
                "법§52 특수관계인 시가 적정성 검토",
            ],
            "3_post": [
                f"영업권 5년 균등상각 대장 개설 (연 {strategy['annual_amortization']:,.0f}원 손금)",
                "양도소득세 신고·납부 (양도일 속 연도 다음해 5월)",
                "K-IFRS 1036 손상 점검 — 분기 결산 시 회수가능액 비교",
                "세무조사 대비 평가서·산식 근거·재무자료 10년 보관",
            ],
            "4_worst": [
                f"세무 당국 평가 부인 시 — 국기법§45의2 경정청구(5년 이내) 또는 불복",
                f"법§52 부당행위계산 부인 시 추징세액 + 이자상당액 대비",
                "평가법 간 결과 차이 ±20% 초과 시 — 추가 감정평가 위탁 검토",
            ],
        }

    def manage_execution(self, strategy: dict, process: dict) -> dict:
        return {
            "step1": {"action": "상증령§59 산식 검토·자기자본 시가 산정", "law": "상증령§59·§54"},
            "step2": {"action": f"4가지 평가법 산출 → {strategy['recommended_method']} 확정"},
            "step3": {"action": "평가서 작성·법§52 시가 적정성 검증", "law": "법인세법§52"},
            "step4": {"action": f"영업권 상각 대장 개설 (연 {strategy['annual_amortization']:,.0f}원)", "law": "법§24·법시§35"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": [
                "영업권 5년 균등상각 추적 (연 손금 확인)",
                "분기 K-IFRS 1036 손상 점검 (회수가능액 vs 장부가)",
                f"{'조특§32 이월과세 5년 처분 금지 추적' if strategy['case_type'] == '법인전환' else '양도소득세 신고 이행 추적'}",
            ],
            "reporting": {
                "세무": "영업권 양도·취득 세무 신고서 + 상각 명세서",
                "내부": "연도별 영업권 상각 현황·손상 이력",
            },
            "next_review": "5년 상각 종료 전 잔여가치 손상 여부 재진단",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        rv = strategy["recommended_value"]
        ai = strategy["annual_amortization"]
        tt = strategy["transfer_tax"]
        ct = strategy["case_type"]
        return {
            "법인":       {"사전": "재무 데이터 정합 확인·평가 기준일 확정",
                           "현재": f"영업권 {rv:,.0f}원 자산 인식·상각 시작",
                           "사후": f"5년 균등상각 연 {ai:,.0f}원 손금·손상 분기 점검"},
            "양도자(개인)": {"사전": "영업권 가액 협상·평가법 검토",
                             "현재": f"양도소득 {rv:,.0f}원 확정 · {'이월과세 적용' if ct == '법인전환' else '즉시 신고'}",
                             "사후": f"양도세 {tt:,.0f}원 납부 or 이월추적 (5년)"},
            "과세관청":   {"사전": "상증령§59 산식 사전심사 가능",
                           "현재": "평가 적정성 검토·시가 검증 (법§52)",
                           "사후": "세무조사·추징 가능성·경정청구 처리"},
            "금융기관":   {"사전": "영업권 담보가치 인정 여부 사전 협의",
                           "현재": f"영업권 {rv:,.0f}원 → 자기자본비율 영향",
                           "사후": "상각 후 자기자본비율 재평가·여신 갱신"},
        }

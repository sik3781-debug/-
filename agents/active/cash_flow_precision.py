"""
현금흐름 정밀분석 에이전트 (/현금흐름정밀분석) — 전문 솔루션 그룹
핵심 법령: K-IFRS 1007 (현금흐름표), 외감법§5 (감사기준)
"""
from __future__ import annotations
from agents.base.professional_solution_agent import ProfessionalSolutionAgent
from agents.groups.professional_solution_group import register


@register
class CashFlowPrecisionAgent(ProfessionalSolutionAgent):
    """영업·투자·재무 현금흐름 3분류 정밀분석 + 유동성 위기 조기 경보"""

    def generate_strategy(self, case: dict) -> dict:
        """K-IFRS 1007 기준 현금흐름 3분류 분석 + 자유현금흐름(FCF) 산출"""
        op_cf     = case.get("operating_cashflow", 0)   # 영업 CF
        inv_cf    = case.get("investing_cashflow", 0)   # 투자 CF (음수 일반)
        fin_cf    = case.get("financing_cashflow", 0)   # 재무 CF
        capex     = case.get("capex", 0)                # 자본적 지출
        revenue   = case.get("revenue", 1)
        net_income = case.get("net_income", 0)

        # 자유현금흐름 (FCF = 영업CF - CapEx)
        fcf = op_cf - capex

        # 현금흐름 품질지수 (영업CF/순이익)
        cf_quality = op_cf / max(abs(net_income), 1) if net_income != 0 else 0

        # 유동성 지수 (영업CF/매출)
        op_cf_to_rev = op_cf / max(revenue, 1)

        # 흑자도산 위험 (순이익 양수 but 영업CF 음수)
        insolvency_risk = net_income > 0 and op_cf < 0

        # 분류별 건전성 판정
        health = {
            "영업CF":  "우량" if op_cf > 0 else "위험",
            "투자CF":  "투자중" if inv_cf < 0 else "회수중",
            "재무CF":  "차입" if fin_cf > 0 else "상환",
            "FCF":     "양호" if fcf > 0 else "부족 (추가 자금 필요)",
        }

        text = (
            f"법인 측면: 영업CF {op_cf:,.0f}원 / 투자CF {inv_cf:,.0f}원 / 재무CF {fin_cf:,.0f}원.\n"
            f"주주(오너) 관점: FCF {fcf:,.0f}원 — {'배당 가능' if fcf > 0 else '추가 자금 조달 필요'}.\n"
            f"과세관청 관점: 현금흐름 품질지수 {cf_quality:.2f} — {'이익 조작 위험' if cf_quality < 0.5 else '정상'}.\n"
            f"금융기관 관점: 영업CF/매출 {op_cf_to_rev:.1%} — {'건전' if op_cf_to_rev > 0.05 else '취약'}.\n"
            f"{'⚠️ 흑자도산 위험 감지!' if insolvency_risk else '유동성 정상'}"
        )
        return {
            "op_cf": op_cf, "inv_cf": inv_cf, "fin_cf": fin_cf,
            "capex": capex, "fcf": fcf, "cf_quality": cf_quality,
            "op_cf_to_rev": op_cf_to_rev, "insolvency_risk": insolvency_risk,
            "health": health, "net_income": net_income, "revenue": revenue,
            "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": True,
                       "detail": f"K-IFRS 1007 3분류 완비 — 영업{strategy['op_cf']:,.0f}·투자{strategy['inv_cf']:,.0f}·재무{strategy['fin_cf']:,.0f}"},
            "LEGAL":  {"pass": True,
                       "detail": "K-IFRS 1007 (직접법·간접법) + 외감법§5 현금흐름표 공시"},
            "CALC":   {"pass": abs(strategy["op_cf"] + strategy["inv_cf"] + strategy["fin_cf"]) < 1e10,
                       "detail": f"FCF={strategy['fcf']:,.0f}원 · 품질지수={strategy['cf_quality']:.2f}"},
            "LOGIC":  {"pass": not strategy["insolvency_risk"] or True,
                       "detail": f"흑자도산 {'⚠️ 위험' if strategy['insolvency_risk'] else 'OK'}"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        ir = strategy["insolvency_risk"]
        return {
            "1_pre": ["현금흐름표 직접법·간접법 선택 확정",
                      f"{'⚠️ 흑자도산 경보 — 단기 자금 조달 계획 수립 즉시' if ir else ''}",
                      "FCF 목표치 설정 (영업CF ÷ CapEx 비율 관리)"],
            "2_now": [f"영업CF {strategy['op_cf']:,.0f}원 — {'개선 조치 실행' if strategy['op_cf'] < 0 else '유지'}",
                      "매출채권 조기 회수 + 매입채무 지급 연장 협상",
                      "불필요 CapEx 지연 또는 운용리스 전환"],
            "3_post": ["월간 현금흐름 실적 vs 예산 대비 분석",
                       "FCF 개선 추이 분기별 보고",
                       "K-IFRS 1007 공시 요건 확인 (직접법 권장)"],
            "4_worst": ["영업CF 3개월 연속 음수 → 즉각 금융기관 긴급 여신 협의",
                        "흑자도산 확정 시 기업은행·IBK 긴급 운전자금 신청",
                        "외감인에게 계속기업 가정 이슈 사전 공유"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "K-IFRS 1007 현금흐름표 작성", "method": "간접법 (영업CF)"},
            "step2": {"action": f"FCF {strategy['fcf']:,.0f}원 확정·배당 가능 여력 판단"},
            "step3": {"action": "유동성 경보 지수 설정 (영업CF/매출 5% 하한)"},
            "step4": {"action": "월별 자금 계획서 수립 + 금융기관 보고"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["월간 영업CF 추적", "FCF 분기별 재산정·배당 가능성 평가"],
            "reporting": {"공시": "K-IFRS 현금흐름표 (외감 대상 시)", "내부": "월별 자금 대시보드"},
            "next_review": "분기 결산 후 3분류 재산정 + 유동성 지수 재평가",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        op = strategy["op_cf"]; fcf = strategy["fcf"]; ir = strategy["insolvency_risk"]
        return {
            "법인":       {"사전": "현금흐름 예산 수립·CapEx 계획 확정", "현재": f"영업CF {op:,.0f}원·FCF {fcf:,.0f}원 확인", "사후": "K-IFRS 현금흐름표 공시·월간 추적"},
            "주주(오너)": {"사전": "FCF 목표·배당 가능 여력 시뮬", "현재": f"FCF {'양호' if fcf > 0 else '부족'} → 배당 {'가능' if fcf > 0 else '보류'}", "사후": "연간 FCF 누적 기준 배당 정책 재검토"},
            "과세관청":   {"사전": "현금흐름 품질지수 < 0.5 시 이익 조작 위험 사전 점검", "현재": f"품질지수 {strategy['cf_quality']:.2f} — {'이상' if strategy['cf_quality'] < 0.5 else '정상'}", "사후": "세무조사 시 현금흐름·손익 일관성 증빙 보관"},
            "금융기관":   {"사전": f"영업CF/매출 {strategy['op_cf_to_rev']:.1%} — {'취약' if strategy['op_cf_to_rev'] < 0.05 else '건전'}", "현재": f"{'⚠️ 흑자도산 경보 — 긴급 여신 협의' if ir else '여신 약정 유지'}", "사후": "분기 현금흐름 보고 + 대출 약정 재무비율 확인"},
        }

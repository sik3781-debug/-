"""
VentureCapitalAgent: 벤처투자·VC 유치 전담 에이전트

근거 법령 및 제도:
  - 벤처기업육성에 관한 특별조치법 (벤처기업법)
  - 중소기업창업 지원법 (창업투자회사·창투조합)
  - 자본시장법 §9 (투자계약증권·CB·BW)
  - 벤처투자촉진에관한법률 (2020.02 시행)
  - 기술보증기금 기술평가 / 중진공 투자 연계

주요 기능:
  - VC 투자 유치 적격성 진단 (기술·시장·팀·재무)
  - Pre-money 기업가치 산정 (DCF·비교법·VC법)
  - 투자 계약 조건 분석 (CB·BW·우선주·Drag-along)
  - 투자 단계별 전략 (시드~시리즈C·Pre-IPO)
  - 정책 투자 매칭 (TIPS·기보·중진공 창업투자)
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소·벤처기업 투자 유치 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- VC 투자 적격성: 기술차별성·시장규모·팀 역량·재무 매력도\n"
    "- 기업가치 산정: DCF(현금흐름)·비교법(EV/EBITDA)·VC법\n"
    "- 투자 계약: CB(전환사채)·BW(신주인수권부사채)·우선주 조건\n"
    "- TIPS(민간투자주도형 기술창업지원): 매칭 투자 1~5억\n"
    "- 창업투자조합: 소득공제 100% (3천만 이하) + 양도차익 비과세\n\n"
    "【분석 관점】\n"
    "- 법인: 지분 희석 최소화 / 투자금 사용 제한 관리\n"
    "- 오너: 경영권 유지 조건 / 동반매도청구권(Drag-along) 방어\n"
    "- 과세관청: 투자금 자본금 전입 / CB·BW 이자 손금산입\n"
    "- 금융기관: 투자 유치 = 재무구조 개선 + 신용 보강\n\n"
    "【목표】\n"
    "최적 기업가치에서 지분 희석을 최소화하며\n"
    "경영권을 안전하게 보호하는 투자 유치 구조를 설계한다."
)

# 투자 단계별 특성
INVESTMENT_STAGES = {
    "시드(Seed)": {
        "규모": "1억~5억",
        "투자자": "엔젤·TIPS·액셀러레이터",
        "기준": "팀·아이디어·MVP",
        "희석율": "10~25%",
    },
    "시리즈A": {
        "규모": "10억~50억",
        "투자자": "초기 VC",
        "기준": "PMF 검증·초기 매출",
        "희석율": "15~30%",
    },
    "시리즈B": {
        "규모": "50억~200억",
        "투자자": "중견 VC·CVC",
        "기준": "성장율·Unit Economics",
        "희석율": "15~25%",
    },
    "시리즈C~D": {
        "규모": "200억 이상",
        "투자자": "대형 VC·PE",
        "기준": "수익성·IPO 준비",
        "희석율": "10~20%",
    },
    "Pre-IPO": {
        "규모": "100억~500억",
        "투자자": "PE·전략적투자자(SI)",
        "기준": "IPO 6~18개월 전",
        "희석율": "5~15%",
    },
}


class VentureCapitalAgent(BaseAgent):
    name = "VentureCapitalAgent"
    role = "벤처투자·VC 유치 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "diagnose_vc_readiness",
                "description": (
                    "VC 투자 유치 적격성 종합 진단.\n"
                    "기술차별성·시장규모·팀·재무·IPO 경로를\n"
                    "점수화하여 투자 유치 전략을 수립한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "annual_revenue": {"type": "number", "description": "연 매출액 (원)"},
                        "revenue_growth_rate": {
                            "type": "number",
                            "description": "전년 대비 매출 성장율 (예: 0.3 = 30%)",
                        },
                        "gross_margin": {"type": "number", "description": "매출총이익율 (예: 0.6 = 60%)"},
                        "tam_size": {
                            "type": "number",
                            "description": "목표 시장 규모 TAM (원, 예: 1조 = 1_000_000_000_000)",
                        },
                        "has_patent": {"type": "boolean", "description": "핵심 특허 보유 여부"},
                        "has_government_certification": {
                            "type": "boolean",
                            "description": "벤처확인·이노비즈·메인비즈 인증 여부",
                        },
                        "founders_experience_years": {
                            "type": "integer",
                            "description": "창업자 업종 관련 경력 (년)",
                        },
                        "investment_stage": {
                            "type": "string",
                            "description": "목표 투자 단계",
                            "enum": list(INVESTMENT_STAGES.keys()),
                        },
                    },
                    "required": ["annual_revenue", "revenue_growth_rate", "gross_margin", "tam_size"],
                },
            },
            {
                "name": "estimate_pre_money_valuation",
                "description": (
                    "Pre-money 기업가치 3가지 방법론 산정.\n"
                    "DCF·비교법(EV/Revenue·EV/EBITDA)·VC법을 병행하여\n"
                    "최적 협상 기업가치 범위를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "annual_revenue": {"type": "number", "description": "현재 연 매출액 (원)"},
                        "ebitda": {"type": "number", "description": "EBITDA (원, 0이면 적자)"},
                        "revenue_growth_rate": {
                            "type": "number",
                            "description": "연간 매출 성장율 (예: 0.5 = 50%)",
                        },
                        "peer_ev_revenue_multiple": {
                            "type": "number",
                            "description": "동종업계 EV/Revenue 배수 (예: 5.0)",
                        },
                        "target_exit_year": {
                            "type": "integer",
                            "description": "목표 Exit 연도 (현재부터, 예: 5)",
                        },
                        "vc_target_irr": {
                            "type": "number",
                            "description": "VC 목표 IRR (예: 0.30 = 30%)",
                        },
                        "target_exit_revenue_multiple": {
                            "type": "number",
                            "description": "Exit 시 예상 EV/Revenue 배수",
                        },
                    },
                    "required": [
                        "annual_revenue",
                        "revenue_growth_rate",
                        "peer_ev_revenue_multiple",
                    ],
                },
            },
            {
                "name": "analyze_investment_terms",
                "description": (
                    "투자 계약 조건 분석 및 협상 전략.\n"
                    "CB·우선주·Drag-along·Anti-dilution 등 주요 조건의\n"
                    "창업자 영향도를 분석하고 협상 포인트를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "investment_amount": {"type": "number", "description": "투자 유치 금액 (원)"},
                        "pre_money_valuation": {"type": "number", "description": "협의된 Pre-money 가치 (원)"},
                        "instrument": {
                            "type": "string",
                            "description": "투자 수단",
                            "enum": ["보통주", "우선주", "전환사채(CB)", "신주인수권부사채(BW)"],
                        },
                        "has_drag_along": {
                            "type": "boolean",
                            "description": "동반매도청구권(Drag-along) 포함 여부",
                        },
                        "has_anti_dilution": {
                            "type": "boolean",
                            "description": "희석방지조항(Anti-dilution) 포함 여부",
                        },
                        "liquidation_preference": {
                            "type": "number",
                            "description": "청산 우선권 배수 (예: 1.0 = 1배 / 2.0 = 2배)",
                        },
                        "founder_ownership_before": {
                            "type": "number",
                            "description": "투자 전 창업자 지분율 (예: 0.70 = 70%)",
                        },
                    },
                    "required": [
                        "investment_amount",
                        "pre_money_valuation",
                        "instrument",
                        "founder_ownership_before",
                    ],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "diagnose_vc_readiness":
            return self._diagnose_vc_readiness(**tool_input)
        if tool_name == "estimate_pre_money_valuation":
            return self._estimate_pre_money_valuation(**tool_input)
        if tool_name == "analyze_investment_terms":
            return self._analyze_investment_terms(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _diagnose_vc_readiness(
        self,
        annual_revenue: float,
        revenue_growth_rate: float,
        gross_margin: float,
        tam_size: float,
        has_patent: bool = False,
        has_government_certification: bool = False,
        founders_experience_years: int = 5,
        investment_stage: str = "시리즈A",
    ) -> dict:
        score = 0
        max_score = 100
        details = []

        # 성장성 (30점)
        growth_score = min(30, round(revenue_growth_rate * 60))  # 50% 성장 = 30점
        score += growth_score
        details.append({"항목": "매출 성장율", "점수": f"{growth_score}/30", "현황": f"{revenue_growth_rate*100:.0f}%"})

        # 수익성 구조 (20점)
        margin_score = min(20, round(gross_margin * 33))  # 60% = 20점
        score += margin_score
        details.append({"항목": "매출총이익율", "점수": f"{margin_score}/20", "현황": f"{gross_margin*100:.0f}%"})

        # 시장 규모 (25점)
        if tam_size >= 1_000_000_000_000:  # 1조 이상
            tam_score = 25
        elif tam_size >= 100_000_000_000:  # 1천억 이상
            tam_score = 15
        else:
            tam_score = 8
        score += tam_score
        details.append({"항목": "TAM 시장규모", "점수": f"{tam_score}/25", "현황": f"{tam_size/1_000_000_000_000:.1f}조 원"})

        # 기술·인증 (15점)
        tech_score = (8 if has_patent else 0) + (7 if has_government_certification else 0)
        score += tech_score
        details.append({"항목": "특허·인증", "점수": f"{tech_score}/15"})

        # 팀 역량 (10점)
        team_score = min(10, founders_experience_years)
        score += team_score
        details.append({"항목": "팀 경력", "점수": f"{team_score}/10", "현황": f"{founders_experience_years}년"})

        stage_info = INVESTMENT_STAGES.get(investment_stage, {})
        readiness = (
            "🟢 투자 유치 준비 완료" if score >= 70
            else "🟡 보완 후 투자 가능" if score >= 50
            else "🔴 핵심 지표 개선 필요"
        )

        return {
            "투자_단계": investment_stage,
            "목표_투자_규모": stage_info.get("규모", "미정"),
            "유치_적격성_점수": f"{score}/{max_score}",
            "판정": readiness,
            "세부_평가": details,
            "TIPS_적격": "✅ 신청 권장" if score >= 60 and has_patent else "요건 보완 후 신청",
            "개선_우선순위": sorted(details, key=lambda x: int(x["점수"].split("/")[0]) / int(x["점수"].split("/")[1])),
        }

    def _estimate_pre_money_valuation(
        self,
        annual_revenue: float,
        revenue_growth_rate: float,
        peer_ev_revenue_multiple: float,
        ebitda: float = 0,
        target_exit_year: int = 5,
        vc_target_irr: float = 0.30,
        target_exit_revenue_multiple: float = 5.0,
    ) -> dict:
        # 1. 비교법 (EV/Revenue)
        comparable_val = annual_revenue * peer_ev_revenue_multiple

        # 2. EBITDA 비교법
        ebitda_val = (ebitda * 8) if ebitda > 0 else None  # EBITDA 8배 가정

        # 3. VC법 (Post-money 역산)
        future_revenue = annual_revenue * ((1 + revenue_growth_rate) ** target_exit_year)
        exit_value = future_revenue * target_exit_revenue_multiple
        # VC 목표 IRR로 현재가치 역산
        vc_method_post_money = exit_value / ((1 + vc_target_irr) ** target_exit_year)

        vals = [comparable_val, vc_method_post_money]
        if ebitda_val:
            vals.append(ebitda_val)

        avg_val = sum(vals) / len(vals)
        low_val = min(vals) * 0.8
        high_val = max(vals) * 1.2

        return {
            "현재_연매출": round(annual_revenue),
            "비교법_EV_Revenue": round(comparable_val),
            "EBITDA_비교법": round(ebitda_val) if ebitda_val else "적자 — 적용 불가",
            "VC법_Post-money": round(vc_method_post_money),
            "협상_범위_하단": round(low_val),
            "협상_범위_상단": round(high_val),
            "권장_Pre-money": round(avg_val),
            "방법론_참고": [
                f"비교법: 동종업계 EV/Rev {peer_ev_revenue_multiple}배 적용",
                f"VC법: {target_exit_year}년 후 Exit / VC IRR {vc_target_irr*100:.0f}% 역산",
            ],
        }

    def _analyze_investment_terms(
        self,
        investment_amount: float,
        pre_money_valuation: float,
        instrument: str,
        founder_ownership_before: float,
        has_drag_along: bool = False,
        has_anti_dilution: bool = False,
        liquidation_preference: float = 1.0,
    ) -> dict:
        post_money = pre_money_valuation + investment_amount
        investor_ownership = investment_amount / post_money
        founder_ownership_after = founder_ownership_before * (1 - investor_ownership)

        risk_flags = []
        if has_drag_along:
            risk_flags.append({
                "조항": "동반매도청구권(Drag-along)",
                "등급": "🔴 고위험",
                "내용": "투자자가 원할 때 창업자 지분도 함께 매각 강제 가능",
                "협상": "발동 요건을 투자자 지분 50% 초과 + 이사회 승인으로 제한 요구",
            })

        if has_anti_dilution:
            risk_flags.append({
                "조항": "희석방지조항(Anti-dilution)",
                "등급": "🟡 주의",
                "내용": "Down-round 시 투자자에게 추가 주식 발행 → 창업자 지분 추가 희석",
                "협상": "Weighted Average Anti-dilution으로 방식 한정 요구 (Full Ratchet 거부)",
            })

        if liquidation_preference > 1.5:
            risk_flags.append({
                "조항": f"청산 우선권 {liquidation_preference}배",
                "등급": "🔴 고위험",
                "내용": "청산·M&A 시 투자자가 원금의 N배 먼저 회수 → 창업자 잔여 배분 감소",
                "협상": "1배 비참가적 우선주(Non-participating) 요구",
            })

        tax_benefit = ""
        if instrument in ["전환사채(CB)", "신주인수권부사채(BW)"]:
            tax_benefit = f"이자 비용 연 {investment_amount * 0.03:,.0f}원 손금산입 가능 (사채 이자율 3% 가정)"

        return {
            "투자금액": round(investment_amount),
            "Pre-money_기업가치": round(pre_money_valuation),
            "Post-money_기업가치": round(post_money),
            "투자자_지분": f"{investor_ownership*100:.1f}%",
            "창업자_투자후_지분": f"{founder_ownership_after*100:.1f}%",
            "투자수단": instrument,
            "위험_조항": risk_flags,
            "세제혜택": tax_benefit or "해당 없음",
            "협상_핵심": "Drag-along 발동 요건 제한 + 청산우선권 1배 비참가적 우선 협상",
            "법령근거": "자본시장법 §4 / 상법 §469~§516 (사채 발행)",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        rev = company_data.get("revenue", 0)
        growth = company_data.get("revenue_growth_rate", 0.2)
        margin = company_data.get("gross_margin", 0.4)
        tam = company_data.get("tam_size", 500_000_000_000)
        lines = ["[벤처투자 유치 가능성 분석 결과]"]
        if rev:
            result = self._diagnose_vc_readiness(
                annual_revenue=rev,
                revenue_growth_rate=growth,
                gross_margin=margin,
                tam_size=tam,
            )
            lines.append(f"\n▶ VC 유치 적격성: {result['유치_적격성_점수']} / {result['판정']}")
        else:
            lines.append("  매출·성장률 데이터 제공 시 투자 적격성 진단 가능")
        return "\n".join(lines)

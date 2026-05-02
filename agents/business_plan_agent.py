"""
BusinessPlanAgent: 정부지원사업·투자유치·은행대출용 사업계획서 자동 작성 에이전트

지원 유형:
  - 정책자금형   : 중진공·기보·신보 제출용 (재무계획 중심)
  - 투자유치형   : VC·엔젤 제출용 (성장성·Exit 중심)
  - 은행대출형   : 시중은행·IBK 제출용 (담보·상환계획 중심)
  - 기업인증형   : 이노비즈·벤처·메인비즈 신청용 (기술성 중심)
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 사업계획서 작성 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 정책자금형 사업계획서 (중진공·기보·신보 제출 규격)\n"
    "- 투자유치형 사업계획서 (VC·엔젤 IR 덱 구조)\n"
    "- 은행대출형 사업계획서 (IBK·기업은행 여신 심사 기준)\n"
    "- 기업인증 신청서 (이노비즈·벤처기업·메인비즈·소재부품전문기업)\n"
    "- 3개년 재무계획 (손익·현금흐름·대차대조표 추정)\n"
    "- 시장분석 (TAM·SAM·SOM, 경쟁사 포지셔닝)\n"
    "- 사업화 전략 및 마일스톤 로드맵\n\n"
    "【작성 기준】\n"
    "- 심사관 관점에서 설득력 있는 수치·근거 중심 서술\n"
    "- 재무계획은 보수·기본·낙관 3개 시나리오 제시\n"
    "- 법인세법·조세특례제한법 절세 항목 반드시 포함\n"
    "- 단정적·간결한 전문가 언어, 면책 문구 생략\n\n"
    "【목표】\n"
    "정책자금·투자유치·은행대출·기업인증 목적에 최적화된 사업계획서를 작성하여\n"
    "심사 통과율을 극대화한다. 재무계획(3개년 손익·현금흐름)을 수치 기반으로 작성하고\n"
    "절세 전략을 내포하여 법인·주주(오너) 관점의 실익을 동시에 확보한다.\n"
    "산출물 수준: 전문위원이 서명해도 무방한 완성도의 사업계획서"
)


class BusinessPlanAgent(BaseAgent):
    name  = "BusinessPlanAgent"
    role  = "사업계획서 작성·IR 전략 전문가"
    system_prompt = _SYS

    PLAN_TYPES = {
        "policy":      "정책자금형 (중진공·기보·신보)",
        "investment":  "투자유치형 (VC·엔젤·IR)",
        "bank":        "은행대출형 (IBK·시중은행)",
        "cert":        "기업인증형 (이노비즈·벤처·메인비즈)",
    }

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "draft_financial_plan",
                "description": "3개년 재무계획(손익·현금흐름)을 보수·기본·낙관 시나리오별로 작성합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "base_revenue":    {"type": "number", "description": "현재 연매출 (원)"},
                        "growth_rate_y1":  {"type": "number", "description": "1년차 목표 성장률 (%)"},
                        "growth_rate_y2":  {"type": "number", "description": "2년차 목표 성장률 (%)"},
                        "growth_rate_y3":  {"type": "number", "description": "3년차 목표 성장률 (%)"},
                        "gross_margin":    {"type": "number", "description": "매출총이익률 (%)"},
                        "opex_ratio":      {"type": "number", "description": "운영비용 비율 (매출 대비 %)"},
                        "loan_amount":     {"type": "number", "description": "신청 자금 규모 (원)"},
                        "interest_rate":   {"type": "number", "description": "예상 이자율 (%)"},
                        "repayment_years": {"type": "integer", "description": "상환 기간 (년)"},
                    },
                    "required": ["base_revenue", "growth_rate_y1", "growth_rate_y2",
                                 "growth_rate_y3", "gross_margin", "opex_ratio"],
                },
            },
            {
                "name": "analyze_market_size",
                "description": "TAM·SAM·SOM 시장규모를 산출하고 목표 시장 점유율을 제시합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "industry":             {"type": "string", "description": "업종"},
                        "domestic_market":      {"type": "number", "description": "국내 시장 규모 (원)"},
                        "target_segment":       {"type": "string", "description": "목표 고객 세그먼트"},
                        "current_market_share": {"type": "number", "description": "현재 점유율 (%)"},
                        "target_market_share":  {"type": "number", "description": "3년 후 목표 점유율 (%)"},
                    },
                    "required": ["industry", "target_segment"],
                },
            },
            {
                "name": "check_certification_eligibility",
                "description": "기업인증(이노비즈·벤처·메인비즈) 신청 적격 여부를 판단합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "rd_expense_ratio":   {"type": "number",  "description": "매출 대비 R&D 비용 비율 (%)"},
                        "has_patent":         {"type": "boolean", "description": "특허 보유 여부"},
                        "employees":          {"type": "integer", "description": "상시 근로자 수"},
                        "years_in_operation": {"type": "integer", "description": "업력 (년)"},
                        "debt_ratio":         {"type": "number",  "description": "부채비율 (%)"},
                        "target_cert":        {"type": "string",  "description": "목표 인증 (innobiz/venture/mainbiz)"},
                    },
                    "required": ["rd_expense_ratio", "has_patent", "employees",
                                 "years_in_operation", "target_cert"],
                },
            },
        ]

    # ── 툴 핸들러 ──────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "draft_financial_plan":
            return self._draft_financial_plan(**tool_input)
        if tool_name == "analyze_market_size":
            return self._analyze_market_size(**tool_input)
        if tool_name == "check_certification_eligibility":
            return self._check_cert(**tool_input)
        return {"error": f"알 수 없는 툴: {tool_name}"}

    def _draft_financial_plan(
        self, base_revenue: float,
        growth_rate_y1: float, growth_rate_y2: float, growth_rate_y3: float,
        gross_margin: float, opex_ratio: float,
        loan_amount: float = 0, interest_rate: float = 3.5, repayment_years: int = 5,
    ) -> dict:
        """3개년 재무계획 — 보수·기본·낙관 시나리오 (2026년 귀속 법인세율 적용)."""
        scenarios = {
            "보수": (growth_rate_y1 * 0.7, growth_rate_y2 * 0.7, growth_rate_y3 * 0.7),
            "기본": (growth_rate_y1,        growth_rate_y2,        growth_rate_y3),
            "낙관": (growth_rate_y1 * 1.3,  growth_rate_y2 * 1.3,  growth_rate_y3 * 1.3),
        }
        gm  = gross_margin / 100
        op  = opex_ratio / 100
        annual_interest  = loan_amount * (interest_rate / 100)
        annual_repayment = loan_amount / repayment_years if repayment_years else 0

        def corp_tax(ebit: float) -> float:
            """법인세법 §55 — 2026년 귀속 세율"""
            if ebit <= 0:
                return 0.0
            elif ebit <= 200_000_000:
                return ebit * 0.10
            elif ebit <= 20_000_000_000:
                return 20_000_000 + (ebit - 200_000_000) * 0.20
            elif ebit <= 300_000_000_000:
                return 3_980_000_000 + (ebit - 20_000_000_000) * 0.22
            else:
                return 69_580_000_000 + (ebit - 300_000_000_000) * 0.25

        result = {}
        for scen_name, (g1, g2, g3) in scenarios.items():
            rows = []
            for yr, gr in enumerate([g1, g2, g3], start=1):
                rev = base_revenue * ((1 + gr / 100) ** yr)
                gp  = rev * gm
                op_profit = gp - rev * op
                ebit = op_profit - annual_interest
                tax  = corp_tax(ebit)
                net  = ebit - tax
                rows.append({
                    "연도": f"Y{yr}",
                    "매출(원)":      round(rev),
                    "매출총이익(원)": round(gp),
                    "영업이익(원)":   round(op_profit),
                    "세전이익(원)":   round(ebit),
                    "법인세(원)":    round(tax),
                    "순이익(원)":    round(net),
                    "순이익률(%)":   round(net / rev * 100, 1) if rev else 0,
                })
            result[f"{scen_name} 시나리오"] = rows

        return {
            "3개년_재무계획":    result,
            "신청자금(원)":      round(loan_amount),
            "연간_이자비용(원)":  round(annual_interest),
            "연간_원금상환(원)":  round(annual_repayment),
            "법인세_기준":       "법인세법 §55 (2026년 귀속: 10%/20%/22%/25%)",
            "비고":             "보수=기본×70%, 낙관=기본×130%",
        }

    def _analyze_market_size(
        self, industry: str, target_segment: str,
        domestic_market: float = 0,
        current_market_share: float = 0,
        target_market_share: float = 0,
    ) -> dict:
        """TAM·SAM·SOM 시장 규모 분석."""
        TAM = domestic_market
        SAM = TAM * 0.30 if TAM else 0          # 접근 가능 시장 (30% 가정)
        SOM_cur = TAM * (current_market_share / 100) if TAM else 0
        SOM_tgt = TAM * (target_market_share  / 100) if TAM else 0
        return {
            "업종":                   industry,
            "목표_세그먼트":           target_segment,
            "TAM_전체시장(원)":        round(TAM),
            "SAM_접근가능시장(원)":     round(SAM),
            "SOM_현재점유액(원)":       round(SOM_cur),
            "SOM_목표점유액(원)":       round(SOM_tgt),
            "현재_점유율(%)":          current_market_share,
            "목표_점유율(%)":          target_market_share,
            "주의":                   "국내시장 규모 미입력 시 SAM·SOM 계산 불가 — 통계청·산업연구원 자료 확인 필요",
        }

    def _check_cert(
        self, rd_expense_ratio: float, has_patent: bool,
        employees: int, years_in_operation: int,
        debt_ratio: float = 200.0, target_cert: str = "innobiz",
    ) -> dict:
        """기업인증 신청 적격성 판단."""
        results = {
            "이노비즈": {
                "적격": rd_expense_ratio >= 3.0 and years_in_operation >= 3,
                "R&D_비율_충족": rd_expense_ratio >= 3.0,
                "업력_충족":     years_in_operation >= 3,
                "주요혜택":      "정책자금 우대금리, 공공조달 가점, 세액공제 우선 적용",
            },
            "벤처기업": {
                "적격": (rd_expense_ratio >= 5.0 or has_patent) and employees >= 1,
                "R&D_또는_특허": rd_expense_ratio >= 5.0 or has_patent,
                "주요혜택":      "법인세 50% 감면(5년), 취득세 75% 감면, 고용보험료 지원",
            },
            "메인비즈": {
                "적격": years_in_operation >= 3 and employees >= 5,
                "업력_충족":     years_in_operation >= 3,
                "인원_충족":     employees >= 5,
                "주요혜택":      "정책자금 우대, 공공조달 가점, 경영혁신 컨설팅 지원",
            },
        }
        cert_map = {"innobiz": "이노비즈", "venture": "벤처기업", "mainbiz": "메인비즈"}
        primary  = results.get(cert_map.get(target_cert, "이노비즈"), {})
        return {
            "인증별_적격성":    results,
            "우선_추천_인증":   cert_map.get(target_cert, target_cert),
            "신청_가능_여부":   primary.get("적격", False),
            "근거_법령":       "중소기업 기술혁신 촉진법 / 벤처기업육성에 관한 특별조치법",
        }

    # ── 공개 인터페이스 ────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        """COMPANY_DATA를 받아 최적 사업계획서 유형 및 초안을 반환합니다."""
        n   = company_data.get("company_name", "대상법인")
        rev = company_data.get("revenue", 0)
        ni  = company_data.get("net_income", 0)
        emp = company_data.get("employees", 10)
        yrs = company_data.get("years_in_operation", 5)
        pp  = company_data.get("provisional_payment", 0)
        te  = max(company_data.get("total_equity", 1), 1)
        td  = company_data.get("total_debt", 0)
        dr  = td / te * 100
        ind = company_data.get("industry", "제조업")
        rd  = company_data.get("rd_expense", 0)
        rd_r = rd / rev * 100 if rev else 0
        bv  = company_data.get("business_value", rev * 3)

        # 사업계획서 유형 자동 판단
        if bv > 10_000_000_000:
            plan_type = "investment"
        elif dr > 200:
            plan_type = "bank"
        elif rd_r >= 3.0:
            plan_type = "cert"
        else:
            plan_type = "policy"

        query = (
            f"[분석 대상] {n} | 업종: {ind} | 업력: {yrs}년 | 직원: {emp}명\n"
            f"[재무 현황] 매출: {rev:,.0f}원 | 순이익: {ni:,.0f}원 | 부채비율: {dr:.0f}%\n"
            f"[기타 현황] R&D비용: {rd:,.0f}원({rd_r:.1f}%) | 가지급금: {pp:,.0f}원\n"
            f"[사업계획서 유형] {self.PLAN_TYPES.get(plan_type)}\n\n"
            f"위 기업에 대해 {self.PLAN_TYPES.get(plan_type)} 사업계획서를 작성하십시오.\n"
            "구성: 회사 개요 / 사업 현황 / 시장 분석 / 사업화 전략 / "
            "3개년 재무계획(보수·기본·낙관) / 자금 사용 계획\n"
            "법인세 절세 항목(R&D 세액공제·통합투자세액공제 등) 반드시 포함"
        )
        return self.run(query, reset=True)

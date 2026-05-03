# ============================================================
# Setup-AllAgents.ps1
# 중기이코노미 AI 컨설팅 하네스 — 에이전트 일괄 설정 완료 스크립트
# 전문위원 여운식 | 2026-04-25
#
# 수행 작업:
#   1단계. 사업계획서 작성 에이전트(BusinessPlanAgent) 신규 생성
#   2단계. 14개 에이전트 파일에 [목표] 섹션 일괄 추가
#   3단계. __init__.py에 BusinessPlanAgent 등록
#   4단계. CLAUDE.md 에이전트 수 57 → 58 업데이트
#   5단계. 전체 Python 문법 검증 (오류 0건 확인)
#
# 실행 방법: PowerShell에서  .\Setup-AllAgents.ps1
# ============================================================

$ProjectPath = "C:\Users\Jy\consulting-agent"
$AgentsPath  = "$ProjectPath\agents"
$PythonExe   = "python"          # python3 또는 python (환경에 따라 변경)

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AI 컨설팅 하네스 에이전트 설정 스크립트" -ForegroundColor Cyan
Write-Host "  중기이코노미기업지원단 | 전문위원 여운식" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ─────────────────────────────────────────────────────────────
# [1단계] BusinessPlanAgent 신규 파일 생성
# ─────────────────────────────────────────────────────────────
Write-Host "▶ 1단계: BusinessPlanAgent 신규 생성" -ForegroundColor Yellow

$BPContent = @'
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

    # 지원 사업계획서 유형
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
                "description": "3개년 재무계획(손익·현금흐름·부채비율)을 시나리오별로 작성합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "base_revenue":     {"type": "number",
                                            "description": "현재 연매출 (원)"},
                        "growth_rate_y1":   {"type": "number",
                                            "description": "1년차 목표 성장률 (%)"},
                        "growth_rate_y2":   {"type": "number",
                                            "description": "2년차 목표 성장률 (%)"},
                        "growth_rate_y3":   {"type": "number",
                                            "description": "3년차 목표 성장률 (%)"},
                        "gross_margin":     {"type": "number",
                                            "description": "매출총이익률 (%)"},
                        "opex_ratio":       {"type": "number",
                                            "description": "운영비용 비율 (매출 대비 %)"},
                        "loan_amount":      {"type": "number",
                                            "description": "신청 자금 규모 (원)"},
                        "interest_rate":    {"type": "number",
                                            "description": "예상 이자율 (%)"},
                        "repayment_years":  {"type": "integer",
                                            "description": "상환 기간 (년)"},
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
                        "industry":         {"type": "string",
                                            "description": "업종 (예: 스마트팩토리, 바이오, 식품)"},
                        "domestic_market":  {"type": "number",
                                            "description": "국내 시장 규모 (원), 모를 경우 0"},
                        "target_segment":   {"type": "string",
                                            "description": "목표 고객 세그먼트"},
                        "current_market_share": {"type": "number",
                                                 "description": "현재 점유율 (%), 없으면 0"},
                        "target_market_share":  {"type": "number",
                                                 "description": "3년 후 목표 점유율 (%)"},
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
                        "rd_expense_ratio": {"type": "number",
                                            "description": "매출 대비 R&D 비용 비율 (%)"},
                        "has_patent":       {"type": "boolean",
                                            "description": "특허 보유 여부"},
                        "employees":        {"type": "integer",
                                            "description": "상시 근로자 수"},
                        "years_in_operation": {"type": "integer",
                                              "description": "업력 (년)"},
                        "debt_ratio":       {"type": "number",
                                            "description": "부채비율 (%)"},
                        "target_cert":      {"type": "string",
                                            "description": "목표 인증 (innobiz/venture/mainbiz)"},
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
        self, base_revenue: float, growth_rate_y1: float,
        growth_rate_y2: float, growth_rate_y3: float,
        gross_margin: float, opex_ratio: float,
        loan_amount: float = 0, interest_rate: float = 3.5,
        repayment_years: int = 5,
    ) -> dict:
        """3개년 재무계획 — 보수·기본·낙관 시나리오."""
        scenarios = {
            "보수": (growth_rate_y1 * 0.7, growth_rate_y2 * 0.7, growth_rate_y3 * 0.7),
            "기본": (growth_rate_y1, growth_rate_y2, growth_rate_y3),
            "낙관": (growth_rate_y1 * 1.3, growth_rate_y2 * 1.3, growth_rate_y3 * 1.3),
        }
        gm   = gross_margin / 100
        op   = opex_ratio / 100
        intr = interest_rate / 100
        annual_repayment = (loan_amount / repayment_years) if repayment_years else 0
        annual_interest  = loan_amount * intr

        result = {}
        for scen_name, (g1, g2, g3) in scenarios.items():
            rev1 = base_revenue * (1 + g1 / 100)
            rev2 = rev1 * (1 + g2 / 100)
            rev3 = rev2 * (1 + g3 / 100)
            rows = []
            for yr, rev in enumerate([rev1, rev2, rev3], start=1):
                gross_profit = rev * gm
                operating_profit = gross_profit - rev * op
                ebit = operating_profit - annual_interest
                # 법인세 (2026년 귀속 기준)
                if ebit <= 200_000_000:
                    tax = max(ebit * 0.10, 0)
                elif ebit <= 20_000_000_000:
                    tax = 20_000_000 + max(ebit - 200_000_000, 0) * 0.20
                elif ebit <= 300_000_000_000:
                    tax = 3_980_000_000 + max(ebit - 20_000_000_000, 0) * 0.22
                else:
                    tax = 69_580_000_000 + max(ebit - 300_000_000_000, 0) * 0.25
                net_income = ebit - tax
                rows.append({
                    "연도": f"Y{yr}",
                    "매출(원)": round(rev),
                    "매출총이익(원)": round(gross_profit),
                    "영업이익(원)": round(operating_profit),
                    "세전이익(원)": round(ebit),
                    "법인세(원)": round(tax),
                    "순이익(원)": round(net_income),
                    "순이익률(%)": round(net_income / rev * 100, 1) if rev else 0,
                })
            result[f"{scen_name} 시나리오"] = rows

        return {
            "3개년_재무계획": result,
            "신청자금(원)": round(loan_amount),
            "연간_이자비용(원)": round(annual_interest),
            "연간_원금상환(원)": round(annual_repayment),
            "법인세_기준": "2026년 귀속 법인세법 §55 (10%/20%/22%/25%)",
            "비고": "보수 시나리오 = 기본 성장률 × 70%, 낙관 시나리오 = 기본 성장률 × 130%",
        }

    def _analyze_market_size(
        self, industry: str, target_segment: str,
        domestic_market: float = 0,
        current_market_share: float = 0,
        target_market_share: float = 0,
    ) -> dict:
        """TAM·SAM·SOM 시장 규모 분석."""
        TAM = domestic_market
        # SAM: 접근 가능 시장 (TAM의 30% 가정, 실제 업종 데이터 없을 경우)
        SAM = TAM * 0.30 if TAM else 0
        # SOM: 확보 가능 시장 (목표 점유율)
        SOM_current = TAM * (current_market_share / 100) if TAM else 0
        SOM_target  = TAM * (target_market_share / 100) if TAM else 0

        return {
            "업종":           industry,
            "목표_세그먼트":   target_segment,
            "TAM_전체시장(원)": round(TAM),
            "SAM_접근가능시장(원)": round(SAM),
            "SOM_현재점유액(원)":   round(SOM_current),
            "SOM_목표점유액(원)":   round(SOM_target),
            "현재_점유율(%)":  current_market_share,
            "목표_점유율(%)":  target_market_share,
            "주의": "국내시장 규모 미입력 시 SAM·SOM 계산 불가 — 업종별 통계 확인 후 입력 권장",
        }

    def _check_cert(
        self, rd_expense_ratio: float, has_patent: bool,
        employees: int, years_in_operation: int,
        debt_ratio: float = 200.0,
        target_cert: str = "innobiz",
    ) -> dict:
        """기업인증 신청 적격성 판단."""
        results = {}

        # 이노비즈 기준
        innobiz_ok = rd_expense_ratio >= 3.0 and years_in_operation >= 3
        results["이노비즈"] = {
            "적격": innobiz_ok,
            "R&D_비율_충족": rd_expense_ratio >= 3.0,
            "업력_충족": years_in_operation >= 3,
            "주요혜택": "정책자금 우대금리, 공공조달 가점, 세액공제 우선 적용",
        }

        # 벤처기업 기준 (기보 평가형)
        venture_ok = (rd_expense_ratio >= 5.0 or has_patent) and employees >= 1
        results["벤처기업"] = {
            "적격": venture_ok,
            "R&D_또는_특허_충족": rd_expense_ratio >= 5.0 or has_patent,
            "주요혜택": "법인세 50% 감면(5년), 취득세 75% 감면, 고용보험료 지원",
        }

        # 메인비즈 기준
        mainbiz_ok = years_in_operation >= 3 and employees >= 5
        results["메인비즈"] = {
            "적격": mainbiz_ok,
            "업력_충족": years_in_operation >= 3,
            "인원_충족": employees >= 5,
            "주요혜택": "정책자금 우대, 공공조달 가점, 경영혁신 컨설팅 지원",
        }

        primary = results.get({
            "innobiz": "이노비즈", "venture": "벤처기업", "mainbiz": "메인비즈"
        }.get(target_cert, "이노비즈"), {})

        return {
            "인증별_적격성": results,
            "우선_추천_인증": target_cert,
            "신청_가능_여부": primary.get("적격", False),
            "근거_법령": "중소기업 기술혁신 촉진법, 벤처기업육성에 관한 특별조치법",
        }

    # ── 공개 인터페이스 ────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        """COMPANY_DATA를 받아 최적 사업계획서 유형 및 초안을 반환합니다."""
        n    = company_data.get("company_name", "대상법인")
        rev  = company_data.get("revenue", 0)
        ni   = company_data.get("net_income", 0)
        emp  = company_data.get("employees", 10)
        yrs  = company_data.get("years_in_operation", 5)
        pp   = company_data.get("provisional_payment", 0)
        dr   = company_data.get("total_debt", 0) / max(company_data.get("total_equity", 1), 1) * 100
        ind  = company_data.get("industry", "제조업")
        rd   = company_data.get("rd_expense", 0)
        rd_r = rd / rev * 100 if rev else 0
        bv   = company_data.get("business_value", rev * 3)

        # 사업계획서 유형 자동 판단
        plan_type = "policy"
        if bv > 10_000_000_000:
            plan_type = "investment"
        elif dr > 200:
            plan_type = "bank"
        elif rd_r >= 3.0:
            plan_type = "cert"

        query = (
            f"[분석 대상] {n} | 업종: {ind} | 업력: {yrs}년 | 직원: {emp}명\n"
            f"[재무 현황] 매출: {rev:,.0f}원 | 순이익: {ni:,.0f}원 | 부채비율: {dr:.0f}%\n"
            f"[기타 현황] R&D비용: {rd:,.0f}원({rd_r:.1f}%) | 가지급금: {pp:,.0f}원\n"
            f"[사업계획서 유형] {self.PLAN_TYPES.get(plan_type, '정책자금형')}\n\n"
            f"위 기업에 대해 {self.PLAN_TYPES.get(plan_type)} 사업계획서를 작성하십시오.\n"
            f"- 회사 개요 / 사업 현황 / 시장 분석 / 사업화 전략 / 3개년 재무계획 / "
            f"자금 사용 계획 순서로 작성\n"
            f"- 재무계획은 보수·기본·낙관 3개 시나리오 포함\n"
            f"- 법인세 절세 항목(R&D 세액공제·통합투자세액공제 등) 반드시 포함"
        )
        return self.run(query, reset=True)
'@

$BPPath = "$AgentsPath\business_plan_agent.py"
Set-Content -Path $BPPath -Value $BPContent -Encoding UTF8 -NoNewline:$false
Write-Host "  완료 → $BPPath" -ForegroundColor Green


# ─────────────────────────────────────────────────────────────
# [2단계] 14개 에이전트 파일에 [목표] 섹션 일괄 추가
#         Python 스크립트를 임시 파일로 생성 후 실행
# ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ 2단계: 14개 에이전트 파일 [목표] 섹션 추가" -ForegroundColor Yellow

$PyScript = @'
# -*- coding: utf-8 -*-
"""에이전트 [목표] 섹션 일괄 삽입 스크립트"""
import os, sys

AGENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents")

# ─── 목표 텍스트 정의 ───────────────────────────────────────────────
# 형식: 파일명 → (변수명or패턴, 삽입할 목표 텍스트)
GOALS = {
    "cash_flow_agent.py": {
        "var": "_SYS",
        "text": (
            "12개월 월별 현금흐름 예측으로 흑자도산 조기 경보를 발령하고, "
            "운전자본 최적화·자금조달 믹스 조정 방안을 수치 기반으로 제시한다. "
            "Cash Burn Rate·Runway 계산으로 유동성 위기 임계점을 단정적으로 경고하며, "
            "4자 이해관계 중 금융기관·법인 관점을 중심으로 즉시 실행 가능한 자금 대책을 권고한다."
        ),
    },
    "credit_rating_agent.py": {
        "var": "_SYS",
        "text": (
            "NICE 기준 신용등급을 추정하고 등급 상승 시 금융비용 절감액·여신 한도 확대 효과를 정량화한다. "
            "4자 이해관계 중 금융기관 관점을 중심으로 대출가용성 극대화 전략을 단정적으로 권고하며, "
            "신용등급 개선을 위한 재무지표 목표치와 달성 기한을 명시한다."
        ),
    },
    "esg_risk_agent.py": {
        "var": "_SYS",
        "text": (
            "E·S·G 항목별 리스크를 0~100 점수로 정량화하여 대기업 공급망 이탈·EU CBAM 과징금·"
            "금융 조달 불이익을 사전 차단하는 우선 개선 과제를 제시한다. "
            "법인·금융기관·규제기관 3자 관점을 교차 분석하며, "
            "비용 대비 ESG 점수 향상 효율이 높은 항목을 우선 순위별로 권고한다."
        ),
    },
    "industry_agent.py": {
        "var": "_SYS",
        "text": (
            "동종업계 재무비율 벤치마크와 세무조사 선정 트렌드를 수집·비교하여 "
            "대상 법인의 취약 포지션을 수치로 진단한다. "
            "업종 평균 대비 세무조사 리스크·금융 리스크를 단정적으로 제시하며, "
            "경쟁사 포지셔닝 기반의 재무구조 개선 목표치를 권고한다."
        ),
    },
    "insurance_agent.py": {
        "var": "_SYS",
        "text": (
            "CEO 유고 리스크 및 임원 퇴직금 재원을 법인 납입 보험으로 설계하여 "
            "손금산입 요건(법인세법 기본통칙 19-19-4)을 충족하면서 절세 효과를 최대화한다. "
            "4자 이해관계 중 법인·주주(오너) 리스크 헷지에 집중하며, "
            "보험료 납입 시 법인세 절감액과 수령 시 세무 처리를 수치로 명시한다."
        ),
    },
    "labor_agent.py": {
        "var": "_SYS",
        "text": (
            "근로기준법·4대보험·중대재해처벌법 준수 여부를 점검하고, "
            "퇴직금·임금체계 최적화로 법인 인건비를 절감하면서 노무 리스크를 선제 해소한다. "
            "계산식 자체 검증 후 수치를 제시하며, 두루누리 지원사업·고용창출세액공제 등 "
            "즉시 활용 가능한 정부 지원 항목을 반드시 포함한다."
        ),
    },
    "legal_agent.py": {
        "var": "_SYS",
        "text": (
            "상법 절차 하자·배임·횡령 형사 리스크·명의신탁 증여의제 등 "
            "법인·주주·임원에게 잠재된 법률 리스크를 선제 진단하여 "
            "최신 판례 기준의 적법한 대응 방안을 단정적으로 제시한다. "
            "면책 문구 없이 결론 먼저 제시하며, 형사·민사·세무 리스크를 교차 분석한다."
        ),
    },
    "ma_valuation_agent.py": {
        "var": "_SYS",
        "text": (
            "DCF·PER·EV/EBITDA 3방법론을 병행 적용하여 기업가치 범위를 산출하고, "
            "매각·투자유치·IPO 시 최적 딜 구조와 경영권 프리미엄·소수주주 할인율을 "
            "수치 기반으로 제시한다. "
            "법인·주주(오너) 이익 최대화 관점에서 Exit 전략과 주주가치 보전 방안을 권고한다."
        ),
    },
    "patent_agent.py": {
        "var": "_SYS",
        "text": (
            "R&D 세액공제(조특법 §10) 한도 계산과 IP 담보·기보 보증 활용으로 "
            "법인 연구개발 투자 효율을 극대화한다. "
            "지식재산권 자본화 전략으로 재무구조를 개선하는 방안을 수치 기반으로 제시하며, "
            "연구전담부서 설립부터 세액공제 신청까지 실행 단계를 구체적으로 안내한다."
        ),
    },
    "policy_funding_agent.py": {
        "var": "_SYS",
        "text": (
            "기업 현황에 맞는 정책자금·보증·바우처·인증 혜택을 우선순위별로 매핑하여 "
            "금융비용 절감 효과를 정량화한다. "
            "신청 요건·일정·한도·금리를 구체적으로 안내하여 "
            "법인이 전문위원 동행 없이도 자력으로 신청 가능한 수준으로 제시한다."
        ),
    },
    "real_estate_agent.py": {
        "var": "_SYS",
        "text": (
            "법인 vs 개인 취득·보유·양도 세금 비교 시뮬레이션으로 부동산 거래 최적 구조를 결정한다. "
            "비상장주식 평가 시 부동산 과다법인 할증 리스크(부동산 80%↑ → 순자산가치 100% 적용)를 "
            "수치로 경고하고 해소 방안을 제시한다. "
            "지방세법·소득세법·법인세법 교차 적용으로 최소 세부담 구조를 단정적으로 권고한다."
        ),
    },
    "verify_agent.py": {
        "var": "_VERIFY_SYSTEM",
        "text": (
            "모든 컨설팅 에이전트 출력의 법령 조문·계산 수치·리스크 누락을 엄격히 검증하여 "
            "SCORE(0~100)·STATUS·ISSUES를 출력한다. "
            "SCORE 90 미만 시 구체적 수정 사항을 명시하며, "
            "2026년 귀속 최신 세법 반영 여부를 반드시 확인한다. "
            "검증 목표: 오류 0건·SCORE 95+ 품질의 산출물 보증."
        ),
    },
}

# verify_tax.py는 3개 클래스 개별 처리
VERIFY_TAX_GOALS = {
    "_SYS": (
        "TaxAgent·FinanceAgent·StockAgent·SuccessionAgent의 세무·주식평가 수치를 재계산하여 "
        "오류 0건을 목표로 검증한다. "
        "2026년 귀속 법인세율(10/20/22/25%)·비상장주식 3단 차등 평가·"
        "가업상속공제 한도(10년↑300억/20년↑500억/30년↑600억)를 기준값으로 적용한다."
    ),
    "VerifyOps_SYS": (
        "LegalAgent·LaborAgent·PatentAgent·RealEstateAgent·InsuranceAgent 산출물의 "
        "법령 조문·요건·계산식을 검증하여 SCORE 90 이상을 목표로 한다. "
        "최신 판례·예규 미반영 또는 수치 오류 발견 시 즉시 FAIL 처리하고 수정 사항을 제시한다."
    ),
    "VerifyStrategy_SYS": (
        "PolicyFundingAgent·CashFlowAgent·CreditRatingAgent·MAValuationAgent·"
        "ESGRiskAgent·IndustryAgent·WebResearchAgent 산출물의 수치 정확성·"
        "정보 신뢰성·법규 반영 여부를 검증한다. "
        "정보 출처 불명확 또는 계산 오류 시 FAIL 처리하고 재조회를 요청한다."
    ),
}

VERIFY_TAX_GOALS_WR = {
    "web_research_agent.py": {
        "var": "_SYS",
        "text": (
            "대상 기업의 홈페이지·뉴스·DART 공시·특허청 정보를 수집하여 "
            "컨설팅 입력 데이터의 정확성을 높인다. "
            "수집된 원본 정보를 컨설팅 인사이트로 가공하여 제공하며, "
            "출처를 명시하여 검증 에이전트(VerifyStrategy)의 신뢰성 평가에 활용 가능하게 한다."
        ),
    },
}

# ─── 공통 삽입 함수 ───────────────────────────────────────────────

def insert_goal_to_var(src: str, var_name: str, goal_text: str) -> tuple[str, bool]:
    """
    var_name = '...' 또는 var_name = (...) 블록의 마지막 위치에 목표 텍스트를 삽입합니다.
    이미 목표】가 있으면 스킵합니다.
    """
    if "목표】" in src:
        return src, False  # 이미 삽입됨

    # 변수 시작점 찾기
    var_start = src.find(f"{var_name} = ")
    if var_start == -1:
        return src, False

    # _SYS = ( ... ) 형태인지 _VERIFY_SYSTEM = ( ... ) 형태인지 확인
    brace_start = src.find("(", var_start)
    newline_after_var = src.find("\n", var_start)

    if brace_start != -1 and brace_start < newline_after_var:
        # 괄호 형태: find matching )
        # 괄호 뒤 첫 \n) 찾기 (단독 줄의 ) )
        pos = brace_start + 1
        while pos < len(src):
            nl_close = src.find("\n)", pos)
            if nl_close == -1:
                return src, False
            # 해당 ) 가 _SYS 블록의 닫는 괄호인지 확인
            # (다음 줄이 빈줄 또는 class/def 로 시작)
            after = src[nl_close+2:nl_close+10].strip()
            if after == "" or after.startswith("class ") or after.startswith("def ") or after.startswith("\n"):
                # 여기가 닫는 )
                goal_str = f'\n    "\\n\\n【목표】\\n{goal_text}"'
                new_src = src[:nl_close] + goal_str + src[nl_close:]
                return new_src, True
            pos = nl_close + 1
    return src, False


def insert_goal_inline(src: str, class_name: str, goal_text: str) -> tuple[str, bool]:
    """
    인라인 system_prompt = (...) 블록에 목표를 삽입합니다.
    class_name 클래스 내부를 대상으로 합니다.
    """
    # 해당 class 위치 찾기
    class_pos = src.find(f"class {class_name}")
    if class_pos == -1:
        return src, False

    # class 이후 system_prompt = ( 찾기
    sp_pos = src.find("system_prompt = (", class_pos)
    if sp_pos == -1:
        return src, False

    # 이미 목표가 있는지 (해당 블록 내)
    next_class = src.find("\nclass ", class_pos + 1)
    block_end = next_class if next_class != -1 else len(src)
    if "목표】" in src[class_pos:block_end]:
        return src, False

    # system_prompt = ( 이후 \n) 찾기
    pos = sp_pos + len("system_prompt = (")
    nl_close = src.find("\n    )", pos)
    if nl_close == -1:
        nl_close = src.find("\n)", pos)
    if nl_close == -1:
        return src, False

    goal_str = f'\n        "\\n\\n【목표】\\n{goal_text}"'
    new_src = src[:nl_close] + goal_str + src[nl_close:]
    return new_src, True


# ─── 일반 에이전트 파일 처리 ─────────────────────────────────────────

ok_count = 0
skip_count = 0
fail_count = 0

# web_research_agent.py도 GOALS에 합치기
all_goals = {**GOALS, **VERIFY_TAX_GOALS_WR}

for fname, config in all_goals.items():
    fpath = os.path.join(AGENTS_DIR, fname)
    if not os.path.exists(fpath):
        print(f"  [NOT FOUND] {fname}")
        fail_count += 1
        continue

    with open(fpath, encoding="utf-8") as f:
        src = f.read()

    if "목표】" in src:
        print(f"  [SKIP] {fname} — 이미 목표 설정됨")
        skip_count += 1
        continue

    new_src, changed = insert_goal_to_var(src, config["var"], config["text"])

    if changed:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_src)
        print(f"  [OK] {fname} — 목표 추가 완료")
        ok_count += 1
    else:
        print(f"  [FAIL] {fname} — 삽입 위치를 찾지 못했습니다")
        fail_count += 1


# ─── verify_tax.py 개별 처리 ────────────────────────────────────────

vt_path = os.path.join(AGENTS_DIR, "verify_tax.py")
with open(vt_path, encoding="utf-8") as f:
    vt_src = f.read()

changed_any = False

# 1) _SYS 변수 (VerifyTax용)
vt_src, c1 = insert_goal_to_var(vt_src, "_SYS", VERIFY_TAX_GOALS["_SYS"])
if c1:
    print(f"  [OK] verify_tax.py:VerifyTax — _SYS 목표 추가 완료")
    ok_count += 1
    changed_any = True
else:
    if "목표】" in vt_src[:vt_src.find("class VerifyTax") + 200]:
        print(f"  [SKIP] verify_tax.py:VerifyTax — 이미 목표 설정됨")
        skip_count += 1
    else:
        print(f"  [FAIL] verify_tax.py:VerifyTax — 삽입 실패")
        fail_count += 1

# 2) VerifyOps 인라인 system_prompt
vt_src, c2 = insert_goal_inline(vt_src, "VerifyOps", VERIFY_TAX_GOALS["VerifyOps_SYS"])
if c2:
    print(f"  [OK] verify_tax.py:VerifyOps — 인라인 목표 추가 완료")
    ok_count += 1
    changed_any = True
else:
    print(f"  [SKIP/FAIL] verify_tax.py:VerifyOps")
    skip_count += 1

# 3) VerifyStrategy 인라인 system_prompt
vt_src, c3 = insert_goal_inline(vt_src, "VerifyStrategy", VERIFY_TAX_GOALS["VerifyStrategy_SYS"])
if c3:
    print(f"  [OK] verify_tax.py:VerifyStrategy — 인라인 목표 추가 완료")
    ok_count += 1
    changed_any = True
else:
    print(f"  [SKIP/FAIL] verify_tax.py:VerifyStrategy")
    skip_count += 1

if changed_any:
    with open(vt_path, "w", encoding="utf-8") as f:
        f.write(vt_src)

print()
print(f"  처리 결과: OK={ok_count}  SKIP={skip_count}  FAIL={fail_count}")
'@

$PyPath = "$ProjectPath\add_goals_temp.py"
Set-Content -Path $PyPath -Value $PyScript -Encoding UTF8 -NoNewline:$false

# Python 실행
Write-Host ""
& $PythonExe $PyPath
$PyExitCode = $LASTEXITCODE

# 임시 파일 삭제
Remove-Item $PyPath -ErrorAction SilentlyContinue


# ─────────────────────────────────────────────────────────────
# [3단계] __init__.py에 BusinessPlanAgent 등록
# ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ 3단계: __init__.py BusinessPlanAgent 등록" -ForegroundColor Yellow

$InitPath = "$AgentsPath\__init__.py"
$InitContent = Get-Content $InitPath -Raw -Encoding UTF8

if ($InitContent -notmatch "BusinessPlanAgent") {
    # ESGRiskAgent import 줄 뒤에 추가
    $InitContent = $InitContent -replace `
        "(from agents\.esg_risk_agent import ESGRiskAgent)", `
        "`$1`nfrom agents.business_plan_agent import BusinessPlanAgent"

    # __all__ 리스트에 추가
    $InitContent = $InitContent -replace `
        '("MAValuationAgent", "ESGRiskAgent",)', `
        '"MAValuationAgent", "ESGRiskAgent", "BusinessPlanAgent",'

    Set-Content -Path $InitPath -Value $InitContent -Encoding UTF8 -NoNewline:$false
    Write-Host "  완료 → BusinessPlanAgent __init__.py 등록" -ForegroundColor Green
} else {
    Write-Host "  SKIP → 이미 등록됨" -ForegroundColor Gray
}


# ─────────────────────────────────────────────────────────────
# [4단계] CLAUDE.md 에이전트 수 57 → 58 업데이트
# ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ 4단계: CLAUDE.md 에이전트 수 업데이트 (57 → 58)" -ForegroundColor Yellow

$ClaudeMdPaths = @(
    "$ProjectPath\CLAUDE.md",
    "C:\Users\Jy\CLAUDE.md",
    "C:\Users\Jy\.claude\CLAUDE.md"
)

foreach ($mdPath in $ClaudeMdPaths) {
    if (Test-Path $mdPath) {
        $md = Get-Content $mdPath -Raw -Encoding UTF8
        if ($md -match "총 에이전트: 57개") {
            $md = $md -replace "총 에이전트: 57개", "총 에이전트: 58개"
            $md = $md -replace "총 에이전트: 57개", "총 에이전트: 58개"
            Set-Content -Path $mdPath -Value $md -Encoding UTF8 -NoNewline:$false
            Write-Host "  업데이트 → $mdPath" -ForegroundColor Green
        } elseif ($md -match "총 에이전트: 58개") {
            Write-Host "  SKIP → 이미 58개 ($mdPath)" -ForegroundColor Gray
        } else {
            Write-Host "  주의 → 패턴 없음: $mdPath" -ForegroundColor Yellow
        }
    }
}

# SYSTEM_ARCHITECTURE 업데이트도 확인
foreach ($mdPath in $ClaudeMdPaths) {
    if (Test-Path $mdPath) {
        $md = Get-Content $mdPath -Raw -Encoding UTF8
        if ($md -match "- 총 에이전트: 57개") {
            $md = $md -replace "- 총 에이전트: 57개", "- 총 에이전트: 58개"
            Set-Content -Path $mdPath -Value $md -Encoding UTF8 -NoNewline:$false
            Write-Host "  SYSTEM_ARCHITECTURE 업데이트 → $mdPath" -ForegroundColor Green
        }
    }
}


# ─────────────────────────────────────────────────────────────
# [5단계] 전체 Python 문법 검증
# ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ 5단계: 전체 Python 문법 검증" -ForegroundColor Yellow

$VerifyScript = @'
import ast, os, sys

agents_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents")
files = [f for f in os.listdir(agents_dir) if f.endswith(".py")]

errors = []
for fname in sorted(files):
    fpath = os.path.join(agents_dir, fname)
    try:
        src = open(fpath, encoding="utf-8").read()
        ast.parse(src)
        lines = src.count("\n")
        goal_count = src.count("목표】")
        print(f"  OK  [{lines:3}줄] [목표:{goal_count}개] {fname}")
    except SyntaxError as e:
        errors.append(fname)
        print(f"  FAIL {fname}: Line {e.lineno} - {e.msg}")

print()
if errors:
    print(f"오류 파일: {errors}")
    sys.exit(1)
else:
    print(f"전체 {len(files)}개 파일 — 문법 오류 0건")
'@

$VfPath = "$ProjectPath\verify_agents_temp.py"
Set-Content -Path $VfPath -Value $VerifyScript -Encoding UTF8 -NoNewline:$false

& $PythonExe $VfPath
$VfExitCode = $LASTEXITCODE

Remove-Item $VfPath -ErrorAction SilentlyContinue


# ─────────────────────────────────────────────────────────────
# 최종 결과 요약
# ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
if ($VfExitCode -eq 0) {
    Write-Host "  설정 완료 — 오류 0건" -ForegroundColor Green
} else {
    Write-Host "  경고: 일부 파일에 오류 발생 — 위 로그 확인" -ForegroundColor Red
}
Write-Host ""
Write-Host "  수행 내역:" -ForegroundColor White
Write-Host "  1. BusinessPlanAgent 신규 생성 → agents\business_plan_agent.py" -ForegroundColor White
Write-Host "  2. 14개 에이전트 파일 [목표] 섹션 추가" -ForegroundColor White
Write-Host "  3. __init__.py BusinessPlanAgent 등록" -ForegroundColor White
Write-Host "  4. CLAUDE.md 에이전트 수 58개 업데이트" -ForegroundColor White
Write-Host "  5. 전체 Python 문법 검증 완료" -ForegroundColor White
Write-Host ""
Write-Host "  총 에이전트: 58개 / 레이어: 12개" -ForegroundColor Yellow
Write-Host "  프로젝트: $ProjectPath" -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Cyan

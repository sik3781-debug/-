"""
ConsultingAgents: 전문 분야별 특화 에이전트
- TaxAgent       : 법인세 절세 전략
- StockAgent     : 비상장주식 평가 및 주식 이동
- SuccessionAgent: 가업승계 (자녀법인 활용 포함)
- FinanceAgent   : 재무구조 개선 및 리스크 헷지
"""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent

# ────────────────────────────────────────────────────────────────────────────
# 공통 시스템 프롬프트 서문
# ────────────────────────────────────────────────────────────────────────────
_COMMON_HEADER = (
    "당신은 중기이코노미기업지원단 소속 중소기업 전문 경영컨설턴트입니다.\n"
    "모든 솔루션은 아래 4자 이해관계를 반드시 교차 분석하여 제시합니다.\n"
    "- 법인: 세무리스크 최소화 / 손금 최대화 / 재무구조 건전성\n"
    "- 주주(오너): 가처분소득 극대화 / 지분가치 보전 / 승계비용 최소화\n"
    "- 과세관청: 최신 세법·판례 기준 적법성 / 세무조사 리스크 제거\n"
    "- 금융기관: 신용등급·담보 영향 / 대출가용성 유지\n\n"
    "【답변 기준】\n"
    "- 최신 개정 상법·세법 및 대법원·고등법원 판례 반영\n"
    "- 법률·세법 오류 및 계산 공식·결과값 자체 검증 후 답변\n"
    "- 단정적·간결한 전문가 언어, 불필요한 면책 문구 생략\n"
    "- 우선 적용 법령: 조세특례제한법 > 법인세법 > 소득세법 > 국세기본법 > 상법 > 상속세및증여세법\n\n"
    "【핵심 세법 기준값 — 2026년 귀속】\n"
    "- 법인세율: 2억↓ 10% / 2억~200억 20% / 200억~3,000억 22% / 3,000억↑ 25%\n"
    "- 가지급금 인정이자율: 4.6% (법인세법 시행규칙 제43조)\n"
    "- 비상장주식: 일반법인 순손익3:순자산2 / 부동산50~80% 순손익2:순자산3 / 부동산80%↑·창업3년↓ 순자산100%\n"
    "- 증여재산공제: 배우자 6억 / 성년 5천만 / 미성년 2천만 / 혼인·출산 각 +1억(합산 최대 1억)\n"
    "- 가업상속공제: 10년↑ 300억 / 20년↑ 500억 / 30년↑ 600억(최대, 상증세법 제18조의2)"
)


# ────────────────────────────────────────────────────────────────────────────
# 1. 법인세 절세 에이전트
# ────────────────────────────────────────────────────────────────────────────
class TaxAgent(BaseAgent):
    name = "TaxAgent"
    role = "법인세 절세 전략 전문가"
    system_prompt = (
        _COMMON_HEADER
        + "\n\n【전문 분야】\n"
        "법인세 절세 전략, 임원 보수 최적화, 퇴직금 절세, 가지급금 해결, "
        "접대비·복리후생비 한도 관리, 연구인력개발비 세액공제 등\n\n"
        "【목표】\n"
        "법인의 2026년 귀속 과세표준 기준 법인세 부담을 합법적으로 최소화하는 "
        "절세 전략 3가지 이상을 수치(절세액·실효세율) 포함하여 제시한다.\n"
        "산출물 기준: 계산식 자체검증 완료 / 근거 조문 명시 / 4자 이해관계 반영 / "
        "즉시 실행 가능한 액션플랜 포함"
    )

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_corporate_tax",
                "description": "과세표준에 따른 법인세 및 지방소득세를 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "taxable_income": {
                            "type": "number",
                            "description": "과세표준 금액 (원)",
                        }
                    },
                    "required": ["taxable_income"],
                },
            }
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_corporate_tax":
            return self._calc_corporate_tax(tool_input["taxable_income"])
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _calc_corporate_tax(income: float) -> dict[str, Any]:
        """2026년 귀속 법인세율 적용 (법인세법 제55조 / 2026년 1월 1일 이후 개시 사업연도)."""
        brackets = [
            (200_000_000, 0.10),
            (20_000_000_000, 0.20),
            (300_000_000_000, 0.22),
            (float("inf"), 0.25),
        ]
        tax = 0.0
        prev = 0.0
        for limit, rate in brackets:
            if income <= 0:
                break
            taxable = min(income, limit) - prev
            tax += taxable * rate
            prev = limit
            if income <= limit:
                break

        local_tax = tax * 0.1
        total = tax + local_tax
        return {
            "과세표준": f"{income:,.0f}원",
            "법인세": f"{tax:,.0f}원",
            "지방소득세(10%)": f"{local_tax:,.0f}원",
            "합계": f"{total:,.0f}원",
            "실효세율": f"{total / income * 100:.2f}%",
        }


# ────────────────────────────────────────────────────────────────────────────
# 2. 비상장주식 평가 에이전트
# ────────────────────────────────────────────────────────────────────────────
class StockAgent(BaseAgent):
    name = "StockAgent"
    role = "비상장주식 평가 및 주식 이동 전문가"
    system_prompt = (
        _COMMON_HEADER
        + "\n\n【전문 분야】\n"
        "비상장주식 보충적 평가(순손익가치·순자산가치), 주식 이동 전략, "
        "차명주식 해소, 명의신탁 해지 리스크 분석, 증여·양도세 최적화\n\n"
        "【목표】\n"
        "상증세법 제54~56조 기준 1주당 평가액을 부동산비율·업력에 따라 정확히 산정하고, "
        "주식 이동(증여·양도·감자)의 세부담·리스크를 4자 관점에서 비교 분석하여 "
        "최적 이전 시점·방법·수량을 수치로 제시한다.\n"
        "산출물 기준: 평가 산식 명시(가중치 포함) / 부동산비율 3단 차등 적용 확인 / "
        "증여세·양도세 비교 시뮬레이션 / 차명주식 해소 리스크 포함"
    )

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_unlisted_stock_value",
                "description": (
                    "상증세법 제54~56조 보충적 평가방법으로 비상장주식 1주당 가액을 산정합니다. "
                    "부동산 비율과 창업연수에 따라 가중치를 3단으로 차등 적용합니다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "net_asset_per_share": {
                            "type": "number",
                            "description": "1주당 순자산가치 (원)",
                        },
                        "net_income_per_share": {
                            "type": "number",
                            "description": "1주당 최근 3년 가중평균 순손익가치 (원)",
                        },
                        "real_estate_ratio": {
                            "type": "number",
                            "description": "자산 중 부동산·부동산권리 비율 (0.0~1.0). 예: 0.55 = 55%",
                        },
                        "startup_years": {
                            "type": "number",
                            "description": "창업 후 경과 연수. 3년 이하이면 순자산 100% 적용",
                        },
                    },
                    "required": [
                        "net_asset_per_share",
                        "net_income_per_share",
                        "real_estate_ratio",
                        "startup_years",
                    ],
                },
            }
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_unlisted_stock_value":
            return self._calc_stock_value(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _calc_stock_value(
        net_asset_per_share: float,
        net_income_per_share: float,
        real_estate_ratio: float,
        startup_years: float,
    ) -> dict[str, Any]:
        """
        상증세법 제54~56조 3단 차등 평가
        ① 창업 3년 이내: 순자산 100%
        ② 부동산 비율 80% 이상: 순자산 100%
        ③ 부동산 비율 50~80% 미만: 순손익 2 : 순자산 3
        ④ 일반법인(부동산 50% 미만): 순손익 3 : 순자산 2
        """
        # 창업 3년 이내 — 순자산만
        if startup_years <= 3:
            label = "창업 3년 이내 법인"
            basis = "상증세법 제56조"
            asset_w, income_w = 1.0, 0.0
            note = "순손익가치 적용 불가 → 순자산가치 100% 강제 적용"

        # 부동산 80% 이상 — 순자산만
        elif real_estate_ratio >= 0.80:
            label = "부동산 비율 80% 이상 법인"
            basis = "상증세법 제55조"
            asset_w, income_w = 1.0, 0.0
            note = f"부동산비율 {real_estate_ratio*100:.1f}% → 순자산가치 100% 적용"

        # 부동산 50~80% 미만 — 순손익 2 : 순자산 3
        elif real_estate_ratio >= 0.50:
            label = "부동산 과다법인 (50%≤비율<80%)"
            basis = "상증세법 제55조"
            asset_w, income_w = 3/5, 2/5
            note = f"부동산비율 {real_estate_ratio*100:.1f}% → 순손익2:순자산3 가중치 적용"

        # 일반법인 — 순손익 3 : 순자산 2
        else:
            label = "일반법인"
            basis = "상증세법 제54조"
            asset_w, income_w = 2/5, 3/5
            note = f"부동산비율 {real_estate_ratio*100:.1f}% → 순손익3:순자산2 가중치 적용"

        value = net_asset_per_share * asset_w + net_income_per_share * income_w
        floor = net_asset_per_share * 0.8  # 하한: 순자산의 80%
        final = max(value, floor)

        return {
            "법인 구분": label,
            "적용 근거": basis,
            "가중치": f"순자산 {asset_w*100:.0f}% + 순손익 {income_w*100:.0f}%",
            "산출 내역": note,
            "가중평균 산출가액": f"{value:,.0f}원",
            "하한(순자산의 80%)": f"{floor:,.0f}원",
            "최종 1주당 평가액": f"{final:,.0f}원",
            "검증": f"하한 적용 {'O (가중평균 < 하한)' if value < floor else 'X (가중평균 ≥ 하한)'}",
        }


# ────────────────────────────────────────────────────────────────────────────
# 3. 가업승계 에이전트
# ────────────────────────────────────────────────────────────────────────────
class SuccessionAgent(BaseAgent):
    name = "SuccessionAgent"
    role = "가업승계 전문가"
    system_prompt = (
        _COMMON_HEADER
        + "\n\n【전문 분야】\n"
        "가업상속공제(상증세법 제18조의2), 창업자금 증여특례(조특법 제30조의5), "
        "자녀법인 활용 승계 전략, 주식 단계적 이전, 사전·사후 관리 요건\n\n"
        "【목표】\n"
        "대표이사의 경영권·지분을 후계자에게 이전할 때 상속·증여세 부담을 "
        "가업상속공제(최대 600억) 및 자녀법인 활용으로 합법적으로 최소화하는 "
        "단계별 실행 로드맵을 수치(절세액·사후관리 의무)와 함께 제시한다.\n"
        "산출물 기준: 업력별 공제한도 명시(10년↑300억/20년↑500억/30년↑600억) / "
        "사후관리 7년 요건 포함 / 자녀법인·증여특례 대안 비교 / 4자 이해관계 교차 분석"
    )

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_inheritance_deduction",
                "description": "가업상속공제 한도 및 절감 효과를 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "business_years": {
                            "type": "integer",
                            "description": "피상속인의 가업 영위 기간 (년)",
                        },
                        "business_value": {
                            "type": "number",
                            "description": "가업 자산 가액 (원)",
                        },
                    },
                    "required": ["business_years", "business_value"],
                },
            }
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_inheritance_deduction":
            return self._calc_deduction(**tool_input)
        return super().handle_tool(tool_name, tool_input)
    @staticmethod
    def _calc_deduction(business_years: int, business_value: float) -> dict[str, Any]:
        """상증세법 제18조의2 가업상속공제 한도 (2026년 기준)."""
        if business_years >= 30:
            limit = 60_000_000_000
            tier = "30년 이상"
        elif business_years >= 20:
            limit = 50_000_000_000
            tier = "20년 이상 ~ 30년 미만"
        elif business_years >= 10:
            limit = 30_000_000_000
            tier = "10년 이상 ~ 20년 미만"
        else:
            limit = 0
            tier = "10년 미만 — 공제 불가"

        deduction = min(business_value, limit)
        tax_saving = deduction * 0.5

        return {
            "가업 영위 기간": f"{business_years}년 ({tier})",
            "공제 한도": f"{limit/1e8:,.0f}억원" if limit else "해당 없음 (10년 미만)",
            "적용 공제액": f"{deduction/1e8:,.1f}억원",
            "예상 절세 효과(최고세율 50% 기준)": f"{tax_saving/1e8:,.1f}억원",
            "근거 조문": "상증세법 제18조의2",
            "사후관리": "상속 후 7년간 가업 유지·주식 처분·고용 유지 의무",
            "주의": "실제 세액은 전체 상속재산·누진세율 구조에 따라 달라집니다.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 4. 재무구조 개선 에이전트
# ────────────────────────────────────────────────────────────────────────────
class FinanceAgent(BaseAgent):
    name = "FinanceAgent"
    role = "재무구조 개선 및 리스크 헷지 전문가"
    system_prompt = (
        _COMMON_HEADER
        + "\n\n【전문 분야】\n"
        "부채비율 개선, 가지급금 해결, 자본잠식 해소, 유동성 리스크 관리, "
        "특허패키지·연구개발 세액공제 활용, 인사노무 비용 최적화\n\n"
        "【목표】\n"
        "법인의 재무비율(부채비율·유동비율·이자보상배율)을 금융기관 여신 기준선 이상으로 "
        "개선하고, 가지급금·자본잠식 등 즉시 해소 필요 항목의 구체적 실행 방안을 "
        "비용·기간·리스크 수치와 함께 제시한다.\n"
        "산출물 기준: 현재 재무비율 진단 → 목표 수치 → 실행 방안 3가지 이상 / "
        "금융기관 신용등급 영향 분석 포함 / 가지급금 인정이자율 4.6% 적용 검증"
    )

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "analyze_financial_ratios",
                "description": "주요 재무비율을 분석하고 개선 방향을 제시합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "total_assets": {"type": "number", "description": "총자산 (원)"},
                        "total_equity": {"type": "number", "description": "자기자본 (원)"},
                        "total_debt": {"type": "number", "description": "총부채 (원)"},
                        "current_assets": {"type": "number", "description": "유동자산 (원)"},
                        "current_liabilities": {"type": "number", "description": "유동부채 (원)"},
                        "net_income": {"type": "number", "description": "당기순이익 (원)"},
                    },
                    "required": [
                        "total_assets", "total_equity", "total_debt",
                        "current_assets", "current_liabilities", "net_income",
                    ],
                },
            }
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "analyze_financial_ratios":
            return self._analyze(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _analyze(
        total_assets: float, total_equity: float, total_debt: float,
        current_assets: float, current_liabilities: float, net_income: float,
    ) -> dict[str, Any]:
        debt_ratio = total_debt / total_equity * 100 if total_equity else float("inf")
        current_ratio = current_assets / current_liabilities * 100 if current_liabilities else float("inf")
        roe = net_income / total_equity * 100 if total_equity else 0.0

        def grade(ratio: float, good: float, warn: float, higher_is_better: bool) -> str:
            if higher_is_better:
                return "양호" if ratio >= good else ("주의" if ratio >= warn else "위험")
            else:
                return "양호" if ratio <= good else ("주의" if ratio <= warn else "위험")

        return {
            "부채비율": f"{debt_ratio:.1f}% ({grade(debt_ratio, 100, 200, False)})",
            "유동비율": f"{current_ratio:.1f}% ({grade(current_ratio, 150, 100, True)})",
            "ROE": f"{roe:.2f}%",
            "자본잠식 여부": "해당 없음" if total_equity > 0 else "자본잠식",
        }

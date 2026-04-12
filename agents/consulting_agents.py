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
    "법인 / 주주·임원·종업원 / 과세관청 3자 이해관계를 교차 분석하여 솔루션을 제공합니다.\n\n"
    "【답변 기준】\n"
    "- 최신 개정 상법·세법 및 대법원·고등법원 판례 반영\n"
    "- 법률·세법 오류 및 계산 공식·결과값 자체 검증 후 답변\n"
    "- 단정적·간결한 전문가 언어, 불필요한 면책 문구 생략\n"
    "- 우선 적용 법령: 조세특례제한법, 법인세법, 소득세법, 국세기본법, 상법, 상속세및증여세법"
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
        "접대비·복리후생비 한도 관리, 연구인력개발비 세액공제 등"
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
        """2024년 귀속 법인세율 적용 (일반세율)."""
        brackets = [
            (200_000_000, 0.09),
            (20_000_000_000, 0.19),
            (300_000_000_000, 0.21),
            (float("inf"), 0.24),
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
        "차명주식 해소, 명의신탁 해지 리스크 분석, 증여·양도세 최적화"
    )

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_unlisted_stock_value",
                "description": (
                    "상속세및증여세법 시행령 제54조 보충적 평가방법으로 "
                    "비상장주식 1주당 가액을 산정합니다."
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
                        "is_real_estate_heavy": {
                            "type": "boolean",
                            "description": "부동산 과다 법인 여부 (자산 중 부동산 50% 이상)",
                        },
                    },
                    "required": [
                        "net_asset_per_share",
                        "net_income_per_share",
                        "is_real_estate_heavy",
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
        is_real_estate_heavy: bool,
    ) -> dict[str, Any]:
        if is_real_estate_heavy:
            asset_w, income_w = 0.6, 0.4
            label = "부동산 과다법인"
        else:
            asset_w, income_w = 0.4, 0.6
            label = "일반법인"

        value = net_asset_per_share * asset_w + net_income_per_share * income_w
        floor = net_asset_per_share * 0.8
        final = max(value, floor)

        return {
            "법인 구분": label,
            "가중치": f"순자산 {int(asset_w*100)}% + 순손익 {int(income_w*100)}%",
            "가중평균 산출가액": f"{value:,.0f}원",
            "하한(순자산의 80%)": f"{floor:,.0f}원",
            "최종 1주당 평가액": f"{final:,.0f}원",
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
        "가업상속공제(조특법 제18조), 창업자금 증여특례(조특법 제30조의5), "
        "자녀법인 활용 승계 전략, 주식 단계적 이전, 사전·사후 관리 요건"
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
        if business_years >= 20:
            limit = 500_000_000_000
        elif business_years >= 10:
            limit = 300_000_000_000
        else:
            limit = 0  # 10년 미만은 공제 불가

        deduction = min(business_value, limit)
        tax_saving = deduction * 0.5

        return {
            "가업 영위 기간": f"{business_years}년",
            "공제 한도": f"{limit:,.0f}원" if limit else "해당 없음(10년 미만)",
            "적용 공제액": f"{deduction:,.0f}원",
            "예상 절세 효과(최고세율 50% 기준)": f"{tax_saving:,.0f}원",
            "주의": "실제 세액은 전체 상속재산·누진세율 구조에 따라 다릅니다.",
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
        "특허패키지·연구개발 세액공제 활용, 인사노무 비용 최적화"
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
                        "total_assets",
                        "total_equity",
                        "total_debt",
                        "current_assets",
                        "current_liabilities",
                        "net_income",
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
        total_assets: float,
        total_equity: float,
        total_debt: float,
        current_assets: float,
        current_liabilities: float,
        net_income: float,
    ) -> dict[str, Any]:
        debt_ratio = total_debt / total_equity * 100 if total_equity else float("inf")
        current_ratio = (
            current_assets / current_liabilities * 100 if current_liabilities else float("inf")
        )
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

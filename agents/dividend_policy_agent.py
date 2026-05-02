"""
DividendPolicyAgent: 배당정책 설계 전담 에이전트

근거 법령:
  - 상법 제462조~제464조의2 (이익배당, 중간배당, 현물배당)
  - 소득세법 제17조, 제56조 (배당소득, 배당세액공제)
  - 소득세법 제14조 제3항 (금융소득 종합과세 기준: 2,000만 원)
  - 법인세법 제18조의3 (수입배당금 익금불산입)
  - 상속세및증여세법 제41조의2 (초과배당 증여세 과세)

주요 기능:
  - 배당 vs. 급여 비교 (오너 실수령액 최대화)
  - 금융소득 종합과세 임계점 관리 (2,000만 원 기준)
  - 자녀법인을 통한 배당 구조 최적화
  - 의제배당 과세 시뮬레이션
  - 초과배당 증여세 리스크 진단 (상증세법 §41의2)
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 배당정책 및 주주환원 전략 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 이익배당 구조 설계 (현금배당·주식배당·중간배당·현물배당)\n"
    "- 금융소득 종합과세 임계점(2,000만 원) 관리 전략\n"
    "- 오너 배당 vs. 급여 최적 혼합 비율 계산\n"
    "- 자녀법인 배당 수취 시 수입배당금 익금불산입 (법인세법 §18의3)\n"
    "- 초과배당 증여세 과세 (상증세법 §41의2): 지분율 초과 배당 수취 시\n"
    "- 의제배당: 자본 감소·잉여금 자본 전입·법인 해산 시 과세\n\n"
    "【분석 관점】\n"
    "- 법인: 미처분이익잉여금 관리 / 재무구조 건전화\n"
    "- 오너: 배당 실수령액 극대화 / 금융소득 종합과세 회피\n"
    "- 과세관청: 초과배당 증여세 / 배당소득 원천징수 적정 여부\n"
    "- 금융기관: 배당 지급 후 유동성 / 자기자본 감소 영향\n\n"
    "【목표】\n"
    "법인의 이익잉여금을 세부담 최소화 방식으로\n"
    "오너·주주에게 환원하는 최적 배당 경로를 설계한다."
)

# 배당소득세율 (소득세법 §17, 원천징수 14% + 지방세 10%)
DIV_WITHHOLDING = 0.154   # 14% × 1.1 (지방소득세 포함)

# 금융소득 종합과세 기준 (소득세법 §14③)
FINANCIAL_INCOME_THRESHOLD = 20_000_000  # 2,000만 원

# 수입배당금 익금불산입률 (법인세법 §18의3 / 2026년 귀속)
# 지분율 기준
INTER_CORP_DIV_EXCLUSION = {
    100: 1.00,   # 완전자법인: 100%
    50: 0.80,    # 50% 이상: 80%
    20: 0.40,    # 20% 이상 50% 미만: 40%
    0: 0.00,     # 20% 미만: 0%
}

# 소득세율 (2026년 귀속)
INCOME_TAX_BRACKETS = [
    (12_000_000, 0.06),
    (46_000_000, 0.15),
    (88_000_000, 0.24),
    (150_000_000, 0.35),
    (300_000_000, 0.38),
    (500_000_000, 0.40),
    (1_000_000_000, 0.42),
    (float("inf"), 0.45),
]


def _calc_income_tax(taxable: float) -> float:
    """종합소득 누진세 계산"""
    prev = 0
    tax = 0.0
    for limit, rate in INCOME_TAX_BRACKETS:
        if taxable <= 0:
            break
        bracket = min(taxable - prev, limit - prev) if limit != float("inf") else taxable - prev
        if bracket <= 0:
            prev = limit
            continue
        slab = min(taxable, limit) - prev
        tax += slab * rate
        prev = limit
        if taxable <= limit:
            break
    return tax * 1.1  # 지방소득세 포함


class DividendPolicyAgent(BaseAgent):
    name = "DividendPolicyAgent"
    role = "배당정책 설계 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_dividend_tax",
                "description": (
                    "배당 지급 시 개인 주주의 배당소득세 계산.\n"
                    "금융소득 종합과세 여부에 따른 분리과세·종합과세 비교."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "dividend_amount": {"type": "number", "description": "배당 금액 (원)"},
                        "other_financial_income": {
                            "type": "number",
                            "description": "기타 금융소득 (이자·배당 합산, 원)",
                        },
                        "other_income": {
                            "type": "number",
                            "description": "근로소득·사업소득 등 종합소득 합계 (원)",
                        },
                    },
                    "required": ["dividend_amount", "other_financial_income", "other_income"],
                },
            },
            {
                "name": "optimize_dividend_salary",
                "description": (
                    "오너 가처분소득 극대화를 위한 배당·급여 최적 혼합 비율 계산.\n"
                    "금융소득 종합과세 임계점을 고려한 배당 한도 및 급여 조정안 제시."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "distributable_profit": {"type": "number", "description": "처분 가능 이익잉여금 (원)"},
                        "current_salary": {"type": "number", "description": "현재 연간 급여 (원)"},
                        "other_financial_income": {"type": "number", "description": "기타 금융소득 (원)"},
                        "corp_tax_rate": {"type": "number", "description": "법인세율 (0~0.25)"},
                    },
                    "required": ["distributable_profit", "current_salary", "corp_tax_rate"],
                },
            },
            {
                "name": "check_excess_dividend_risk",
                "description": (
                    "초과배당 증여세 리스크 진단 (상증세법 §41의2).\n"
                    "지분율을 초과하여 배당을 수취한 경우 증여세 과세 가능성을 검토한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "total_dividend": {"type": "number", "description": "법인 총 배당액 (원)"},
                        "shareholder_stake_pct": {
                            "type": "number",
                            "description": "해당 주주 지분율 (0~100, %)",
                        },
                        "actual_received": {"type": "number", "description": "실제 수령 배당액 (원)"},
                    },
                    "required": ["total_dividend", "shareholder_stake_pct", "actual_received"],
                },
            },
        ]

    # ── 툴 구현 ────────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_dividend_tax":
            return self._calc_dividend_tax(**tool_input)
        if tool_name == "optimize_dividend_salary":
            return self._optimize_dividend_salary(**tool_input)
        if tool_name == "check_excess_dividend_risk":
            return self._check_excess_dividend_risk(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _calc_dividend_tax(
        self,
        dividend_amount: float,
        other_financial_income: float,
        other_income: float,
    ) -> dict:
        total_financial = dividend_amount + other_financial_income

        # 분리과세 (14% + 지방세)
        withholding_tax = dividend_amount * DIV_WITHHOLDING

        # 종합과세 여부
        if total_financial > FINANCIAL_INCOME_THRESHOLD:
            # 종합과세 대상: 금융소득 전체를 다른 종합소득과 합산
            taxable_total = other_income + total_financial
            total_tax = _calc_income_tax(taxable_total)
            # 종합소득에서 기타소득만의 세액
            tax_without_div = _calc_income_tax(other_income)
            # 배당세액공제 (Gross-up: 11%)
            grossup = dividend_amount * 0.11
            dividend_tax_global = total_tax - tax_without_div - grossup
            mode = "종합과세"
            applicable_tax = max(dividend_tax_global, 0)
        else:
            mode = "분리과세(원천징수)"
            applicable_tax = withholding_tax

        return {
            "배당금액": round(dividend_amount),
            "금융소득_합계": round(total_financial),
            "종합과세_여부": total_financial > FINANCIAL_INCOME_THRESHOLD,
            "과세방식": mode,
            "적용_세액": round(applicable_tax),
            "실수령액": round(dividend_amount - applicable_tax),
            "실효세율(%)": round(applicable_tax / dividend_amount * 100, 2) if dividend_amount else 0,
            "임계점_잔여": round(max(0, FINANCIAL_INCOME_THRESHOLD - total_financial)),
            "법령근거": "소득세법 §14③, §17, §56",
        }

    def _optimize_dividend_salary(
        self,
        distributable_profit: float,
        current_salary: float,
        corp_tax_rate: float,
        other_financial_income: float = 0,
    ) -> dict:
        # 금융소득 종합과세 임계점 고려 최대 배당액
        max_div_before_threshold = max(0, FINANCIAL_INCOME_THRESHOLD - other_financial_income)

        # 배당 시 법인: 법인세 납부 후 잉여금에서 지급
        after_tax_profit = distributable_profit * (1 - corp_tax_rate)
        safe_dividend = min(after_tax_profit, max_div_before_threshold)

        # 급여 증액 vs. 배당 효과
        salary_tax = current_salary * 0.35  # 가정 35% 한계세율
        div_tax_safe = safe_dividend * DIV_WITHHOLDING

        return {
            "처분가능이익잉여금": round(distributable_profit),
            "법인세_차감후_배당재원": round(after_tax_profit),
            "종합과세_임계점_여유": round(max_div_before_threshold),
            "권장_배당액(종합과세_미달)": round(safe_dividend),
            "배당_예상세액": round(div_tax_safe),
            "배당_예상실수령액": round(safe_dividend - div_tax_safe),
            "권장_전략": (
                f"배당 {safe_dividend:,.0f}원(분리과세 14%) + "
                f"잔여 {after_tax_profit - safe_dividend:,.0f}원은 법인 내 유보 또는 급여 조정"
            ),
            "법령근거": "소득세법 §14③ (금융소득 종합과세 기준 2,000만 원)",
        }

    def _check_excess_dividend_risk(
        self,
        total_dividend: float,
        shareholder_stake_pct: float,
        actual_received: float,
    ) -> dict:
        stake = shareholder_stake_pct / 100
        proportional_amount = total_dividend * stake
        excess = actual_received - proportional_amount

        if excess <= 0:
            return {
                "초과배당": False,
                "지분율_비례배당액": round(proportional_amount),
                "실수령액": round(actual_received),
                "초과금액": 0,
                "증여세_리스크": "없음",
            }

        # 상증세법 §41의2: 초과배당액에 증여세 과세 (수혜자 기준)
        # 단, 지분율 30% 이상 주주(최대주주)와 특수관계인이 수혜자인 경우
        gift_tax_base = excess
        # 증여세율 적용 (단순화: 1억 초과 20% 구간 가정)
        gift_tax_estimate = gift_tax_base * 0.20 - 10_000_000  # 1억~5억 구간

        return {
            "초과배당": True,
            "지분율_비례배당액": round(proportional_amount),
            "실수령액": round(actual_received),
            "초과금액": round(excess),
            "증여세_과세대상": round(gift_tax_base),
            "증여세_추정액": round(max(0, gift_tax_estimate)),
            "증여세_리스크": "🔴 고위험 — 과세관청 시정 요구 가능",
            "법령근거": "상속세및증여세법 §41의2 (초과배당에 따른 이익의 증여)",
            "권고": "지분율 비례 배당 원칙 준수 / 불가피 시 사전 세무 검토 필수",
        }

    # ── analyze() 인터페이스 ───────────────────────────────────────────────

    def analyze(self, company_data: dict[str, Any]) -> str:
        profit = company_data.get("retained_earnings", 0)
        salary = company_data.get("ceo_salary", 0)
        corp_rate = company_data.get("corp_tax_rate", 0.20)
        other_fin = company_data.get("other_financial_income", 0)

        lines = ["[배당정책 설계 분석 결과]"]

        if profit:
            opt = self._optimize_dividend_salary(profit, salary, corp_rate, other_fin)
            lines.append(f"\n▶ 최적 배당 설계")
            lines.append(f"  권장 배당액: {opt['권장_배당액(종합과세_미달)']:,.0f}원 (분리과세 14% 적용)")
            lines.append(f"  배당 실수령액: {opt['배당_예상실수령액']:,.0f}원")
            lines.append(f"  전략: {opt['권장_전략']}")
        else:
            lines.append("  이익잉여금 데이터 부족 — retained_earnings 입력 필요")

        return "\n".join(lines)

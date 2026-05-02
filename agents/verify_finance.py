"""
VerifyFinance: 재무 수치 교차검증 전담 에이전트

역할:
  - GROUP G·I 재무 계산값의 수식 정합성 검증
  - 손익계산서·재무상태표 항목 간 논리 모순 탐지
  - 세금 계산(법인세·부가세·4대보험) 재산출 비교
  - 이상값(Outlier) 탐지 — 업종 평균 대비 급격한 이탈

근거 기준:
  - 한국채택국제회계기준(K-IFRS) / 일반기업회계기준(K-GAAP)
  - 법인세법 제55조 (세율 구간), 부가가치세법 §29
  - 국민연금법·건강보험법·고용보험법 보험료율
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 재무 수치 교차검증 전문가입니다.\n\n"
    "【역할】\n"
    "- 재무 계산값의 수식 정합성 독립 재검증\n"
    "- 손익·재무상태표 항목 간 논리 일관성 확인\n"
    "- 세금·보험료 계산 재산출 및 오류 식별\n"
    "- 업종 평균 대비 이상값 탐지\n\n"
    "【검증 원칙】\n"
    "- 오류 발견 시 정정값과 근거 조문을 반드시 함께 제시\n"
    "- 단순 수치 확인이 아닌 경제적 합리성도 함께 판단\n"
    "- 검증 불가 항목은 '데이터 부족'으로 명시"
)


class VerifyFinance(BaseAgent):
    name = "VerifyFinance"
    role = "재무 수치 교차검증 전담"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "verify_tax_calculation",
                "description": "법인세·부가세·소득세 계산값 독립 재검증",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tax_type": {
                            "type": "string",
                            "enum": ["법인세", "부가세", "소득세"],
                        },
                        "tax_base": {"type": "number", "description": "과세표준 (원)"},
                        "reported_tax": {"type": "number", "description": "신고·계산된 세액 (원)"},
                        "fiscal_year": {"type": "integer", "description": "귀속 연도 (예: 2025)"},
                    },
                    "required": ["tax_type", "tax_base", "reported_tax"],
                },
            },
            {
                "name": "verify_financial_ratios",
                "description": "재무비율 계산 정합성 및 업종 벤치마크 비교",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "revenue": {"type": "number"},
                        "operating_profit": {"type": "number"},
                        "net_profit": {"type": "number"},
                        "total_assets": {"type": "number"},
                        "total_equity": {"type": "number"},
                        "total_debt": {"type": "number"},
                        "industry": {"type": "string"},
                    },
                    "required": ["revenue", "total_assets", "total_equity"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "verify_tax_calculation":
            return self._verify_tax_calculation(**tool_input)
        if tool_name == "verify_financial_ratios":
            return self._verify_financial_ratios(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _verify_tax_calculation(
        self,
        tax_type: str,
        tax_base: float,
        reported_tax: float,
        fiscal_year: int = 2025,
    ) -> dict:
        errors = []
        recalc = 0.0

        if tax_type == "법인세":
            # 2026년 귀속~: 10/20/22/25% / 2025년 귀속까지: 9/19/21/24%
            if fiscal_year >= 2026:
                brackets = [(200_000_000, 0.10), (20_000_000_000, 0.20),
                            (300_000_000_000, 0.22), (float("inf"), 0.25)]
            else:
                brackets = [(200_000_000, 0.09), (20_000_000_000, 0.19),
                            (300_000_000_000, 0.21), (float("inf"), 0.24)]
            prev = 0.0
            for limit, rate in brackets:
                if tax_base <= prev:
                    break
                recalc += (min(tax_base, limit) - prev) * rate
                prev = limit

        elif tax_type == "부가세":
            recalc = tax_base * 0.10  # 표준세율 10%

        elif tax_type == "소득세":
            # 2025년 귀속 기준 8구간
            so_brackets = [
                (14_000_000, 0.06), (50_000_000, 0.15),
                (88_000_000, 0.24), (150_000_000, 0.35),
                (300_000_000, 0.38), (500_000_000, 0.40),
                (1_000_000_000, 0.42), (float("inf"), 0.45),
            ]
            prev = 0.0
            for limit, rate in so_brackets:
                if tax_base <= prev:
                    break
                recalc += (min(tax_base, limit) - prev) * rate
                prev = limit

        gap = abs(recalc - reported_tax)
        gap_pct = gap / recalc * 100 if recalc else 0

        if gap_pct > 0.5:
            errors.append({
                "항목": f"{tax_type} 계산 오류",
                "신고액": round(reported_tax),
                "재계산액": round(recalc),
                "차이": round(gap),
                "오류율": f"{gap_pct:.2f}%",
            })

        return {
            "세목": tax_type,
            "과세표준": round(tax_base),
            "귀속연도": fiscal_year,
            "신고세액": round(reported_tax),
            "재계산세액": round(recalc),
            "검증결과": "✅ 일치" if not errors else "❌ 수정 필요",
            "오류상세": errors,
        }

    def _verify_financial_ratios(
        self,
        revenue: float,
        total_assets: float,
        total_equity: float,
        operating_profit: float = 0,
        net_profit: float = 0,
        total_debt: float = 0,
        industry: str = "제조업",
    ) -> dict:
        # 업종 평균 벤치마크
        bench = {
            "제조업":   {"영업이익률": 5.0, "부채비율": 120, "ROE": 8.0},
            "도소매업": {"영업이익률": 3.0, "부채비율": 150, "ROE": 6.0},
            "서비스업": {"영업이익률": 8.0, "부채비율": 80,  "ROE": 10.0},
            "건설업":   {"영업이익률": 4.0, "부채비율": 200, "ROE": 7.0},
        }
        b = bench.get(industry, bench["제조업"])

        op_margin = (operating_profit / revenue * 100) if revenue else 0
        debt_ratio = (total_debt / total_equity * 100) if total_equity else 0
        roe = (net_profit / total_equity * 100) if total_equity else 0

        flags = []
        if revenue and abs(op_margin - b["영업이익률"]) > b["영업이익률"] * 0.5:
            flags.append(f"영업이익률 {op_margin:.1f}% — 업종평균 {b['영업이익률']}% 대비 이상")
        if total_equity and debt_ratio > b["부채비율"] * 1.5:
            flags.append(f"부채비율 {debt_ratio:.0f}% — 업종평균 {b['부채비율']}% 초과")

        return {
            "업종": industry,
            "영업이익률": f"{op_margin:.1f}%",
            "부채비율": f"{debt_ratio:.0f}%",
            "ROE": f"{roe:.1f}%",
            "업종_벤치마크": b,
            "이상값_탐지": flags if flags else ["정상 범위"],
            "검증결과": "❌ 이상값 확인 필요" if flags else "✅ 정상",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        rev = company_data.get("revenue", 0)
        op = company_data.get("operating_profit", 0)
        eq = company_data.get("equity", rev * 0.4)
        debt = company_data.get("total_debt", rev * 0.3)
        ind = company_data.get("industry", "제조업")
        lines = ["[재무 수치 교차검증 결과]"]
        result = self._verify_financial_ratios(rev, rev * 1.5, eq, op, 0, debt, ind)
        lines.append(f"\n▶ 영업이익률: {result['영업이익률']} / 부채비율: {result['부채비율']}")
        lines.append(f"  이상값: {result['이상값_탐지'][0]}")
        return "\n".join(lines)

"""
FinancialForecastAgent: 재무예측·예산편성 전담 에이전트

주요 기능:
  - 손익계산서·재무상태표 3개년 예측 모델
  - 예산 편성 및 예산 대비 실적 (Budget vs. Actual) 분석
  - 매출 성장률·원가율·영업이익률 추세 분석
  - 흑자도산(Profitable Insolvency) 위험 조기 경보
  - 현금흐름 3개월 단기 예측 + 연간 예측
"""

from __future__ import annotations
import json
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 재무예측 및 예산 편성 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 손익계산서·재무상태표 3개년 추세 분석 및 예측\n"
    "- 예산 편성(Budget Planning) 및 예실대비(Budget vs. Actual) 분석\n"
    "- 매출 성장률·원가율·영업이익률·EBITDA 관리회계 지표\n"
    "- 흑자도산 위험 진단: 매출↑ 이면서 현금↓ 패턴 탐지\n"
    "- 단기(3개월) / 연간 / 3개년 현금흐름 예측\n"
    "- 감도분석(Sensitivity Analysis): 매출 ±10~30% 시나리오\n\n"
    "【분석 관점】\n"
    "- 법인: 재무구조 건전성 / 차입금 상환 능력 / 영업현금 창출력\n"
    "- 오너: 가처분 현금 계획 / 배당 재원 가시성\n"
    "- 금융기관: 부채비율 · DSCR · 커버리지비율 · 신용등급 영향\n"
    "- 과세관청: 조정계정 적정성 / 이익 조정 여부\n\n"
    "【목표】\n"
    "오너가 숫자를 보는 순간 '지금 해야 할 재무 의사결정'을 즉시 파악할 수 있는\n"
    "실행형 예측 리포트를 제공한다."
)

# 업종별 평균 영업이익률 벤치마크 (통계청·한국은행 기업경영분석 2024년 기준)
INDUSTRY_OPM_BENCH = {
    "제조업":       0.065,
    "건설업":       0.042,
    "도소매업":     0.032,
    "음식숙박업":   0.058,
    "정보통신업":   0.112,
    "부동산업":     0.148,
    "운수업":       0.038,
    "서비스업":     0.071,
    "기타":         0.055,
}

# DSCR 안전 기준
DSCR_SAFE = 1.25   # 1.25 이상: 안전
DSCR_WARN = 1.00   # 1.00~1.25: 주의
# 1.00 미만: 위험


class FinancialForecastAgent(BaseAgent):
    name = "FinancialForecastAgent"
    role = "재무예측·예산편성 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "forecast_pnl",
                "description": (
                    "3개년 손익계산서 예측. 과거 데이터 기반 성장률을 적용하여\n"
                    "매출·매출원가·판관비·영업이익·당기순이익을 시뮬레이션한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "revenue_history": {
                            "type": "array",
                            "description": "최근 3년 매출액 리스트 [3년전, 2년전, 직전년도] (원)",
                            "items": {"type": "number"},
                        },
                        "cogs_ratio": {
                            "type": "number",
                            "description": "매출원가율 (0~1, 예: 0.65)",
                        },
                        "sga_ratio": {
                            "type": "number",
                            "description": "판관비율 (0~1, 예: 0.20)",
                        },
                        "growth_override": {
                            "type": "number",
                            "description": "성장률 강제 지정 (0~1). 미입력 시 과거 추세 자동 계산",
                        },
                        "industry": {
                            "type": "string",
                            "description": "업종명 (벤치마크 비교용)",
                            "enum": list(INDUSTRY_OPM_BENCH.keys()),
                        },
                    },
                    "required": ["revenue_history", "cogs_ratio", "sga_ratio"],
                },
            },
            {
                "name": "budget_vs_actual",
                "description": "예산 대비 실적 분석. 주요 계정별 차이금액·차이율·원인 분류를 반환한다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "budget": {
                            "type": "object",
                            "description": "예산 데이터 {계정명: 금액}",
                        },
                        "actual": {
                            "type": "object",
                            "description": "실적 데이터 {계정명: 금액}",
                        },
                        "period": {
                            "type": "string",
                            "description": "분석 기간 (예: 2026년 1분기)",
                        },
                    },
                    "required": ["budget", "actual"],
                },
            },
            {
                "name": "cashflow_warning",
                "description": (
                    "흑자도산 위험 진단. 영업이익은 양수이지만 운전자본 증가로\n"
                    "현금이 부족해지는 패턴을 탐지하고 경보 수준을 반환한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "net_income": {"type": "number", "description": "당기순이익 (원)"},
                        "operating_cashflow": {"type": "number", "description": "영업활동 현금흐름 (원)"},
                        "receivables_change": {"type": "number", "description": "매출채권 증감 (원, 증가=양수)"},
                        "inventory_change": {"type": "number", "description": "재고자산 증감 (원, 증가=양수)"},
                        "payables_change": {"type": "number", "description": "매입채무 증감 (원, 증가=양수)"},
                        "total_debt": {"type": "number", "description": "총차입금 (원)"},
                        "annual_debt_service": {"type": "number", "description": "연간 원리금 상환액 (원)"},
                    },
                    "required": ["net_income", "operating_cashflow", "total_debt", "annual_debt_service"],
                },
            },
        ]

    # ── 툴 구현 ────────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "forecast_pnl":
            return self._forecast_pnl(**tool_input)
        if tool_name == "budget_vs_actual":
            return self._budget_vs_actual(**tool_input)
        if tool_name == "cashflow_warning":
            return self._cashflow_warning(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _forecast_pnl(
        self,
        revenue_history: list[float],
        cogs_ratio: float,
        sga_ratio: float,
        growth_override: float | None = None,
        industry: str = "기타",
    ) -> dict:
        # 과거 성장률 계산 (CAGR)
        if growth_override is not None:
            growth = growth_override
        elif len(revenue_history) >= 2:
            years = len(revenue_history) - 1
            growth = (revenue_history[-1] / revenue_history[0]) ** (1 / years) - 1
        else:
            growth = 0.05  # 기본 5%

        base = revenue_history[-1]
        forecasts = []
        for i in range(1, 4):
            rev = base * ((1 + growth) ** i)
            cogs = rev * cogs_ratio
            gp = rev - cogs
            sga = rev * sga_ratio
            op_income = gp - sga
            op_margin = op_income / rev if rev else 0
            bench = INDUSTRY_OPM_BENCH.get(industry, 0.055)
            gap_vs_bench = op_margin - bench

            forecasts.append({
                "연도": f"예측 {i}년차",
                "매출액": round(rev),
                "매출원가": round(cogs),
                "매출총이익": round(gp),
                "판관비": round(sga),
                "영업이익": round(op_income),
                "영업이익률(%)": round(op_margin * 100, 2),
                "업종평균대비(pp)": round(gap_vs_bench * 100, 2),
            })

        return {
            "적용_성장률(%)": round(growth * 100, 2),
            "업종": industry,
            "업종평균_영업이익률(%)": round(INDUSTRY_OPM_BENCH.get(industry, 0.055) * 100, 2),
            "3개년_예측": forecasts,
            "법령근거": "한국은행 기업경영분석 2024 / 통계청 산업별 경영지표",
        }

    def _budget_vs_actual(
        self,
        budget: dict[str, float],
        actual: dict[str, float],
        period: str = "",
    ) -> dict:
        result = []
        all_keys = set(budget) | set(actual)
        for k in sorted(all_keys):
            b = budget.get(k, 0)
            a = actual.get(k, 0)
            diff = a - b
            diff_pct = (diff / b * 100) if b else 0
            status = "정상" if abs(diff_pct) <= 5 else ("주의" if abs(diff_pct) <= 15 else "이상")
            result.append({
                "계정": k,
                "예산": round(b),
                "실적": round(a),
                "차이": round(diff),
                "차이율(%)": round(diff_pct, 1),
                "상태": status,
            })

        total_diff = sum(r["차이"] for r in result if "이익" in r["계정"] or "수익" in r["계정"])
        return {
            "분석기간": period,
            "계정별_분석": result,
            "이익항목_누계차이": round(total_diff),
            "이상항목수": sum(1 for r in result if r["상태"] == "이상"),
        }

    def _cashflow_warning(
        self,
        net_income: float,
        operating_cashflow: float,
        total_debt: float,
        annual_debt_service: float,
        receivables_change: float = 0,
        inventory_change: float = 0,
        payables_change: float = 0,
    ) -> dict:
        # 흑자도산 지표
        cashflow_gap = net_income - operating_cashflow
        working_capital_drain = receivables_change + inventory_change - payables_change
        profitable_insolvency_risk = net_income > 0 and operating_cashflow < 0

        # DSCR
        dscr = operating_cashflow / annual_debt_service if annual_debt_service else 99
        if dscr >= DSCR_SAFE:
            dscr_status = "안전"
        elif dscr >= DSCR_WARN:
            dscr_status = "주의"
        else:
            dscr_status = "위험"

        # 종합 경보
        if profitable_insolvency_risk or dscr < DSCR_WARN:
            alert = "🔴 고위험 — 즉시 유동성 대책 수립 필요"
        elif cashflow_gap > net_income * 0.3 or dscr < DSCR_SAFE:
            alert = "🟡 주의 — 운전자본 관리 강화 필요"
        else:
            alert = "🟢 정상 — 지속 모니터링"

        return {
            "당기순이익": round(net_income),
            "영업현금흐름": round(operating_cashflow),
            "순이익_현금흐름_괴리": round(cashflow_gap),
            "운전자본_유출": round(working_capital_drain),
            "흑자도산_위험": profitable_insolvency_risk,
            "DSCR": round(dscr, 3),
            "DSCR_기준": f"안전≥{DSCR_SAFE} / 주의≥{DSCR_WARN} / 위험<{DSCR_WARN}",
            "DSCR_상태": dscr_status,
            "종합경보": alert,
            "권고사항": (
                "매출채권 회수 기간 단축 및 재고 감축 우선 실행" if profitable_insolvency_risk
                else "영업현금흐름 개선 및 차입금 구조 재검토"
            ),
        }

    # ── analyze() 인터페이스 (orchestrator __USE_ANALYZE__ 방식) ───────────

    def analyze(self, company_data: dict[str, Any]) -> str:
        revenue = company_data.get("revenue_3y", [])
        cogs_r = company_data.get("cogs_ratio", 0.65)
        sga_r = company_data.get("sga_ratio", 0.20)
        industry = company_data.get("industry", "기타")
        net_income = company_data.get("net_income", 0)
        op_cf = company_data.get("operating_cashflow", net_income * 0.8)
        total_debt = company_data.get("total_debt", 0)
        debt_service = company_data.get("annual_debt_service", total_debt * 0.15)

        lines = ["[재무예측 분석 결과]"]

        if revenue:
            fc = self._forecast_pnl(revenue, cogs_r, sga_r, industry=industry)
            lines.append(f"\n▶ 3개년 손익 예측 (성장률 {fc['적용_성장률(%)']:.1f}%)")
            for yr in fc["3개년_예측"]:
                lines.append(
                    f"  {yr['연도']}: 매출 {yr['매출액']:,.0f}원 / "
                    f"영업이익 {yr['영업이익']:,.0f}원 ({yr['영업이익률(%)']:.1f}%) / "
                    f"업종대비 {yr['업종평균대비(pp)']:+.1f}pp"
                )

        if total_debt and debt_service:
            warn = self._cashflow_warning(net_income, op_cf, total_debt, debt_service)
            lines.append(f"\n▶ 유동성 경보: {warn['종합경보']}")
            lines.append(f"  DSCR: {warn['DSCR']} ({warn['DSCR_상태']}) / 흑자도산위험: {warn['흑자도산_위험']}")
            lines.append(f"  권고: {warn['권고사항']}")

        return "\n".join(lines)

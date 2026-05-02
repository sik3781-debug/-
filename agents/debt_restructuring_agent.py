"""
DebtRestructuringAgent: 부채 구조조정 전담 에이전트

근거 법령·제도:
  - 채무자 회생 및 파산에 관한 법률 (회생법)
  - 기업구조조정 촉진법 (기촉법)
  - 중소기업 경영안정자금 (중진공)
  - 신용보증기금·기술보증기금 보증 재조정
  - 한국자산관리공사(캠코) 기업구조조정 지원

주요 기능:
  - 부채 구조 진단 (유동/고정, 단기차입금 집중도, 이자부담)
  - 차입금 재조정 시나리오 (만기 연장·금리 인하·DES)
  - 채무재조정 신청 적격성 판단 (기촉법·회생법 선택 기준)
  - 정책금융 대환·전환 최적화 (중진공·기보·신보)
  - 이자보상배율·DSCR 개선 시뮬레이션
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 부채 구조조정 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 부채 구조 진단: 단기차입 집중도·이자보상배율·DSCR\n"
    "- 차입금 만기 연장·금리 인하·DES(채무의 주식전환) 시나리오\n"
    "- 기업구조조정 촉진법(기촉법) vs. 회생법 적용 기준 비교\n"
    "- 중진공·기보·신보 정책금융 대환 최적화\n"
    "- 캠코(한국자산관리공사) 기업구조조정 지원 활용\n\n"
    "【분석 관점】\n"
    "- 법인: 이자비용 절감 / 재무구조 건전화 / 신용등급 개선\n"
    "- 오너: 개인 연대보증 해제 / 경영권 유지\n"
    "- 과세관청: DES 시 채무면제이익 과세 (법인세법 §17)\n"
    "- 금융기관: 대손충당금 절감 / 부실채권 정리\n\n"
    "【목표】\n"
    "현금흐름을 유지하면서 이자부담을 최소화하고,\n"
    "오너의 경영권을 보호하는 최적 구조조정 방안을 설계한다."
)

# 주요 재무 안전 기준
SAFETY_BENCHMARKS = {
    "부채비율":      {"안전": 1.0, "주의": 2.0, "위험": 3.0},   # 배
    "유동비율":      {"안전": 1.5, "주의": 1.0, "위험": 0.5},   # 배
    "이자보상배율":  {"안전": 3.0, "주의": 1.5, "위험": 1.0},   # 배
    "DSCR":         {"안전": 1.25, "주의": 1.0, "위험": 0.8},  # 배
}

# 정책금융 대환 옵션 (2026년 기준)
POLICY_FINANCE = {
    "중진공_긴급경영안정자금": {"한도": 1_000_000_000, "금리": 0.0250, "기간": "5년(거치2년)"},
    "신보_보증부대출": {"한도": 3_000_000_000, "금리": 0.0380, "기간": "5년"},
    "기보_기술보증": {"한도": 3_000_000_000, "금리": 0.0350, "기간": "7년"},
    "캠코_채권매입후재지원": {"한도": 2_000_000_000, "금리": 0.0300, "기간": "10년"},
}


class DebtRestructuringAgent(BaseAgent):
    name = "DebtRestructuringAgent"
    role = "부채 구조조정 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "diagnose_debt_structure",
                "description": (
                    "부채 구조 종합 진단.\n"
                    "주요 재무 안전 기준 대비 현황을 평가하고\n"
                    "위험 등급과 즉시 대응 과제를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "total_debt": {"type": "number", "description": "총차입금 (원)"},
                        "short_term_debt": {"type": "number", "description": "단기차입금 (원, 1년 이내)"},
                        "total_equity": {"type": "number", "description": "자기자본 (원)"},
                        "current_assets": {"type": "number", "description": "유동자산 (원)"},
                        "current_liabilities": {"type": "number", "description": "유동부채 (원)"},
                        "operating_income": {"type": "number", "description": "영업이익 (원)"},
                        "interest_expense": {"type": "number", "description": "이자비용 (원)"},
                        "operating_cashflow": {"type": "number", "description": "영업현금흐름 (원)"},
                        "annual_debt_service": {"type": "number", "description": "연간 원리금 상환액 (원)"},
                    },
                    "required": ["total_debt", "total_equity", "operating_income", "interest_expense"],
                },
            },
            {
                "name": "simulate_restructuring",
                "description": (
                    "차입금 재조정 시나리오 시뮬레이션.\n"
                    "만기 연장·금리 인하·DES·정책금융 대환 등\n"
                    "시나리오별 이자비용 절감·현금흐름 개선 효과를 비교한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "current_debt": {"type": "number", "description": "현재 차입금 잔액 (원)"},
                        "current_rate": {"type": "number", "description": "현재 평균 금리 (0~1)"},
                        "current_maturity_years": {"type": "number", "description": "현재 평균 만기 (년)"},
                        "des_amount": {
                            "type": "number",
                            "description": "DES 전환 대상 금액 (원, 선택)",
                        },
                        "share_price": {
                            "type": "number",
                            "description": "DES 적용 주식 가격 (원/주, DES 시)",
                        },
                    },
                    "required": ["current_debt", "current_rate", "current_maturity_years"],
                },
            },
            {
                "name": "match_policy_finance",
                "description": (
                    "정책금융 대환 최적 매칭.\n"
                    "현재 차입 현황을 기반으로 중진공·신보·기보·캠코\n"
                    "정책금융 대환 시 금리절감·기간연장 효과를 계산한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "debt_amount": {"type": "number", "description": "대환 대상 차입금 (원)"},
                        "current_rate": {"type": "number", "description": "현재 금리 (0~1)"},
                        "credit_grade": {
                            "type": "string",
                            "description": "신용등급 (예: BBB-, BB+)",
                        },
                        "has_technology": {"type": "boolean", "description": "기술평가 가능 기업 여부"},
                    },
                    "required": ["debt_amount", "current_rate"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "diagnose_debt_structure":
            return self._diagnose_debt_structure(**tool_input)
        if tool_name == "simulate_restructuring":
            return self._simulate_restructuring(**tool_input)
        if tool_name == "match_policy_finance":
            return self._match_policy_finance(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _diagnose_debt_structure(
        self,
        total_debt: float,
        total_equity: float,
        operating_income: float,
        interest_expense: float,
        short_term_debt: float = 0,
        current_assets: float = 0,
        current_liabilities: float = 0,
        operating_cashflow: float = 0,
        annual_debt_service: float = 0,
    ) -> dict:
        metrics = {}

        # 부채비율
        debt_ratio = total_debt / total_equity if total_equity else 999
        metrics["부채비율"] = round(debt_ratio, 2)

        # 유동비율
        current_ratio = current_assets / current_liabilities if current_liabilities else 999
        metrics["유동비율"] = round(current_ratio, 2)

        # 이자보상배율
        icr = operating_income / interest_expense if interest_expense else 999
        metrics["이자보상배율"] = round(icr, 2)

        # DSCR
        dscr = operating_cashflow / annual_debt_service if annual_debt_service else 0
        metrics["DSCR"] = round(dscr, 2)

        # 단기차입 집중도
        short_ratio = short_term_debt / total_debt if total_debt else 0
        metrics["단기차입_집중도(%)"] = round(short_ratio * 100, 1)

        # 종합 위험등급
        risk_flags = []
        if debt_ratio > SAFETY_BENCHMARKS["부채비율"]["위험"]:
            risk_flags.append("🔴 부채비율 300% 초과")
        if current_ratio < SAFETY_BENCHMARKS["유동비율"]["위험"]:
            risk_flags.append("🔴 유동비율 50% 미만")
        if icr < SAFETY_BENCHMARKS["이자보상배율"]["위험"]:
            risk_flags.append("🔴 이자보상배율 1배 미만 (영업이익으로 이자도 못 갚음)")
        if short_ratio > 0.70:
            risk_flags.append("🟡 단기차입 집중도 70% 초과 — 유동성 리스크")

        overall = "🔴 즉시 구조조정" if len(risk_flags) >= 2 else "🟡 점진적 개선" if risk_flags else "🟢 안정"

        return {
            "재무_지표": metrics,
            "벤치마크": {k: f"안전≥{v['안전']} / 주의≥{v['주의']} / 위험<{v['위험']}" for k, v in SAFETY_BENCHMARKS.items()},
            "위험_플래그": risk_flags,
            "종합_진단": overall,
            "권고": (
                "기촉법 신청 또는 정책금융 대환 즉시 추진" if len(risk_flags) >= 2
                else "단기차입 장기전환 + 정책금융 대환 검토" if risk_flags
                else "현 재무구조 유지 — 추가 차입 시 DSCR 1.25 이상 유지"
            ),
        }

    def _simulate_restructuring(
        self,
        current_debt: float,
        current_rate: float,
        current_maturity_years: float,
        des_amount: float = 0,
        share_price: float = 0,
    ) -> dict:
        current_interest = current_debt * current_rate
        current_annual_principal = current_debt / current_maturity_years

        scenarios = []

        # 시나리오 1: 만기 연장 (5→10년)
        ext_maturity = current_maturity_years * 2
        ext_principal = current_debt / ext_maturity
        scenarios.append({
            "시나리오": "만기 연장 (기간 2배)",
            "연이자": round(current_interest),
            "연원금": round(ext_principal),
            "연간_원리금": round(current_interest + ext_principal),
            "현재대비_절감액": round(current_annual_principal - ext_principal),
        })

        # 시나리오 2: 금리 인하 (현재 → 정책금리 2.5%)
        new_rate = 0.025
        lower_interest = current_debt * new_rate
        scenarios.append({
            "시나리오": f"금리 인하 ({current_rate*100:.1f}% → {new_rate*100:.1f}%)",
            "연이자": round(lower_interest),
            "연원금": round(current_annual_principal),
            "연간_원리금": round(lower_interest + current_annual_principal),
            "현재대비_절감액": round(current_interest - lower_interest),
        })

        # 시나리오 3: DES (채무의 주식전환)
        if des_amount and share_price:
            des_shares = int(des_amount / share_price)
            remain_debt = current_debt - des_amount
            remain_interest = remain_debt * current_rate
            scenarios.append({
                "시나리오": "DES (채무의 주식전환)",
                "전환대상_채무": round(des_amount),
                "발행주식수": des_shares,
                "잔여차입금": round(remain_debt),
                "연이자_절감": round(des_amount * current_rate),
                "주의": "DES 시 채무면제이익 과세 (법인세법 §17) — 세무 검토 필수",
            })

        return {
            "현재_차입금": round(current_debt),
            "현재_연이자": round(current_interest),
            "현재_연원금": round(current_annual_principal),
            "시나리오_비교": scenarios,
            "권장_시나리오": "만기 연장 + 정책금융 대환 병행" if current_rate > 0.04 else "만기 연장 우선",
        }

    def _match_policy_finance(
        self,
        debt_amount: float,
        current_rate: float,
        credit_grade: str = "BBB-",
        has_technology: bool = False,
    ) -> dict:
        matches = []
        for name, info in POLICY_FINANCE.items():
            if debt_amount <= info["한도"]:
                saving = debt_amount * (current_rate - info["금리"])
                if saving > 0:
                    matches.append({
                        "상품": name,
                        "한도": f"{info['한도']//100_000_000:.0f}억 원",
                        "금리": f"{info['금리']*100:.2f}%",
                        "기간": info["기간"],
                        "연간_이자절감": round(saving),
                        "적합도": "✅ 최우선" if "중진공" in name or (has_technology and "기보" in name) else "◎ 검토",
                    })

        if not matches:
            matches.append({"상품": "캠코 채권매입후재지원", "안내": "채권 매각 후 재지원 구조"})

        return {
            "대환_대상_금액": round(debt_amount),
            "현재_금리": f"{current_rate*100:.2f}%",
            "추천_정책금융": matches,
            "법령근거": "중소기업진흥에 관한 법률 / 신용보증기금법 / 기술보증기금법",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        total_debt = company_data.get("total_debt", 0)
        equity = company_data.get("total_equity", 0)
        op_income = company_data.get("operating_income", 0)
        interest = company_data.get("interest_expense", 0)

        lines = ["[부채 구조조정 분석 결과]"]
        if total_debt and equity:
            diag = self._diagnose_debt_structure(total_debt, equity, op_income, interest)
            lines.append(f"\n▶ 부채 구조 종합 진단: {diag['종합_진단']}")
            lines.append(f"  부채비율: {diag['재무_지표']['부채비율']:.1f}배 / 이자보상배율: {diag['재무_지표']['이자보상배율']:.1f}배")
            if diag["위험_플래그"]:
                lines.append(f"  위험: {' | '.join(diag['위험_플래그'])}")
            lines.append(f"  권고: {diag['권고']}")
        else:
            lines.append("  차입금·자기자본 데이터 부족 — total_debt / total_equity 입력 필요")
        return "\n".join(lines)

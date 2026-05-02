"""
ExecutivePayAgent: 임원보수설계 전담 에이전트
- 급여·배당·퇴직금 믹스별 법인+개인 세부담 최적화
- 2026년 귀속 법인세율 적용 (10%/20%/22%/25%)
- 임원 퇴직금 손금산입 한도 계산
"""

from __future__ import annotations

from agents.base_agent import BaseAgent

_SYS = (
    "당신은 임원보수 최적화 전문 컨설턴트입니다.\n"
    "법인세법·소득세법 최신 기준으로 임원의\n"
    "급여·배당·퇴직금 구조를 최적화합니다.\n\n"
    "【핵심 법령 기준】\n"
    "- 임원 급여: 정관·주총 결의 한도 내 손금산입 (법인세법 §43)\n"
    "- 임원 퇴직금: 정관 또는 주총 결의 필수 (법인세법 시행령 §44)\n"
    "- 퇴직금 손금한도: 최종 3년 평균급여 × 1/10 × 근속연수 (법인세법 시행령 §44②)\n"
    "- 초과 퇴직금: 손금불산입 → 배당 또는 상여처분\n"
    "- 배당소득: 2000만 이하 분리과세 14% / 초과 종합과세 (금융소득종합과세)\n"
    "- 근로소득: 근로소득공제 후 종합소득세 6~45%\n"
    "- 퇴직소득세: 근속연수공제 + 환산급여공제 후 세율 적용 (퇴직소득세 별도 계산)\n"
    "- 2026년 귀속 법인세율: 2억↓10% / 2억~200억20% / 200억~3000억22% / 3000억↑25%\n\n"
    "【최적화 3가지 축】\n"
    "1. 급여 최적화: 누진세 최소화 구간 설계, 4대보험 부담 고려\n"
    "2. 배당 최적화: 금융소득종합과세 임계점 관리 (연 2000만)\n"
    "3. 퇴직금 최적화: 손금한도 최대 활용, 퇴직소득세 유리성 활용\n\n"
    "【4자 이해관계 교차분석 필수】\n"
    "- 법인: 급여·퇴직금 손금산입 극대화 → 법인세 절감\n"
    "- 주주(오너): 개인 가처분소득 극대화, 누진세 최소화\n"
    "- 과세관청: 임원 과다급여 부당행위계산부인 (법인세법 §52), 퇴직금 한도 초과 불인정\n"
    "- 금융기관: 급여·배당 구조가 신용등급·대출심사에 미치는 영향\n\n"
    "【목표】\n"
    "임원의 현재 급여·법인 순이익·근속연수를 입력받아\n"
    "급여·배당·퇴직금 최적 믹스를 시뮬레이션하고\n"
    "법인+개인 합산 세부담 최소화 방안과\n"
    "단계별 실행 계획을 제시한다.\n"
    "수치 계산 오류 0건, 법령 조문 명시, 4자 이해관계 반영 필수."
)


class ExecutivePayAgent(BaseAgent):
    name = "ExecutivePayAgent"
    role = "임원보수 최적화 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_retirement_pay_limit",
                "description": "임원 퇴직금 손금산입 한도 계산 (법인세법 시행령 §44②)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "avg_salary_3y": {
                            "type": "number",
                            "description": "최종 3년 평균 연봉 (원)",
                        },
                        "years_of_service": {
                            "type": "number",
                            "description": "근속연수 (년)",
                        },
                        "actual_retirement_pay": {
                            "type": "number",
                            "description": "실제 지급 예정 퇴직금 (원)",
                        },
                    },
                    "required": ["avg_salary_3y", "years_of_service", "actual_retirement_pay"],
                },
            },
            {
                "name": "calc_retirement_income_tax",
                "description": "퇴직소득세 계산 (소득세법 §48~55)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "retirement_pay": {
                            "type": "number",
                            "description": "퇴직금 총액 (원)",
                        },
                        "years_of_service": {
                            "type": "number",
                            "description": "근속연수 (년)",
                        },
                    },
                    "required": ["retirement_pay", "years_of_service"],
                },
            },
            {
                "name": "optimize_pay_mix",
                "description": "급여·배당·퇴직금 최적 믹스 시뮬레이션",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "corp_net_income": {
                            "type": "number",
                            "description": "법인 세전 순이익 (원)",
                        },
                        "current_salary": {
                            "type": "number",
                            "description": "현재 임원 연봉 (원)",
                        },
                        "years_of_service": {
                            "type": "number",
                            "description": "근속연수 (년)",
                        },
                        "share_ratio": {
                            "type": "number",
                            "description": "임원 지분율 (0~1)",
                        },
                        "retained_earnings": {
                            "type": "number",
                            "description": "이익잉여금 (원)",
                        },
                        "other_income": {
                            "type": "number",
                            "description": "기타 종합소득 (원, 기본값 0)",
                        },
                    },
                    "required": ["corp_net_income", "current_salary", "years_of_service"],
                },
            },
            {
                "name": "design_retirement_pay_plan",
                "description": "퇴직금 지급 계획 및 임원 보수 규정 설계 가이드",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "current_salary": {
                            "type": "number",
                            "description": "현재 임원 연봉 (원)",
                        },
                        "years_of_service": {
                            "type": "number",
                            "description": "현재 근속연수 (년)",
                        },
                        "planned_retirement_year": {
                            "type": "integer",
                            "description": "예정 퇴직 연도 (예: 2035)",
                        },
                        "salary_increase_rate": {
                            "type": "number",
                            "description": "연평균 급여 인상률 (0~1, 예: 0.05 = 5%)",
                        },
                    },
                    "required": ["current_salary", "years_of_service", "planned_retirement_year"],
                },
            },
        ]

    # ──────────────────────────────────────────────────────────────────────
    # 세율 계산 유틸
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _corp_tax(taxable: float) -> float:
        """2026년 귀속 법인세 (지방소득세 10% 포함)."""
        if taxable <= 0:
            return 0.0
        if taxable <= 200_000_000:
            base = taxable * 0.10
        elif taxable <= 20_000_000_000:
            base = 200_000_000 * 0.10 + (taxable - 200_000_000) * 0.20
        elif taxable <= 300_000_000_000:
            base = (
                200_000_000 * 0.10
                + (20_000_000_000 - 200_000_000) * 0.20
                + (taxable - 20_000_000_000) * 0.22
            )
        else:
            base = (
                200_000_000 * 0.10
                + (20_000_000_000 - 200_000_000) * 0.20
                + (300_000_000_000 - 20_000_000_000) * 0.22
                + (taxable - 300_000_000_000) * 0.25
            )
        return base * 1.1

    @staticmethod
    def _income_tax(gross: float) -> float:
        """종합소득세 (지방소득세 10% 포함)."""
        if gross <= 0:
            return 0.0
        BRACKETS = [
            (14_000_000, 0.06, 0),
            (50_000_000, 0.15, 1_260_000),
            (88_000_000, 0.24, 5_760_000),
            (150_000_000, 0.35, 15_440_000),
            (300_000_000, 0.38, 19_940_000),
            (500_000_000, 0.40, 25_940_000),
            (1_000_000_000, 0.42, 35_940_000),
            (float("inf"), 0.45, 65_940_000),
        ]
        for limit, rate, deduction in BRACKETS:
            if gross <= limit:
                return (gross * rate - deduction) * 1.1
        return (gross * 0.45 - 65_940_000) * 1.1

    @staticmethod
    def _earned_income_deduction(salary: float) -> float:
        """근로소득공제 (소득세법 §47)."""
        if salary <= 5_000_000:
            return salary * 0.70
        elif salary <= 15_000_000:
            return 3_500_000 + (salary - 5_000_000) * 0.40
        elif salary <= 45_000_000:
            return 7_500_000 + (salary - 15_000_000) * 0.15
        elif salary <= 100_000_000:
            return 12_000_000 + (salary - 45_000_000) * 0.05
        else:
            return 14_750_000

    @staticmethod
    def _years_of_service_deduction(years: float) -> float:
        """근속연수공제 (소득세법 §48)."""
        y = int(years)
        if y <= 5:
            return y * 300_000
        elif y <= 10:
            return 1_500_000 + (y - 5) * 500_000
        elif y <= 20:
            return 4_000_000 + (y - 10) * 800_000
        else:
            return 12_000_000 + (y - 20) * 1_200_000

    def _retirement_income_tax(self, retirement_pay: float, years: float) -> dict:
        """퇴직소득세 계산."""
        yos_deduction = self._years_of_service_deduction(years)
        retirement_income = max(0, retirement_pay - yos_deduction)

        # 환산급여 = (퇴직소득 - 근속연수공제) / 근속연수 × 12
        if years > 0:
            converted_salary = retirement_income / years * 12
        else:
            converted_salary = 0

        # 환산급여공제
        if converted_salary <= 8_000_000:
            converted_deduction = converted_salary * 1.0
        elif converted_salary <= 70_000_000:
            converted_deduction = 8_000_000 + (converted_salary - 8_000_000) * 0.60
        elif converted_salary <= 120_000_000:
            converted_deduction = 45_200_000 + (converted_salary - 70_000_000) * 0.55
        elif converted_salary <= 300_000_000:
            converted_deduction = 72_700_000 + (converted_salary - 120_000_000) * 0.45
        else:
            converted_deduction = 153_700_000 + (converted_salary - 300_000_000) * 0.35

        taxable_converted = max(0, converted_salary - converted_deduction)

        # 환산산출세액 (일반 소득세율 적용)
        converted_tax = self._income_tax(taxable_converted) / 1.1  # 지방소득세 제외 후 재계산
        # 퇴직소득 산출세액 = 환산산출세액 / 12 × 근속연수
        retirement_tax_base = converted_tax / 12 * years
        retirement_tax = retirement_tax_base * 1.1  # 지방소득세 포함

        return {
            "퇴직금총액": f"{retirement_pay:,.0f}원",
            "근속연수공제": f"{yos_deduction:,.0f}원 ({int(years)}년)",
            "퇴직소득": f"{retirement_income:,.0f}원",
            "환산급여": f"{converted_salary:,.0f}원",
            "환산급여공제": f"{converted_deduction:,.0f}원",
            "퇴직소득세(지방포함)": f"{retirement_tax:,.0f}원",
            "실효세율": f"{(retirement_tax / retirement_pay * 100) if retirement_pay > 0 else 0:.1f}%",
            "조문": "소득세법 §48(근속연수공제), §49(환산급여공제), §55(세율)",
        }

    # ──────────────────────────────────────────────────────────────────────
    # 툴 핸들러
    # ──────────────────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "calc_retirement_pay_limit":
            return self._calc_retirement_pay_limit(**tool_input)
        elif tool_name == "calc_retirement_income_tax":
            return self._retirement_income_tax(**tool_input)
        elif tool_name == "optimize_pay_mix":
            return self._optimize_pay_mix(**tool_input)
        elif tool_name == "design_retirement_pay_plan":
            return self._design_retirement_pay_plan(**tool_input)
        return {"error": f"알 수 없는 툴: {tool_name}"}

    def _calc_retirement_pay_limit(
        self,
        avg_salary_3y: float,
        years_of_service: float,
        actual_retirement_pay: float,
    ) -> dict:
        """퇴직금 손금산입 한도 계산."""
        # 법인세법 시행령 §44②: 1/10 × 근속연수 × 최종3년 평균급여
        tax_limit = avg_salary_3y * (1 / 10) * years_of_service
        excess = max(0, actual_retirement_pay - tax_limit)
        excess_corp_tax = excess  # 손금불산입 → 익금 환원 없이 법인세 과세표준 증가

        status = "적정" if excess == 0 else "한도 초과"

        return {
            "조문": "법인세법 시행령 §44② (임원 퇴직금 손금산입 한도)",
            "산식": "최종 3년 평균급여 × 1/10 × 근속연수",
            "최종3년_평균급여": f"{avg_salary_3y:,.0f}원",
            "근속연수": f"{years_of_service:.1f}년",
            "손금산입_한도": f"{tax_limit:,.0f}원",
            "실제_지급예정": f"{actual_retirement_pay:,.0f}원",
            "한도_초과액": f"{excess:,.0f}원",
            "초과액_처분": "손금불산입 → 배당 또는 상여 처분" if excess > 0 else "해당 없음",
            "상태": status,
            "절세_전략": (
                "한도 내 최대 지급 + 퇴직금 지급규정 정관·주총 결의로 사전 확정 필요. "
                "임원 임기 중 중간정산 활용으로 근속연수 초기화 후 재기산 가능."
                if excess == 0
                else f"초과액 {excess:,.0f}원 손금불산입 리스크. 급여 수준 조정 또는 지급 시기 분산 검토 필요."
            ),
        }

    def _optimize_pay_mix(
        self,
        corp_net_income: float,
        current_salary: float,
        years_of_service: float,
        share_ratio: float = 1.0,
        retained_earnings: float = 0,
        other_income: float = 0,
    ) -> dict:
        """급여·배당·퇴직금 최적 믹스 시뮬레이션."""

        scenarios = {}

        # ──── 현재 구조 ────
        ei_deduction = self._earned_income_deduction(current_salary)
        gross = current_salary - ei_deduction + other_income
        personal_tax_now = self._income_tax(gross)
        corp_tax_now = self._corp_tax(max(0, corp_net_income - current_salary))
        total_now = personal_tax_now + corp_tax_now
        scenarios["현재구조"] = {
            "연봉": f"{current_salary:,.0f}원",
            "배당": "0원",
            "개인소득세": f"{personal_tax_now:,.0f}원",
            "법인세": f"{corp_tax_now:,.0f}원",
            "합산세부담": f"{total_now:,.0f}원",
        }

        # ──── 급여 최적화 (45% 구간 직전) ────
        # 5억 이하에서 급여 세부담 최적점 탐색
        optimal_salary = min(current_salary, 500_000_000)
        # 500만~5억 구간에서 법인 손금산입 효과와 개인 세부담 크로스 포인트 탐색
        best_salary = current_salary
        best_total = total_now
        for s in range(50_000_000, 500_000_000, 10_000_000):
            ei = self._earned_income_deduction(s)
            p_tax = self._income_tax(s - ei + other_income)
            c_tax = self._corp_tax(max(0, corp_net_income - s))
            total = p_tax + c_tax
            if total < best_total:
                best_total = total
                best_salary = s

        ei_opt = self._earned_income_deduction(best_salary)
        p_tax_opt = self._income_tax(best_salary - ei_opt + other_income)
        c_tax_opt = self._corp_tax(max(0, corp_net_income - best_salary))
        scenarios["급여최적화"] = {
            "연봉": f"{best_salary:,.0f}원",
            "배당": "0원",
            "개인소득세": f"{p_tax_opt:,.0f}원",
            "법인세": f"{c_tax_opt:,.0f}원",
            "합산세부담": f"{best_total:,.0f}원",
            "현재대비_절감": f"{total_now - best_total:,.0f}원",
        }

        # ──── 급여 + 배당 믹스 (배당 2000만 한도) ────
        div_limit = 20_000_000
        salary_mix = best_salary
        corp_profit_after_salary = max(0, corp_net_income - salary_mix)
        dividend_corp_tax = self._corp_tax(corp_profit_after_salary)
        # 배당은 세후 이익잉여금에서 (단순화: 법인세 차감 후 배당 가능)
        available_for_div = corp_profit_after_salary - dividend_corp_tax
        actual_div = min(div_limit, available_for_div * share_ratio)
        div_tax = actual_div * 0.154  # 14% + 지방 10%
        ei_mix = self._earned_income_deduction(salary_mix)
        p_tax_mix = self._income_tax(salary_mix - ei_mix + other_income)
        total_mix = p_tax_mix + div_tax + dividend_corp_tax
        scenarios["급여+배당믹스(배당2000만)"] = {
            "연봉": f"{salary_mix:,.0f}원",
            "배당": f"{actual_div:,.0f}원",
            "개인소득세(급여분)": f"{p_tax_mix:,.0f}원",
            "배당소득세(14%+지방)": f"{div_tax:,.0f}원",
            "법인세": f"{dividend_corp_tax:,.0f}원",
            "합산세부담": f"{total_mix:,.0f}원",
            "현재대비_절감": f"{total_now - total_mix:,.0f}원",
            "주의": "배당 2000만 초과 시 금융소득종합과세 전환",
        }

        # 최적 시나리오 선택
        scenario_costs = {
            k: float(v["합산세부담"].replace(",", "").replace("원", ""))
            for k, v in scenarios.items()
        }
        best_scenario = min(scenario_costs, key=lambda k: scenario_costs[k])

        return {
            "법인_세전순이익": f"{corp_net_income:,.0f}원",
            "현재_임원연봉": f"{current_salary:,.0f}원",
            "시나리오_비교": scenarios,
            "추천_시나리오": best_scenario,
            "추천_근거": "법인+개인 합산 세부담 최소화 기준",
            "퇴직금_전략": (
                f"근속연수 {years_of_service:.0f}년 기준 퇴직금 손금한도: "
                f"{current_salary * (1/10) * years_of_service:,.0f}원. "
                "퇴직금을 최대 한도까지 설계하면 퇴직소득세 유리(저세율) 효과로 추가 절세 가능."
            ),
        }

    def _design_retirement_pay_plan(
        self,
        current_salary: float,
        years_of_service: float,
        planned_retirement_year: int,
        salary_increase_rate: float = 0.03,
    ) -> dict:
        """퇴직금 지급 계획 설계."""
        from datetime import datetime

        current_year = datetime.now().year
        remaining_years = planned_retirement_year - current_year

        # 예상 최종 3년 평균 급여 (인상률 적용)
        final_salary = current_salary * ((1 + salary_increase_rate) ** remaining_years)
        avg_salary_3y = (
            final_salary * (1 / (1 + salary_increase_rate))
            + final_salary
            + final_salary * (1 + salary_increase_rate)
        ) / 3

        total_years = years_of_service + remaining_years
        tax_limit = avg_salary_3y * (1 / 10) * total_years

        # 퇴직소득세 계산
        ret_tax_info = self._retirement_income_tax(tax_limit, total_years)

        return {
            "현재_연봉": f"{current_salary:,.0f}원",
            "현재_근속연수": f"{years_of_service:.0f}년",
            "퇴직_예정_연도": planned_retirement_year,
            "잔여_근무기간": f"{remaining_years}년",
            "연평균_급여_인상률": f"{salary_increase_rate*100:.1f}%",
            "퇴직_시점_예상_연봉": f"{final_salary:,.0f}원",
            "최종3년_평균급여(추정)": f"{avg_salary_3y:,.0f}원",
            "총_근속연수": f"{total_years:.0f}년",
            "손금산입_한도(퇴직금)": f"{tax_limit:,.0f}원",
            "퇴직소득세_계산": ret_tax_info,
            "실행_권고사항": [
                "현재 시점에서 임원 보수 지급규정 정관에 명시 (주총 특별결의)",
                "퇴직금 지급배수 규정 마련 (예: 1배수 = 1년치 평균급여)",
                "중간정산 활용 검토 (근속연수 초기화 효과)",
                "퇴직연금(DC형) 도입으로 퇴직금 분산 적립 — 법인 비용 선인식",
                "5년마다 보수 지급규정 검토·갱신",
            ],
            "조문": "법인세법 시행령 §44② (퇴직금 손금한도), 소득세법 §48~55 (퇴직소득세)",
        }

    # ──────────────────────────────────────────────────────────────────────
    # 공개 인터페이스
    # ──────────────────────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        """임원보수 최적화 분석 메인 인터페이스."""
        corp_income = company_data.get("corp_net_income", 0)
        current_salary = company_data.get("ceo_annual_salary", 0)
        years = company_data.get("years_of_service", 10)
        share_ratio = company_data.get("share_ratio", 1.0)
        retained = company_data.get("retained_earnings", 0)
        retirement_year = company_data.get("planned_retirement_year", 2035)

        query = (
            f"【임원보수 최적화 분석 요청】\n"
            f"- 법인 세전순이익: {corp_income:,.0f}원\n"
            f"- 대표이사 현재 연봉: {current_salary:,.0f}원\n"
            f"- 근속연수: {years}년\n"
            f"- 대표이사 지분율: {share_ratio*100:.1f}%\n"
            f"- 이익잉여금: {retained:,.0f}원\n"
            f"- 퇴직 예정 연도: {retirement_year}년\n\n"
            "1. 임원 퇴직금 손금산입 한도를 계산하고,\n"
            "2. 급여·배당·퇴직금 최적 믹스를 시뮬레이션하며,\n"
            "3. 퇴직금 지급 계획과 임원 보수 규정 설계 방안을 제시하십시오.\n"
            "4자 이해관계(법인/주주/과세관청/금융기관) 관점을 모두 포함하십시오."
        )
        return self.run(query, reset=True)

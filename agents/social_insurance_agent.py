"""
SocialInsuranceAgent: 4대보험 최적화 전담 에이전트

근거 법령:
  - 국민연금법 제88조 (보험료율 9%)
  - 건강보험법 제69조 (보험료율 7.09%, 2024~2026년 동결)
  - 장기요양보험법 제8조 (건보료 × 12.95%)
  - 고용보험법 제49조의2 (실업급여 1.8% 노사각 0.9%)
  - 산재보험법 제13조 (업종별 차등 / 사업주 전액 부담)

주요 기능:
  - 급여 수준별 4대보험 부담액 자동 계산
  - 법인 부담 vs. 직원 부담 분리 명시
  - 임원보수 vs. 급여 구조 최적화 (4대보험 절감 관점)
  - 두루누리 사회보험료 지원 적격성 검토 (10인 미만 사업장)
  - 일용직·파트타임 고용 시 절감 효과 분석
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 4대보험 및 사회보험료 최적화 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 국민연금·건강보험·장기요양·고용보험·산재보험 정확한 요율 적용\n"
    "- 임원 vs. 직원 급여 구조별 4대보험 부담 비교\n"
    "- 두루누리 지원: 월 270만 원 미만 근로자 / 10인 미만 사업장\n"
    "- 일용직·단시간 근로자 활용 시 보험료 절감 구조\n"
    "- 건강보험 정산(연말 보수총액 신고) 사전 대비\n"
    "- 임원 보수를 급여 대신 배당으로 전환 시 4대보험 효과 분석\n\n"
    "【분석 관점】\n"
    "- 법인: 4대보험 사용자 부담 최소화 / 손금 인정 범위 확인\n"
    "- 오너: 실수령액 극대화 / 노후 연금 수급 전략\n"
    "- 과세관청: 보수총액 신고 정확성 / 허위신고 리스크\n"
    "- 금융기관: 인건비 구조의 지속가능성\n\n"
    "【목표】\n"
    "법적 의무를 100% 준수하면서 사업주·근로자 양측의 실부담을 최소화한다."
)

# ── 2026년 4대보험 요율 ──────────────────────────────────────────────────
RATES = {
    "국민연금": {
        "total": 0.09,
        "employer": 0.045,
        "employee": 0.045,
        "상한월보수": 6_170_000,   # 2025년 기준 (2026년 미변경 가정)
        "하한월보수": 390_000,
    },
    "건강보험": {
        "total": 0.0709,
        "employer": 0.03545,
        "employee": 0.03545,
        "장기요양배율": 0.1295,    # 건보료 × 12.95%
    },
    "고용보험_실업급여": {
        "total": 0.018,
        "employer": 0.009,
        "employee": 0.009,
    },
    "고용보험_고용안정": {
        # 사업주만 부담 / 상시근로자 규모별
        "150인미만": 0.0025,
        "150인이상_우선지원": 0.0045,
        "150인이상": 0.0065,
        "1000인이상": 0.0085,
    },
    "산재보험": {
        # 업종별 상이 / 전액 사업주 부담
        "제조업": 0.0100,
        "건설업": 0.0363,
        "도소매업": 0.0072,
        "음식숙박업": 0.0111,
        "정보통신업": 0.0062,
        "운수업": 0.0098,
        "기타": 0.0085,
    },
}

# 두루누리 지원 기준 (2026년 기준, 10인 미만 사업장 / 신규가입자)
DURU_THRESHOLD = 2_700_000      # 월 270만 원 미만
DURU_SUPPORT_RATE = 0.80        # 80% 지원 (고용보험·국민연금 사업주 부담분)


class SocialInsuranceAgent(BaseAgent):
    name = "SocialInsuranceAgent"
    role = "4대보험 최적화 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_insurance",
                "description": (
                    "월 보수 기준 4대보험 전체 계산.\n"
                    "국민연금·건강보험·장기요양·고용보험·산재보험의\n"
                    "사업주·근로자 부담액 및 합계를 반환한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "monthly_salary": {"type": "number", "description": "월 보수액 (원)"},
                        "industry": {
                            "type": "string",
                            "description": "업종 (산재보험율 적용)",
                            "enum": list(RATES["산재보험"].keys()),
                        },
                        "employee_count": {"type": "integer", "description": "상시 근로자 수 (고용안정보험료율 결정)"},
                        "is_priority_support": {
                            "type": "boolean",
                            "description": "우선지원대상기업 여부",
                        },
                    },
                    "required": ["monthly_salary"],
                },
            },
            {
                "name": "check_duru_support",
                "description": (
                    "두루누리 사회보험료 지원 적격성 및 지원 예상액 계산.\n"
                    "10인 미만 사업장 + 월 270만 원 미만 근로자 대상."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employee_count": {"type": "integer", "description": "상시 근로자 수"},
                        "monthly_salary": {"type": "number", "description": "해당 근로자 월 보수액 (원)"},
                        "is_new_insured": {
                            "type": "boolean",
                            "description": "신규 가입 여부 (기존 가입자 지원 제외)",
                        },
                    },
                    "required": ["employee_count", "monthly_salary", "is_new_insured"],
                },
            },
            {
                "name": "compare_salary_vs_dividend",
                "description": (
                    "임원 보수를 급여 vs. 배당으로 지급할 때\n"
                    "4대보험·소득세·법인세 통합 효과를 비교한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "annual_amount": {"type": "number", "description": "연간 지급 금액 (원)"},
                        "marginal_income_tax_rate": {
                            "type": "number",
                            "description": "한계소득세율 (0~0.45)",
                        },
                        "corp_tax_rate": {
                            "type": "number",
                            "description": "법인세율 (0~0.25, 예: 0.20)",
                        },
                        "industry": {
                            "type": "string",
                            "description": "업종 (산재보험율용)",
                        },
                    },
                    "required": ["annual_amount", "marginal_income_tax_rate", "corp_tax_rate"],
                },
            },
        ]

    # ── 툴 구현 ────────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_insurance":
            return self._calc_insurance(**tool_input)
        if tool_name == "check_duru_support":
            return self._check_duru_support(**tool_input)
        if tool_name == "compare_salary_vs_dividend":
            return self._compare_salary_vs_dividend(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _calc_insurance(
        self,
        monthly_salary: float,
        industry: str = "기타",
        employee_count: int = 5,
        is_priority_support: bool = True,
    ) -> dict:
        result = {}

        # 국민연금 (상한 적용)
        nps_base = min(monthly_salary, RATES["국민연금"]["상한월보수"])
        nps_base = max(nps_base, RATES["국민연금"]["하한월보수"])
        nps_emp = round(nps_base * RATES["국민연금"]["employer"])
        nps_ee = round(nps_base * RATES["국민연금"]["employee"])
        result["국민연금"] = {"사업주": nps_emp, "근로자": nps_ee, "합계": nps_emp + nps_ee}

        # 건강보험
        hi_emp = round(monthly_salary * RATES["건강보험"]["employer"])
        hi_ee = round(monthly_salary * RATES["건강보험"]["employee"])
        lci_emp = round(hi_emp * RATES["건강보험"]["장기요양배율"])
        lci_ee = round(hi_ee * RATES["건강보험"]["장기요양배율"])
        result["건강보험"] = {"사업주": hi_emp, "근로자": hi_ee, "합계": hi_emp + hi_ee}
        result["장기요양보험"] = {"사업주": lci_emp, "근로자": lci_ee, "합계": lci_emp + lci_ee}

        # 고용보험 실업급여
        ei_emp = round(monthly_salary * RATES["고용보험_실업급여"]["employer"])
        ei_ee = round(monthly_salary * RATES["고용보험_실업급여"]["employee"])
        result["고용보험_실업급여"] = {"사업주": ei_emp, "근로자": ei_ee, "합계": ei_emp + ei_ee}

        # 고용안정보험
        if employee_count < 150:
            gs_rate = RATES["고용보험_고용안정"]["150인미만"]
        elif is_priority_support:
            gs_rate = RATES["고용보험_고용안정"]["150인이상_우선지원"]
        elif employee_count < 1000:
            gs_rate = RATES["고용보험_고용안정"]["150인이상"]
        else:
            gs_rate = RATES["고용보험_고용안정"]["1000인이상"]
        gs_emp = round(monthly_salary * gs_rate)
        result["고용안정보험"] = {"사업주": gs_emp, "근로자": 0, "합계": gs_emp}

        # 산재보험 (사업주 전액)
        wc_rate = RATES["산재보험"].get(industry, RATES["산재보험"]["기타"])
        wc_emp = round(monthly_salary * wc_rate)
        result["산재보험"] = {"사업주": wc_emp, "근로자": 0, "합계": wc_emp}

        # 총합
        total_emp = sum(v["사업주"] for v in result.values())
        total_ee = sum(v["근로자"] for v in result.values())
        result["합계"] = {
            "사업주": total_emp,
            "근로자": total_ee,
            "총합계": total_emp + total_ee,
            "사업주_월보수대비(%)": round(total_emp / monthly_salary * 100, 2) if monthly_salary else 0,
        }
        result["월보수"] = round(monthly_salary)
        result["산재보험_업종"] = industry
        return result

    def _check_duru_support(
        self,
        employee_count: int,
        monthly_salary: float,
        is_new_insured: bool,
    ) -> dict:
        eligible = (
            employee_count < 10
            and monthly_salary < DURU_THRESHOLD
            and is_new_insured
        )

        if not eligible:
            reasons = []
            if employee_count >= 10:
                reasons.append(f"상시근로자 {employee_count}인 (기준: 10인 미만)")
            if monthly_salary >= DURU_THRESHOLD:
                reasons.append(f"월보수 {monthly_salary:,.0f}원 (기준: 270만 원 미만)")
            if not is_new_insured:
                reasons.append("기존 가입자 (신규 가입자만 지원)")
            return {"지원대상": False, "사유": reasons}

        ins = self._calc_insurance(monthly_salary)
        nps_support = round(ins["국민연금"]["사업주"] * DURU_SUPPORT_RATE)
        ei_support = round(ins["고용보험_실업급여"]["사업주"] * DURU_SUPPORT_RATE)
        monthly_support = nps_support + ei_support
        annual_support = monthly_support * 12

        return {
            "지원대상": True,
            "지원율": f"{DURU_SUPPORT_RATE*100:.0f}%",
            "월_국민연금_지원": nps_support,
            "월_고용보험_지원": ei_support,
            "월_지원합계": monthly_support,
            "연간_지원합계": annual_support,
            "법령근거": "고용보험 및 산업재해보상보험의 보험료징수 등에 관한 법률 §48의3",
        }

    def _compare_salary_vs_dividend(
        self,
        annual_amount: float,
        marginal_income_tax_rate: float,
        corp_tax_rate: float,
        industry: str = "기타",
    ) -> dict:
        monthly = annual_amount / 12

        # 급여 방식
        ins = self._calc_insurance(monthly, industry=industry)
        emp_ins_annual = ins["합계"]["사업주"] * 12
        ee_ins_annual = ins["합계"]["근로자"] * 12
        corp_deduction = annual_amount + emp_ins_annual          # 법인 손금
        corp_tax_saving = corp_deduction * corp_tax_rate         # 법인세 절감
        income_tax_salary = annual_amount * marginal_income_tax_rate  # 개인 소득세
        net_salary = annual_amount - ee_ins_annual - income_tax_salary

        # 배당 방식 (배당가산세율 14% 분리과세 또는 종합과세)
        # 법인세 먼저 납부 후 배당: 법인세 차감 후 배당 재원
        after_corp_tax = annual_amount * (1 - corp_tax_rate)
        # 배당소득세 (14% 원천징수 / 종합과세 시 한계세율)
        div_tax_rate_low = 0.154   # 14% + 지방세 10%
        div_tax = min(after_corp_tax * marginal_income_tax_rate, after_corp_tax * div_tax_rate_low)
        net_dividend = after_corp_tax - div_tax

        # 비교
        return {
            "연간지급액": round(annual_amount),
            "급여방식": {
                "법인_4대보험부담": round(emp_ins_annual),
                "법인_손금합계": round(corp_deduction),
                "법인세_절감": round(corp_tax_saving),
                "개인_4대보험부담": round(ee_ins_annual),
                "개인_소득세": round(income_tax_salary),
                "개인_실수령액": round(net_salary),
            },
            "배당방식": {
                "법인세_납부": round(annual_amount * corp_tax_rate),
                "배당재원": round(after_corp_tax),
                "배당소득세": round(div_tax),
                "개인_실수령액": round(net_dividend),
            },
            "실수령액_차이": round(net_salary - net_dividend),
            "유리한_방식": "급여" if net_salary >= net_dividend else "배당",
            "주의사항": "임원 보수는 정관·주총결의로 지급 한도 설정 필수 / 배당은 미처분이익잉여금 존재 전제",
        }

    # ── analyze() 인터페이스 ───────────────────────────────────────────────

    def analyze(self, company_data: dict[str, Any]) -> str:
        avg_salary = company_data.get("avg_monthly_salary", 0)
        emp_count = company_data.get("employee_count", 10)
        industry = company_data.get("industry", "기타")

        lines = ["[4대보험 최적화 분석 결과]"]

        if avg_salary:
            ins = self._calc_insurance(avg_salary, industry=industry, employee_count=emp_count)
            total = ins["합계"]
            lines.append(f"\n▶ 1인당 4대보험 (월 {avg_salary:,.0f}원 기준)")
            lines.append(f"  사업주 부담: {total['사업주']:,.0f}원 ({total['사업주_월보수대비(%)']:.1f}%)")
            lines.append(f"  근로자 부담: {total['근로자']:,.0f}원")
            lines.append(f"  전체 직원 연간 사업주 부담: {total['사업주'] * emp_count * 12:,.0f}원")

            if emp_count < 10:
                duru = self._check_duru_support(emp_count, avg_salary, True)
                if duru["지원대상"]:
                    lines.append(f"\n▶ 두루누리 지원 적격 — 월 {duru['월_지원합계']:,.0f}원 절감 가능")
        else:
            lines.append("  급여 데이터 부족 — avg_monthly_salary 입력 필요")

        return "\n".join(lines)

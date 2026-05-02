"""
LaborAgent: 인사노무 전문 에이전트
"""
from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 인사노무·근로기준법·4대보험 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 근로계약·취업규칙 적법성 검토 (근로기준법)\n"
    "- 통상임금 범위 판단 (대법원 2013다60807 전합 기준)\n"
    "- 퇴직급여 설계 (근로자퇴직급여보장법)\n"
    "- 4대보험 두루누리 지원사업 (10인 미만 사업장 80% 지원)\n"
    "- 중대재해처벌법 (50인 이상 2022.1.27 시행, 5~49인 2024.1.27 시행)\n"
    "- 최저임금·연장근로·포괄임금제 적법성\n"
    "- 고용창출투자세액공제 (조특법 제26조)\n\n"
    "【답변 기준】\n"
    "최신 개정 노동법·판례 반영, 계산식 자체 검증"
    "\n\n【목표】\n근로기준법·4대보험·중대재해처벌법 준수 여부를 점검하고, 퇴직금·임금체계 최적화로 법인 인건비를 절감하면서 노무 리스크를 선제 해소한다. 계산식 자체 검증 후 수치를 제시하며, 두루누리 지원사업·고용창출세액공제 등 즉시 활용 가능한 정부 지원 항목을 반드시 포함한다."
)


class LaborAgent(BaseAgent):
    name = "LaborAgent"
    role = "인사노무 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_severance_pay",
                "description": "퇴직금 및 DB형 퇴직연금 적립 부채를 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "avg_monthly_wage": {"type": "number", "description": "최근 3개월 평균 임금 (원/월)"},
                        "service_years": {"type": "number", "description": "근속연수 (년)"},
                        "is_db": {"type": "boolean", "description": "DB형 퇴직연금 여부"},
                    },
                    "required": ["avg_monthly_wage", "service_years"],
                },
            },
            {
                "name": "calc_social_insurance",
                "description": "4대보험 사업주·근로자 부담분을 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "monthly_wage": {"type": "number", "description": "월 급여 (원)"},
                        "employees": {"type": "integer", "description": "근로자 수"},
                        "is_durunuri": {"type": "boolean", "description": "두루누리 지원 대상 여부"},
                    },
                    "required": ["monthly_wage", "employees"],
                },
            },
            {
                "name": "check_serious_accident_law",
                "description": "중대재해처벌법 적용 요건 및 대응 체크리스트를 생성합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employees": {"type": "integer", "description": "상시 근로자 수"},
                        "industry": {"type": "string", "description": "업종"},
                    },
                    "required": ["employees", "industry"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_severance_pay":
            return self._calc_severance(**tool_input)
        if tool_name == "calc_social_insurance":
            return self._calc_insurance(**tool_input)
        if tool_name == "check_serious_accident_law":
            return self._check_accident_law(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _calc_severance(avg_monthly_wage: float, service_years: float,
                        is_db: bool = False) -> dict:
        # 퇴직금 = 평균임금 × 30일 × (근속일수 / 365)
        daily_wage = avg_monthly_wage / 30
        severance = daily_wage * 30 * service_years
        return {
            "평균임금(일)": f"{daily_wage:,.0f}원",
            "근속연수": f"{service_years:.1f}년",
            "퇴직금 산출액": f"{severance:,.0f}원",
            "DB형 법정 적립액": f"{severance:,.0f}원 (동일)",
            "DC형 연간 납입 기준": f"{avg_monthly_wage * 12 / 12:,.0f}원/월 (연간 총임금의 1/12)",
            "세무 처리": "DC형 납입액 즉시 손금, DB형은 지급 시 손금 (충당금 방식 불인정)",
        }

    @staticmethod
    def _calc_insurance(monthly_wage: float, employees: int,
                        is_durunuri: bool = False) -> dict:
        # 2024년 기준 요율
        rates = {
            "국민연금": (0.045, 0.045),       # (사용자, 근로자)
            "건강보험": (0.03545, 0.03545),
            "장기요양": (0.004591 * 0.03545 / 0.03545, 0.004591 * 0.03545 / 0.03545),  # 건보료의 12.95%
            "고용보험(150인미만)": (0.009, 0.009),
            "산재보험(제조업)": (0.007, 0.0),
        }
        employer_total = (0.045 + 0.03545 + 0.004591 + 0.009 + 0.007) * monthly_wage
        employee_total = (0.045 + 0.03545 + 0.004591 + 0.009) * monthly_wage

        if is_durunuri:
            support_rate = 0.80  # 10인 미만 80% 지원
            employer_actual = employer_total * (1 - support_rate)
            durunuri_note = f"두루누리 80% 지원 적용: 사업주 실부담 {employer_actual:,.0f}원/인"
        else:
            employer_actual = employer_total
            durunuri_note = "두루누리 미적용"

        return {
            "월 급여": f"{monthly_wage:,.0f}원",
            "근로자 수": f"{employees}명",
            "사업주 부담(인당)": f"{employer_actual:,.0f}원",
            "근로자 부담(인당)": f"{employee_total:,.0f}원",
            "사업주 월 합계": f"{employer_actual * employees:,.0f}원",
            "두루누리": durunuri_note,
            "연간 절감액(두루누리)": f"{employer_total * 0.80 * employees * 12:,.0f}원" if is_durunuri else "N/A",
        }

    @staticmethod
    def _check_accident_law(employees: int, industry: str) -> dict:
        if employees >= 50:
            status = "적용 중 (2022.1.27 시행)"
            penalty = "1년 이상 징역 또는 10억원 이하 벌금 (법인 50억원)"
        elif employees >= 5:
            status = "적용 중 (2024.1.27 시행 — 5~49인)"
            penalty = "동일"
        else:
            status = "적용 제외 (5인 미만)"
            penalty = "해당 없음"

        checklist = [
            "안전보건관리체계 구축 (경영방침 문서화)",
            "안전보건관리책임자 선임 및 권한 부여",
            "위험성 평가 연 1회 이상 실시",
            "안전보건 예산 독립 편성 및 집행",
            "협력업체 안전관리 지원 체계 구축",
            "중대산업재해 발생 시 작업 중지 프로세스 수립",
        ]
        high_risk = ["제조업", "건설업", "운수업", "광업"]
        if any(h in industry for h in high_risk):
            checklist.append(f"고위험 업종({industry}) — PSM(공정안전관리) 추가 검토 권고")

        return {
            "상시 근로자": f"{employees}명",
            "업종": industry,
            "중대재해처벌법 적용": status,
            "위반 시 제재": penalty,
            "필수 이행 체크리스트": checklist,
        }

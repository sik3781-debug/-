"""
HRDAgent: 인적자원개발·교육훈련 지원금 전담 에이전트

근거 법령 및 제도:
  - 고용보험법 §29~§33 (사업주 직업능력개발훈련 지원)
  - 근로자직업능력개발법 (직업훈련 체계)
  - 국가기술자격법 (기술자격 취득 지원)
  - 고용노동부 사업주훈련지원금 고시
  - 내일채움공제 (중소기업진흥공단 운영)
  - 청년내일채움공제 (고용노동부)

주요 기능:
  - 사업주 직업훈련비 지원금 계산 (훈련시간·인원·단가)
  - 내일채움공제·청년내일채움공제 납입·적립 시뮬레이션
  - 훈련 유형별 환급률 비교 (집체·현장·원격·혼합)
  - 우선지원대상기업(우선대상기업) 요건 판단
  - 훈련 계획 수립 → 지원금 극대화 전략
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 인적자원개발(HRD) 및 교육훈련 지원금 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 사업주훈련지원금: 집체·현장·원격·혼합 훈련 환급 계산\n"
    "- 우선지원대상기업 지원 단가 적용 (일반기업 대비 최대 3배)\n"
    "- 내일채움공제: 5년 적립 후 3,000만 원 수령 구조\n"
    "- 청년내일채움공제: 2년형(1,200만)/3년형(3,000만) 선택\n"
    "- 직업능력개발훈련 의무 (고용보험 피보험자 수 기준)\n"
    "- 훈련비 지원 한도 계산 (연간 보험료 납부액 기준)\n\n"
    "【분석 관점】\n"
    "- 법인: 훈련비 전액 손금산입 + 정부 지원금 환급\n"
    "- 오너: 핵심인재 장기근속 유도 / 이직률 감소\n"
    "- 과세관청: 훈련비 지원금 수령액 익금 여부 (비과세)\n"
    "- 금융기관: 인적자본 투자 = 기업 성장성 평가 긍정\n\n"
    "【목표】\n"
    "정부 지원 훈련 제도를 최대한 활용하여\n"
    "인재 개발 비용을 최소화하고 핵심 인재를 장기 보유한다."
)

# 우선지원대상기업 기준 (고용보험법 시행령 §12)
PRIORITY_SUPPORT_THRESHOLD = {
    "제조업": 500,
    "광업·건설업·운수업": 300,
    "기타": 100,
}

# 훈련 유형별 지원 단가 (원/시간, 우선지원대상기업 기준, 2025년)
TRAINING_UNIT_COST = {
    "집체훈련": 5_000,    # 강사 파견 / 집합 교육
    "현장훈련(OJT)": 3_000,
    "원격훈련": 2_000,
    "혼합훈련": 4_000,
}


class HRDAgent(BaseAgent):
    name = "HRDAgent"
    role = "인적자원개발·교육훈련 지원금 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_training_subsidy",
                "description": (
                    "사업주 직업훈련비 지원금 계산.\n"
                    "훈련 유형·시간·인원·우선지원 여부를 기반으로\n"
                    "연간 환급 가능 금액과 신청 절차를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employees": {"type": "integer", "description": "상시 근로자 수"},
                        "industry": {"type": "string", "description": "업종"},
                        "training_type": {
                            "type": "string",
                            "description": "훈련 유형",
                            "enum": list(TRAINING_UNIT_COST.keys()),
                        },
                        "training_hours": {"type": "number", "description": "총 훈련 시간 (시간)"},
                        "trainees": {"type": "integer", "description": "훈련 참여 인원 (명)"},
                        "annual_insurance_premium": {
                            "type": "number",
                            "description": "연간 고용보험료 납부액 (원)",
                        },
                    },
                    "required": ["employees", "industry", "training_type", "training_hours", "trainees"],
                },
            },
            {
                "name": "simulate_naeil_fund",
                "description": (
                    "내일채움공제·청년내일채움공제 적립 시뮬레이션.\n"
                    "기업·근로자·정부 납입액과 만기 수령액을\n"
                    "연도별로 산출하고 세제 혜택을 분석한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "fund_type": {
                            "type": "string",
                            "description": "공제 유형",
                            "enum": ["내일채움공제_5년", "청년내일채움공제_2년", "청년내일채움공제_3년"],
                        },
                        "employee_monthly": {
                            "type": "number",
                            "description": "근로자 월 납입액 (원)",
                        },
                        "employer_monthly": {
                            "type": "number",
                            "description": "기업 월 납입액 (원)",
                        },
                        "employees_enrolled": {
                            "type": "integer",
                            "description": "가입 근로자 수 (명)",
                        },
                    },
                    "required": ["fund_type", "employee_monthly", "employer_monthly"],
                },
            },
            {
                "name": "plan_hrd_strategy",
                "description": (
                    "연간 HRD 지원금 극대화 전략 수립.\n"
                    "훈련 계획·공제 가입·자격취득 지원을 패키지화하여\n"
                    "인재개발 비용 대비 효과를 최대화하는 계획을 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employees": {"type": "integer", "description": "상시 근로자 수"},
                        "industry": {"type": "string", "description": "업종"},
                        "annual_training_budget": {"type": "number", "description": "연간 훈련 예산 (원)"},
                        "key_skills_needed": {
                            "type": "array",
                            "description": "필요 역량·기술 목록",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["employees", "industry", "annual_training_budget"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_training_subsidy":
            return self._calc_training_subsidy(**tool_input)
        if tool_name == "simulate_naeil_fund":
            return self._simulate_naeil_fund(**tool_input)
        if tool_name == "plan_hrd_strategy":
            return self._plan_hrd_strategy(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _calc_training_subsidy(
        self,
        employees: int,
        industry: str,
        training_type: str,
        training_hours: float,
        trainees: int,
        annual_insurance_premium: float = 0,
    ) -> dict:
        # 우선지원대상기업 여부 판단
        threshold = PRIORITY_SUPPORT_THRESHOLD.get(industry, PRIORITY_SUPPORT_THRESHOLD["기타"])
        is_priority = employees <= threshold

        unit_cost = TRAINING_UNIT_COST.get(training_type, 3_000)
        if not is_priority:
            unit_cost = round(unit_cost * 0.5)  # 일반기업 50% 수준

        subsidy_per_person = unit_cost * training_hours
        total_subsidy = subsidy_per_person * trainees

        # 연간 한도: 보험료 납부액의 240% (우선) / 100% (일반)
        limit_rate = 2.4 if is_priority else 1.0
        annual_limit = annual_insurance_premium * limit_rate if annual_insurance_premium else None

        capped = False
        if annual_limit and total_subsidy > annual_limit:
            total_subsidy = annual_limit
            capped = True

        return {
            "우선지원대상기업": "✅ 해당" if is_priority else "❌ 해당 없음",
            "훈련유형": training_type,
            "지원단가": f"{unit_cost:,}원/시간",
            "훈련시간": f"{training_hours}시간",
            "훈련인원": f"{trainees}명",
            "인당_지원액": round(subsidy_per_person),
            "총_지원금": round(total_subsidy),
            "연간_한도적용": "✅ 한도 소진" if capped else "한도 내",
            "신청절차": [
                "훈련 실시 전 HRD-Net(www.hrd.go.kr) 훈련과정 등록",
                "훈련 실시 후 30일 이내 지원금 신청",
                "근로자 출석부·훈련일지 첨부 필수",
            ],
            "법령근거": "고용보험법 §29 / 근로자직업능력개발법 §20",
        }

    def _simulate_naeil_fund(
        self,
        fund_type: str,
        employee_monthly: float,
        employer_monthly: float,
        employees_enrolled: int = 1,
    ) -> dict:
        # 공제 유형별 정부 지원 구조
        fund_config = {
            "내일채움공제_5년": {"months": 60, "gov_total": 0, "description": "5년 만기, 기업·근로자 납입"},
            "청년내일채움공제_2년": {"months": 24, "gov_total": 4_000_000, "description": "2년 만기, 정부 400만 지원"},
            "청년내일채움공제_3년": {"months": 36, "gov_total": 16_000_000, "description": "3년 만기, 정부 1,600만 지원"},
        }
        config = fund_config.get(fund_type, fund_config["내일채움공제_5년"])
        months = config["months"]
        gov_total = config["gov_total"]

        emp_total = employee_monthly * months
        employer_total = employer_monthly * months
        # 이자(이율 약 2.5% 가정)
        avg_balance = (emp_total + employer_total + gov_total) / 2
        interest = avg_balance * 0.025 * (months / 12)
        total_payout = emp_total + employer_total + gov_total + round(interest)

        annual_employer_cost = employer_monthly * 12 * employees_enrolled
        tax_deduction = annual_employer_cost  # 전액 손금산입

        return {
            "공제유형": fund_type,
            "적립기간": f"{months}개월 ({months//12}년)",
            "근로자_총납입": round(emp_total),
            "기업_총납입": round(employer_total),
            "정부_지원금": round(gov_total),
            "예상_이자": round(interest),
            "만기_수령액_추정": round(total_payout),
            "기업_연간_비용": round(annual_employer_cost),
            "손금산입_가능액": round(tax_deduction),
            "핵심효과": f"근로자 {months//12}년 장기근속 유도 / 이직 시 기업납입금 환급",
            "세제혜택": "기업 납입금 전액 손금산입 (법인세법 시행령 §44)",
        }

    def _plan_hrd_strategy(
        self,
        employees: int,
        industry: str,
        annual_training_budget: float,
        key_skills_needed: list[str] | None = None,
    ) -> dict:
        key_skills_needed = key_skills_needed or ["직무 역량", "안전교육", "리더십"]

        threshold = PRIORITY_SUPPORT_THRESHOLD.get(industry, PRIORITY_SUPPORT_THRESHOLD["기타"])
        is_priority = employees <= threshold

        # 훈련 지원금 추정
        max_subsidy_per_person = 5_000 * 40  # 집체훈련 40시간
        if not is_priority:
            max_subsidy_per_person = round(max_subsidy_per_person * 0.5)
        estimated_subsidy = max_subsidy_per_person * employees

        plan = [
            {
                "프로그램": "집체훈련 (핵심 직무역량)",
                "대상": "전 직원",
                "연간시간": "20~40시간",
                "예상지원금": f"{max_subsidy_per_person * employees:,.0f}원",
                "방법": "HRD-Net 등록 훈련기관 활용",
            },
            {
                "프로그램": "내일채움공제 가입",
                "대상": "핵심인재 3~5년차",
                "월납입": "기업 20만/근로자 10만",
                "효과": "5년 후 근로자 3,000만 원 수령 / 이직 억제",
                "기업비용": "월 20만 × 인원 (손금산입)",
            },
            {
                "프로그램": "국가기술자격 취득 지원",
                "대상": "생산·기술직",
                "지원내용": "응시료·교재비 지원 / 취득 시 인센티브",
                "효과": "기술 수준 공식 인증 / 입찰 가점",
            },
        ]

        return {
            "임직원수": employees,
            "우선지원대상기업": "✅" if is_priority else "❌",
            "연간_훈련예산": round(annual_training_budget),
            "예상_정부지원금": round(estimated_subsidy),
            "순_부담_비용": round(max(0, annual_training_budget - estimated_subsidy)),
            "핵심_역량": key_skills_needed,
            "HRD_실행계획": plan,
            "기대효과": [
                f"정부 지원금 {estimated_subsidy:,.0f}원 환급",
                "인당 역량 향상 → 생산성 10~15% 개선 (중소기업 평균)",
                "내일채움공제 가입 시 5년 이직률 30~40% 감소",
            ],
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        emp = company_data.get("employees", 0)
        ind = company_data.get("industry", "제조업")
        budget = company_data.get("training_budget", emp * 500_000)
        lines = ["[HRD·교육훈련 지원금 분석 결과]"]
        result = self._plan_hrd_strategy(emp, ind, budget)
        lines.append(f"\n▶ 예상 정부 지원금: {result['예상_정부지원금']:,.0f}원")
        lines.append(f"  우선지원대상기업: {result['우선지원대상기업']}")
        return "\n".join(lines)

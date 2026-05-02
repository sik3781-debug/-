"""
ProvisionalPaymentAgent: 가지급금 전담 에이전트
- 해소 방법 5가지별 세부담 비교 시뮬레이션
- 4.6% 인정이자 계산 (법인세법 시행규칙 §43)
- 2026년 귀속 법인세율 적용 (10%/20%/22%/25%)
"""

from __future__ import annotations

import json
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 가지급금 해소 전문 컨설턴트입니다.\n"
    "법인세법·소득세법·상속세및증여세법 최신 개정 기준으로\n"
    "가지급금 해소 전략과 세부담 시뮬레이션을 제공합니다.\n\n"
    "【핵심 법령 기준】\n"
    "- 인정이자율: 4.6% (법인세법 시행규칙 §43, 2025년 귀속)\n"
    "- 가지급금 인정이자 미수취 시: 익금산입 + 대표이사 상여처분 (소득세 원천징수)\n"
    "- 2026년 귀속 법인세율: 2억↓10% / 2억~200억20% / 200억~3000억22% / 3000억↑25%\n"
    "- 배당소득세: 2000만 이하 분리과세 14% / 초과분 종합과세\n"
    "- 근로소득세: 종합소득세율 6~45% (2026 귀속)\n\n"
    "【가지급금 해소 5가지 방법】\n"
    "1. 급여증액법: 대표이사 급여 인상하여 법인에 상환\n"
    "2. 배당지급법: 이익잉여금 배당으로 상환\n"
    "3. 직접상환법: 대표이사 개인자산 매각·현금 상환\n"
    "4. DES(Debt-Equity Swap): 채무를 주식으로 전환\n"
    "5. 자본감소법: 유상감자로 환급 후 상환\n\n"
    "【4자 이해관계 교차분석 필수】\n"
    "- 법인: 손금산입 극대화, 법인세 절감, 세무조사 리스크 최소화\n"
    "- 주주(오너): 개인 가처분소득 극대화, 누진세 회피\n"
    "- 과세관청: 인정이자 과세, 상여처분, 부당행위계산부인 적용 가능성\n"
    "- 금융기관: 가지급금이 재무비율에 미치는 영향 (부채비율 왜곡)\n\n"
    "【목표】\n"
    "가지급금 잔액·법인 순이익·대표이사 종합소득 수준을 입력받아\n"
    "5가지 해소 방법별 법인세+소득세 합산 세부담을 시뮬레이션하고\n"
    "최적 해소 전략과 단계별 실행 로드맵을 제시한다.\n"
    "수치 계산 오류 0건, 법령 조문 명시, 4자 이해관계 반영 필수."
)


class ProvisionalPaymentAgent(BaseAgent):
    name = "ProvisionalPaymentAgent"
    role = "가지급금 해소 전략 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_deemed_interest",
                "description": "가지급금 인정이자 계산 및 세무리스크 분석",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "balance": {
                            "type": "number",
                            "description": "가지급금 잔액 (원)",
                        },
                        "months": {
                            "type": "integer",
                            "description": "해당 사업연도 보유 개월수",
                        },
                        "corp_income": {
                            "type": "number",
                            "description": "법인 과세표준 (원, 인정이자 익금산입 후)",
                        },
                    },
                    "required": ["balance", "months", "corp_income"],
                },
            },
            {
                "name": "compare_resolution_methods",
                "description": "가지급금 해소 5가지 방법별 세부담 비교 시뮬레이션",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "balance": {
                            "type": "number",
                            "description": "가지급금 잔액 (원)",
                        },
                        "corp_net_income": {
                            "type": "number",
                            "description": "법인 순이익 (세전, 원)",
                        },
                        "ceo_annual_salary": {
                            "type": "number",
                            "description": "대표이사 현재 연봉 (원)",
                        },
                        "ceo_other_income": {
                            "type": "number",
                            "description": "대표이사 기타 종합소득 (원, 기본값 0)",
                        },
                        "retained_earnings": {
                            "type": "number",
                            "description": "법인 이익잉여금 (원)",
                        },
                        "share_ratio": {
                            "type": "number",
                            "description": "대표이사 지분율 (0~1, 예: 0.7 = 70%)",
                        },
                    },
                    "required": [
                        "balance",
                        "corp_net_income",
                        "ceo_annual_salary",
                    ],
                },
            },
            {
                "name": "build_resolution_roadmap",
                "description": "최적 해소 방법 선택 후 단계별 실행 로드맵 작성",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "method": {
                            "type": "string",
                            "enum": ["salary", "dividend", "direct", "des", "capital_reduction"],
                            "description": "해소 방법 (salary=급여증액, dividend=배당, direct=직접상환, des=DES, capital_reduction=자본감소)",
                        },
                        "balance": {
                            "type": "number",
                            "description": "가지급금 잔액 (원)",
                        },
                        "annual_repayment": {
                            "type": "number",
                            "description": "연간 상환 계획액 (원)",
                        },
                    },
                    "required": ["method", "balance", "annual_repayment"],
                },
            },
        ]

    # ──────────────────────────────────────────────────────────────────────
    # 세율 계산 유틸
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _corp_tax(taxable: float) -> float:
        """2026년 귀속 법인세 계산 (지방소득세 10% 포함)."""
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
        return base * 1.1  # 지방소득세 10%

    @staticmethod
    def _income_tax(gross: float) -> float:
        """종합소득세 계산 (지방소득세 10% 포함, 2026 귀속 기준)."""
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
        """근로소득공제 계산 (소득세법 §47)."""
        if salary <= 5_000_000:
            return salary * 0.70
        elif salary <= 15_000_000:
            return 3_500_000 + (salary - 5_000_000) * 0.40
        elif salary <= 45_000_000:
            return 7_500_000 + (salary - 15_000_000) * 0.15
        elif salary <= 100_000_000:
            return 12_000_000 + (salary - 45_000_000) * 0.05
        else:
            return 14_750_000  # 한도

    # ──────────────────────────────────────────────────────────────────────
    # 툴 핸들러
    # ──────────────────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "calc_deemed_interest":
            return self._calc_deemed_interest(**tool_input)
        elif tool_name == "compare_resolution_methods":
            return self._compare_resolution_methods(**tool_input)
        elif tool_name == "build_resolution_roadmap":
            return self._build_resolution_roadmap(**tool_input)
        return {"error": f"알 수 없는 툴: {tool_name}"}

    def _calc_deemed_interest(
        self, balance: float, months: int, corp_income: float
    ) -> dict:
        """인정이자 계산."""
        rate = 0.046  # 법인세법 시행규칙 §43
        deemed_interest = balance * rate * (months / 12)

        # 법인 추가 법인세 (인정이자 익금산입)
        corp_tax_before = self._corp_tax(corp_income)
        corp_tax_after = self._corp_tax(corp_income + deemed_interest)
        corp_tax_increase = corp_tax_after - corp_tax_before

        # 대표이사 상여처분 → 소득세 추가 부담
        # (단순화: 상여 = 인정이자 전액)
        return {
            "인정이자율": "4.6% (법인세법 시행규칙 §43)",
            "가지급금_잔액": f"{balance:,.0f}원",
            "보유_개월": months,
            "인정이자_연간": f"{deemed_interest:,.0f}원",
            "법인_추가_법인세": f"{corp_tax_increase:,.0f}원",
            "대표이사_상여처분_금액": f"{deemed_interest:,.0f}원",
            "리스크_요약": (
                "인정이자를 미수취 시: 법인 익금산입 + 대표이사 상여처분 이중 과세. "
                "세무조사 적출 시 소득세 원천징수 미이행 가산세(3%) 추가 부과 가능."
            ),
            "조문_근거": "법인세법 §52(부당행위계산부인), 법인세법 시행규칙 §43, 소득세법 §20",
        }

    def _compare_resolution_methods(
        self,
        balance: float,
        corp_net_income: float,
        ceo_annual_salary: float,
        ceo_other_income: float = 0,
        retained_earnings: float = 0,
        share_ratio: float = 1.0,
    ) -> dict:
        """5가지 해소 방법 세부담 비교."""
        results = {}

        # ① 급여증액법
        # 법인: 급여 증액분 손금산입 → 법인세 절감
        # 개인: 증가 급여 → 근로소득세 부담
        salary_increase = balance  # 1년간 상환 가정 (단순화)
        corp_save = self._corp_tax(corp_net_income) - self._corp_tax(
            max(0, corp_net_income - salary_increase)
        )
        old_ei = self._earned_income_deduction(ceo_annual_salary)
        new_salary = ceo_annual_salary + salary_increase
        new_ei = self._earned_income_deduction(new_salary)
        old_gross = ceo_annual_salary - old_ei + ceo_other_income
        new_gross = new_salary - new_ei + ceo_other_income
        personal_tax_increase = self._income_tax(new_gross) - self._income_tax(old_gross)
        net_cost_salary = personal_tax_increase - corp_save
        results["①급여증액법"] = {
            "법인_세금절감": f"{corp_save:,.0f}원",
            "개인_추가_소득세": f"{personal_tax_increase:,.0f}원",
            "순세부담": f"{net_cost_salary:,.0f}원",
            "장점": "손금산입으로 법인세 절감 동시 가능",
            "단점": "누진세율 구간에 따라 개인 세부담 급증, 건강보험료 증가",
            "적합조건": "대표이사 종합소득이 낮은 경우 (5억 이하)",
        }

        # ② 배당지급법
        # 이익잉여금 배당 → 배당소득세 (14% 분리 or 종합과세)
        dividend_amount = min(balance, retained_earnings * share_ratio) if retained_earnings else balance * 0.5
        if dividend_amount <= 20_000_000:
            div_tax = dividend_amount * 0.154  # 14% + 지방 10%
        else:
            # 초과분 종합과세 (그로스업 미적용 단순화)
            div_tax = 20_000_000 * 0.154 + self._income_tax(
                ceo_other_income + ceo_annual_salary + dividend_amount - 20_000_000
            ) - self._income_tax(ceo_other_income + ceo_annual_salary)
        results["②배당지급법"] = {
            "배당_가능액": f"{dividend_amount:,.0f}원",
            "배당소득세": f"{div_tax:,.0f}원",
            "순세부담": f"{div_tax:,.0f}원",
            "장점": "이익잉여금 활용, 손금불산입이지만 배당세율 낮을 수 있음",
            "단점": "이익잉여금 부족 시 불가, 법인 현금 유출",
            "적합조건": "이익잉여금 충분하고 대표이사 금융소득 2000만 이하인 경우",
        }

        # ③ 직접상환법
        # 개인자산 처분 → 양도소득세 발생 가능 (자산 종류에 따라 다름)
        results["③직접상환법"] = {
            "상환액": f"{balance:,.0f}원",
            "세금부담": "0원 (현금 상환 시) / 양도소득세 별도 (부동산·주식 처분 시)",
            "순세부담": "자산 종류에 따라 상이",
            "장점": "가장 단순·확실한 해소 방법, 추가 세금 없음 (현금 상환 시)",
            "단점": "대표이사 개인 유동자산 필요",
            "적합조건": "대표이사 개인 현금·예금 충분한 경우",
        }

        # ④ DES (Debt-Equity Swap)
        # 가지급금 채무를 주식으로 전환 → 지분희석 but 세금 없음
        # 상증세법 §39 저가발행 주의 필요
        results["④DES(채무주식전환)"] = {
            "전환_주식_가치": f"{balance:,.0f}원",
            "세금부담": "0원 (공정가액 발행 시)",
            "주의사항": "발행가액 < 비상장주식 평가액 시 저가발행 증여세 과세 위험 (상증세법 §39)",
            "장점": "법인 현금 유출 없이 부채 해소",
            "단점": "지분 희석, 비상장주식 평가 복잡, 주주간 분쟁 가능",
            "적합조건": "법인 순자산 충분하고 지분 희석 문제없는 경우",
        }

        # ⑤ 자본감소법
        # 유상감자 → 대표이사 지분 감자 → 감자대가 수령 후 상환
        # 의제배당 과세 주의
        results["⑤자본감소법"] = {
            "감자대가": f"{balance:,.0f}원",
            "의제배당_과세": "감자대가 - 취득원가 = 의제배당 (배당소득세 과세)",
            "세금부담": "의제배당액 × 배당세율 (실제 취득원가에 따라 상이)",
            "장점": "자본 구조 정리 병행 가능",
            "단점": "절차 복잡 (상법 §343이하 준수), 의제배당 과세, 시간 소요",
            "적합조건": "법인 자본금이 과다하여 자본 구조 조정이 필요한 경우",
        }

        # 최적 방법 추천
        costs = {
            "①급여증액법": net_cost_salary,
            "②배당지급법": div_tax,
            "③직접상환법": 0,
        }
        best = min(costs, key=lambda k: costs[k])

        return {
            "가지급금_잔액": f"{balance:,.0f}원",
            "비교_결과": results,
            "추천_방법": best,
            "추천_근거": "법인+개인 합산 세부담 최소화 기준",
            "공통_주의사항": (
                "가지급금 해소 과정에서 부당행위계산부인(법인세법 §52) 적용 가능성 사전 검토 필수. "
                "해소 후 3년 이내 세무조사 대비 증빙 완비 필요."
            ),
        }

    def _build_resolution_roadmap(
        self, method: str, balance: float, annual_repayment: float
    ) -> dict:
        """단계별 실행 로드맵."""
        years = int(balance / annual_repayment) + (1 if balance % annual_repayment else 0)

        METHOD_MAP = {
            "salary": {
                "명칭": "급여증액법",
                "단계": [
                    "1단계: 임원 보수 한도 주주총회 결의 (상법 §388)",
                    "2단계: 원천징수 이행상황신고서 수정 신고 (필요 시)",
                    "3단계: 급여 증액분 법인 통장 수령 후 가지급금 상환",
                    "4단계: 가지급금 원장 정리 및 증빙 보관",
                    "5단계: 사업연도 종료 후 인정이자 정산",
                ],
                "증빙서류": ["주주총회의사록", "임원보수규정 개정본", "법인 및 개인 통장 이체 내역"],
            },
            "dividend": {
                "명칭": "배당지급법",
                "단계": [
                    "1단계: 재무제표 확정 및 이익잉여금 잔액 확인",
                    "2단계: 이사회 배당 결의 (상법 §462)",
                    "3단계: 주주총회 배당 결의 (정관 위임 여부 확인)",
                    "4단계: 배당소득세 원천징수 (14%) 및 납부",
                    "5단계: 배당금 수령 후 가지급금 즉시 상환",
                ],
                "증빙서류": ["이사회의사록", "주주총회의사록", "배당금 지급 내역", "원천징수영수증"],
            },
            "direct": {
                "명칭": "직접상환법",
                "단계": [
                    "1단계: 대표이사 개인 자산 현황 파악",
                    "2단계: 개인 계좌 → 법인 계좌 이체 (가지급금 상환 적요 기재)",
                    "3단계: 가지급금 원장 감소 처리",
                    "4단계: 이자 정산 및 원천징수 납부",
                    "5단계: 세무신고서 가지급금 잔액 '0' 반영",
                ],
                "증빙서류": ["이체확인증", "가지급금 원장 사본", "차용증(기존 작성분)"],
            },
            "des": {
                "명칭": "DES(채무주식전환)",
                "단계": [
                    "1단계: 비상장주식 공정가액 평가 (상증세법 §54 보충적 평가)",
                    "2단계: 이사회 신주발행 결의 (상법 §416)",
                    "3단계: 주주 우선배정 또는 제3자 배정 절차 이행",
                    "4단계: 주금납입 → 현물출자(채권) 방식으로 가지급금 상계",
                    "5단계: 법인등기부 변경 등기",
                    "6단계: 저가발행 여부 검토 → 문제 없으면 종결",
                ],
                "증빙서류": ["비상장주식 평가서", "이사회의사록", "주금납입영수증", "법인등기사항증명서"],
            },
            "capital_reduction": {
                "명칭": "자본감소법",
                "단계": [
                    "1단계: 주주총회 특별결의 (출석 주주 2/3 이상, 상법 §438)",
                    "2단계: 채권자 이의제출 공고 (상법 §439, 1개월 이상)",
                    "3단계: 감자대가 지급 → 의제배당 계산",
                    "4단계: 배당소득세 원천징수 및 납부",
                    "5단계: 지급받은 감자대가로 가지급금 상환",
                    "6단계: 자본금 변경 법인등기",
                ],
                "증빙서류": ["주주총회의사록", "채권자 공고문", "의제배당계산서", "원천징수영수증"],
            },
        }

        info = METHOD_MAP.get(method, {})
        return {
            "해소_방법": info.get("명칭", method),
            "가지급금_잔액": f"{balance:,.0f}원",
            "연간_상환_계획": f"{annual_repayment:,.0f}원",
            "예상_완료_기간": f"{years}년",
            "실행_단계": info.get("단계", []),
            "필요_증빙서류": info.get("증빙서류", []),
            "완료_후_확인사항": [
                "법인 장부상 가지급금 계정 '0' 확인",
                "인정이자 정산 완료 확인",
                "세무신고서 반영 여부 확인 (법인세·원천세)",
                "세무조사 대비 증빙 파일 5년 보관",
            ],
        }

    # ──────────────────────────────────────────────────────────────────────
    # 공개 인터페이스
    # ──────────────────────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        """가지급금 분석 메인 인터페이스."""
        balance = company_data.get("provisional_payment_balance", 0)
        corp_income = company_data.get("corp_net_income", 0)
        ceo_salary = company_data.get("ceo_annual_salary", 0)
        retained = company_data.get("retained_earnings", 0)
        share_ratio = company_data.get("share_ratio", 1.0)

        query = (
            f"【가지급금 해소 전략 분석 요청】\n"
            f"- 가지급금 잔액: {balance:,.0f}원\n"
            f"- 법인 세전순이익: {corp_income:,.0f}원\n"
            f"- 대표이사 현재 연봉: {ceo_salary:,.0f}원\n"
            f"- 이익잉여금: {retained:,.0f}원\n"
            f"- 대표이사 지분율: {share_ratio*100:.1f}%\n\n"
            "1. 인정이자 계산 및 현재 세무리스크를 분석하고,\n"
            "2. 5가지 해소 방법별 세부담을 비교하며,\n"
            "3. 최적 해소 방법으로 단계별 실행 로드맵을 제시하십시오.\n"
            "4자 이해관계(법인/주주/과세관청/금융기관) 관점을 모두 포함하십시오."
        )
        return self.run(query, reset=True)

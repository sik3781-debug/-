"""
NomineeStockAgent: 차명주식 전담 에이전트
- 명의신탁 증여의제 과세 계산 (상증세법 §45의2)
- 차명주식 해소 단계별 로드맵
- 상여처분·세무리스크 분석
"""

from __future__ import annotations

from agents.base_agent import BaseAgent

_SYS = (
    "당신은 차명주식 해소 전문 컨설턴트입니다.\n"
    "상속세및증여세법·법인세법·소득세법 최신 기준으로\n"
    "차명주식 현황 진단과 해소 전략을 제공합니다.\n\n"
    "【핵심 법령 기준】\n"
    "- 명의신탁 증여의제: 상증세법 §45의2 (조세회피 목적 추정 → 증여세 과세)\n"
    "- 명의신탁 해소 시: 원 명의신탁 시점 기준 증여의제 과세 (부과제척기간 10년~15년)\n"
    "- 차명주식 배당 귀속: 실질귀속 원칙 (국세기본법 §14) → 실제 주주에게 귀속\n"
    "- 명의수탁자 처분 시: 횡령죄 성립 가능, 양도소득세는 실질귀속자(명의신탁자)에게 과세\n"
    "- 과점주주 간주취득세: 지방세법 §7⑤ (지분 50% 초과 시 취득세 간주)\n\n"
    "【차명주식 해소 4가지 방법】\n"
    "1. 명의개서법: 명의수탁자 → 실제 주주로 명의 변경\n"
    "2. 증여법: 명의수탁자가 실제 주주에게 증여 (증여세 과세 후 해소)\n"
    "3. 매매법: 명의수탁자 → 실제 주주에게 유상 양도 (양도소득세 주의)\n"
    "4. 자기주식 취득법: 법인이 명의수탁자 지분 매입 후 소각\n\n"
    "【증여의제 과세 요건】\n"
    "- 타인 명의로 주식을 등기한 사실\n"
    "- 조세회피 목적 추정 (반증 가능하나 요건 엄격)\n"
    "- 제척기간: 일반 10년, 사기·기타 부정행위 15년\n\n"
    "【4자 이해관계 교차분석 필수】\n"
    "- 법인: 실제 주주 확정으로 배당·의결권 분쟁 해소, 세무조사 리스크 제거\n"
    "- 주주(오너): 지분 실질화로 가업승계 기반 마련, 증여의제 과세 선제 대응\n"
    "- 과세관청: 명의신탁 증여의제 과세, 양도소득세 탈루 여부 조사\n"
    "- 금융기관: 실제 지배주주 확정으로 신용 평가 정확성 제고\n\n"
    "【목표】\n"
    "차명주식 현황·취득 시기·비상장주식 평가액을 입력받아\n"
    "증여의제 과세 위험을 정량화하고 최적 해소 방법과\n"
    "단계별 실행 로드맵 및 세무 리스크 헷지 방안을 제시한다.\n"
    "수치 계산 오류 0건, 법령 조문 명시, 4자 이해관계 반영 필수."
)


class NomineeStockAgent(BaseAgent):
    name = "NomineeStockAgent"
    role = "차명주식 해소 전략 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_deemed_gift_tax",
                "description": "명의신탁 증여의제 증여세 계산 (상증세법 §45의2)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "stock_value_at_trust": {
                            "type": "number",
                            "description": "명의신탁 당시 주식 평가액 (원)",
                        },
                        "shares": {
                            "type": "integer",
                            "description": "차명주식 주수",
                        },
                        "trust_year": {
                            "type": "integer",
                            "description": "명의신탁 연도 (예: 2010)",
                        },
                        "current_year": {
                            "type": "integer",
                            "description": "현재 연도 (예: 2026)",
                        },
                        "relationship": {
                            "type": "string",
                            "enum": ["spouse", "adult_child", "minor_child", "other_relative", "third_party"],
                            "description": "명의수탁자와의 관계",
                        },
                    },
                    "required": ["stock_value_at_trust", "shares", "trust_year", "current_year", "relationship"],
                },
            },
            {
                "name": "compare_resolution_methods",
                "description": "차명주식 해소 4가지 방법별 세부담 비교",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "current_stock_value": {
                            "type": "number",
                            "description": "현재 주당 평가액 (원)",
                        },
                        "shares": {
                            "type": "integer",
                            "description": "차명주식 주수",
                        },
                        "acquisition_cost": {
                            "type": "number",
                            "description": "명의수탁자 취득원가 (원, 전체)",
                        },
                        "relationship": {
                            "type": "string",
                            "enum": ["spouse", "adult_child", "minor_child", "other_relative", "third_party"],
                            "description": "명의수탁자와의 관계",
                        },
                        "trustee_income": {
                            "type": "number",
                            "description": "명의수탁자 연간 종합소득 (원, 증여세 계산용)",
                        },
                    },
                    "required": ["current_stock_value", "shares", "acquisition_cost", "relationship"],
                },
            },
            {
                "name": "build_resolution_roadmap",
                "description": "차명주식 해소 단계별 실행 로드맵 작성",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "method": {
                            "type": "string",
                            "enum": ["name_transfer", "gift", "sale", "treasury"],
                            "description": "해소 방법 선택",
                        },
                        "shares": {
                            "type": "integer",
                            "description": "차명주식 주수",
                        },
                        "current_stock_value": {
                            "type": "number",
                            "description": "현재 주당 평가액 (원)",
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "해소 긴급도 (세무조사 임박 여부 등)",
                        },
                    },
                    "required": ["method", "shares", "current_stock_value"],
                },
            },
        ]

    # ──────────────────────────────────────────────────────────────────────
    # 세율 계산 유틸
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _gift_tax(taxable: float) -> float:
        """증여세 계산 (상증세법 §26, 지방소득세 없음)."""
        if taxable <= 0:
            return 0.0
        BRACKETS = [
            (100_000_000, 0.10, 0),
            (500_000_000, 0.20, 10_000_000),
            (1_000_000_000, 0.30, 60_000_000),
            (3_000_000_000, 0.40, 160_000_000),
            (float("inf"), 0.50, 460_000_000),
        ]
        for limit, rate, deduction in BRACKETS:
            if taxable <= limit:
                return taxable * rate - deduction
        return taxable * 0.50 - 460_000_000

    @staticmethod
    def _gift_deduction(relationship: str) -> float:
        """증여재산공제 (상증세법 §53)."""
        return {
            "spouse": 600_000_000,
            "adult_child": 50_000_000,
            "minor_child": 20_000_000,
            "other_relative": 10_000_000,
            "third_party": 0,
        }.get(relationship, 0)

    @staticmethod
    def _transfer_tax(gain: float) -> float:
        """비상장주식 양도소득세 (소득세법 §104 중소기업 20%, 지방 포함)."""
        if gain <= 0:
            return 0.0
        # 중소기업 비상장주식: 20% (지방소득세 10% 포함)
        return gain * 0.20 * 1.1

    @staticmethod
    def _prescription_check(trust_year: int, current_year: int) -> dict:
        """부과제척기간 체크."""
        elapsed = current_year - trust_year
        if elapsed >= 15:
            status = "제척기간 도과 (15년 초과) — 과세 불가 (부정행위 기준)"
            risk = "low"
        elif elapsed >= 10:
            status = "일반 제척기간(10년) 도과 — 부정행위(사기 등) 해당 시 15년 적용 가능"
            risk = "medium"
        else:
            status = f"제척기간 진행 중 ({elapsed}년 경과 / 10년 기준)"
            risk = "high"
        return {"경과년수": elapsed, "제척기간_상태": status, "과세_위험도": risk}

    # ──────────────────────────────────────────────────────────────────────
    # 툴 핸들러
    # ──────────────────────────────────────────────────────────────────────

    def handle_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "calc_deemed_gift_tax":
            return self._calc_deemed_gift_tax(**tool_input)
        elif tool_name == "compare_resolution_methods":
            return self._compare_resolution_methods(**tool_input)
        elif tool_name == "build_resolution_roadmap":
            return self._build_resolution_roadmap(**tool_input)
        return {"error": f"알 수 없는 툴: {tool_name}"}

    def _calc_deemed_gift_tax(
        self,
        stock_value_at_trust: float,
        shares: int,
        trust_year: int,
        current_year: int,
        relationship: str,
    ) -> dict:
        """명의신탁 증여의제 과세 계산."""
        total_value = stock_value_at_trust * shares
        deduction = self._gift_deduction(relationship)
        taxable = max(0, total_value - deduction)
        gift_tax = self._gift_tax(taxable)

        # 가산세: 무신고 20% + 납부불성실 0.022%/일 (단순화: 연 8.03%)
        elapsed = current_year - trust_year
        penalty_rate = 0.20  # 무신고가산세
        late_pay_rate = 0.0803  # 납부불성실가산세 연율 (0.022%×365)
        total_penalty = gift_tax * (penalty_rate + late_pay_rate * elapsed)
        total_burden = gift_tax + total_penalty

        prescription = self._prescription_check(trust_year, current_year)

        return {
            "조문": "상증세법 §45의2 (명의신탁 재산의 증여의제)",
            "명의신탁_당시_주식가치": f"{total_value:,.0f}원",
            "증여재산공제": f"{deduction:,.0f}원 ({relationship})",
            "과세표준": f"{taxable:,.0f}원",
            "증여세_본세": f"{gift_tax:,.0f}원",
            "무신고가산세(20%)": f"{gift_tax * 0.20:,.0f}원",
            "납부불성실가산세": f"{gift_tax * late_pay_rate * elapsed:,.0f}원 ({elapsed}년)",
            "합산_세금부담": f"{total_burden:,.0f}원",
            "부과제척기간": prescription,
            "주의사항": (
                "명의신탁 증여의제는 조세회피 목적 추정이므로 반증 책임이 납세자에게 있음. "
                "반증 성공 시 증여세 면제 가능하나 입증 요건 엄격 (대법원 2017두41740 등)."
            ),
        }

    def _compare_resolution_methods(
        self,
        current_stock_value: float,
        shares: int,
        acquisition_cost: float,
        relationship: str,
        trustee_income: float = 0,
    ) -> dict:
        """4가지 해소 방법 세부담 비교."""
        total_current_value = current_stock_value * shares
        deduction = self._gift_deduction(relationship)

        # ① 명의개서법 (실질 주주로 돌리기)
        # 이 경우 증여의제 과세 위험 → 사전 확인 필요
        name_transfer_risk = (
            "원 명의신탁 시점 기준 증여세 과세 가능. "
            "단, 실질귀속 원칙 적용 및 조세회피 목적 없음 입증 시 면제 가능."
        )

        # ② 증여법: 명의수탁자 → 실제 주주에게 증여
        gift_taxable = max(0, total_current_value - deduction)
        gift_tax_amt = self._gift_tax(gift_taxable)

        # ③ 매매법: 양도소득세 계산
        capital_gain = total_current_value - acquisition_cost
        transfer_tax_amt = self._transfer_tax(capital_gain)

        # ④ 자기주식 취득법: 의제배당 계산
        # 의제배당 = 매입가 - 취득원가
        # 법인이 자기주식 취득 → 소각 → 실제 주주에게 귀속
        buyback_price = total_current_value  # 공정가액 가정
        deemed_dividend = max(0, buyback_price - acquisition_cost)
        if deemed_dividend <= 20_000_000:
            treasury_tax = deemed_dividend * 0.154
        else:
            treasury_tax = 20_000_000 * 0.154 + self._gift_tax(deemed_dividend - 20_000_000) * 0.5  # 단순화

        return {
            "차명주식_현재가치": f"{total_current_value:,.0f}원",
            "방법별_세부담_비교": {
                "①명의개서법": {
                    "세금부담": "증여의제 과세 위험 (금액 불확실 — 명의신탁 당시 가치 기준)",
                    "리스크": name_transfer_risk,
                    "장점": "가장 간단한 절차",
                    "단점": "세무리스크 상존, 전문가 법률 검토 필수",
                },
                "②증여법": {
                    "과세표준": f"{gift_taxable:,.0f}원",
                    "증여재산공제": f"{deduction:,.0f}원",
                    "증여세": f"{gift_tax_amt:,.0f}원",
                    "장점": "명확한 세금 납부로 리스크 완전 해소",
                    "단점": f"증여세 {gift_tax_amt:,.0f}원 현금 납부 필요",
                },
                "③매매법": {
                    "양도차익": f"{capital_gain:,.0f}원",
                    "양도소득세(중소기업20%+지방)": f"{transfer_tax_amt:,.0f}원",
                    "장점": "명의수탁자 세부담 명확",
                    "단점": "대금 지급 자금원 소명 필요, 특수관계인 거래 시 시가 적용",
                },
                "④자기주식취득법": {
                    "의제배당": f"{deemed_dividend:,.0f}원",
                    "배당소득세(추정)": f"{treasury_tax:,.0f}원",
                    "장점": "법인이 직접 해소, 지분 소각으로 정리 완결",
                    "단점": "법인 현금 유출, 상법 절차 복잡 (§341이하)",
                },
            },
            "추천_기준": "세금 부담 최소 + 법적 안전성 = ②증여법 또는 ③매매법 우선 검토",
            "공통_주의사항": (
                "차명주식 해소 시 과점주주 간주취득세 주의 (지방세법 §7⑤). "
                "지분 50% 초과 전환 시 부동산 등 자산에 대한 간주취득세 발생 가능."
            ),
        }

    def _build_resolution_roadmap(
        self,
        method: str,
        shares: int,
        current_stock_value: float,
        urgency: str = "medium",
    ) -> dict:
        """단계별 실행 로드맵."""
        total_value = current_stock_value * shares

        METHOD_MAP = {
            "name_transfer": {
                "명칭": "명의개서법",
                "기간": "1~2개월",
                "단계": [
                    "1단계: 법률전문가(세무사·변호사) 검토 — 조세회피 목적 해당 여부 판단",
                    "2단계: 명의신탁 당시 증빙 수집 (차용증·계약서·자금 출처 증명)",
                    "3단계: 실질귀속 원칙 입증 자료 준비 (국세기본법 §14)",
                    "4단계: 주주명부 개서 신청",
                    "5단계: 법인등기부 주주 현황 반영",
                    "6단계: 세무서 신고 검토 (필요 시 수정신고)",
                ],
                "위험도": "high" if urgency == "high" else "medium",
            },
            "gift": {
                "명칭": "증여법",
                "기간": "2~3개월",
                "단계": [
                    "1단계: 비상장주식 평가 (상증세법 §54 보충적 평가법)",
                    "2단계: 증여계약서 작성 (명의수탁자 → 실제 주주)",
                    "3단계: 주주명부 개서 및 법인 주식대장 정리",
                    "4단계: 증여세 신고 (증여일로부터 3개월 이내, 상증세법 §68)",
                    "5단계: 증여세 납부 (분납 또는 연부연납 검토)",
                    "6단계: 증여세 납부 영수증 보관",
                ],
                "위험도": "low",
            },
            "sale": {
                "명칭": "매매법",
                "기간": "2~3개월",
                "단계": [
                    "1단계: 비상장주식 평가 (시가 또는 보충적 평가)",
                    "2단계: 주식매매계약서 작성 (시가 기준 매매가 설정)",
                    "3단계: 대금 이체 및 영수증 확보",
                    "4단계: 주주명부 개서",
                    "5단계: 양도소득세 신고 (양도일이 속하는 달 말일로부터 2개월, 소득세법 §110)",
                    "6단계: 매수자(실제 주주) 취득세 검토 (해당 시)",
                ],
                "위험도": "low",
            },
            "treasury": {
                "명칭": "자기주식취득법",
                "기간": "3~6개월",
                "단계": [
                    "1단계: 이사회 자기주식 취득 결의 (상법 §341)",
                    "2단계: 비상장주식 공정가액 평가",
                    "3단계: 법인 → 명의수탁자에게 매입대금 지급",
                    "4단계: 의제배당 계산 및 원천징수 (14%) 납부",
                    "5단계: 자기주식 소각 이사회 결의 (상법 §343)",
                    "6단계: 법인등기부 자본금 감소 등기",
                ],
                "위험도": "medium",
            },
        }

        info = METHOD_MAP.get(method, {})
        urgency_note = {
            "high": "⚠️ 세무조사 임박 — 즉시 법률전문가 자문 후 진행 필요",
            "medium": "통상 절차대로 진행 가능",
            "low": "여유 있게 최적 타이밍 선택 가능",
        }.get(urgency, "")

        return {
            "해소_방법": info.get("명칭", method),
            "차명주식_총가치": f"{total_value:,.0f}원",
            "예상_소요기간": info.get("기간", "미정"),
            "긴급도": urgency,
            "긴급도_참고": urgency_note,
            "과세_위험도": info.get("위험도", "medium"),
            "실행_단계": info.get("단계", []),
            "완료_후_확인사항": [
                "법인 주주명부 실제 주주 명의로 확정",
                "세금 납부 및 신고 완료 확인",
                "관련 계약서·증빙 5년 이상 보관",
                "과점주주 간주취득세 검토 완료",
                "향후 유사 거래 재발 방지 내부 규정 정비",
            ],
        }

    # ──────────────────────────────────────────────────────────────────────
    # 공개 인터페이스
    # ──────────────────────────────────────────────────────────────────────

    def analyze(self, company_data: dict) -> str:
        """차명주식 분석 메인 인터페이스."""
        nominee_shares = company_data.get("nominee_shares", 0)
        stock_value = company_data.get("stock_value_per_share", 0)
        acquisition_cost = company_data.get("acquisition_cost", 0)
        trust_year = company_data.get("trust_year", 2010)
        relationship = company_data.get("relationship", "third_party")
        total_shares = company_data.get("total_shares", 10000)

        query = (
            f"【차명주식 해소 전략 분석 요청】\n"
            f"- 차명주식 수량: {nominee_shares:,}주 / 총 발행주식: {total_shares:,}주\n"
            f"- 현재 주당 평가액: {stock_value:,.0f}원\n"
            f"- 명의수탁자 취득원가: {acquisition_cost:,.0f}원\n"
            f"- 명의신탁 연도: {trust_year}년\n"
            f"- 명의수탁자 관계: {relationship}\n\n"
            "1. 명의신탁 증여의제 과세 위험을 계산하고,\n"
            "2. 4가지 해소 방법별 세부담을 비교하며,\n"
            "3. 최적 해소 방법으로 단계별 실행 로드맵을 제시하십시오.\n"
            "4자 이해관계(법인/주주/과세관청/금융기관) 관점을 모두 포함하십시오."
        )
        return self.run(query, reset=True)

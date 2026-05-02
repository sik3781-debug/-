"""
SubcontractAgent: 하도급 관리 전담 에이전트

근거 법령:
  - 하도급거래 공정화에 관한 법률 (하도급법) 전반
  - 하도급법 제3조 (서면교부 의무)
  - 하도급법 제13조 (하도급대금 지급 — 60일 이내)
  - 하도급법 제13조의2 (어음할인료·지연이자)
  - 공정거래법 제23조 (불공정거래행위 금지)
  - 대·중소기업 상생협력 촉진에 관한 법률

주요 기능:
  - 하도급 계약 적법성 체크리스트 (서면교부·단가·대금지급 기준)
  - 하도급대금 지급 지연 이자 계산 (하도급법 §13의2)
  - 원사업자 vs. 수급사업자 지위 판단 기준
  - 기술탈취·자료제공요구 리스크 진단
  - 납품단가 조정 신청 절차 및 효과 분석
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 하도급법 및 공정거래 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 하도급법 위반 리스크 진단: 서면교부·단가 후려치기·대금 지연\n"
    "- 하도급대금 지급 지연 이자 계산 (연 15.5% / 하도급법 §13의2)\n"
    "- 원사업자·수급사업자 지위 판단 (매출액 기준)\n"
    "- 납품단가 조정 신청 (원자재비 상승 시 공정위 신청 절차)\n"
    "- 기술자료 제공 요구 거절권 및 비밀유지협약(NDA) 설계\n"
    "- 상생협력 의무 이행: 동반성장지수 관리\n\n"
    "【분석 관점】\n"
    "- 법인(원사업자): 하도급법 과징금·손해배상 리스크 최소화\n"
    "- 법인(수급사업자): 대금 회수 권리 강화 / 단가 조정 청구\n"
    "- 과세관청: 하도급 거래 세금계산서 적정성\n"
    "- 금융기관: 납품채권 담보 (팩토링·외상매출채권담보대출)\n\n"
    "【목표】\n"
    "하도급 거래를 하도급법 100% 준수 구조로 정비하고,\n"
    "수급사업자로서의 법적 권리를 최대한 확보한다."
)

# 하도급대금 지연이자율 (하도급법 §13의2 / 2026년 기준)
DELAY_INTEREST_RATE = 0.155  # 연 15.5%

# 하도급법 적용 기준 (매출액)
SUBCONTRACT_THRESHOLD = {
    "제조·수리": {"원사업자": 3_000_000_000, "수급사업자": 3_000_000_000},
    "건설": {"원사업자": 3_000_000_000, "수급사업자": 3_000_000_000},
    "용역": {"원사업자": 3_000_000_000, "수급사업자": 3_000_000_000},
}

# 하도급대금 법정 지급 기한
PAYMENT_DEADLINE = 60  # 60일 이내 (목적물 수령일 기산)


class SubcontractAgent(BaseAgent):
    name = "SubcontractAgent"
    role = "하도급 관리 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "check_subcontract_compliance",
                "description": (
                    "하도급 계약 적법성 체크리스트 진단.\n"
                    "서면교부·단가 결정·대금 지급·기술탈취 방지 항목별\n"
                    "위반 여부와 리스크 등급을 반환한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "has_written_contract": {"type": "boolean", "description": "서면 계약서 교부 여부"},
                        "payment_days": {"type": "integer", "description": "실제 대금 지급 소요일"},
                        "unit_price_negotiated": {
                            "type": "boolean",
                            "description": "단가 서면 협의 여부 (일방 통보 아닌 협의)",
                        },
                        "has_nda": {"type": "boolean", "description": "기술자료 비밀유지협약 체결 여부"},
                        "payment_method": {
                            "type": "string",
                            "description": "대금 지급 방법",
                            "enum": ["현금", "어음", "외상매출채권담보"],
                        },
                        "transaction_type": {
                            "type": "string",
                            "description": "거래 유형",
                            "enum": ["제조·수리", "건설", "용역"],
                        },
                    },
                    "required": ["has_written_contract", "payment_days", "unit_price_negotiated"],
                },
            },
            {
                "name": "calc_delay_interest",
                "description": (
                    "하도급대금 지급 지연 이자 계산 (하도급법 §13의2).\n"
                    "지연 일수·미지급 금액 기준 법정 이자를 산출하고\n"
                    "공정위 신고 시 과징금 추정액을 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "unpaid_amount": {"type": "number", "description": "미지급 하도급대금 (원)"},
                        "delay_days": {"type": "integer", "description": "지급 지연 일수 (법정 60일 초과분)"},
                        "num_transactions": {
                            "type": "integer",
                            "description": "위반 건수 (과징금 산정용)",
                        },
                    },
                    "required": ["unpaid_amount", "delay_days"],
                },
            },
            {
                "name": "plan_price_adjustment",
                "description": (
                    "납품단가 조정 신청 계획 수립.\n"
                    "원자재비 상승율을 입력받아 조정 신청 요건 충족 여부,\n"
                    "예상 단가 인상률, 공정위 신청 절차를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "material_cost_increase_pct": {
                            "type": "number",
                            "description": "원자재비 상승율 (%, 예: 15)",
                        },
                        "material_cost_ratio": {
                            "type": "number",
                            "description": "납품가격 중 원자재비 비중 (0~1)",
                        },
                        "contract_amount": {"type": "number", "description": "연간 하도급 계약금액 (원)"},
                        "months_since_contract": {
                            "type": "integer",
                            "description": "계약 체결 후 경과 월수",
                        },
                    },
                    "required": ["material_cost_increase_pct", "material_cost_ratio", "contract_amount"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "check_subcontract_compliance":
            return self._check_subcontract_compliance(**tool_input)
        if tool_name == "calc_delay_interest":
            return self._calc_delay_interest(**tool_input)
        if tool_name == "plan_price_adjustment":
            return self._plan_price_adjustment(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _check_subcontract_compliance(
        self,
        has_written_contract: bool,
        payment_days: int,
        unit_price_negotiated: bool,
        has_nda: bool = False,
        payment_method: str = "현금",
        transaction_type: str = "제조·수리",
    ) -> dict:
        issues = []
        risk_level = "🟢 정상"

        if not has_written_contract:
            issues.append({
                "항목": "서면교부 미이행",
                "조항": "하도급법 §3",
                "제재": "과징금 최대 1억 원",
                "등급": "🔴 고위험",
            })
            risk_level = "🔴 고위험"

        if payment_days > PAYMENT_DEADLINE:
            issues.append({
                "항목": f"대금 지급 지연 ({payment_days}일 / 기준 60일)",
                "조항": "하도급법 §13",
                "제재": f"지연이자 연 {DELAY_INTEREST_RATE*100:.1f}% + 과징금",
                "등급": "🔴 고위험",
            })
            risk_level = "🔴 고위험"

        if not unit_price_negotiated:
            issues.append({
                "항목": "단가 일방 결정 (서면 협의 없음)",
                "조항": "하도급법 §3의2",
                "제재": "시정명령·과징금",
                "등급": "🟡 주의",
            })
            if risk_level == "🟢 정상":
                risk_level = "🟡 주의"

        if payment_method == "어음":
            issues.append({
                "항목": "어음 지급 — 어음할인료 수급사업자 전가 금지",
                "조항": "하도급법 §13의2",
                "제재": "어음할인료 지급 의무",
                "등급": "🟡 주의",
            })

        if not has_nda:
            issues.append({
                "항목": "기술자료 비밀유지협약 미체결",
                "조항": "하도급법 §12의3",
                "제재": "기술탈취 시 3배 손해배상",
                "등급": "🟡 주의",
            })

        return {
            "종합_위험등급": risk_level,
            "위반_항목수": len(issues),
            "위반_상세": issues,
            "즉시_조치": (
                "① 서면 계약서 즉시 교부 ② 지급일 60일 이내로 단축 ③ NDA 체결"
                if issues else "현재 하도급법 준수 — 정기 점검 지속"
            ),
        }

    def _calc_delay_interest(
        self,
        unpaid_amount: float,
        delay_days: int,
        num_transactions: int = 1,
    ) -> dict:
        interest = unpaid_amount * DELAY_INTEREST_RATE * delay_days / 365

        # 공정위 과징금 추정 (위반금액의 2배 이내)
        penalty_estimate = unpaid_amount * 0.5 * num_transactions

        return {
            "미지급_하도급대금": round(unpaid_amount),
            "지연_일수": delay_days,
            "법정_이자율": f"연 {DELAY_INTEREST_RATE*100:.1f}%",
            "지연_이자액": round(interest),
            "위반_건수": num_transactions,
            "과징금_추정": round(penalty_estimate),
            "총_노출_금액": round(interest + penalty_estimate),
            "법령근거": "하도급거래 공정화에 관한 법률 §13의2",
            "권고": "즉시 미지급 대금 + 이자 지급 / 공정위 자진신고 시 과징금 감경 가능",
        }

    def _plan_price_adjustment(
        self,
        material_cost_increase_pct: float,
        material_cost_ratio: float,
        contract_amount: float,
        months_since_contract: int = 3,
    ) -> dict:
        # 조정 요건: 원자재비 15% 이상 상승 시 신청 가능 (하도급법 §16의2)
        threshold = 15.0
        eligible = material_cost_increase_pct >= threshold and months_since_contract >= 3

        # 단가 인상 기대액
        price_increase_ratio = material_cost_ratio * (material_cost_increase_pct / 100)
        expected_increase = contract_amount * price_increase_ratio

        return {
            "원자재비_상승율(%)": round(material_cost_increase_pct, 1),
            "신청_요건_충족": eligible,
            "신청_기준": f"원자재비 {threshold:.0f}% 이상 상승 + 계약 후 3개월 경과",
            "경과_월수": months_since_contract,
            "예상_단가_인상율(%)": round(price_increase_ratio * 100, 2),
            "연간_인상_기대금액": round(expected_increase),
            "신청_절차": [
                "① 원자재비 상승 증빙자료 준비 (구매전표·단가표)",
                "② 원사업자에 서면 조정 신청",
                "③ 원사업자 10일 내 미협의 시 — 하도급분쟁조정협의회 신청",
                "④ 공정거래위원회 신고 (과징금·시정명령)",
            ],
            "법령근거": "하도급거래 공정화에 관한 법률 §16의2 (납품단가 조정)",
            "미신청_기회비용": round(expected_increase),
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        has_contract = company_data.get("has_written_subcontract", True)
        payment_days = company_data.get("subcontract_payment_days", 60)
        unpaid = company_data.get("unpaid_subcontract", 0)

        lines = ["[하도급 관리 분석 결과]"]
        check = self._check_subcontract_compliance(has_contract, payment_days, True)
        lines.append(f"\n▶ 하도급 준수 진단: {check['종합_위험등급']}")
        if check["위반_항목수"]:
            lines.append(f"  위반 {check['위반_항목수']}건 — {check['즉시_조치']}")

        if unpaid:
            delay = payment_days - 60 if payment_days > 60 else 0
            if delay:
                interest = self._calc_delay_interest(unpaid, delay)
                lines.append(f"\n▶ 지연이자 노출: {interest['총_노출_금액']:,.0f}원")

        return "\n".join(lines)

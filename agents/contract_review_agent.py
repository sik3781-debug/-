"""
ContractReviewAgent: 계약 검토 전담 에이전트

근거 법령:
  - 민법 제103~104조 (반사회적 법률행위·불공정 행위 무효)
  - 약관의 규제에 관한 법률 (약관규제법)
  - 전자상거래 등에서의 소비자보호에 관한 법률
  - 국가계약법 / 지방계약법 (공공 입찰 계약)
  - 민법 제390조 (채무불이행 손해배상)

주요 기능:
  - 계약서 주요 위험 조항 탐지 (독소 조항·불공정 조항)
  - 손해배상·책임제한·면책 조항 적정성 검토
  - 계약금액·납기·하자보증 표준 조건 비교
  - 계약 해지·해제 사유 및 절차 적정성 분석
  - 공공 입찰 계약 특수 조건 체크리스트
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 계약 검토 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 계약서 독소 조항 탐지: 불공정 손해배상·일방적 해지권·무제한 책임\n"
    "- 약관규제법 위반 조항 무효 판단 (§6~§14)\n"
    "- 공급계약·용역계약·NDA·MOU·투자계약·임대차 계약 유형별 검토\n"
    "- 공공 입찰 계약: 국가계약법·지방계약법 특수 조건\n"
    "- 계약 위반 시 손해배상·지체상금·위약금 산정\n\n"
    "【분석 관점】\n"
    "- 법인: 계약 리스크 최소화 / 손금 처리 적정성\n"
    "- 오너: 개인 연대보증 범위 제한 / 경영권 보호\n"
    "- 과세관청: 계약금액과 세금계산서 일치 여부\n"
    "- 금융기관: 계약채권 담보 가치 / 기성금 지급 조건\n\n"
    "【목표】\n"
    "계약 체결 전 모든 위험 조항을 탐지하여\n"
    "법적 분쟁 가능성을 사전에 차단한다."
)

# 계약 유형별 핵심 체크 항목
CONTRACT_CHECKLIST = {
    "공급계약": ["납품 규격·수량 명시", "대금 지급 조건", "하자보증 기간(1~2년)", "지체상금율(0.1~0.15%/일)", "불가항력 조항"],
    "용역계약": ["업무 범위 명확화", "결과물 소유권", "비밀유지 의무", "중도 해지 조건", "추가 용역 단가"],
    "NDA": ["비밀정보 정의 범위", "유효기간", "위반 시 손해배상", "정보 반환 의무", "예외 사유"],
    "투자계약": ["투자금 사용처 제한", "우선상환권", "희석방지조항", "동반매도청구권(Drag-along)", "선취특권"],
    "임대차": ["임대료 인상 제한", "원상복구 범위", "보증금 반환 조건", "시설 수선 의무", "전대차 허용"],
    "공공입찰": ["지체상금율(1일 0.1%)", "하자보증금(계약금액 2~5%)", "계약 이행보증금(10%)", "물가변동 조정", "부정당업자 제재"],
}

# 불공정 조항 패턴
UNFAIR_PATTERNS = [
    "손해배상 무제한",
    "일방적 계약 변경권",
    "무제한 연장 옵션",
    "과도한 위약금",
    "지식재산권 일방 귀속",
    "불명확한 업무 범위",
    "자동 갱신 + 고지 의무 없음",
]


class ContractReviewAgent(BaseAgent):
    name = "ContractReviewAgent"
    role = "계약 검토 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "review_contract_terms",
                "description": (
                    "계약서 주요 조항 위험 분석.\n"
                    "계약 유형별 핵심 체크 항목과 불공정 조항 패턴을\n"
                    "점검하여 수정 권고사항을 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "contract_type": {
                            "type": "string",
                            "description": "계약 유형",
                            "enum": list(CONTRACT_CHECKLIST.keys()),
                        },
                        "contract_amount": {"type": "number", "description": "계약금액 (원)"},
                        "missing_items": {
                            "type": "array",
                            "description": "누락된 항목 목록",
                            "items": {"type": "string"},
                        },
                        "unfair_clauses": {
                            "type": "array",
                            "description": "발견된 불공정 조항 키워드",
                            "items": {"type": "string"},
                        },
                        "has_personal_guarantee": {
                            "type": "boolean",
                            "description": "대표이사 개인 연대보증 여부",
                        },
                    },
                    "required": ["contract_type", "contract_amount"],
                },
            },
            {
                "name": "calc_penalty",
                "description": (
                    "계약 위반 시 손해배상·지체상금·위약금 계산.\n"
                    "지체 일수·계약금액·약정 율을 기반으로 제재액을 산출한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "contract_amount": {"type": "number", "description": "계약금액 (원)"},
                        "delay_days": {"type": "integer", "description": "지체 일수"},
                        "penalty_rate_per_day": {
                            "type": "number",
                            "description": "일일 지체상금율 (예: 0.001 = 0.1%/일)",
                        },
                        "max_penalty_ratio": {
                            "type": "number",
                            "description": "최대 지체상금 한도율 (계약금액 대비, 예: 0.10)",
                        },
                    },
                    "required": ["contract_amount", "delay_days", "penalty_rate_per_day"],
                },
            },
            {
                "name": "check_public_contract",
                "description": (
                    "공공 입찰 계약 특수 조건 체크리스트.\n"
                    "국가계약법·지방계약법 기준 이행보증금·하자보증금·\n"
                    "지체상금·부정당업자 제재 요건을 점검한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "contract_amount": {"type": "number", "description": "계약금액 (원)"},
                        "contract_type": {
                            "type": "string",
                            "description": "계약 유형",
                            "enum": ["물품", "공사", "용역"],
                        },
                        "performance_bond_paid": {"type": "boolean", "description": "이행보증금 납부 여부"},
                        "warranty_bond_paid": {"type": "boolean", "description": "하자보증금 납부 여부"},
                    },
                    "required": ["contract_amount", "contract_type"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "review_contract_terms":
            return self._review_contract_terms(**tool_input)
        if tool_name == "calc_penalty":
            return self._calc_penalty(**tool_input)
        if tool_name == "check_public_contract":
            return self._check_public_contract(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _review_contract_terms(
        self,
        contract_type: str,
        contract_amount: float,
        missing_items: list[str] | None = None,
        unfair_clauses: list[str] | None = None,
        has_personal_guarantee: bool = False,
    ) -> dict:
        missing_items = missing_items or []
        unfair_clauses = unfair_clauses or []
        required = CONTRACT_CHECKLIST.get(contract_type, [])
        issues = []

        for item in missing_items:
            if item in required:
                issues.append({"항목": item, "유형": "누락", "등급": "🔴 고위험"})

        for clause in unfair_clauses:
            if any(p in clause for p in UNFAIR_PATTERNS):
                issues.append({"항목": clause, "유형": "불공정 조항", "등급": "🔴 고위험"})

        if has_personal_guarantee:
            issues.append({
                "항목": "대표이사 개인 연대보증",
                "유형": "리스크",
                "등급": "🟡 주의",
                "권고": "보증 범위 금액·기간 한정 / 특정채무 보증으로 전환 협의",
            })

        overall = "🔴 계약 수정 후 체결" if any(i["등급"] == "🔴 고위험" for i in issues) else "🟡 일부 수정 검토" if issues else "🟢 체결 가능"

        return {
            "계약유형": contract_type,
            "계약금액": round(contract_amount),
            "종합_판정": overall,
            "문제_항목수": len(issues),
            "문제_상세": issues,
            "필수_포함_항목": required,
            "법령근거": "약관의 규제에 관한 법률 §6~§14 (불공정약관 무효)",
        }

    def _calc_penalty(
        self,
        contract_amount: float,
        delay_days: int,
        penalty_rate_per_day: float,
        max_penalty_ratio: float = 0.10,
    ) -> dict:
        daily_penalty = contract_amount * penalty_rate_per_day
        total_penalty = daily_penalty * delay_days
        max_penalty = contract_amount * max_penalty_ratio
        capped = total_penalty > max_penalty

        return {
            "계약금액": round(contract_amount),
            "지체일수": delay_days,
            "일일_지체상금율": f"{penalty_rate_per_day*100:.3f}%",
            "일일_지체상금": round(daily_penalty),
            "지체상금_합계": round(min(total_penalty, max_penalty)),
            "한도_초과여부": capped,
            "최대_지체상금": round(max_penalty),
            "법령근거": "국가계약법 시행규칙 §75 (지체상금율)",
        }

    def _check_public_contract(
        self,
        contract_amount: float,
        contract_type: str,
        performance_bond_paid: bool = False,
        warranty_bond_paid: bool = False,
    ) -> dict:
        # 이행보증금: 계약금액의 10%
        perf_bond = contract_amount * 0.10
        # 하자보증금: 공사 5%, 물품·용역 2%
        warranty_rate = 0.05 if contract_type == "공사" else 0.02
        warranty_bond = contract_amount * warranty_rate

        issues = []
        if not performance_bond_paid:
            issues.append(f"이행보증금 미납부 — {perf_bond:,.0f}원 (계약금액 10%)")
        if not warranty_bond_paid:
            issues.append(f"하자보증금 미납부 — {warranty_bond:,.0f}원 (계약금액 {warranty_rate*100:.0f}%)")

        return {
            "계약금액": round(contract_amount),
            "계약유형": contract_type,
            "이행보증금": round(perf_bond),
            "이행보증금_납부": "✅" if performance_bond_paid else "❌",
            "하자보증금": round(warranty_bond),
            "하자보증금_납부": "✅" if warranty_bond_paid else "❌",
            "미비_사항": issues,
            "지체상금율": "1일 0.1% (최대 계약금액 30%)",
            "법령근거": "국가를 당사자로 하는 계약에 관한 법률 시행령",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        lines = ["[계약 리스크 분석 결과]"]
        has_pg = company_data.get("has_personal_guarantee", False)
        if has_pg:
            lines.append("\n▶ 대표이사 개인 연대보증 감지 — 보증 범위 한정 협의 권장")
        lines.append("  계약서 원문 제공 시 조항별 상세 검토 가능")
        return "\n".join(lines)

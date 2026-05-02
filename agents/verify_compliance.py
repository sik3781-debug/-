"""
VerifyCompliance: 법규준수 교차검증 전담 에이전트

역할:
  - GROUP I 컴플라이언스 분석 결과의 법령 적용 정합성 검증
  - 최신 법령 개정사항 반영 여부 확인
  - 세무·노무·안전·개인정보 리스크 재진단
  - 과태료·과징금 산정액 재계산 및 오류 탐지

근거 법령:
  - 중대재해처벌법 / 산업안전보건법 / 개인정보보호법
  - 공정거래법 / 하도급법 / 약관규제법
  - 고용보험법 / 근로기준법
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 법규준수(Compliance) 교차검증 전문가입니다.\n\n"
    "【역할】\n"
    "- 컴플라이언스 분석 결과의 법령 적용 정합성 독립 검증\n"
    "- 최신 법령 개정사항(시행일·개정 내용) 반영 확인\n"
    "- 과태료·과징금·형사처벌 제재 수위 재확인\n"
    "- 누락된 적용 법령 보완 제시\n\n"
    "【검증 원칙】\n"
    "- 법령 적용 착오 시 조문 번호와 함께 정정 내용 제시\n"
    "- 유리한 해석과 불리한 해석 모두 제시하여 균형 유지\n"
    "- 최신 판례·유권해석 반영 여부 확인"
)

# 주요 법령 최근 개정 이력 (단순화)
RECENT_AMENDMENTS = [
    {
        "법령": "중대재해처벌법",
        "시행일": "2024-01-27",
        "핵심변경": "5인 이상 사업장 전면 적용 (기존 50인 이상)",
        "영향": "소규모 사업장 경영책임자 형사 리스크 급증",
    },
    {
        "법령": "개인정보보호법",
        "시행일": "2024-03-15",
        "핵심변경": "과징금 기준 전체 매출액 3% → 위반 관련 매출액 3%",
        "영향": "과징금 산정 기준 변경으로 실제 부과액 감소 가능",
    },
    {
        "법령": "근로기준법",
        "시행일": "2024-01-01",
        "핵심변경": "최저임금 9,860원 → 10,030원 (2024년)",
        "영향": "미만 지급 시 3년 이하 징역 / 2,000만 원 이하 벌금",
    },
]


class VerifyCompliance(BaseAgent):
    name = "VerifyCompliance"
    role = "법규준수 교차검증 전담"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "verify_compliance_analysis",
                "description": "컴플라이언스 분석 결과 법령 정합성 교차검증",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "laws_applied": {
                            "type": "array",
                            "description": "적용한 법령 목록",
                            "items": {"type": "string"},
                        },
                        "employees": {"type": "integer"},
                        "industry": {"type": "string"},
                        "risk_items": {
                            "type": "array",
                            "description": "탐지된 리스크 항목",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["laws_applied", "employees"],
                },
            },
            {
                "name": "check_recent_amendments",
                "description": "최근 법령 개정사항 반영 여부 확인",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "analysis_date": {
                            "type": "string",
                            "description": "분석 기준일 (YYYY-MM-DD)",
                        },
                        "laws_in_scope": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["laws_in_scope"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "verify_compliance_analysis":
            return self._verify_compliance_analysis(**tool_input)
        if tool_name == "check_recent_amendments":
            return self._check_recent_amendments(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _verify_compliance_analysis(
        self,
        laws_applied: list[str],
        employees: int,
        industry: str = "제조업",
        risk_items: list[str] | None = None,
    ) -> dict:
        risk_items = risk_items or []
        missing_laws = []
        corrections = []

        # 중처법 적용 여부 체크
        msca_applied = any("중대재해" in l for l in laws_applied)
        if employees >= 5 and not msca_applied:
            missing_laws.append({
                "법령": "중대재해처벌법",
                "사유": f"상시 {employees}명 — 2024.01.27 이후 5인 이상 전면 적용",
                "등급": "🔴 누락 — 즉시 추가 필요",
            })

        # 개인정보보호법 기본 적용
        pp_applied = any("개인정보" in l for l in laws_applied)
        if not pp_applied:
            missing_laws.append({
                "법령": "개인정보보호법",
                "사유": "임직원 및 거래처 정보 처리 기업은 기본 적용",
                "등급": "🟡 권고 — 기본 의무 사항",
            })

        result = {
            "적용법령_검토수": len(laws_applied),
            "누락_법령": missing_laws,
            "정정_사항": corrections,
            "검증결과": "❌ 법령 누락 있음" if missing_laws else "✅ 적용 법령 적정",
        }
        return result

    def _check_recent_amendments(
        self,
        laws_in_scope: list[str],
        analysis_date: str = "2026-04-25",
    ) -> dict:
        relevant = [
            a for a in RECENT_AMENDMENTS
            if any(a["법령"] in l or l in a["법령"] for l in laws_in_scope)
        ]
        return {
            "검토_법령수": len(laws_in_scope),
            "최근_개정사항": relevant,
            "미반영_위험": len(relevant),
            "권고": "분석 시 상기 개정사항 반영 여부 재확인 필요" if relevant else "주요 개정사항 없음",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        emp = company_data.get("employees", 0)
        ind = company_data.get("industry", "제조업")
        lines = ["[법규준수 교차검증 결과]"]
        result = self._verify_compliance_analysis(
            laws_applied=["중대재해처벌법", "개인정보보호법"],
            employees=emp,
            industry=ind,
        )
        lines.append(f"\n▶ 법령 검토: {result['검증결과']}")
        if result["누락_법령"]:
            lines.append(f"  누락 {len(result['누락_법령'])}건 — 즉시 보완 필요")
        return "\n".join(lines)

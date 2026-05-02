"""
ComplianceAgent: 법규준수·컴플라이언스 전담 에이전트

근거 법령:
  - 공정거래법 / 하도급법 / 가맹사업법
  - 중대재해처벌법 (2022.01 시행, 5인 이상 사업장)
  - 산업안전보건법 / 화학물질관리법(화관법) / 화학물질등록평가법(화평법)
  - 개인정보보호법 / 전자상거래소비자보호법
  - 공익신고자보호법 / 부패방지권익위법

주요 기능:
  - 업종·규모별 법규준수 위험 스캔 (필수 법령 체크리스트)
  - 중대재해처벌법 준수 현황 진단 (안전보건관리체계 구축 여부)
  - 공정거래법 위반 리스크 (시장지배적 지위 남용·부당 공동행위)
  - 컴플라이언스 프로그램 설계 (내부신고채널·처벌규정·교육계획)
  - 법규 위반 과태료·벌금·과징금 추정
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 법규준수(Compliance) 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 업종·규모별 적용 법령 필수 체크리스트 진단\n"
    "- 중대재해처벌법: 안전보건관리체계 구축 여부 / 경영책임자 의무\n"
    "- 공정거래법: 시장지배적 지위 남용 / 부당 공동행위 / 불공정거래\n"
    "- 개인정보보호법: 개인정보 처리방침 / 수탁자 관리\n"
    "- 컴플라이언스 프로그램: 내부신고채널·교육·처벌규정 설계\n\n"
    "【분석 관점】\n"
    "- 법인: 과태료·과징금·형사 리스크 사전 제거\n"
    "- 오너(경영책임자): 중대재해처벌법 형사책임 / 공정거래법 고발\n"
    "- 과세관청: 법규 위반 가산세·환수금 연계\n"
    "- 금융기관: 컴플라이언스 리스크가 신용평가에 미치는 영향\n\n"
    "【목표】\n"
    "모든 적용 법령을 100% 준수하는 자율 컴플라이언스 시스템을 구축하여\n"
    "경영책임자의 형사 리스크를 완전히 차단한다."
)

# 중대재해처벌법 적용 범위 (2024년 1월 27일부터 5인 이상 전면 적용)
MSCA_THRESHOLD = 5  # 상시 근로자 5인 이상

# 주요 법규 위반 제재 (추정)
PENALTIES = {
    "중대재해처벌법_사망": {"벌금": "10억 이하", "징역": "1년 이상"},
    "공정거래법_담합": {"과징금": "관련매출액 10% 이하", "징역": "3년 이하"},
    "개인정보보호법_유출": {"과징금": "매출액 3% 이하", "과태료": "5천만 원 이하"},
    "하도급법_지연": {"과징금": "위반금액 2배 이내"},
    "산업안전보건법": {"과태료": "5천만 원 이하", "징역": "5년 이하"},
}


class ComplianceAgent(BaseAgent):
    name = "ComplianceAgent"
    role = "법규준수·컴플라이언스 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "scan_compliance_risks",
                "description": (
                    "업종·규모별 법규준수 위험 스캔.\n"
                    "필수 적용 법령 체크리스트를 기반으로\n"
                    "위반 위험 항목과 개선 우선순위를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employees": {"type": "integer", "description": "상시 근로자 수"},
                        "industry": {"type": "string", "description": "업종"},
                        "annual_revenue": {"type": "number", "description": "연 매출액 (원)"},
                        "has_safety_org": {"type": "boolean", "description": "안전보건관리체계 구축 여부"},
                        "has_privacy_policy": {"type": "boolean", "description": "개인정보처리방침 수립 여부"},
                        "has_compliance_program": {"type": "boolean", "description": "컴플라이언스 프로그램 운영 여부"},
                        "handles_chemicals": {"type": "boolean", "description": "화학물질 취급 여부"},
                    },
                    "required": ["employees", "industry", "annual_revenue"],
                },
            },
            {
                "name": "diagnose_msca_compliance",
                "description": (
                    "중대재해처벌법(중처법) 준수 현황 진단.\n"
                    "안전보건관리체계 구축 9대 의무 이행 여부를 점검하고\n"
                    "경영책임자 형사 리스크를 수치화한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employees": {"type": "integer", "description": "상시 근로자 수"},
                        "has_safety_manager": {"type": "boolean", "description": "안전보건관리책임자 선임 여부"},
                        "has_safety_budget": {"type": "boolean", "description": "안전보건 예산 편성 여부"},
                        "has_hazard_assessment": {"type": "boolean", "description": "위험성 평가 실시 여부"},
                        "has_emergency_plan": {"type": "boolean", "description": "비상대응계획 수립 여부"},
                        "recent_accident": {"type": "boolean", "description": "최근 3년 내 중대재해 발생 여부"},
                        "industry": {"type": "string", "description": "업종"},
                    },
                    "required": ["employees", "has_safety_manager", "has_safety_budget"],
                },
            },
            {
                "name": "design_compliance_program",
                "description": (
                    "컴플라이언스 프로그램 설계안.\n"
                    "내부신고채널·교육계획·처벌규정·모니터링 체계를\n"
                    "기업 규모에 맞게 설계한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employees": {"type": "integer", "description": "임직원 수"},
                        "risk_areas": {
                            "type": "array",
                            "description": "주요 리스크 영역 리스트",
                            "items": {"type": "string"},
                        },
                        "budget": {"type": "number", "description": "컴플라이언스 예산 (원/년)"},
                    },
                    "required": ["employees", "risk_areas"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "scan_compliance_risks":
            return self._scan_compliance_risks(**tool_input)
        if tool_name == "diagnose_msca_compliance":
            return self._diagnose_msca_compliance(**tool_input)
        if tool_name == "design_compliance_program":
            return self._design_compliance_program(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _scan_compliance_risks(
        self,
        employees: int,
        industry: str,
        annual_revenue: float,
        has_safety_org: bool = False,
        has_privacy_policy: bool = False,
        has_compliance_program: bool = False,
        handles_chemicals: bool = False,
    ) -> dict:
        risks = []

        if employees >= MSCA_THRESHOLD and not has_safety_org:
            risks.append({
                "법령": "중대재해처벌법",
                "위험": "안전보건관리체계 미구축 — 경영책임자 1년 이상 징역",
                "등급": "🔴 고위험",
                "조치": "안전보건관리책임자 선임 + 위험성 평가 즉시 실시",
            })

        if not has_privacy_policy:
            risks.append({
                "법령": "개인정보보호법",
                "위험": "개인정보처리방침 미수립 — 과태료 최대 5천만 원",
                "등급": "🟡 주의",
                "조치": "개인정보처리방침 홈페이지 게시 + 수탁자 현황 관리대장 작성",
            })

        if handles_chemicals:
            risks.append({
                "법령": "화학물질관리법(화관법)",
                "위험": "취급시설 허가·신고 미이행 시 영업정지",
                "등급": "🔴 고위험",
                "조치": "화학물질 취급 허가 현황 점검 + MSDS 비치",
            })

        if annual_revenue >= 10_000_000_000 and not has_compliance_program:
            risks.append({
                "법령": "공정거래법",
                "위험": "매출 100억 이상 기업 — 컴플라이언스 프로그램 미운영 시 과징금 감경 불가",
                "등급": "🟡 주의",
                "조치": "공정거래 자율준수 프로그램(CP) 도입",
            })

        overall = "🔴 즉시 조치" if any(r["등급"] == "🔴 고위험" for r in risks) else "🟡 점진적 정비" if risks else "🟢 양호"

        return {
            "임직원수": employees,
            "업종": industry,
            "종합_위험등급": overall,
            "위험_항목수": len(risks),
            "위험_상세": risks,
            "우선_조치": risks[0]["조치"] if risks else "현행 유지 — 연 1회 정기 점검",
        }

    def _diagnose_msca_compliance(
        self,
        employees: int,
        has_safety_manager: bool,
        has_safety_budget: bool,
        has_hazard_assessment: bool = False,
        has_emergency_plan: bool = False,
        recent_accident: bool = False,
        industry: str = "제조업",
    ) -> dict:
        if employees < MSCA_THRESHOLD:
            return {"적용여부": False, "사유": f"상시 근로자 {employees}명 — 중처법 5인 이상 사업장만 적용"}

        obligations = [
            ("안전보건관리책임자 선임", has_safety_manager),
            ("안전보건 예산 편성", has_safety_budget),
            ("위험성 평가 실시", has_hazard_assessment),
            ("비상대응계획 수립", has_emergency_plan),
        ]
        fulfilled = sum(1 for _, ok in obligations if ok)
        score = round(fulfilled / len(obligations) * 100)

        risk_level = (
            "🔴 고위험 — 경영책임자 형사 처벌 가능" if score < 50
            else "🟡 주의 — 일부 의무 미이행" if score < 100
            else "🟢 양호 — 전 의무 이행"
        )

        result = {
            "적용여부": True,
            "이행_점수": f"{score}/100",
            "의무_이행_현황": [{"의무": k, "이행": "✅" if v else "❌"} for k, v in obligations],
            "위험등급": risk_level,
            "미이행_의무": [k for k, v in obligations if not v],
        }

        if recent_accident:
            result["추가경고"] = "🔴 최근 3년 내 중대재해 발생 — 재발 시 가중처벌 가능 (중처법 §6)"

        return result

    def _design_compliance_program(
        self,
        employees: int,
        risk_areas: list[str],
        budget: float = 0,
    ) -> dict:
        if not budget:
            budget = employees * 300_000  # 1인당 연 30만 원

        components = [
            {"구성요소": "컴플라이언스 정책 선언", "비용": "자체 작성", "우선순위": 1},
            {"구성요소": "내부신고채널 구축 (익명보장)", "비용": "50~200만 원", "우선순위": 1},
            {"구성요소": "임직원 준법교육 (연 2회)", "비용": f"{employees * 50_000:,.0f}원/년", "우선순위": 2},
            {"구성요소": "리스크 영역별 내부 감사", "비용": "200~500만 원/년", "우선순위": 2},
            {"구성요소": "외부 법률 자문 계약", "비용": "월 50~150만 원", "우선순위": 3},
        ]

        return {
            "임직원수": employees,
            "주요_리스크": risk_areas,
            "연간_예산": round(budget),
            "프로그램_구성요소": components,
            "기대효과": "공정거래법 위반 시 과징금 30~40% 감경 (CP 운영 입증 시)",
            "법령근거": "공정거래 자율준수 프로그램 운영 등에 관한 지침 (공정위)",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        emp = company_data.get("employees", 0)
        ind = company_data.get("industry", "제조업")
        rev = company_data.get("revenue", 0)
        lines = ["[컴플라이언스 리스크 분석 결과]"]
        scan = self._scan_compliance_risks(emp, ind, rev)
        lines.append(f"\n▶ 종합 위험등급: {scan['종합_위험등급']} / 위험 {scan['위험_항목수']}건")
        if scan["우선_조치"] != "현행 유지 — 연 1회 정기 점검":
            lines.append(f"  즉시 조치: {scan['우선_조치']}")
        return "\n".join(lines)

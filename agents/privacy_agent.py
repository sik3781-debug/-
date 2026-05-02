"""
PrivacyAgent: 개인정보보호법 전담 에이전트

근거 법령:
  - 개인정보보호법 (2023.09 개정 / 2024.03 시행)
  - 개인정보보호법 시행령 / 시행규칙
  - 정보통신망 이용촉진 및 정보보호 등에 관한 법률
  - EU GDPR (해외 수출입 기업 적용)
  - 개인정보의 안전성 확보조치 기준 (개인정보위 고시)

주요 기능:
  - 개인정보 처리 적법성 기반 진단 (수집·이용·제공·파기)
  - 개인정보 영향평가(PIA) 필요성 판단
  - 개인정보보호 수준 진단 (기술적·관리적·물리적 보호조치)
  - 위반 시 과징금·과태료 추정
  - PIMS(개인정보보호 인증) 획득 로드맵
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 개인정보보호법 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 개인정보 처리 적법 기반 진단 (동의·계약·법령·정당한 이익)\n"
    "- 개인정보 처리방침 수립·공개 요건 (개인정보보호법 §30)\n"
    "- 개인정보 영향평가(PIA): 5만 명 이상 민감정보 처리 기관\n"
    "- 기술적·관리적·물리적 안전조치 기준 진단\n"
    "- PIMS(개인정보보호 관리체계 인증) 획득 지원\n"
    "- 개인정보 유출 사고 대응 절차 (72시간 신고 의무)\n\n"
    "【분석 관점】\n"
    "- 법인: 과징금·과태료 리스크 제거 / 정보주체 신뢰 제고\n"
    "- 오너: 형사처벌(징역 5년 이하) 회피 / 영업비밀 보호\n"
    "- 과세관청: 개인정보 관련 비용의 손금 처리 적정성\n"
    "- 금융기관: 개인정보 사고 시 신용등급 하락 리스크\n\n"
    "【목표】\n"
    "개인정보보호 법령을 완전 준수하는 체계를 구축하여\n"
    "과징금·형사처벌 리스크를 원천 차단한다."
)

# 개인정보 유형별 민감도
SENSITIVITY_LEVELS = {
    "일반개인정보": {"level": 1, "예시": "성명, 주소, 연락처"},
    "고유식별정보": {"level": 2, "예시": "주민등록번호, 여권번호, 운전면허번호"},
    "민감정보": {"level": 3, "예시": "건강, 병력, 유전정보, 성적 지향, 정치적 견해"},
    "신용정보": {"level": 2, "예시": "신용등급, 금융거래 내역"},
}

# 위반 유형별 제재
VIOLATION_PENALTIES = {
    "처리방침_미수립": {"과태료": "3천만 원 이하", "형사": "해당 없음"},
    "동의_없는_수집": {"과태료": "3천만 원 이하", "과징금": "위반 관련 매출액 3% 이하"},
    "안전조치_미흡": {"과태료": "3천만 원 이하", "형사": "2년 이하 징역"},
    "유출_미신고": {"과태료": "3천만 원 이하", "형사": "해당 없음"},
    "파기_의무_위반": {"과태료": "3천만 원 이하", "형사": "해당 없음"},
    "제3자_무단_제공": {"과징금": "위반 관련 매출액 3% 이하", "형사": "5년 이하 징역"},
}


class PrivacyAgent(BaseAgent):
    name = "PrivacyAgent"
    role = "개인정보보호 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "diagnose_privacy_compliance",
                "description": (
                    "개인정보보호법 준수 현황 종합 진단.\n"
                    "수집·이용·보관·파기 전 단계 적법성과\n"
                    "기술적·관리적 보호조치 이행 수준을 점검한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employees": {"type": "integer", "description": "임직원 수"},
                        "data_subjects_count": {"type": "integer", "description": "개인정보 처리 정보주체 수 (명)"},
                        "has_privacy_policy": {"type": "boolean", "description": "개인정보처리방침 수립·공개 여부"},
                        "has_privacy_officer": {"type": "boolean", "description": "개인정보보호책임자(CPO) 지정 여부"},
                        "has_consent_process": {"type": "boolean", "description": "적법한 동의 수집 절차 여부"},
                        "has_technical_measures": {"type": "boolean", "description": "기술적 안전조치(암호화·접근통제) 여부"},
                        "has_processor_contract": {"type": "boolean", "description": "수탁사 개인정보 처리 위탁 계약 여부"},
                        "processes_sensitive_data": {"type": "boolean", "description": "민감정보·고유식별정보 처리 여부"},
                        "annual_revenue": {"type": "number", "description": "연 매출액 (원, 과징금 산정용)"},
                    },
                    "required": ["employees", "data_subjects_count", "has_privacy_policy"],
                },
            },
            {
                "name": "estimate_violation_penalty",
                "description": (
                    "개인정보보호법 위반 시 과징금·과태료 추정.\n"
                    "위반 유형·매출액·정보주체 수를 기반으로\n"
                    "최대 제재액과 자진신고 감경 혜택을 산출한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "violation_type": {
                            "type": "string",
                            "description": "위반 유형",
                            "enum": list(VIOLATION_PENALTIES.keys()),
                        },
                        "annual_revenue": {"type": "number", "description": "연 매출액 (원)"},
                        "data_subjects_affected": {"type": "integer", "description": "피해 정보주체 수 (명)"},
                        "self_reported": {"type": "boolean", "description": "자진신고 여부 (과징금 30% 감경)"},
                    },
                    "required": ["violation_type", "annual_revenue", "data_subjects_affected"],
                },
            },
            {
                "name": "plan_pims_certification",
                "description": (
                    "PIMS(개인정보보호 관리체계 인증) 획득 로드맵.\n"
                    "현황 갭 분석 → 준비 기간 → 비용 추정 → 인증 유지 계획을\n"
                    "단계별로 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employees": {"type": "integer", "description": "임직원 수"},
                        "current_compliance_score": {
                            "type": "number",
                            "description": "현재 준수 수준 (0~100점 자가진단)",
                        },
                        "budget": {"type": "number", "description": "개인정보보호 예산 (원/년)"},
                        "target_months": {
                            "type": "integer",
                            "description": "인증 목표 기간 (개월)",
                        },
                    },
                    "required": ["employees", "current_compliance_score"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "diagnose_privacy_compliance":
            return self._diagnose_privacy_compliance(**tool_input)
        if tool_name == "estimate_violation_penalty":
            return self._estimate_violation_penalty(**tool_input)
        if tool_name == "plan_pims_certification":
            return self._plan_pims_certification(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _diagnose_privacy_compliance(
        self,
        employees: int,
        data_subjects_count: int,
        has_privacy_policy: bool,
        has_privacy_officer: bool = False,
        has_consent_process: bool = False,
        has_technical_measures: bool = False,
        has_processor_contract: bool = False,
        processes_sensitive_data: bool = False,
        annual_revenue: float = 0,
    ) -> dict:
        issues = []
        score = 0
        total = 5

        if has_privacy_policy:
            score += 1
        else:
            issues.append({
                "항목": "개인정보처리방침 미수립",
                "등급": "🔴 고위험",
                "과태료": "3천만 원 이하",
                "조치": "처리방침 수립 후 홈페이지 공개 (개인정보보호법 §30)",
            })

        if has_privacy_officer:
            score += 1
        else:
            issues.append({
                "항목": "개인정보보호책임자(CPO) 미지정",
                "등급": "🟡 주의",
                "과태료": "1천만 원 이하",
                "조치": "임원급 CPO 지정 + 개인정보위 신고 (§31)",
            })

        if has_consent_process:
            score += 1
        else:
            issues.append({
                "항목": "적법한 동의 수집 절차 미비",
                "등급": "🔴 고위험",
                "과징금": f"{annual_revenue * 0.03:,.0f}원 이하 (매출액 3%)" if annual_revenue else "매출액 3% 이하",
                "조치": "동의서 재설계: 수집목적·항목·보유기간·제3자 제공 여부 명시 (§15~§17)",
            })

        if has_technical_measures:
            score += 1
        else:
            issues.append({
                "항목": "기술적 안전조치(암호화·접근통제) 미흡",
                "등급": "🔴 고위험",
                "과태료": "3천만 원 이하",
                "형사": "2년 이하 징역",
                "조치": "개인정보 암호화·접근권한 최소화·접속기록 보관 (안전성 확보조치 기준)",
            })

        if has_processor_contract:
            score += 1
        else:
            issues.append({
                "항목": "수탁사 위탁 계약서 미비",
                "등급": "🟡 주의",
                "과태료": "3천만 원 이하",
                "조치": "위탁 계약서에 처리 목적·기간·관리감독 조항 포함 (§26)",
            })

        if processes_sensitive_data:
            issues.append({
                "항목": "민감정보·고유식별정보 처리 — 별도 동의 필수",
                "등급": "🟡 주의",
                "조치": "민감정보 처리 시 별도 동의 + 최소 수집 원칙 적용 (§23·§24)",
            })

        # PIA 필요성 판단
        pia_required = data_subjects_count >= 50_000 and processes_sensitive_data

        compliance_pct = round(score / total * 100)
        overall = (
            "🔴 즉시 조치" if compliance_pct < 60
            else "🟡 점진적 개선" if compliance_pct < 100
            else "🟢 양호"
        )

        return {
            "정보주체_수": f"{data_subjects_count:,}명",
            "준수율": f"{compliance_pct}%",
            "종합_위험등급": overall,
            "문제_항목수": len(issues),
            "문제_상세": issues,
            "PIA_의무여부": "✅ 필요" if pia_required else "해당 없음",
            "유출_신고의무": "72시간 이내 개인정보위 신고 + 정보주체 통지 (§34)",
        }

    def _estimate_violation_penalty(
        self,
        violation_type: str,
        annual_revenue: float,
        data_subjects_affected: int,
        self_reported: bool = False,
    ) -> dict:
        penalty_info = VIOLATION_PENALTIES.get(violation_type, {})
        max_penalty = 0

        # 과징금 계산 (매출액 3% 기준)
        if "과징금" in penalty_info:
            max_penalty = annual_revenue * 0.03
            if self_reported:
                max_penalty *= 0.70  # 30% 감경

        # 과태료 (3천만 원 한도)
        fine = 30_000_000
        if data_subjects_affected > 100_000:
            fine = 30_000_000  # 최대치
        elif data_subjects_affected > 10_000:
            fine = 20_000_000
        else:
            fine = 10_000_000

        return {
            "위반유형": violation_type,
            "정보주체_피해수": f"{data_subjects_affected:,}명",
            "최대_과징금": f"{max_penalty:,.0f}원" if max_penalty else "해당 없음",
            "예상_과태료": f"{fine:,.0f}원",
            "형사처벌": penalty_info.get("형사", "해당 없음"),
            "자진신고_감경": "과징금 30% 감경 적용" if self_reported else "미적용",
            "법령근거": "개인정보보호법 §75~§76 (과태료), §64의2 (과징금)",
        }

    def _plan_pims_certification(
        self,
        employees: int,
        current_compliance_score: float,
        budget: float = 0,
        target_months: int = 12,
    ) -> dict:
        if not budget:
            budget = employees * 500_000  # 1인당 연 50만 원

        gap = 100 - current_compliance_score
        prep_months = max(3, round(gap / 10))  # 갭 10점당 1개월

        roadmap = [
            {"단계": "1단계 현황 진단", "기간": "1~2개월", "내용": "개인정보 처리현황 파악·갭분석", "비용": "500~1,000만 원"},
            {"단계": "2단계 제도 정비", "기간": f"3~{prep_months}개월", "내용": "처리방침·동의서·위탁계약서 정비", "비용": "300~600만 원"},
            {"단계": "3단계 기술조치", "기간": f"{prep_months}~{prep_months+2}개월", "내용": "암호화·접근통제·접속기록 시스템 구축", "비용": "1,000~3,000만 원"},
            {"단계": "4단계 사전 심사", "기간": f"{prep_months+3}개월", "내용": "내부 모의심사 + 컨설팅사 예비진단", "비용": "500만 원"},
            {"단계": "5단계 인증 심사", "기간": f"{prep_months+4}개월", "내용": "개인정보보호위원회 인증심사 신청", "비용": "심사수수료 300~800만 원"},
        ]

        return {
            "현재_준수점수": f"{current_compliance_score:.0f}/100",
            "인증_갭": f"{gap:.0f}점",
            "예상_준비기간": f"{prep_months+4}개월",
            "연간_예산": round(budget),
            "총비용_추정": "2,600~5,400만 원",
            "인증_로드맵": roadmap,
            "인증_효과": [
                "개인정보 관련 입찰 가점 (공공기관 발주 시)",
                "과징금 감경 사유 (개인정보보호위원회 인정)",
                "정보주체 신뢰 제고 — 기업 브랜드 가치 향상",
            ],
            "유효기간": "인증 취득 후 3년 (연간 사후관리 심사)",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        emp = company_data.get("employees", 0)
        rev = company_data.get("revenue", 0)
        subjects = company_data.get("data_subjects_count", 1000)
        has_pp = company_data.get("has_privacy_policy", False)
        lines = ["[개인정보보호 준수 분석 결과]"]
        result = self._diagnose_privacy_compliance(
            employees=emp,
            data_subjects_count=subjects,
            has_privacy_policy=has_pp,
            annual_revenue=rev,
        )
        lines.append(f"\n▶ 준수율: {result['준수율']} / {result['종합_위험등급']}")
        lines.append(f"  문제 항목: {result['문제_항목수']}건 / PIA: {result['PIA_의무여부']}")
        return "\n".join(lines)

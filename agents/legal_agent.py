"""
LegalAgent: 상법·형사·공정거래 법률 리스크 전문 에이전트
"""
from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 상법·형사법·공정거래법 전문 법률 컨설턴트입니다.\n"
    "법인 / 주주·임원 / 과세관청 3자 관점을 교차 분석하여 리스크를 진단합니다.\n\n"
    "【전문 분야】\n"
    "- 상법 절차 위반(이사회·주주총회 결의 하자, 등기 해태)\n"
    "- 차등배당 요건(상법 제464조의2), 의결권 없는 주식 설계\n"
    "- 배임·횡령 형사 리스크(형법 제355·356조)\n"
    "- 명의신탁 증여의제(상증세법 제45조의2) 및 형사 처벌\n"
    "- 특수관계인 거래 공정거래법 리스크(공정거래법 제47조)\n"
    "- 임원 책임보험(D&O), 법인 대표 연대보증 해소\n\n"
    "【답변 기준】\n"
    "최신 개정 상법·판례 반영, 단정적·전문가 언어, 면책 문구 생략"
)


class LegalAgent(BaseAgent):
    name = "LegalAgent"
    role = "상법·형사·공정거래 법률 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "analyze_corporate_procedure",
                "description": "이사회·주주총회 결의의 법적 유효성 및 하자 리스크를 분석합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "resolution_type": {"type": "string", "description": "결의 유형 (이사회/주주총회/임시주주총회)"},
                        "issue": {"type": "string", "description": "검토할 사안 설명"},
                        "directors_count": {"type": "integer", "description": "이사 수"},
                        "shareholders_count": {"type": "integer", "description": "주주 수"},
                    },
                    "required": ["resolution_type", "issue"],
                },
            },
            {
                "name": "check_related_party_risk",
                "description": "특수관계인 거래의 공정거래법·상법 리스크를 평가합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transaction_type": {"type": "string", "description": "거래 유형 (자금·상품·용역·부동산)"},
                        "annual_amount": {"type": "number", "description": "연간 거래금액 (원)"},
                        "ownership_ratio": {"type": "number", "description": "특수관계인 지분율 (%)"},
                    },
                    "required": ["transaction_type", "annual_amount", "ownership_ratio"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "analyze_corporate_procedure":
            return self._analyze_procedure(**tool_input)
        if tool_name == "check_related_party_risk":
            return self._check_rp_risk(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _analyze_procedure(resolution_type: str, issue: str,
                           directors_count: int = 3, shareholders_count: int = 5) -> dict:
        # 이사회: 재적 과반수 출석 + 출석 과반수 찬성
        # 주주총회 보통결의: 출석 과반수 + 발행주식 1/4 이상
        # 주주총회 특별결의: 출석 2/3 이상 + 발행주식 1/3 이상
        risks = []
        if "배당" in issue:
            risks.append("차등배당: 상법 제464조의2에 따른 정관 규정 및 주주 동의 요건 확인 필수")
        if "임원" in issue or "이사" in issue:
            risks.append("이사 선임: 주주총회 보통결의 + 임기 3년 이내 정관 규정 확인")
        if "합병" in issue or "분할" in issue:
            risks.append("합병·분할: 주주총회 특별결의 + 채권자 보호절차(상법 제527조의5) 이행 필수")
        return {
            "결의 유형": resolution_type,
            "이사회 의결 요건": f"재적 {directors_count}명 중 과반수 출석, 출석 과반수 찬성",
            "주총 보통결의": "출석 주주 과반수 + 발행주식 총수의 1/4 이상",
            "주총 특별결의": "출석 주주 2/3 이상 + 발행주식 총수의 1/3 이상",
            "발견 리스크": risks if risks else ["특이 리스크 없음"],
            "필수 조치": "의사록 적법 작성·보관 (상법 제373조), 변경등기 2주 내 이행",
        }

    @staticmethod
    def _check_rp_risk(transaction_type: str, annual_amount: float, ownership_ratio: float) -> dict:
        # 공정거래법 제47조: 상호출자제한기업집단 적용 (중소법인은 해당 없을 수 있음)
        # 상증세법 일감몰아주기: 수혜법인 세후영업이익 × (정상거래비율 초과분 × 주주 지분율)
        threshold_30 = ownership_ratio >= 30
        risk_level = "높음" if threshold_30 and annual_amount >= 1_000_000_000 else "보통"
        items = [
            f"거래 유형: {transaction_type}",
            f"연간 거래금액: {annual_amount:,.0f}원",
            f"지분율: {ownership_ratio}% ({'공정거래법 신고 대상 검토 필요' if threshold_30 else '일반 거래'})",
        ]
        if annual_amount >= 500_000_000:
            items.append("일감몰아주기 증여세(상증세법 제45조의3) 해당 여부 검토 요망")
        return {
            "리스크 등급": risk_level,
            "분석 항목": items,
            "권고": "독립기업 원칙(Arm's Length) 준수, 이사회 승인 및 계약서 체결 필수",
        }

"""
QueryClassifierAgent: 사용자 질의 → 최적 에이전트 자동 라우팅 에이전트

역할:
  - 자연어 질의를 분석하여 담당 에이전트 집합을 자동 선별
  - 질의 복잡도 판단 (단일 에이전트 vs 전체 orchestrator 실행)
  - 쿼리를 에이전트별 최적 입력 형태로 전처리
  - 중복 에이전트 호출 방지 및 실행 우선순위 결정

설계 철학:
  - 질의 키워드 → 에이전트 매핑 테이블 기반 1차 분류
  - 복합 질의(가업승계 + 세금 + 주식) → 멀티 에이전트 자동 조합
  - 단순 질의 → 단일 전담 에이전트 직접 라우팅 (orchestrator 생략)
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 컨설팅 질의 분류 및 에이전트 라우팅 전문가입니다.\n\n"
    "【역할】\n"
    "- 사용자 질의의 핵심 키워드·의도 분석\n"
    "- 최적 담당 에이전트 집합 선별 및 우선순위 부여\n"
    "- 복합 질의의 서브 질의 분해\n"
    "- 실행 모드 결정 (단일·멀티·전체 orchestrator)\n\n"
    "【분류 원칙】\n"
    "- 단일 도메인 질의 → 전담 에이전트 1~3개\n"
    "- 복합 도메인 질의 → 그룹별 병렬 실행\n"
    "- '종합 분석' 키워드 → 전체 orchestrator 실행"
)

# 키워드 → 에이전트 매핑
KEYWORD_MAP = {
    # 세무·절세
    "법인세": ["TaxAgent", "FinanceAgent"],
    "절세": ["TaxAgent", "FinanceAgent", "GiftTaxAgent"],
    "가지급금": ["ProvisionalPaymentAgent", "TaxAgent"],
    "임원퇴직금": ["ExecutivePayAgent", "TaxAgent"],
    "R&D": ["RDTaxCreditAgent", "TaxAgent"],
    "투자세액공제": ["InvestTaxCreditAgent", "TaxAgent"],
    "부가가치세": ["VATAgent"],
    "배당": ["DividendPolicyAgent", "TaxAgent"],
    # 주식·승계
    "비상장주식": ["StockAgent", "GiftTaxAgent"],
    "주식평가": ["StockAgent"],
    "가업승계": ["SuccessionAgent", "GiftTaxAgent", "InheritanceTaxAgent", "StockAgent"],
    "차명주식": ["NomineeStockAgent", "StockAgent"],
    "증여": ["GiftTaxAgent", "StockAgent"],
    "상속": ["InheritanceTaxAgent", "SuccessionAgent"],
    # 재무
    "재무구조": ["FinanceAgent", "CreditRatingAgent", "DebtRestructuringAgent"],
    "현금흐름": ["CashFlowAgent", "FinancialForecastAgent"],
    "운전자본": ["WorkingCapitalAgent", "CashFlowAgent"],
    "부채": ["DebtRestructuringAgent", "FinanceAgent"],
    "원가": ["CostAnalysisAgent"],
    "손익분기": ["CostAnalysisAgent"],
    # 노무·HR
    "4대보험": ["SocialInsuranceAgent", "LaborAgent"],
    "성과급": ["PerformancePayAgent", "LaborAgent"],
    "교육훈련": ["HRDAgent", "LaborAgent"],
    "근로계약": ["LaborAgent"],
    # 컴플라이언스
    "중대재해": ["ComplianceAgent"],
    "컴플라이언스": ["ComplianceAgent", "LegalAgent"],
    "개인정보": ["PrivacyAgent", "ComplianceAgent"],
    "계약": ["ContractReviewAgent", "LegalAgent"],
    # 전략·성장
    "해외수출": ["TradeAgent", "GlobalExpansionAgent"],
    "FTA": ["TradeAgent"],
    "IPO": ["IPOAgent", "FinanceAgent"],
    "M&A": ["MAValuationAgent", "StockAgent"],
    "DX": ["DXAgent"],
    "공급망": ["SupplyChainAgent"],
    "VC": ["VentureCapitalAgent"],
    "투자유치": ["VentureCapitalAgent", "IPOAgent"],
    # 특허·부동산
    "특허": ["PatentAgent"],
    "부동산": ["RealEstateAgent"],
    "보험": ["InsuranceAgent"],
    # 종합
    "종합": [],  # → 전체 orchestrator
    "전체분석": [],
}


class QueryClassifierAgent(BaseAgent):
    name = "QueryClassifierAgent"
    role = "질의 분류·에이전트 라우팅 전담"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "classify_query",
                "description": (
                    "사용자 질의를 분석하여 최적 에이전트 집합 선별.\n"
                    "단일·멀티·전체 orchestrator 실행 모드를 결정하고\n"
                    "에이전트별 입력 쿼리를 생성한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_query": {"type": "string", "description": "사용자 자연어 질의"},
                        "company_data_keys": {
                            "type": "array",
                            "description": "이미 보유한 company_data 필드 목록",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["user_query"],
                },
            },
            {
                "name": "decompose_complex_query",
                "description": (
                    "복합 질의를 단일 도메인 서브 질의로 분해.\n"
                    "각 서브 질의별 담당 에이전트와 실행 순서를 결정한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_query": {"type": "string"},
                        "detected_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["user_query"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "classify_query":
            return self._classify_query(**tool_input)
        if tool_name == "decompose_complex_query":
            return self._decompose_complex_query(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _classify_query(
        self,
        user_query: str,
        company_data_keys: list[str] | None = None,
    ) -> dict:
        company_data_keys = company_data_keys or []
        matched_agents: set[str] = set()
        matched_keywords = []

        for kw, agents in KEYWORD_MAP.items():
            if kw in user_query:
                matched_keywords.append(kw)
                if not agents:  # 종합 키워드
                    return {
                        "실행모드": "FULL_ORCHESTRATOR",
                        "설명": f"'{kw}' 키워드 → 전체 47개 에이전트 orchestrator 실행",
                        "예상_소요시간": "약 3~5분",
                    }
                matched_agents.update(agents)

        agent_list = sorted(matched_agents)
        mode = (
            "SINGLE" if len(agent_list) <= 2
            else "MULTI" if len(agent_list) <= 8
            else "FULL_ORCHESTRATOR"
        )

        return {
            "원문_질의": user_query,
            "매칭_키워드": matched_keywords,
            "실행모드": mode,
            "선별_에이전트": agent_list,
            "에이전트_수": len(agent_list),
            "실행_권장": (
                "단일 에이전트 직접 호출" if mode == "SINGLE"
                else "멀티 에이전트 병렬 실행" if mode == "MULTI"
                else "전체 orchestrator 실행"
            ),
        }

    def _decompose_complex_query(
        self,
        user_query: str,
        detected_domains: list[str] | None = None,
    ) -> dict:
        detected_domains = detected_domains or []

        sub_queries = []
        if "가업승계" in user_query or "승계" in user_query:
            sub_queries.append({
                "서브질의": "현재 비상장주식 1주당 평가가치 산출",
                "담당에이전트": "StockAgent",
                "순서": 1,
            })
            sub_queries.append({
                "서브질의": "지분 증여 시 증여세 계산 및 절세 전략",
                "담당에이전트": "GiftTaxAgent",
                "순서": 2,
            })
            sub_queries.append({
                "서브질의": "가업상속공제 요건 충족 여부 및 절감액",
                "담당에이전트": "SuccessionAgent",
                "순서": 2,
            })

        if "절세" in user_query or "법인세" in user_query:
            sub_queries.append({
                "서브질의": "법인세 절감 가능 항목 전수 스캔",
                "담당에이전트": "TaxAgent",
                "순서": 1,
            })

        if not sub_queries:
            sub_queries.append({
                "서브질의": user_query,
                "담당에이전트": "TaxAgent",
                "순서": 1,
                "비고": "분류 불가 — TaxAgent 기본 처리",
            })

        return {
            "원문_질의": user_query,
            "분해_서브질의수": len(sub_queries),
            "서브질의_목록": sub_queries,
            "병렬_실행_가능": [q for q in sub_queries if q["순서"] == 1],
            "순차_실행_필요": [q for q in sub_queries if q["순서"] > 1],
        }

    def classify(self, query: str) -> dict:
        """외부에서 직접 호출하는 단축 메서드"""
        return self._classify_query(user_query=query)

    def analyze(self, company_data: dict[str, Any]) -> str:
        lines = ["[질의 분류·라우팅 시스템 준비 완료]"]
        lines.append(f"\n▶ 키워드 매핑 규칙: {len(KEYWORD_MAP)}개")
        lines.append("  사용자 질의 입력 시 자동 에이전트 라우팅 활성화")
        return "\n".join(lines)

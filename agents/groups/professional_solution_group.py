"""전문 솔루션 그룹 레지스트리
중기이코노미 11대 전문 영역 컨설팅 에이전트 통합 분류
"""
from __future__ import annotations

PROFESSIONAL_SOLUTION_GROUP: dict = {
    "name": "전문 솔루션 그룹",
    "description": "중소기업 전문 컨설팅 11대 영역 통합 솔루션",
    "domains": [
        "법인세 절세 전략",
        "비상장주식 평가 및 주식 이동",
        "가업승계",
        "차명주식 해소",
        "가지급금 해결",
        "임원·주주·종업원 절세",
        "특허패키지 컨설팅",
        "재무구조 개선 및 리스크헷지",
        "인사노무",
        "상속·증여세 절세",
        "금융기관 관점 진단",
    ],
    "workflow": "4단계: 전략생성→리스크점검&헷지→과정관리→사후관리",
    "validation_axes": ["DOMAIN", "LEGAL", "CALC", "LOGIC", "CROSS"],
    "matrix": "4자관점(법인·주주·과세관청·금융기관) × 3시점(Pre·Now·Post) = 12셀",
    "members": [
        # CYCLE 4 보강 완료 14종
        "TreasuryStockLiquidationAgent",
        "Section45_5TaxStrategyAgent",
        "NonListedStockPrecisionAgent",
        "SuccessionRoadmapAgent",
        "FinancialRatioPrecisionAgent",
        "TreasuryStockStrategyAgent",
        "SpecialCorpTransactionAgent",
        "CorporateBenefitsFundAgent",
        "CivilTrustAgent",
        "ChildCorpDesignAgent",
        "CapitalStructureImprovementAgent",
        "PatentCashflowSimulator",
        "RetainedEarningsManagementAgent",
        "ValuationOptimizationAgent",
        "RealEstateValuationAgent",
        "RealEstateDesktopAppraisalAgent",
    ],
}


def register(agent_class):
    """에이전트를 전문 솔루션 그룹에 등록 (데코레이터)"""
    name = agent_class.__name__
    if name not in PROFESSIONAL_SOLUTION_GROUP["members"]:
        PROFESSIONAL_SOLUTION_GROUP["members"].append(name)
    agent_class._group = "전문 솔루션 그룹"
    agent_class._classification = "전문영역"
    return agent_class


def list_members() -> list[str]:
    """전문 솔루션 그룹 멤버 목록 반환"""
    return PROFESSIONAL_SOLUTION_GROUP["members"]


def is_member(agent_class) -> bool:
    """에이전트가 그룹 멤버인지 확인"""
    return agent_class.__name__ in PROFESSIONAL_SOLUTION_GROUP["members"]

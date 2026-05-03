"""
tools/visualize_system.py
==========================
69-agent system architecture text map generator
Usage: python -X utf8 tools/visualize_system.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

AGENT_GROUPS = {
    "A. 세무 (4)": ["TaxAgent", "VATAgent", "RDTaxCreditAgent", "InvestTaxCreditAgent"],
    "B. 법인 운영 (5)": ["ExecutivePayAgent", "PerformancePayAgent", "ProvisionalPaymentAgent", "RelatedPartyAgent", "DividendPolicyAgent"],
    "C. 주식·승계 (7)": ["StockAgent", "NomineeStockAgent", "SuccessionAgent", "GiftTaxAgent", "InheritanceTaxAgent", "MAValuationAgent", "IPOAgent"],
    "D. 재무·리스크 (4)": ["FinanceAgent", "CreditRatingAgent", "DebtRestructuringAgent", "CashFlowAgent"],
    "E. 특허·기술 (3)": ["PatentAgent", "RDTaxCreditAgent*", "DXAgent"],
    "F. 부동산 (5)": ["RealEstateAgent", "real_estate_valuation", "real_estate_desktop_appraisal", "CostAnalysisAgent", "FinancialForecastAgent"],
    "G. 자금·외부 (6)": ["PolicyFundingAgent", "SubcontractAgent", "FranchiseAgent", "GlobalExpansionAgent", "IndustryAgent", "LaborAgent"],
    "H. 전문 (6)": ["LegalAgent", "InsuranceAgent", "SocialInsuranceAgent", "ESGRiskAgent", "BusinessPlanAgent", "WebResearchAgent"],
    "신설 14종": [
        "KoreanAccountingEnforcer", "LongTermAssetTransfer", "ChildCorpDesign",
        "SpecialCorpTransaction", "CivilTrust", "TreasuryStockStrategy",
        "ValuationOptimization", "RetainedEarningsManagement", "CorporateBenefitsFund",
        "RealEstateDesktopAppraisal", "PatentCashflowSimulator", "ScenarioComparator",
        "PIIMaskingAgent", "InitialMeetingOrchestrator",
    ],
    "자가 진화 3종": ["DiscoveryAgent", "ExecutorAgent", "VerifierAgent"],
    "AutoFix": ["AutoFixV2"],
}

PATTERNS = {
    "succession_mega": ("가업승계 메가", 11),
    "stock_valuation_precision": ("비상장주식 정밀 평가", 5),
    "retained_earnings_integrated": ("미처분이익잉여금 통합", 5),
    "capital_structure_funding": ("재무구조+정책자금", 4),
    "patent_npv": ("특허 NPV 통합", 4),
}


def box(title: str, items: list[str], width: int = 62) -> str:
    lines = [f"┌{'─'*(width-2)}┐"]
    lines.append(f"│  {title:<{width-4}}│")
    lines.append(f"├{'─'*(width-2)}┤")
    for item in items:
        lines.append(f"│  • {item:<{width-6}}│")
    lines.append(f"└{'─'*(width-2)}┘")
    return "\n".join(lines)


def print_architecture():
    w = 62
    sep = "=" * w

    print(f"\n{sep}")
    print("  중기이코노미 AI 컨설팅 하네스 v5.8 — 시스템 맵")
    print(f"  에이전트: 69개 | 슬래시 명령: 78개 | 협력 패턴: 5종")
    print(sep)

    # User input layer
    print()
    print("  [사용자] 자연어 입력 1회")
    print("        │")
    print("        ▼")
    print(f"  ┌{'─'*56}┐")
    print(f"  │  CommandRouter  (78개 슬래시 명령 / F1 스코어 매칭) │")
    print(f"  └{'─'*56}┘")
    print("        │ auto_route / ask_user / no_match")
    print("        ▼")

    # Collaboration patterns
    print(f"  ┌{'─'*56}┐")
    print(f"  │  CollaborationPatterns  (5종 메가 패턴)           │")
    print(f"  │                                                    │")
    for key, (name, cnt) in PATTERNS.items():
        print(f"  │    ★ {name:<24}  {cnt:2d}개 에이전트  │")
    print(f"  └{'─'*56}┘")
    print("        │")
    print("        ▼")

    # Agent groups
    print(f"  ┌{'─'*56}┐")
    print(f"  │  ACTIVE 에이전트 레이어 (69개)                     │")
    for grp, agents in AGENT_GROUPS.items():
        print(f"  │    [{grp}]  {len(agents)}종                         │"[:62] + "│")
    print(f"  └{'─'*56}┘")
    print("        │")
    print("        ▼")

    # Validation layer
    print(f"  ┌{'─'*56}┐")
    print(f"  │  self_check 4축 자동 검증                          │")
    print(f"  │    Axis1: 수치    Axis2: 법률                      │")
    print(f"  │    Axis3: 4자관점  Axis4: 회계기준(K-IFRS/SME)     │")
    print(f"  │  KoreanAccountingEnforcer (US-GAAP 용어 차단)      │")
    print(f"  └{'─'*56}┘")
    print("        │")
    print("        ▼")

    # Output layer
    print(f"  ┌{'─'*56}┐")
    print(f"  │  PPTPolisher → 표준 PPT 자동 검수                  │")
    print(f"  │  PostManagementTracker → 사후관리 자동 등록         │")
    print(f"  └{'─'*56}┘")
    print("        │")
    print("        ▼")
    print("  [사용자] PPT 보고서 수령")
    print()
    print(sep)
    print("  자가 진화 (매주 월요일 자동)")
    print("  09:00 Discovery → 10:00 Executor → 10:30 Verifier")
    print(sep)

    # Collaboration pattern detail
    print()
    print("  [메가 패턴 상세: 가업승계 종합]")
    succession_seq = [
        "① LongTermAssetTransfer  — 10년 로드맵",
        "② ChildCorpDesign        — 자녀법인 안전선",
        "③ SpecialCorpTransaction  — §45의5 회피",
        "④ CivilTrust             — 신탁 설계",
        "⑤ TreasuryStockStrategy  — 자기주식 5종",
        "⑥ ValuationOptimization  — 평가 최적화",
        "⑦ RetainedEarnings       — 이익잉여금",
        "⑧ CorporateBenefitsFund  — 사내복지기금",
        "⑨ InheritanceTaxAgent    — 상속·증여세",
        "⑩ TaxRefundClaim         — 경정청구",
        "⑪ ScenarioComparator     — 통합 비교",
    ]
    for s in succession_seq:
        print(f"     {s}")
    print()
    print(sep)


if __name__ == "__main__":
    print_architecture()

"""
workflows/collaboration_patterns.py
=====================================
신설 14종 + 기존 54개 = 68개 자동 협력 네트워크
5가지 협력 패턴 정의 + 자동 시퀀스 결정

사용 예:
    cp = CollaborationPatterns()
    result = cp.run_pattern("가업승계 종합 설계", company_data)
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Any

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)


# ──────────────────────────────────────────────────────────────
# 5가지 협력 패턴 정의
# ──────────────────────────────────────────────────────────────
PATTERNS: dict[str, dict] = {
    "succession_mega": {
        "name": "가업승계 메가",
        "triggers": ["가업승계 종합", "10년 자산 이전", "종합 승계", "가업승계종합"],
        "meta_entry":  "long_term_asset_transfer.LongTermAssetTransferAgent",
        "sequence": [
            "child_corp_design.ChildCorpDesignAgent",
            "special_corp_transaction.SpecialCorpTransactionAgent",
            "civil_trust.CivilTrustAgent",
            "treasury_stock_strategy.TreasuryStockStrategyAgent",
            "valuation_optimization.ValuationOptimizationAgent",
            "retained_earnings_management.RetainedEarningsManagementAgent",
            "corporate_benefits_fund.CorporateBenefitsFundAgent",
            "inheritance_gift_agent.InheritanceTaxAgent",
            "scenario_comparator.TaxRefundClaimAgent",
        ],
        "comparator": "scenario_comparator.ScenarioComparatorAgent",
        "stage_4_pipeline": True,
    },
    "stock_valuation_precision": {
        "name": "비상장주식 정밀 평가",
        "triggers": ["비상장주식 정밀 평가", "비상장 평가", "비상장정밀평가"],
        "meta_entry":  "valuation_optimization.ValuationOptimizationAgent",
        "sequence": [
            "real_estate_valuation.RealEstateValuationAgent",
            "real_estate_desktop_appraisal.RealEstateDesktopAppraisalAgent",
            "treasury_stock_strategy.TreasuryStockStrategyAgent",
            "retained_earnings_management.RetainedEarningsManagementAgent",
        ],
        "comparator": "scenario_comparator.ScenarioComparatorAgent",
        "stage_4_pipeline": False,
    },
    "retained_earnings_integrated": {
        "name": "미처분이익잉여금 통합",
        "triggers": ["미처분이익잉여금", "이익잉여금 처리", "이익잉여금통합처리"],
        "meta_entry":  "retained_earnings_management.RetainedEarningsManagementAgent",
        "sequence": [
            "treasury_stock_strategy.TreasuryStockStrategyAgent",
            "corporate_benefits_fund.CorporateBenefitsFundAgent",
            "inheritance_gift_agent.InheritanceTaxAgent",
            "child_corp_design.ChildCorpDesignAgent",
        ],
        "comparator": "scenario_comparator.ScenarioComparatorAgent",
        "stage_4_pipeline": False,
    },
    "capital_structure_funding": {
        "name": "재무구조+정책자금",
        "triggers": ["재무구조 개선", "자금조달", "재무구조자금조달"],
        "meta_entry":  "capital_structure_improvement.CapitalStructureImprovementAgent",
        "sequence": [
            "scenario_comparator.TaxRefundClaimAgent",
        ],
        "comparator": "scenario_comparator.ScenarioComparatorAgent",
        "stage_4_pipeline": False,
    },
    "patent_npv": {
        "name": "특허 NPV 통합",
        "triggers": ["특허 NPV", "특허 통합", "특허NPV통합"],
        "meta_entry":  "patent_cashflow_simulator.PatentCashflowSimulator",
        "sequence": [
            "valuation_optimization.ValuationOptimizationAgent",
            "scenario_comparator.ScenarioComparatorAgent",
        ],
        "comparator": None,
        "stage_4_pipeline": False,
    },
}


# ──────────────────────────────────────────────────────────────
# 에이전트 동적 로드
# ──────────────────────────────────────────────────────────────
def _load_agent(module_class: str) -> Any:
    """'module_name.ClassName' 형식으로 동적 로드"""
    module_name, class_name = module_class.rsplit(".", 1)
    full_module = f"agents.active.{module_name}"
    try:
        mod = importlib.import_module(full_module)
        return getattr(mod, class_name)()
    except Exception as e:
        return None


# ──────────────────────────────────────────────────────────────
# CollaborationPatterns
# ──────────────────────────────────────────────────────────────
class CollaborationPatterns:
    """
    사용 예:
        cp = CollaborationPatterns()
        result = cp.run_pattern("가업승계 종합 설계", company_data)
        print(result["pattern_name"], result["agents_called"])
    """

    def detect_pattern(self, user_input: str) -> dict | None:
        for pattern_key, config in PATTERNS.items():
            for trigger in config["triggers"]:
                if trigger in user_input:
                    return {"key": pattern_key, "config": config}
        return None

    def run_pattern(self, user_input: str, company_data: dict) -> dict:
        """자연어 입력 → 패턴 감지 → 자동 시퀀스 실행"""
        match = self.detect_pattern(user_input)
        if not match:
            return {"status": "no_pattern", "user_input": user_input}

        config = match["config"]
        pattern_key = match["key"]
        agents_called: list[str] = []
        results: dict[str, Any] = {}

        # 1. 메타 진입점
        meta_cls_str = config["meta_entry"]
        meta_agent = _load_agent(meta_cls_str)
        if meta_agent:
            meta_result = meta_agent.analyze(company_data)
            results["_meta"] = meta_result
            agents_called.append(meta_cls_str.split(".")[-1])

        # 2. 시퀀스 자동 호출
        for agent_str in config["sequence"]:
            agent = _load_agent(agent_str)
            if agent:
                try:
                    r = agent.analyze(company_data)
                    results[agent_str.split(".")[-1]] = r
                    agents_called.append(agent_str.split(".")[-1])
                except Exception:
                    pass

        # 3. 비교기
        if config.get("comparator"):
            comp = _load_agent(config["comparator"])
            if comp:
                comp_data = {**company_data, "scenarios": [
                    v for v in results.values()
                    if isinstance(v, dict) and "scenarios" in v
                ]}
                comp_result = comp.analyze(comp_data)
                results["_comparison"] = comp_result
                agents_called.append("ScenarioComparatorAgent")

        # 4. 4단계 파이프라인 (가업승계 메가에만)
        pipeline_result = None
        if config.get("stage_4_pipeline"):
            from workflows.solution_pipeline import SolutionPipeline
            meta_text = results.get("_meta", {}).get("text", "가업승계 종합 분석")
            pipeline = SolutionPipeline(meta_text, "CollaborationPatterns")
            pipeline_result = pipeline.run()
            results["_4stage"] = pipeline_result.to_dict()

        # 5. 회계기준 강제
        from agents.active.korean_accounting_enforcer import KoreanAccountingStandardsEnforcer
        enforcer = KoreanAccountingStandardsEnforcer()
        is_sme = not company_data.get("is_listed", False)
        results = {k: enforcer.enforce(v, {"is_sme": is_sme})
                   if isinstance(v, dict) else v
                   for k, v in results.items()}

        return {
            "status": "completed",
            "pattern_key": pattern_key,
            "pattern_name": config["name"],
            "agents_called": agents_called,
            "results": results,
            "pipeline": pipeline_result.to_dict() if pipeline_result else None,
            "_accounting_standard": results.get("_meta", {}).get("_accounting_standard"),
        }

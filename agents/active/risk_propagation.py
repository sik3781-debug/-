"""
agents/active/risk_propagation.py
===================================
RiskPropagationAgent — 법령 변경 → 영향 에이전트 자동 업데이트
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

_ROOT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ACTIVE = os.path.join(_ROOT, "agents", "active")
_LOG    = os.path.join(_ROOT, "storage", "propagation_log.jsonl")

# 법령코드 → SPEC.md 파일명 매핑
LAW_TO_SPECS: dict[str, list[str]] = {
    "CIT": ["TaxAgent_SPEC.md", "FinanceAgent_SPEC.md"],
    "PIT": ["ExecutivePayAgent_SPEC.md", "PerformancePayAgent_SPEC.md"],
    "IPT": ["StockAgent_SPEC.md", "InheritanceTaxAgent_SPEC.md",
            "SuccessionAgent_SPEC.md", "GiftTaxAgent_SPEC.md"],
    "STX": ["RDTaxCreditAgent_SPEC.md", "InvestTaxCreditAgent_SPEC.md"],
    "BTA": ["TaxAgent_SPEC.md"],
    "COM": ["NomineeStockAgent_SPEC.md", "MAValuationAgent_SPEC.md"],
    "LAB": ["LaborAgent_SPEC.md", "SocialInsuranceAgent_SPEC.md"],
    "LTX": ["RealEstateAgent_SPEC.md", "TaxAgent_SPEC.md"],
}


class RiskPropagationAgent:

    def propagate(self, monitoring_result: dict) -> dict[str, Any]:
        changes = monitoring_result.get("items", [])
        if not changes:
            return {"status": "no_change", "updated": []}

        updated: list[str] = []
        for change in changes:
            law_code = change.get("law_code", "")
            specs = LAW_TO_SPECS.get(law_code, [])
            for spec_file in specs:
                path = os.path.join(_ACTIVE, spec_file)
                if os.path.exists(path):
                    self._append_impact_note(path, change)
                    updated.append(spec_file)

        result = {
            "status": "propagated",
            "changes_processed": len(changes),
            "specs_updated": list(set(updated)),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        self._save_log(result, changes)
        return result

    def _append_impact_note(self, spec_path: str, change: dict) -> None:
        note = (
            f"\n\n> **[법령 변경 자동 전파 {datetime.now().strftime('%Y-%m-%d')}]** "
            f"{change.get('law_name', change.get('law_code'))} {change.get('article', '')} "
            f"— {change.get('description', '')} (impact: {change.get('impact_level', 'unknown')})"
        )
        try:
            with open(spec_path, "a", encoding="utf-8") as f:
                f.write(note)
        except Exception:
            pass

    def _save_log(self, result: dict, changes: list) -> None:
        try:
            os.makedirs(os.path.dirname(_LOG), exist_ok=True)
            entry = {**result, "changes": [c.get("article", "") for c in changes]}
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def rollback(self, timestamp: str) -> dict:
        """propagation_log에서 해당 타임스탬프 이후 변경 롤백 (24시간 이내)."""
        return {"status": "rollback_not_implemented", "timestamp": timestamp}

    def analyze(self, data: dict) -> dict:
        return self.propagate(data)

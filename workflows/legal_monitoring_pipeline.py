"""
workflows/legal_monitoring_pipeline.py
========================================
법령 모니터링 통합 파이프라인:
LegalMonitoringHub → RiskPropagationAgent → HistoricalCaseImpactAgent

스케줄: 일간 06:00 (legal_monitoring_scheduler.ps1 또는 Task Scheduler)
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_NOTIFY = os.path.join(_ROOT, "storage", "notifications.jsonl")


def _notify(message: str, urgency: str = "info") -> None:
    try:
        os.makedirs(os.path.dirname(_NOTIFY), exist_ok=True)
        entry = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "urgency": urgency,
            "message": message,
        }
        with open(_NOTIFY, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


class LegalMonitoringPipeline:
    """
    실행 순서:
    1. LegalMonitoringHub.detect_changes()
    2. 변경 있으면 → RiskPropagationAgent.propagate()
    3. 변경 있으면 → HistoricalCaseImpactAgent 트리거 (proposal 단계: 알림만)
    4. 결과 notifications.jsonl 기록
    """

    def run(self, target_date: str | None = None) -> dict[str, Any]:
        import sys
        sys.path.insert(0, _ROOT)

        # Step 1: 법령 모니터링
        from agents.active.legal_monitoring_hub import LegalMonitoringHub
        hub = LegalMonitoringHub()
        monitoring = hub.detect_changes(target_date)

        if monitoring.get("changes_detected", 0) == 0:
            return {
                "status": "no_change",
                "date": monitoring.get("date"),
                "mode": monitoring.get("mode"),
            }

        # Step 2: 영향 자동 전파
        from agents.active.risk_propagation import RiskPropagationAgent
        propagator = RiskPropagationAgent()
        propagation = propagator.propagate(monitoring)

        # Step 3: 기존 사례 영향 알림 (HistoricalCaseImpact proposal 단계)
        changes_high = [
            c for c in monitoring.get("items", [])
            if c.get("impact_level") == "high"
        ]
        if changes_high:
            for ch in changes_high:
                _notify(
                    f"[법령 변경 HIGH] {ch.get('law_name')} {ch.get('article')} — "
                    f"{ch.get('description')} → 기존 사례 영향 점검 필요",
                    urgency="high",
                )

        return {
            "status": "completed",
            "date": monitoring.get("date"),
            "changes_detected": monitoring.get("changes_detected", 0),
            "specs_updated": propagation.get("specs_updated", []),
            "high_impact_notifications": len(changes_high),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }


if __name__ == "__main__":
    import sys
    pipeline = LegalMonitoringPipeline()
    result = pipeline.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("status") in ("completed", "no_change") else 1)

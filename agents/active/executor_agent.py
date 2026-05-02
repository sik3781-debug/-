"""
agents/active/executor_agent.py
================================
SystemEnhancementExecutorAgent
Discovery 보고서 → 자동/승인/차단 분류 후 고도화 실행.
스케줄: 월요일 10:00 (Discovery 1시간 후)
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import date
from typing import Any


_ROOT    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_EXEC_LOG = os.path.join(_ROOT, "logs", "executor.jsonl")


class SystemEnhancementExecutorAgent:
    """
    실행 권한 분류:
      AUTO_EXECUTE  — KPI 보정, AutoFix 패턴 영구 적용, 미사용 격리
      USER_APPROVAL — 신설 에이전트, 신설 슬래시 명령, Sunset 확정
      BLOCKED       — 정본 CLAUDE.md, 핵심 에이전트, dotfiles
    """

    AUTO_EXECUTE   = {"kpi_correction", "autofix_pattern_promote",
                      "performance_optimization_candidate"}
    USER_APPROVAL  = {"new_slash_command_candidate", "new_simulator_candidate",
                      "sunset_candidate", "new_agent"}
    BLOCKED        = {"modify_canonical_claude_md", "modify_core_agent",
                      "modify_dotfiles"}

    def execute(self, discovery_report: dict,
                user_approval_fn=None) -> dict:
        """
        Parameters
        ----------
        discovery_report : SystemEnhancementDiscoveryAgent.discover() 결과
        user_approval_fn : callable(item) -> bool (None이면 자동 승인 스킵)
        """
        results: list[dict] = []
        changes: list[str]  = []

        for item in discovery_report.get("prioritized_top10", []):
            action = item.get("action", "")
            category = self._classify(action)

            if category == "BLOCKED":
                results.append({"item": item, "status": "blocked",
                                 "reason": "고위험 항목 — 수동 처리 필요"})
                continue

            if category == "AUTO_EXECUTE":
                result = self._auto_execute(item)
                if result.get("changed"):
                    changes.append(f"AUTO: {action} ({item['count']}건)")
                results.append({"item": item, "status": "auto_executed", **result})

            else:  # USER_APPROVAL
                if user_approval_fn and user_approval_fn(item):
                    result = self._auto_execute(item)
                    changes.append(f"APPROVED: {action}")
                    results.append({"item": item, "status": "user_approved", **result})
                else:
                    results.append({"item": item, "status": "pending_approval",
                                    "message": f"승인 대기: {action}"})

        summary = self._commit_changes(changes)
        self._log(results, changes)

        return {
            "date":    date.today().isoformat(),
            "results": results,
            "changes": changes,
            "summary": summary,
        }

    # ── 분류 ─────────────────────────────────────────────────

    def _classify(self, action: str) -> str:
        if action in self.BLOCKED:
            return "BLOCKED"
        if action in self.AUTO_EXECUTE:
            return "AUTO_EXECUTE"
        return "USER_APPROVAL"

    # ── 자동 실행 ─────────────────────────────────────────────

    def _auto_execute(self, item: dict) -> dict:
        action = item.get("action", "")
        items  = item.get("items", [])

        if action == "autofix_pattern_promote":
            return self._promote_autofix_patterns(items)

        if action == "kpi_correction":
            return self._apply_kpi_corrections(items)

        if action == "performance_optimization_candidate":
            return {"changed": False,
                    "message": f"성능 최적화 후보 {len(items)}개 — 수동 검토 권장"}

        return {"changed": False, "message": f"미구현 액션: {action}"}

    def _promote_autofix_patterns(self, patterns: list) -> dict:
        """AutoFix 패턴 영구 적용 — error_patterns.jsonl 플래그 업데이트"""
        from agents.autofix_agent_v2 import AutoFixAgentV2
        fixer = AutoFixAgentV2()
        promoted = []
        for p in fixer.patterns:
            if p["pattern"] in patterns and not p.get("permanent_applied"):
                p["permanent_applied"] = True
                promoted.append(p["pattern"])
        if promoted:
            fixer._save_patterns()
        return {"changed": bool(promoted),
                "promoted": promoted,
                "message": f"AutoFix 패턴 {len(promoted)}개 영구 적용"}

    def _apply_kpi_corrections(self, agents: list) -> dict:
        """KPI [추정] 마커가 있는 SPEC.md 일괄 보정 (추정값 채움)"""
        from monitoring.kpi_collector import KPICollector
        collector = KPICollector()
        updated = collector.promote_spec_estimates()
        return {"changed": bool(updated),
                "updated_files": updated,
                "message": f"KPI 실측값 적용: {len(updated)}개 파일"}

    # ── git commit ────────────────────────────────────────────

    def _commit_changes(self, changes: list[str]) -> str:
        if not changes:
            return "변경사항 없음"
        msg = f"feat: weekly auto-enhancement {date.today()} ({len(changes)} items)"
        try:
            subprocess.run(
                ["git", "-C", _ROOT, "add", "-A"],
                capture_output=True, timeout=30
            )
            result = subprocess.run(
                ["git", "-C", _ROOT, "commit", "-m", msg],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout.strip() or "committed"
        except Exception as e:
            return f"commit_error: {e}"

    # ── 로그 ─────────────────────────────────────────────────

    def _log(self, results: list, changes: list) -> None:
        os.makedirs(os.path.dirname(_EXEC_LOG), exist_ok=True)
        entry = {
            "date": date.today().isoformat(),
            "total": len(results),
            "auto_executed": sum(1 for r in results if r["status"] == "auto_executed"),
            "pending_approval": sum(1 for r in results if r["status"] == "pending_approval"),
            "blocked": sum(1 for r in results if r["status"] == "blocked"),
            "changes": changes,
        }
        with open(_EXEC_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

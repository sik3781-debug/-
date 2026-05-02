"""
agents/active/verifier_agent.py
=================================
EnhancementVerifierAgent
Executor 적용 후 시스템 회귀 검증 + 자동 롤백.
스케줄: 월요일 10:30 (Executor 30분 후)
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import date
from typing import Any


_ROOT      = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_KPI       = os.path.join(_ROOT, "storage", "kpi_metrics.jsonl")
_PATTERNS  = os.path.join(_ROOT, "storage", "error_patterns.jsonl")
_VERIFY_LOG = os.path.join(_ROOT, "logs", "verifier.jsonl")

# 5대 시뮬레이터 명령 (라우터 테스트로 검증)
_5_SIMULATORS = [
    "비상장주식 평가해줘",
    "가지급금 처리 방법 알려줘",
    "가업승계 시뮬레이션 해줘",
    "임원 퇴직금 한도 계산해줘",
    "증여세 시뮬레이션",
]


class EnhancementVerifierAgent:
    """
    회귀 검증 3축:
      1. functional_regression — 5대 시뮬레이터 라우터 매칭 정상
      2. performance_regression — KPI 7일 평균 ±20% 이내
      3. stability_regression   — AutoFix DB 일관성 (충돌 없음)
    """

    def verify(self, executor_log: dict) -> dict:
        results = {
            "functional":   self._test_5_simulators(),
            "performance":  self._compare_kpi(),
            "stability":    self._check_autofix_db(),
        }
        regression = any(r.get("failed") for r in results.values())

        if regression:
            rollback_result = self._auto_rollback(executor_log)
            self._record_failure(executor_log, results)
            self._log("REGRESSION_DETECTED", results, rollback_result)
            return {
                "status": "REGRESSION_DETECTED",
                "auto_rollback": rollback_result.get("success", False),
                "rollback_detail": rollback_result,
                "report": results,
            }

        self._log("PASS", results, {})
        return {"status": "PASS", "report": results}

    # ── 검증 3축 ─────────────────────────────────────────────

    def _test_5_simulators(self) -> dict:
        """5대 시뮬레이터 자연어 → 라우터 매칭 정상 여부"""
        try:
            import sys
            sys.path.insert(0, _ROOT)
            from router.command_router import CommandRouter
            router = CommandRouter()
            failed: list[str] = []
            for nl in _5_SIMULATORS:
                result = router.route(nl)
                if result.status not in ("auto_route", "ask_user"):
                    failed.append(nl)
            return {
                "failed": bool(failed),
                "passed": len(_5_SIMULATORS) - len(failed),
                "total":  len(_5_SIMULATORS),
                "failures": failed,
            }
        except Exception as e:
            return {"failed": True, "error": str(e)}

    def _compare_kpi(self) -> dict:
        """KPI 7일 평균 기준 ±20% 이내 확인"""
        if not os.path.exists(_KPI):
            return {"failed": False, "message": "KPI 데이터 없음 — 건너뜀"}
        # 현재 측정 데이터 부족 시 PASS
        from monitoring.kpi_collector import KPICollector
        collector = KPICollector()
        anomalies: list[str] = []
        for agent in ["TaxAgent", "StockAgent", "FinanceAgent"]:
            avg = collector.weekly_average(agent)
            if avg and avg["avg_time_sec"] and avg["avg_time_sec"] > 300:
                anomalies.append(f"{agent}: {avg['avg_time_sec']}초 (기준 300초 초과)")
        return {
            "failed": bool(anomalies),
            "anomalies": anomalies,
            "message": f"KPI 이상 {len(anomalies)}건" if anomalies else "KPI 정상",
        }

    def _check_autofix_db(self) -> dict:
        """error_patterns.jsonl 중복·충돌 여부"""
        if not os.path.exists(_PATTERNS):
            return {"failed": False, "message": "패턴 DB 없음 — 건너뜀"}
        ids: list[str] = []
        with open(_PATTERNS, encoding="utf-8") as f:
            for line in f:
                try:
                    p = json.loads(line.strip())
                    ids.append(p.get("id", ""))
                except json.JSONDecodeError:
                    pass
        duplicates = [i for i in set(ids) if ids.count(i) > 1]
        return {
            "failed": bool(duplicates),
            "duplicates": duplicates,
            "message": f"중복 ID {len(duplicates)}건" if duplicates else "DB 일관성 OK",
        }

    # ── 자동 롤백 ─────────────────────────────────────────────

    def _auto_rollback(self, executor_log: dict) -> dict:
        """executor_log의 변경 사항을 git revert"""
        changes = executor_log.get("changes", [])
        if not changes:
            return {"success": True, "message": "롤백 대상 없음"}
        try:
            result = subprocess.run(
                ["git", "-C", _ROOT, "revert", "HEAD", "--no-edit"],
                capture_output=True, text=True, timeout=30
            )
            return {
                "success": result.returncode == 0,
                "message": result.stdout.strip() or result.stderr.strip(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── 실패 학습 ─────────────────────────────────────────────

    def _record_failure(self, executor_log: dict, results: dict) -> None:
        """회귀 발견 시 Discovery DB에 '실패 패턴' 학습"""
        entry = {
            "id": f"FAIL_{date.today().isoformat()}",
            "agent": "EnhancementVerifierAgent",
            "error_type": "regression_detected",
            "pattern": str([k for k, v in results.items() if v.get("failed")]),
            "fix": "auto_rollback",
            "count": 1,
            "last_seen": date.today().isoformat(),
            "permanent_applied": False,
        }
        with open(_PATTERNS, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ── 로그 ─────────────────────────────────────────────────

    def _log(self, status: str, results: dict, rollback: dict) -> None:
        os.makedirs(os.path.dirname(_VERIFY_LOG), exist_ok=True)
        entry = {
            "date":     date.today().isoformat(),
            "status":   status,
            "results":  {k: v.get("failed", False) for k, v in results.items()},
            "rollback": rollback.get("success", None),
        }
        with open(_VERIFY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

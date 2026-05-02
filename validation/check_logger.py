"""
validation/check_logger.py
==========================
자가검증 결과를 logs/self_check.jsonl 에 기록하고
일간 통계를 집계하는 모듈.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, date


_HERE   = os.path.dirname(os.path.abspath(__file__))
_ROOT   = os.path.dirname(_HERE)
_LOG_DIR  = os.path.join(_ROOT, "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "self_check.jsonl")


class CheckLogger:
    """
    사용 예:
        logger = CheckLogger()
        checker = SelfCheck(logger=logger)
        ...
        stats = logger.daily_stats()
    """

    def __init__(self, log_path: str = _LOG_FILE):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def log(self, check_result: dict) -> None:
        """검증 결과 1건을 JSONL에 추가"""
        entry = {
            "ts":           check_result.get("timestamp", datetime.now().isoformat()),
            "agent":        check_result.get("agent", "unknown"),
            "overall_pass": check_result.get("overall_pass", False),
            "failed_axes":  check_result.get("failed_axes", []),
            "action":       check_result.get("action", "unknown"),
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def daily_stats(self, target_date: date | None = None) -> dict:
        """
        일간 통계 반환.

        Returns
        -------
        {
            "date": "2026-05-03",
            "total": int,
            "pass_count": int,
            "pass_rate": float,
            "axis_fail_counts": {"axis_1": N, "axis_2": N, "axis_3": N},
            "auto_fix_count": int,
            "top_failing_agents": [(agent, fail_count), ...],
        }
        """
        if target_date is None:
            target_date = date.today()
        date_str = target_date.isoformat()

        total = 0
        pass_count = 0
        auto_fix_count = 0
        axis_fails: dict[str, int] = defaultdict(int)
        agent_fails: dict[str, int] = defaultdict(int)

        if not os.path.exists(self.log_path):
            return self._empty_stats(date_str)

        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                if not entry.get("ts", "").startswith(date_str):
                    continue
                total += 1
                if entry.get("overall_pass"):
                    pass_count += 1
                else:
                    for ax in entry.get("failed_axes", []):
                        axis_fails[ax] += 1
                    agent_fails[entry.get("agent", "unknown")] += 1
                if entry.get("action") == "auto_fix":
                    auto_fix_count += 1

        pass_rate = pass_count / total if total else 0.0
        top_agents = sorted(agent_fails.items(), key=lambda x: -x[1])[:5]

        return {
            "date": date_str,
            "total": total,
            "pass_count": pass_count,
            "pass_rate": round(pass_rate, 3),
            "axis_fail_counts": {
                "axis_1_calculation":  axis_fails.get("axis_1_calculation", 0),
                "axis_2_legal":        axis_fails.get("axis_2_legal", 0),
                "axis_3_perspective":  axis_fails.get("axis_3_perspective", 0),
            },
            "auto_fix_count": auto_fix_count,
            "top_failing_agents": top_agents,
        }

    def _empty_stats(self, date_str: str) -> dict:
        return {
            "date": date_str, "total": 0, "pass_count": 0, "pass_rate": 0.0,
            "axis_fail_counts": {
                "axis_1_calculation": 0, "axis_2_legal": 0, "axis_3_perspective": 0,
            },
            "auto_fix_count": 0, "top_failing_agents": [],
        }

    def tail(self, n: int = 20) -> list[dict]:
        """최근 N개 로그 항목 반환"""
        if not os.path.exists(self.log_path):
            return []
        lines: list[str] = []
        with open(self.log_path, encoding="utf-8") as f:
            lines = f.readlines()
        return [json.loads(l.strip()) for l in lines[-n:] if l.strip()]

"""
monitoring/kpi_collector.py
============================
에이전트 실행 시 자동 KPI 측정 + 7일 평균 자동 [추정]→[실측] 전환
"""
from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import datetime, date, timedelta
from contextlib import contextmanager


_ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KPI_FILE  = os.path.join(_ROOT, "storage", "kpi_metrics.jsonl")
_ACTIVE    = os.path.join(_ROOT, "agents", "active")


class KPICollector:
    """
    사용 예 (에이전트 실행 래퍼):
        collector = KPICollector()
        with collector.measure("TaxAgent") as m:
            result = agent.run(query)
            m["token_count"] = estimate_tokens(result)
    """

    def __init__(self, kpi_file: str = _KPI_FILE):
        self.kpi_file = kpi_file
        os.makedirs(os.path.dirname(kpi_file), exist_ok=True)

    @contextmanager
    def measure(self, agent_name: str):
        start = time.monotonic()
        metrics: dict = {"token_count": None, "accuracy_pct": None}
        try:
            yield metrics
        finally:
            elapsed = round(time.monotonic() - start, 2)
            self._record(agent_name, elapsed, metrics)

    def _record(self, agent: str, elapsed: float, extra: dict) -> None:
        entry = {
            "date":              date.today().isoformat(),
            "ts":                datetime.now().isoformat(timespec="seconds"),
            "agent":             agent,
            "response_time_sec": elapsed,
            "token_count":       extra.get("token_count"),
            "accuracy_pct":      extra.get("accuracy_pct"),
            "status":            "measured",
        }
        with open(self.kpi_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ── 7일 평균 집계 ─────────────────────────────────────────

    def weekly_average(self, agent: str) -> dict | None:
        """
        최근 7일 측정값 평균 반환.
        충분한 데이터 없으면 None.
        """
        cutoff = date.today() - timedelta(days=7)
        records: list[dict] = []

        if not os.path.exists(self.kpi_file):
            return None

        with open(self.kpi_file, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                if (r.get("agent") == agent
                        and r.get("status") == "measured"
                        and r.get("date", "") >= cutoff.isoformat()):
                    records.append(r)

        if len(records) < 3:  # 최소 3회 측정 필요
            return None

        times   = [r["response_time_sec"] for r in records if r.get("response_time_sec")]
        tokens  = [r["token_count"]       for r in records if r.get("token_count")]
        acc_lst = [r["accuracy_pct"]      for r in records if r.get("accuracy_pct")]

        return {
            "agent":             agent,
            "sample_count":      len(records),
            "avg_time_sec":      round(sum(times) / len(times), 1) if times else None,
            "avg_token_count":   round(sum(tokens) / len(tokens)) if tokens else None,
            "avg_accuracy_pct":  round(sum(acc_lst) / len(acc_lst), 1) if acc_lst else None,
        }

    # ── SPEC.md [추정] → [실측] 전환 ────────────────────────────

    def promote_spec_estimates(self) -> list[str]:
        """
        weekly_average 데이터 있는 에이전트의 SPEC.md에서
        '[추정: ...]' → '[실측: X초 (7일평균 N회)]' 로 교체.
        반환: 갱신된 파일 목록
        """
        updated: list[str] = []
        for fname in os.listdir(_ACTIVE):
            if not fname.endswith("_SPEC.md"):
                continue
            agent = fname.replace("_SPEC.md", "")
            avg = self.weekly_average(agent)
            if not avg:
                continue

            spec_path = os.path.join(_ACTIVE, fname)
            with open(spec_path, encoding="utf-8") as f:
                content = f.read()

            import re
            new_content = re.sub(
                r'\[보정필요: KPI\]|\[추정\]',
                (f"[실측: {avg['avg_time_sec']}초 "
                 f"(7일평균 {avg['sample_count']}회)]"),
                content,
            )
            if new_content != content:
                with open(spec_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                updated.append(fname)

        return updated

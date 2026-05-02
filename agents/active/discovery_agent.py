"""
agents/active/discovery_agent.py
=================================
SystemEnhancementDiscoveryAgent
주간 스캔으로 7가지 고도화 기회 자동 발견·우선순위 산출.
스케줄: 월요일 09:00 자동 (self_evolution_scheduler.ps1)
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import date, timedelta

_ROOT        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PATTERNS    = os.path.join(_ROOT, "storage", "error_patterns.jsonl")
_KPI         = os.path.join(_ROOT, "storage", "kpi_metrics.jsonl")
_ROUTER_LOG  = os.path.join(_ROOT, "logs", "router.jsonl")
_SELF_CHECK  = os.path.join(_ROOT, "logs", "self_check.jsonl")
_CMD_JSON    = os.path.join(_ROOT, "..", "junggi-workspace", "claude-code",
                            "commands", "command_router.json")
_DISCOVERY   = os.path.join(_ROOT, "..", "junggi-workspace", "discovery")


def _load_jsonl(path: str, days: int = 7) -> list[dict]:
    if not os.path.exists(path):
        return []
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line.strip())
                if r.get("date", r.get("ts", "9999")) >= cutoff:
                    records.append(r)
            except json.JSONDecodeError:
                pass
    return records


class SystemEnhancementDiscoveryAgent:
    """
    사용 예:
        agent = SystemEnhancementDiscoveryAgent()
        report = agent.discover()
        print(report["summary"])
    """

    def discover(self) -> dict:
        opps = {
            "1_recurring_errors":         self._find_recurring_errors(),
            "2_frequent_unmatched_nl":    self._find_frequent_nl(),
            "3_unused_commands":          self._find_unused_commands(),
            "4_kpi_underperformers":      self._find_kpi_underperformers(),
            "5_perspective_gaps":         self._find_perspective_gaps(),
            "6_autofix_promotable":       self._find_autofix_patterns(),
            "7_new_simulator_candidates": self._find_simulator_candidates(),
        }
        prioritized = self._prioritize(opps)
        report = self._generate_report(prioritized, opps)
        self._save_report(report)
        return report

    # ── 7가지 발견 로직 ───────────────────────────────────────

    def _find_recurring_errors(self) -> dict:
        """error_patterns.jsonl에서 7일 이상 반복 패턴"""
        patterns = _load_jsonl(_PATTERNS, days=365)
        recurring = [p for p in patterns if p.get("count", 0) >= 7
                     and not p.get("permanent_applied")]
        return {"count": len(recurring), "items": [p["pattern"] for p in recurring[:5]],
                "action": "permanent_fix_candidate"}

    def _find_frequent_nl(self) -> dict:
        """router.jsonl에서 매칭 실패 자연어 빈도"""
        logs = _load_jsonl(_ROUTER_LOG, days=7)
        no_match = [r.get("input", "") for r in logs
                    if r.get("status") == "no_match" and r.get("input")]
        counter = Counter(no_match)
        top = counter.most_common(5)
        return {"count": len(top), "items": [t[0] for t in top],
                "action": "new_slash_command_candidate"}

    def _find_unused_commands(self) -> dict:
        """30일간 호출 0회 슬래시 명령"""
        logs = _load_jsonl(_ROUTER_LOG, days=30)
        used = {r.get("matched_command", "") for r in logs if r.get("matched_command")}
        # command_router.json에서 전체 명령 목록 로드
        all_cmds: set[str] = set()
        if os.path.exists(_CMD_JSON):
            with open(_CMD_JSON, encoding="utf-8") as f:
                raw = json.load(f)
            all_cmds = {k for k in raw if k.startswith("/")}
        unused = sorted(all_cmds - used)
        return {"count": len(unused), "items": unused[:10],
                "action": "sunset_candidate"}

    def _find_kpi_underperformers(self) -> dict:
        """KPI 목표 미달 에이전트"""
        records = _load_jsonl(_KPI, days=7)
        by_agent: dict[str, list[float]] = defaultdict(list)
        for r in records:
            if r.get("response_time_sec") and r.get("agent"):
                by_agent[r["agent"]].append(r["response_time_sec"])
        underperformers = []
        for agent, times in by_agent.items():
            avg = sum(times) / len(times)
            if avg > 120:  # 2분 초과
                underperformers.append({"agent": agent, "avg_sec": round(avg, 1)})
        return {"count": len(underperformers), "items": underperformers[:5],
                "action": "performance_optimization_candidate"}

    def _find_perspective_gaps(self) -> dict:
        """4자관점 누락 빈발 영역 (self_check.jsonl 분석)"""
        logs = _load_jsonl(_SELF_CHECK, days=7)
        axis3_fails = [r for r in logs
                       if "axis_3_perspective" in r.get("failed_axes", [])]
        by_agent: Counter = Counter(r.get("agent", "unknown") for r in axis3_fails)
        top = by_agent.most_common(3)
        return {"count": len(axis3_fails), "items": [t[0] for t in top],
                "action": "perspective_template_enhancement"}

    def _find_autofix_patterns(self) -> dict:
        """AutoFix 5회+ 반복 패턴 → 영구 적용 후보"""
        patterns = _load_jsonl(_PATTERNS, days=365)
        promotable = [p for p in patterns
                      if p.get("count", 0) >= 5 and not p.get("permanent_applied")]
        return {"count": len(promotable),
                "items": [p["pattern"] for p in promotable[:5]],
                "action": "autofix_pattern_promote"}

    def _find_simulator_candidates(self) -> dict:
        """매칭 실패 자연어 중 시뮬레이터 키워드"""
        logs = _load_jsonl(_ROUTER_LOG, days=30)
        sim_keywords = ["평가", "시뮬", "계산", "한도", "세금", "금액"]
        candidates: list[str] = []
        for r in logs:
            inp = r.get("input", "")
            if r.get("status") == "no_match" and any(k in inp for k in sim_keywords):
                candidates.append(inp)
        counter = Counter(candidates).most_common(3)
        return {"count": len(counter),
                "items": [t[0] for t in counter],
                "action": "new_simulator_candidate"}

    # ── 우선순위 산출 ─────────────────────────────────────────

    def _prioritize(self, opps: dict) -> list[dict]:
        WEIGHTS = {
            "1_recurring_errors":         (3, "HIGH"),
            "2_frequent_unmatched_nl":    (3, "HIGH"),
            "3_unused_commands":          (1, "LOW"),
            "4_kpi_underperformers":      (2, "MEDIUM"),
            "5_perspective_gaps":         (2, "MEDIUM"),
            "6_autofix_promotable":       (3, "HIGH"),
            "7_new_simulator_candidates": (2, "MEDIUM"),
        }
        result: list[dict] = []
        for key, data in opps.items():
            cnt   = data.get("count", 0)
            w, pr = WEIGHTS.get(key, (1, "LOW"))
            score = cnt * w
            if score > 0:
                result.append({
                    "key": key, "score": score, "priority": pr,
                    "count": cnt, "action": data.get("action", ""),
                    "items": data.get("items", []),
                })
        return sorted(result, key=lambda x: -x["score"])

    # ── 보고서 생성·저장 ──────────────────────────────────────

    def _generate_report(self, prioritized: list[dict], raw: dict) -> dict:
        top10 = prioritized[:10]
        return {
            "date": date.today().isoformat(),
            "total_opportunities": sum(d["count"] for d in raw.values()),
            "prioritized_top10": top10,
            "summary": (f"발견 기회 {sum(d['count'] for d in raw.values())}건 — "
                        f"TOP: {top10[0]['key'] if top10 else '없음'}"),
            "raw": raw,
        }

    def _save_report(self, report: dict) -> None:
        os.makedirs(_DISCOVERY, exist_ok=True)
        fname = os.path.join(_DISCOVERY,
                             f"discovery_report_{report['date']}.md")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"# 시스템 고도화 발견 보고서\n\n")
            f.write(f"**일자**: {report['date']}  \n")
            f.write(f"**발견 기회**: {report['total_opportunities']}건\n\n")
            f.write("## 우선순위 Top 10\n\n")
            f.write("| 순위 | 발견 유형 | 건수 | 우선도 | 권장 조치 |\n")
            f.write("|---|---|---|---|---|\n")
            for i, item in enumerate(report["prioritized_top10"], 1):
                f.write(f"| {i} | {item['key']} | {item['count']} | "
                        f"{item['priority']} | {item['action']} |\n")
            if report["prioritized_top10"]:
                f.write("\n## 세부 항목\n\n")
                for item in report["prioritized_top10"]:
                    f.write(f"### {item['key']}\n")
                    for sub in item.get("items", [])[:3]:
                        f.write(f"- {sub}\n")
                    f.write("\n")

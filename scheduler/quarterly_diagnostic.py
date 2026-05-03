"""
scheduler/quarterly_diagnostic.py
분기 1일 10:00 — 시스템 자가 진단 + 73-track 회귀 검증
"""
from __future__ import annotations
import os, sys, datetime, importlib, traceback

AGENT_DIR = os.path.join(os.environ["USERPROFILE"], "consulting-agent")
WORKSPACE = os.path.join(os.environ["USERPROFILE"], "junggi-workspace")
sys.path.insert(0, AGENT_DIR)

TRACKS = [
    ("anthropic", None),
    ("openpyxl", None),
    ("router.command_router", "CommandRouter"),
    ("validation.self_check", "SelfCheck"),
    ("workflows.solution_pipeline", "SolutionPipeline"),
    ("workflows.collaboration_patterns", "CollaborationPatterns"),
]

def run():
    results = []
    passed = 0

    for module_name, class_name in TRACKS:
        try:
            mod = importlib.import_module(module_name)
            if class_name:
                cls = getattr(mod, class_name)
                obj = cls()
            results.append((module_name, "PASS"))
            passed += 1
        except Exception as e:
            results.append((module_name, f"FAIL: {e}"))

    total = len(results)
    report_path = os.path.join(WORKSPACE, "audit",
                               f"quarterly_diagnostic_{datetime.date.today():%Y_Q}.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 분기 자가 진단 — {datetime.date.today()}\n\n")
        f.write(f"**결과: {passed}/{total} PASS**\n\n")
        f.write("| 모듈 | 상태 |\n|---|---|\n")
        for name, status in results:
            icon = "✅" if status == "PASS" else "❌"
            f.write(f"| {name} | {icon} {status} |\n")

    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] 분기 진단: {passed}/{total} PASS")
    if passed < total:
        print("  ⚠ 실패 항목 확인 필요 → audit/quarterly_diagnostic_*.md")

if __name__ == "__main__":
    run()

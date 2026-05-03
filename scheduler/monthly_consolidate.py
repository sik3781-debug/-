"""
scheduler/monthly_consolidate.py
월간 1일 07:00 — memory/ 6종 통합 정리 (빈 파일 제거 + 목차 갱신)
"""
from __future__ import annotations
import os, datetime, glob

WORKSPACE = os.path.join(os.environ["USERPROFILE"], "junggi-workspace")
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
CATEGORIES = ["고객사", "세법", "판례", "체크리스트", "사전", "룰북"]

def consolidate_category(cat_path: str) -> dict:
    files = glob.glob(os.path.join(cat_path, "**", "*.md"), recursive=True)
    empty = [f for f in files if os.path.getsize(f) == 0]
    for f in empty:
        os.remove(f)
    return {"total": len(files), "removed_empty": len(empty)}

def run():
    results = {}
    for cat in CATEGORIES:
        path = os.path.join(MEMORY_DIR, cat)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            results[cat] = {"total": 0, "removed_empty": 0}
            continue
        results[cat] = consolidate_category(path)

    report_path = os.path.join(WORKSPACE, "audit",
                               f"monthly_consolidate_{datetime.date.today():%Y%m}.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 월간 Memory Consolidate — {datetime.date.today():%Y년 %m월}\n\n")
        f.write("| 카테고리 | 파일 수 | 빈 파일 제거 |\n|---|---|---|\n")
        for cat, stat in results.items():
            f.write(f"| {cat} | {stat['total']} | {stat['removed_empty']} |\n")

    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] Monthly consolidate 완료")
    for cat, stat in results.items():
        print(f"  {cat}: {stat['total']}개 (제거 {stat['removed_empty']})")

if __name__ == "__main__":
    run()

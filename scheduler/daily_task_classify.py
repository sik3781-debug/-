"""
scheduler/daily_task_classify.py
일간 06:00 — TASKS.md 4자관점 자동 분류
"""
from __future__ import annotations
import os, sys, datetime

WORKSPACE = os.path.join(os.environ["USERPROFILE"], "junggi-workspace")
TASKS_FILE = os.path.join(WORKSPACE, "TASKS.md")

FOUR_PARTIES = {
    "법인": ["법인세", "손금", "익금", "세무조정", "법인", "비용처리"],
    "주주": ["배당", "상속", "증여", "주주", "지분", "가업승계"],
    "과세관청": ["국세청", "세무서", "조사", "과세", "탈세", "경정"],
    "금융기관": ["대출", "신용", "담보", "금융", "은행", "여신"],
}

def classify_line(line: str) -> list[str]:
    tags = []
    for party, keywords in FOUR_PARTIES.items():
        if any(kw in line for kw in keywords):
            tags.append(party)
    return tags or ["미분류"]

def run():
    if not os.path.exists(TASKS_FILE):
        print(f"[SKIP] TASKS.md 없음: {TASKS_FILE}")
        return

    with open(TASKS_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    classified = []
    stats = {p: 0 for p in FOUR_PARTIES}
    stats["미분류"] = 0

    for line in lines:
        tags = classify_line(line.rstrip())
        for t in tags:
            if t in stats:
                stats[t] += 1
        tag_str = " ".join(f"[{t}]" for t in tags) if tags != ["미분류"] else ""
        classified.append(line.rstrip() + (f"  <!-- {tag_str} -->" if tag_str else "") + "\n")

    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        f.writelines(classified)

    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] TASKS.md 4자관점 분류 완료")
    for k, v in stats.items():
        print(f"  {k}: {v}개")

if __name__ == "__main__":
    run()

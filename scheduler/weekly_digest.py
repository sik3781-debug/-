"""
scheduler/weekly_digest.py
주간 월 08:55 — 주간 업무 요약 생성 + 로컬 아카이브 저장
"""
from __future__ import annotations
import os, sys, datetime, json, glob

WORKSPACE = os.path.join(os.environ["USERPROFILE"], "junggi-workspace")
DECISIONS_DIR = os.path.join(WORKSPACE, "decisions")
OUTPUT_DIR = os.path.join(WORKSPACE, "audit")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run():
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    digest_path = os.path.join(OUTPUT_DIR, f"weekly_digest_{week_start:%Y-%m-%d}.md")

    recent_files = []
    for pattern in ["*.md", "*.json"]:
        recent_files += glob.glob(os.path.join(DECISIONS_DIR, pattern))
    recent_files.sort(key=os.path.getmtime, reverse=True)

    lines = [
        f"# 주간 다이제스트 — {week_start:%Y-%m-%d} 주차\n\n",
        f"생성: {datetime.datetime.now():%Y-%m-%d %H:%M}\n\n",
        f"## 최근 decisions/ 파일 ({len(recent_files[:10])}개)\n\n",
    ]
    for f in recent_files[:10]:
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f))
        lines.append(f"- [{os.path.basename(f)}]({f})  _{mtime:%m-%d %H:%M}_\n")

    with open(digest_path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)

    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] 주간 다이제스트 저장: {digest_path}")

if __name__ == "__main__":
    run()

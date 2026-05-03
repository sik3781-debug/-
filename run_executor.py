"""
run_executor.py — 주간 자가 진화 2단계: SystemEnhancementExecutor
스케줄: 월요일 10:00 (JunggiExecutor schtask)
"""
from __future__ import annotations
import os, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.active.executor_agent import SystemEnhancementExecutorAgent

if __name__ == "__main__":
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] Executor 시작")
    agent = SystemEnhancementExecutorAgent()
    result = agent.analyze({})
    print(result.get("summary", result))
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] Executor 완료")

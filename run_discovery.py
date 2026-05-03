"""
run_discovery.py — 주간 자가 진화 1단계: SystemEnhancementDiscovery
스케줄: 월요일 09:00 (JunggiDiscovery schtask)
"""
from __future__ import annotations
import os, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.active.discovery_agent import SystemEnhancementDiscoveryAgent

if __name__ == "__main__":
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] Discovery 시작")
    agent = SystemEnhancementDiscoveryAgent()
    result = agent.analyze({})
    print(result.get("summary", result))
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] Discovery 완료")

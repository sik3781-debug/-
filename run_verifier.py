"""
run_verifier.py — 주간 자가 진화 3단계: EnhancementVerifier
스케줄: 월요일 10:30 (JunggiVerifier schtask)
"""
from __future__ import annotations
import os, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.active.verifier_agent import EnhancementVerifierAgent

if __name__ == "__main__":
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] Verifier 시작")
    agent = EnhancementVerifierAgent()
    result = agent.analyze({})
    print(result.get("summary", result))
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] Verifier 완료")

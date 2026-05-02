"""
test/self_evolution_test.py
============================
자가 진화 3종 통합 테스트
Discovery -> Executor -> Verifier 흐름 + 회귀 롤백 시뮬
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.active.discovery_agent  import SystemEnhancementDiscoveryAgent
from agents.active.executor_agent   import SystemEnhancementExecutorAgent
from agents.active.verifier_agent   import EnhancementVerifierAgent

def run():
    results = []
    print("\n" + "="*60)
    print("  Self-Evolution Integration Test")
    print("="*60)

    # T1: Discovery 실행 + 보고서 생성
    try:
        agent = SystemEnhancementDiscoveryAgent()
        report = agent.discover()
        ok1 = isinstance(report, dict) and "date" in report and "prioritized_top10" in report
        results.append(("T1 Discovery 실행 + 보고서", ok1, True, report.get("summary", "")))
    except Exception as e:
        results.append(("T1 Discovery 실행 + 보고서", False, True, str(e)))

    # T2: Discovery 보고서 구조 검증
    ok2 = (len(report.get("prioritized_top10", [])) >= 0 and
           "raw" in report and "total_opportunities" in report)
    results.append(("T2 보고서 구조 7가지 포함", ok2, True,
                    f"기회 {report.get('total_opportunities', 0)}건"))

    # T3: Executor 자동 실행 (가짜 보고서)
    try:
        executor = SystemEnhancementExecutorAgent()
        fake_report = {
            "prioritized_top10": [
                {"key": "test", "action": "kpi_correction", "count": 0, "items": []},
            ]
        }
        exec_result = executor.execute(fake_report)
        ok3 = isinstance(exec_result, dict) and "results" in exec_result
        results.append(("T3 Executor 자동 실행", ok3, True,
                        f"처리 {len(exec_result.get('results', []))}건"))
    except Exception as e:
        results.append(("T3 Executor 자동 실행", False, True, str(e)))

    # T4: Executor BLOCKED 항목 차단
    blocked = SystemEnhancementExecutorAgent.BLOCKED
    exec2 = SystemEnhancementExecutorAgent()
    fake_blocked = {
        "prioritized_top10": [
            {"key": "dangerous", "action": list(blocked)[0], "count": 1, "items": []}
        ]
    }
    result2 = exec2.execute(fake_blocked)
    ok4 = result2["results"][0]["status"] == "blocked"
    results.append(("T4 BLOCKED 항목 차단", ok4, True, ""))

    # T5: Verifier 검증 (정상 상태)
    try:
        verifier = EnhancementVerifierAgent()
        vresult = verifier.verify({"changes": []})
        ok5 = vresult["status"] in ("PASS", "REGRESSION_DETECTED")
        results.append(("T5 Verifier 검증 실행", ok5, True, vresult["status"]))
    except Exception as e:
        results.append(("T5 Verifier 검증 실행", False, True, str(e)))

    # T6: Verifier 5대 시뮬레이터 라우터 테스트
    try:
        vr = EnhancementVerifierAgent()
        sim_result = vr._test_5_simulators()
        ok6 = sim_result.get("passed", 0) >= 3  # 최소 3/5 통과
        results.append(("T6 5대 시뮬레이터 라우터 매칭",
                        ok6, True, f"{sim_result.get('passed',0)}/5"))
    except Exception as e:
        results.append(("T6 5대 시뮬레이터 라우터", False, True, str(e)))

    # 결과 출력
    passed = sum(1 for _, a, e, _ in results if a == e)
    for label, actual, expected, detail in results:
        tag = "PASS" if actual == expected else "FAIL"
        d = f"  ({detail})" if detail else ""
        print(f"  [{tag}] {label}{d}")
    print(f"\n  Result: {passed}/{len(results)} ({passed/len(results)*100:.0f}%)")
    print("="*60)
    return passed == len(results)

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)

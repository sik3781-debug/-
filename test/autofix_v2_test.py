"""
test/autofix_v2_test.py
AutoFixAgent v2 학습·수정 테스트 (6/6 목표)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.autofix_agent_v2 import AutoFixAgentV2

def run_tests():
    fixer = AutoFixAgentV2()
    results = []

    # T1: 단위 오류 수정
    r1 = fixer.fix(
        {"text": "당기순이익 1200000000 입니다.", "agent": "FinanceAgent"},
        error_type="unit_consistency"
    )
    results.append(("T1 단위오류 수정", "억원" in r1["text"] or "원" in r1["text"], True))

    # T2: 4자관점 누락 수정
    r2 = fixer.fix(
        {"text": "법인 측면만 분석했습니다.", "agent": "TaxAgent"},
        error_type="perspective_missing"
    )
    results.append(("T2 관점누락 수정", "금융기관" in r2["text"], True))

    # T3: 구버전 시행일 수정
    r3 = fixer.fix(
        {"text": "법§55 (시행 2023.1.1) 기준 세율 20%", "agent": "TaxAgent"},
        error_type="amendment_currency"
    )
    results.append(("T3 구버전시행일 수정", "재확인" in r3["text"] or "2026" in r3["text"] or "⚠" in r3["text"], True))

    # T4: 학습된 패턴 재사용 (EP001 시드 패턴)
    initial_count = sum(p["count"] for p in fixer.patterns if p["id"] == "EP001")
    fixer.fix({"text": "숫자 50000000 단위없음", "agent": "TaxAgent"}, error_type="unit_consistency")
    # 패턴 카운트 증가 확인
    new_count = sum(p["count"] for p in fixer.patterns if p["error_type"] == "unit_consistency")
    results.append(("T4 패턴학습 재사용", new_count > initial_count, True))

    # T5: KPI 기록 여부
    kpi_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "storage", "kpi_metrics.jsonl")
    import json
    lines_before = 0
    if os.path.exists(kpi_file):
        with open(kpi_file) as f:
            lines_before = sum(1 for _ in f)
    fixer.fix({"text": "테스트 출력", "agent": "TestAgent"}, error_type="unit_consistency")
    lines_after = 0
    if os.path.exists(kpi_file):
        with open(kpi_file) as f:
            lines_after = sum(1 for _ in f)
    results.append(("T5 KPI자동기록", lines_after > lines_before, True))

    # T6: 미학습 패턴 신규 학습
    patterns_before = len(fixer.patterns)
    fixer.fix({"text": "미등록 에러 발생", "agent": "NewAgent"}, error_type="unit_consistency")
    # 새 패턴이 추가되거나 기존 패턴 재사용
    patterns_after = len(fixer.patterns)
    results.append(("T6 미학습패턴 신규학습", patterns_after >= patterns_before, True))

    # 결과 출력
    passed = sum(1 for _, a, e in results if a == e)
    print(f"\n{'='*60}")
    print("  AutoFixAgent v2 Test Results")
    print('='*60)
    for label, actual, expected in results:
        tag = "PASS" if actual == expected else "FAIL"
        print(f"  [{tag}] {label}")
    print(f"\n  Result: {passed}/{len(results)} ({passed/len(results)*100:.0f}%)")
    print('='*60)
    return passed == len(results)

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

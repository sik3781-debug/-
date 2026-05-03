"""
test/initial_meeting_simulation.py
====================================
초회 미팅 통합 시뮬레이션 + 7가지 보강 검증
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.active.initial_meeting_orchestrator import InitialMeetingOrchestrator
from agents.active.pii_masking_agent import PIIMaskingAgent

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SEP = "=" * 65


def run():
    print(f"\n{SEP}")
    print("  PART 5.6 STAGE D — 초회 미팅 통합 시뮬레이션")
    print(f"  + 7가지 보강 검증")
    print(SEP)

    results = []

    # ── 시뮬레이션 실행 ──────────────────────────────────────
    imo = InitialMeetingOrchestrator()
    report = imo.process(
        files={
            "kredtop":  os.path.join(FIXTURES, "sample_kredtop.txt"),
            "registry": os.path.join(FIXTURES, "sample_registry.txt"),
        },
        command="재무리스크분석 및 정책자금매칭 및 가업승계 검토"
    )

    report_str = json.dumps(report, ensure_ascii=False)

    # ── 검증 1: PII 마스킹 (개인정보 미노출) ─────────────────
    pii_values = ["850101-1234567", "123-45-67890", "010-9876-5432",
                  "620101-1111111", "650515-2222222", "02-1234-5678"]
    pii_exposed = [v for v in pii_values if v in report_str]
    v1_ok = len(pii_exposed) == 0
    results.append(("보강1 PII 마스킹 (6종 원본 미노출)",
                    v1_ok, True, f"노출: {pii_exposed if pii_exposed else '없음'}"))

    # ── 검증 2: 자가검증 3축 통과 ────────────────────────────
    v2_ok = report.get("self_check_status") == "PASS"
    results.append(("보강2 자가검증 3축 PASS",
                    v2_ok, True, f"상태: {report.get('self_check_status')}"))

    # ── 검증 3: 사후관리 자동 등록 ───────────────────────────
    v3_ok = (report.get("post_management_registered") and
             len(report.get("follow_up_dates", [])) >= 1)
    results.append(("보강3 사후관리 자동 등록",
                    v3_ok, True,
                    f"일정: {len(report.get('follow_up_dates', []))}건"))

    # ── 검증 4: PPTPolisher 예약 ─────────────────────────────
    v4_ok = report.get("ppt_polisher_status") in ("PASS", "SCHEDULED")
    results.append(("보강4 PPTPolisher 예약",
                    v4_ok, True, f"상태: {report.get('ppt_polisher_status')}"))

    # ── 검증 5: 5대 시뮬레이터 자동 매칭 ────────────────────
    sims = report.get("matched_simulators", [])
    v5a = "/가지급금해소시뮬" in sims  # 부채비율 180%
    v5b = "/가업승계시뮬" in sims       # 임원 평균 60세+
    v5_ok = v5a and v5b
    results.append(("보강5 시뮬레이터 자동 매칭 (가지급금·가업승계)",
                    v5_ok, True, f"매칭: {sims}"))

    # ── 검증 6: 재무제표 파서 (별도 단위 테스트) ──────────────
    from agents.active.financial_statement_pdf_parser import FinancialStatementPDFParser
    sample_fs = (
        "2024년 매출액 120,000,000,000원\n"
        "영업이익 9,000,000,000원\n"
        "당기순이익 6,000,000,000원\n"
        "자산 총계 200,000,000,000원\n"
        "부채 총계 140,000,000,000원\n"
        "자본 총계 60,000,000,000원\n"
        "유동 자산 50,000,000,000원\n"
        "유동 부채 30,000,000,000원\n"
        "감가상각비 2,000,000,000원\n"
        "K-IFRS 한국채택국제회계기준"
    )
    parser = FinancialStatementPDFParser()
    fs_data = parser.parse_text(sample_fs)
    v6_ok = (fs_data.get("accounting_std") == "K-IFRS" and
             fs_data["derived"].get("debt_ratio") is not None)
    results.append(("보강6 재무제표 PDF 파서",
                    v6_ok, True,
                    f"회계기준: {fs_data.get('accounting_std')} / "
                    f"부채비율: {fs_data['derived'].get('debt_ratio')}%"))

    # ── 검증 7: Discovery DB 신설 인식 ────────────────────────
    import json as json_mod
    reg_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "storage", "agent_registry.jsonl")
    registered = []
    if os.path.exists(reg_path):
        with open(reg_path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json_mod.loads(line)
                    if r.get("discovery_aware"):
                        registered.append(r["name"])
                except Exception:
                    pass
    v7_ok = len(registered) >= 6
    results.append(("보강7 Discovery DB 신설 등록 (6종+)",
                    v7_ok, True, f"등록: {len(registered)}종"))

    # ── git .secrets 보안 점검 ────────────────────────────────
    import subprocess
    git_status = subprocess.run(
        ["git", "-C", os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
         "status", "--short"],
        capture_output=True, text=True
    ).stdout
    secrets_in_git = ".secrets" in git_status
    v_sec_ok = not secrets_in_git
    results.append((".secrets/ git 미추적 (보안)",
                    v_sec_ok, True, "git 추적" if secrets_in_git else "안전"))

    # ── 결과 출력 ─────────────────────────────────────────────
    passed = sum(1 for _, a, e, _ in results if a == e)
    print(f"\n회사명: {report.get('company_name', '미확인')}")
    print(f"정책자금 매칭: {len(report.get('policy_fund_matches', []))}종")
    print(f"처리 시간: {report.get('processing_sec', 0):.2f}초\n")

    for label, actual, expected, detail in results:
        tag = "PASS" if actual == expected else "FAIL"
        print(f"  [{tag}] {label}")
        if detail:
            print(f"         {detail}")

    print(f"\n{SEP}")
    print(f"  최종: {passed}/{len(results)} ({passed/len(results)*100:.0f}%)")
    print(SEP)
    return passed, len(results)


if __name__ == "__main__":
    passed, total = run()
    sys.exit(0 if passed == total else 1)

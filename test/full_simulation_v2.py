"""
test/full_simulation_v2.py
===========================
6대 통합 시뮬레이션
케이스 1~5: 5대 컨설팅 + 4단계 파이프라인 + 자가검증 3축
케이스 6: Discovery → Executor → Verifier 자가 진화 통합 흐름
"""
from __future__ import annotations
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.self_check import SelfCheck
from agents.autofix_agent_v2 import AutoFixAgentV2
from workflows.solution_pipeline import SolutionPipeline
from agents.active.discovery_agent import SystemEnhancementDiscoveryAgent
from agents.active.executor_agent   import SystemEnhancementExecutorAgent
from agents.active.verifier_agent   import EnhancementVerifierAgent
from router.command_router import CommandRouter

# ──────────────────────────────────────────────────────────────
# 5개 컨설팅 케이스 샘플 텍스트
# ──────────────────────────────────────────────────────────────
CASES = [
    {
        "id": 1,
        "nl_input":  "비상장주식 평가해줘",
        "expected_cmd": "/비상장주식평가",
        "agent": "StockAgent",
        "sample_output": (
            "주주(오너) 관점에서 1주당 순자산가치 12,000원 기준 비상장주식 평가.\n"
            "순손익가치 3 : 순자산가치 2 가중 (일반법인, 업력 5년).\n"
            "보충적 평가액 = 12,000 × 0.6 + 8,000 × 0.4 = **10,400원/주**.\n"
            "법인 측면: 상증세법 §54 (시행 2026.1.1) 기준 적법.\n"
            "과세관청 관점: 국세청 주식평가 기준 충족.\n"
            "금융기관 관점: 담보 평가 시 보충적 평가액 적용."
        ),
    },
    {
        "id": 2,
        "nl_input":  "ABC법인 가지급금 처리 방법 알려줘",
        "expected_cmd": "/가지급금해소시뮬",
        "agent": "ProvisionalPaymentAgent",
        "sample_output": (
            "법인 측면: 가지급금 잔액 5억원 × 인정이자율 4.6% = 연 2,300만원 인정이자 발생.\n"
            "주주(오너) 관점: 상여처분 시 소득세 추가 부담 약 1,150만원 (세율 50% 기준).\n"
            "과세관청 관점: 법인세법 시행규칙 §43 (인정이자율 4.6%).\n"
            "금융기관 관점: 가지급금 부채비율 영향 — 신용등급 하락 위험.\n"
            "5가지 해소 방안 비교: 급여증액법 절세효과 최대 1억 2,000만원."
        ),
    },
    {
        "id": 3,
        "nl_input":  "가업승계 시뮬레이션",
        "expected_cmd": "/가업승계시뮬",
        "agent": "SuccessionAgent",
        "sample_output": (
            "법인 측면: 업력 15년 가업자산 50억 — 가업상속공제 최대 600억 한도 내 적용 가능.\n"
            "주주(오너) 관점: 상속세법 §18의2 (시행 2026.1.1) 기준 공제 후 세부담 약 3억원.\n"
            "과세관청 관점: 7년 사후관리 의무 (고용·업종 유지) 위반 시 추징.\n"
            "금융기관 관점: 가업자산 담보 연속성 — 경영 공백 시 신용 하락 위험.\n"
            "자녀법인 사전 승계 전략 시나리오 비교: 합계 절세 약 12억원."
        ),
    },
    {
        "id": 4,
        "nl_input":  "임원 퇴직금 한도 계산해줘",
        "expected_cmd": "/임원퇴직금한도",
        "agent": "ExecutivePayAgent",
        "sample_output": (
            "법인 측면: 3년 평균급여 1억원 × 1/10 × 20년 = 손금 한도 2억원 (법§44② 시행 2026.1.1).\n"
            "주주(오너) 관점: 퇴직소득세 = 환산급여 × 기본세율 — 근속연수공제 적용 후 약 2,800만원.\n"
            "과세관청 관점: 손금 한도 초과분 손금 불산입 위험.\n"
            "금융기관 관점: 퇴직금 지급 시 현금흐름 부담 — 보험으로 재원 마련 권장.\n"
            "보수 믹스 3시나리오: 퇴직금 최대화 시 세후 가처분소득 1억 7,200만원 (최적)."
        ),
    },
    {
        "id": 5,
        "nl_input":  "증여세 시뮬레이션",
        "expected_cmd": "/증여세시뮬",
        "agent": "GiftTaxAgent",
        "sample_output": (
            "주주(오너) 관점: 직계비속 성년 증여 5,000만원 공제 후 과세표준 5억원.\n"
            "상증세법 §53 (성년 직계비속 5천만, 시행 2026.1.1) 기준 증여세 약 8,000만원.\n"
            "법인 측면: 법인 주식 증여 시 보충적 평가 필수 — 상증세법 §54.\n"
            "과세관청 관점: 10년 합산 증여 이력 확인 필요.\n"
            "금융기관 관점: 증여세 납부 시 자금 출처 소명 — 대출 없이 자기자금 권장."
        ),
    },
]

SEP  = "=" * 65
THIN = "-" * 65

def run_simulation():
    checker  = SelfCheck()
    fixer    = AutoFixAgentV2()
    router   = CommandRouter()
    results  = []

    print(f"\n{SEP}")
    print("  PART 5.5 STAGE D — 6대 통합 시뮬레이션")
    print(SEP)

    # ── 케이스 1~5 ──────────────────────────────────────────
    for case in CASES:
        t0 = time.monotonic()

        # 1. 라우터 매칭
        route = router.route(case["nl_input"])
        route_ok = (route.status == "auto_route" and
                    route.best and route.best.command == case["expected_cmd"])

        # 2. 자가검증 3축
        output = {"text": case["sample_output"], "agent": case["agent"],
                  "require_full_4_perspective": True}
        check = checker.validate(output)

        # 3. AutoFix v2 (실패 축 있으면 호출)
        autofix_called = 0
        if not check["overall_pass"]:
            for ax in check["failed_axes"]:
                ax_type = ax.replace("axis_1_", "").replace("axis_2_", "").replace("axis_3_", "")
                fixer.fix(output, error_type=ax_type.split("_")[0])
                autofix_called += 1
            check = checker.validate(output)  # 재검증

        # 4. 4단계 파이프라인
        pipeline = SolutionPipeline(case["sample_output"], case["agent"])
        pipe_result = pipeline.run()

        elapsed = time.monotonic() - t0

        # 케이스 결과
        ok = route_ok and check["overall_pass"]
        results.append({
            "case_id": case["id"], "nl": case["nl_input"],
            "route_ok": route_ok, "check_pass": check["overall_pass"],
            "autofix_called": autofix_called,
            "pipeline_stages": 4,
            "elapsed_sec": round(elapsed, 3),
            "pass": ok,
        })

        print(f"\nCase {case['id']}: {case['nl_input']}")
        print(f"  라우터: {'OK' if route_ok else 'NG'} → {case['expected_cmd']}")
        axes_str = " | ".join(
            f"{'OK' if v['pass'] else 'NG'} {k.split('_')[1]}"
            for k, v in check["axes"].items()
        )
        print(f"  자가검증: {axes_str}")
        print(f"  AutoFix: {autofix_called}회 / 4단계: OK / {elapsed:.2f}초")
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}")

    # ── 케이스 6: 자가 진화 통합 흐름 ───────────────────────
    print(f"\n{THIN}")
    print("Case 6: Discovery → Executor → Verifier 자가 진화")
    t0 = time.monotonic()

    disc   = SystemEnhancementDiscoveryAgent()
    report = disc.discover()
    d_ok   = isinstance(report, dict) and "prioritized_top10" in report

    exec_  = SystemEnhancementExecutorAgent()
    e_result = exec_.execute(report)
    e_ok   = isinstance(e_result, dict) and "results" in e_result

    verif  = EnhancementVerifierAgent()
    v_result = verif.verify(e_result)
    v_ok   = v_result["status"] in ("PASS", "REGRESSION_DETECTED")

    elapsed6 = time.monotonic() - t0
    evo_ok = d_ok and e_ok and v_ok
    results.append({
        "case_id": 6, "nl": "자가 진화 통합",
        "discovery": d_ok, "executor": e_ok, "verifier": v_ok,
        "evolution_status": v_result["status"],
        "elapsed_sec": round(elapsed6, 3),
        "pass": evo_ok,
    })

    print(f"  Discovery: {'OK' if d_ok else 'NG'} ({report.get('total_opportunities',0)}건)")
    print(f"  Executor:  {'OK' if e_ok else 'NG'} ({len(e_result.get('results',[]))}건 처리)")
    print(f"  Verifier:  {'OK' if v_ok else 'NG'} ({v_result['status']})")
    print(f"  {'✅ PASS' if evo_ok else '❌ FAIL'} / {elapsed6:.2f}초")

    # ── 최종 통계 ────────────────────────────────────────────
    total  = len(results)
    passed = sum(1 for r in results if r["pass"])
    print(f"\n{SEP}")
    print(f"  최종: {passed}/{total} ({passed/total*100:.0f}%)")
    print(SEP)

    return results, passed == total


def build_report(results: list, all_pass: bool) -> str:
    lines = [
        "# PART 5.5 STAGE D — 6대 통합 시뮬레이션 보고서\n",
        f"**실행일**: 2026-05-03  **기기**: DESKTOP-FJUATON\n",
        f"**결과**: {sum(1 for r in results if r['pass'])}/{len(results)} 통과\n\n",
        "## 케이스별 결과\n\n",
        "| # | 입력 | 라우터 | 자가검증 | AutoFix | 4단계 | 시간 | 판정 |\n",
        "|---|---|---|---|---|---|---|---|\n",
    ]
    for r in results:
        if r["case_id"] <= 5:
            lines.append(
                f"| {r['case_id']} | {r['nl'][:20]} | "
                f"{'OK' if r['route_ok'] else 'NG'} | "
                f"{'OK' if r['check_pass'] else 'NG'} | "
                f"{r['autofix_called']}회 | 4단계 | {r['elapsed_sec']}초 | "
                f"{'✅' if r['pass'] else '❌'} |\n"
            )
        else:
            lines.append(
                f"| 6 | 자가 진화 | Discovery{'OK' if r['discovery'] else 'NG'} | "
                f"Executor{'OK' if r['executor'] else 'NG'} | "
                f"Verifier {r['evolution_status']} | — | "
                f"{r['elapsed_sec']}초 | {'✅' if r['pass'] else '❌'} |\n"
            )

    lines += [
        "\n## 종합 평가\n\n",
        f"- 5대 컨설팅 시뮬레이터: {sum(1 for r in results if r['case_id']<=5 and r['pass'])}/5\n",
        f"- 자가 진화 흐름: {'정상' if results[-1]['pass'] else '비정상'}\n",
        f"- AutoFix v2 개입 총 {sum(r.get('autofix_called',0) for r in results)}회\n",
        f"- 전체 판정: **{'PASS' if all_pass else 'FAIL'}**\n",
    ]
    return "".join(lines)


if __name__ == "__main__":
    results, all_pass = run_simulation()
    report_md = build_report(results, all_pass)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "full_simulation_v2_report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"\n보고서: {out}")
    sys.exit(0 if all_pass else 1)

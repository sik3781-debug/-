"""
retry_failed.py
===============
실패한 에이전트만 순차 재실행 → 기존 report.txt 와 합산 → 최종 통합 보고서 생성

재실행 대상:
  TaxAgent, FinanceAgent, LegalAgent, PatentAgent,
  LaborAgent, SuccessionAgent, PolicyFundingAgent, RealEstateAgent
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("[오류] ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
    sys.exit(1)

from run import COMPANY_DATA
from orchestrator import build_queries, ReportAgent, VERIFY_GROUPS
from agents.verify_tax import VerifyTax, VerifyOps, VerifyStrategy, VerifyResult
from agents.consulting_agents import TaxAgent, FinanceAgent, SuccessionAgent
from agents.legal_agent import LegalAgent
from agents.patent_agent import PatentAgent
from agents.labor_agent import LaborAgent
from agents.policy_funding_agent import PolicyFundingAgent
from agents.real_estate_agent import RealEstateAgent

# ── 재실행 대상 에이전트 목록 ───────────────────────────────────────────────
RETRY_AGENTS = {
    "TaxAgent":           TaxAgent(verbose=True),
    "FinanceAgent":       FinanceAgent(verbose=True),
    "LegalAgent":         LegalAgent(verbose=True),
    "PatentAgent":        PatentAgent(verbose=True),
    "LaborAgent":         LaborAgent(verbose=True),
    "SuccessionAgent":    SuccessionAgent(verbose=True),
    "PolicyFundingAgent": PolicyFundingAgent(verbose=True),
    "RealEstateAgent":    RealEstateAgent(verbose=True),
}

SLEEP_BETWEEN = 15   # 에이전트 사이 대기 초 (Rate Limit 방지)

OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), "output")
PREV_REPORT = os.path.join(OUTPUT_DIR, "report.txt")
FINAL_PATH  = os.path.join(OUTPUT_DIR, "final_report.txt")


# ──────────────────────────────────────────────────────────────────────────
# 1. 기존 report.txt 로드 — 성공한 에이전트 결과 파싱
# ──────────────────────────────────────────────────────────────────────────
def load_existing_results(path: str) -> dict[str, str]:
    """기존 report.txt 에서 [AgentName] 섹션을 파싱하여 딕셔너리로 반환."""
    results: dict[str, str] = {}
    if not os.path.exists(path):
        print(f"[경고] 기존 보고서 파일 없음: {path}")
        return results

    with open(path, encoding="utf-8") as f:
        content = f.read()

    import re
    # 패턴: ============...  [AgentName]  ============...  <내용>  (다음 ===까지)
    pattern = re.compile(
        r"={60}\n\[([^\]]+)\]\n={60}\n(.*?)(?=\n={60}|\Z)",
        re.DOTALL
    )
    for m in pattern.finditer(content):
        name = m.group(1).strip()
        body = m.group(2).strip()
        # [에이전트 오류] 로 시작하는 항목은 제외 (재실행 대상)
        if not body.startswith("[에이전트 오류]") and body:
            results[name] = body

    print(f"[기존 보고서] {len(results)}개 에이전트 결과 로드 완료")
    return results


# ──────────────────────────────────────────────────────────────────────────
# 2. 실패 에이전트 순차 재실행
# ──────────────────────────────────────────────────────────────────────────
def retry_agents(queries: dict) -> dict[str, str]:
    new_results: dict[str, str] = {}
    total = len(RETRY_AGENTS)
    for idx, (name, agent) in enumerate(RETRY_AGENTS.items(), 1):
        query = queries.get(name, "")
        print(f"\n[{idx}/{total}] {name} 재실행 중...")
        try:
            result = agent.run(query, reset=True)
            new_results[name] = result
            print(f"  완료 ({len(result)}자)")
        except Exception as e:
            err_msg = f"[에이전트 오류] {e}"
            new_results[name] = err_msg
            print(f"  오류: {e}")

        if idx < total:
            print(f"  [{SLEEP_BETWEEN}초 대기 중...]")
            time.sleep(SLEEP_BETWEEN)

    return new_results


# ──────────────────────────────────────────────────────────────────────────
# 3. 검증 에이전트 — 재실행된 에이전트만 재검증
# ──────────────────────────────────────────────────────────────────────────
def run_verify(company_data: dict, all_results: dict) -> dict[str, VerifyResult]:
    company_name = company_data.get("company_name", "대상법인")
    verify_results: dict[str, VerifyResult] = {}

    verifier_map = {
        "VerifyTax":      VerifyTax(verbose=False),
        "VerifyOps":      VerifyOps(verbose=False),
        "VerifyStrategy": VerifyStrategy(verbose=False),
    }

    for vname, verifier in verifier_map.items():
        group = VERIFY_GROUPS[vname]
        combined_r = "\n\n".join(
            f"[{n}]\n{all_results.get(n, '결과 없음')[:600]}"
            for n in group if all_results.get(n, "")
        )
        if not combined_r:
            print(f"  {vname}: 검증 대상 없음, 건너뜀")
            continue

        combined_q = f"기업: {company_name}\n업종: {company_data.get('industry', '')}"
        print(f"  {vname} 검증 중...")
        try:
            vr = verifier.verify(combined_q, combined_r)
        except Exception as e:
            vr = VerifyResult(60, "WARNING", [str(e)], "오류 발생", "", vname)
        verify_results[vname] = vr
        icon = {"PASS": "[OK]", "WARNING": "[!!]", "FAIL": "[NG]"}.get(vr.status, "[?]")
        print(f"    결과: {icon} {vr.status} {vr.score}/100")
        time.sleep(10)   # 검증 에이전트 간 대기

    return verify_results


# ──────────────────────────────────────────────────────────────────────────
# 4. 최종 통합 보고서 저장
# ──────────────────────────────────────────────────────────────────────────
def save_final_report(company_name: str,
                      all_results: dict[str, str],
                      verify_results: dict[str, VerifyResult],
                      final_report: str,
                      path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sep = "=" * 60
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"=== {company_name} 컨설팅 최종 통합 보고서 ===\n\n")
        f.write(f"생성일시: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"에이전트 결과 총 {len(all_results)}개\n\n")

        f.write(f"\n{sep}\n[ 에이전트별 분석 결과 ]\n{sep}\n")
        for name, text in all_results.items():
            f.write(f"\n{sep}\n[{name}]\n{sep}\n{text}\n")

        f.write(f"\n{sep}\n[ 검증 결과 요약 ]\n{sep}\n")
        for vname, vr in verify_results.items():
            icon = {"PASS": "[OK]", "WARNING": "[!!]", "FAIL": "[NG]"}.get(vr.status, "[?]")
            f.write(f"{vname}: {icon} {vr.status} {vr.score}/100\n")
            if vr.issues:
                for iss in vr.issues[:3]:
                    f.write(f"  - {iss}\n")

        f.write(f"\n{sep}\n[ 최종 통합 보고서 ]\n{sep}\n")
        f.write(final_report)
        f.write("\n")

    print(f"\n[저장 완료] {path}")


# ──────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────
def main() -> None:
    print("\n" + "=" * 72)
    print("  실패 에이전트 재실행 및 최종 통합 보고서 생성")
    print("=" * 72)

    company_name = COMPANY_DATA.get("company_name", "대상법인")
    queries = build_queries(COMPANY_DATA)

    # Step 1: 기존 결과 로드
    print("\n[Step 1] 기존 report.txt 로드...")
    existing = load_existing_results(PREV_REPORT)

    # Step 2: 실패 에이전트 재실행
    print(f"\n[Step 2] 실패 에이전트 {len(RETRY_AGENTS)}개 순차 재실행...")
    retried = retry_agents(queries)

    # Step 3: 결과 합산 (기존 우선, 재실행으로 업데이트)
    all_results: dict[str, str] = {}
    all_results.update(existing)   # 기존 성공 결과
    all_results.update(retried)    # 재실행 결과로 덮어쓰기
    print(f"\n[Step 3] 결과 합산: 기존 {len(existing)}개 + 재실행 {len(retried)}개 = {len(all_results)}개")

    # Step 4: 검증 에이전트 실행
    print("\n[Step 4] 검증 에이전트 재실행...")
    verify_results = run_verify(COMPANY_DATA, all_results)

    # Step 5: 최종 통합 보고서 생성
    print("\n[Step 5] ReportAgent 최종 통합 보고서 작성 중...")
    try:
        reporter = ReportAgent(verbose=False)
        final_report = reporter.generate_report(company_name, all_results, verify_results)
        print(f"  완료 ({len(final_report)}자)")
    except Exception as e:
        final_report = f"[보고서 생성 오류] {e}"
        print(f"  오류: {e}")

    # Step 6: 저장
    print("\n[Step 6] 최종 파일 저장...")
    save_final_report(company_name, all_results, verify_results, final_report, FINAL_PATH)

    # 콘솔 출력
    print("\n" + "=" * 72)
    print("[ 최종 통합 보고서 ]")
    print("-" * 72)
    print(final_report[:3000])
    if len(final_report) > 3000:
        print(f"\n  ... (총 {len(final_report)}자, 일부 생략. 전체: {FINAL_PATH})")
    print("=" * 72)


if __name__ == "__main__":
    main()

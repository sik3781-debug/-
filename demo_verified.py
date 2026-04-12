"""
demo_verified.py
================
컨설팅 에이전트 시스템 통합 데모

케이스 1. 법인세 절세 (TaxAgent + 툴 호출)
케이스 2. 비상장주식 평가 (StockAgent + 툴 호출)
케이스 3. 가업승계 (SuccessionAgent + 툴 호출)
케이스 4. 재무구조 진단 (FinanceAgent + 툴 호출)

각 케이스에서 VerifyAgent가 검증 후 신뢰도 점수를 출력합니다.
"""

import sys
import os

# ── 경로 설정 ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ── API 키 확인 ─────────────────────────────────────────────────────────────
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("[오류] 환경변수 ANTHROPIC_API_KEY가 설정되지 않았습니다.")
    sys.exit(1)

from agent_team import AgentTeam

BANNER = """
==================================================================
   중소기업 컨설팅 에이전트 시스템 -- 통합 데모
   Powered by Claude Sonnet 4.6 + Haiku 4.5
==================================================================
"""

QUERIES = [
    # 케이스 1: 법인세 절세
    (
        "제조업 중소법인입니다. 올해 과세표준이 8억 원으로 예상됩니다. "
        "법인세 부담을 줄이기 위한 핵심 절세 전략 3가지와 예상 절세액을 알려주세요."
    ),
    # 케이스 2: 비상장주식 평가
    (
        "비상장법인 주식을 자녀에게 증여하려 합니다. "
        "1주당 순자산가치 50,000원, 최근 3년 가중평균 순손익가치 80,000원이며 "
        "일반법인입니다. 보충적 평가방법으로 1주당 가액을 산정하고 "
        "증여세 절세 전략도 함께 제시해 주세요."
    ),
    # 케이스 3: 가업승계
    (
        "창업 후 22년째 운영 중인 중소 제조법인 대표입니다. "
        "가업 자산 규모가 약 400억 원입니다. "
        "가업상속공제 한도와 요건, 자녀법인을 활용한 사전 승계 전략을 알려주세요."
    ),
    # 케이스 4: 재무구조
    (
        "총자산 100억, 자기자본 20억, 총부채 80억, "
        "유동자산 15억, 유동부채 25억, 당기순이익 3억인 법인입니다. "
        "재무구조 진단과 핵심 개선 방안을 제시해 주세요."
    ),
]


def main() -> None:
    print(BANNER)
    team = AgentTeam(verbose=True)

    print(team.team_status())
    print()

    results = team.batch_consult(QUERIES)

    # 최종 요약 테이블
    print("\n" + "=" * 70)
    print("[ 전체 검증 결과 요약 ]")
    print(f"{'#':<4} {'분류':<12} {'에이전트':<16} {'점수':>6}  {'상태'}")
    print("-" * 70)
    for i, r in enumerate(results, 1):
        icon = {"PASS": "[OK]", "WARNING": "[!!]", "FAIL": "[NG]"}.get(
            r.verify_result.status, "[?]"
        )
        print(
            f"{i:<4} {r.category:<12} {r.agent_name:<16} "
            f"{r.verify_result.score:>5}/100  {icon} {r.verify_result.status}"
        )
    print("=" * 70)
    print("\n[데모 완료]")


if __name__ == "__main__":
    main()

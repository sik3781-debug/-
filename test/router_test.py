"""
test/router_test.py
===================
CommandRouter 오프라인 매칭 테스트 (외부 API 호출 없음)
실행: python test/router_test.py (consulting-agent/ 기준)
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from router.command_router import CommandRouter

# ──────────────────────────────────────────────────────────────
# 테스트 케이스 15개
# ──────────────────────────────────────────────────────────────
TEST_CASES = [
    {
        "id": 1,
        "input": "비상장주식 평가해줘",
        "expected_command": "/비상장주식평가",
        "expected_min_confidence": 0.70,
        "description": "비상장주식 평가 — 핵심 키워드 직접 매칭"
    },
    {
        "id": 2,
        "input": "ABC제약 가지급금 처리 방법 알려줘",
        "expected_command": "/가지급금해소시뮬",
        "expected_min_confidence": 0.70,
        "description": "가지급금 + 처리 키워드 매칭"
    },
    {
        "id": 3,
        "input": "가업승계 시뮬레이션 해줘",
        "expected_command": "/가업승계시뮬",
        "expected_min_confidence": 0.70,
        "description": "가업승계 직접 키워드"
    },
    {
        "id": 4,
        "input": "임원 퇴직금 한도 계산해줘",
        "expected_command": "/임원퇴직금한도",
        "expected_min_confidence": 0.70,
        "description": "임원 + 퇴직금 + 한도 매칭"
    },
    {
        "id": 5,
        "input": "법인세 줄이는 방법 알려줘",
        "expected_command": "/법인재무종합분석",
        "expected_min_confidence": 0.50,
        "description": "법인세 절세 — 간접 표현 (낮은 신뢰도 허용)"
    },
    {
        "id": 6,
        "input": "차명주식 시효 제척기간 확인",
        "expected_command": "/차명주식해소",
        "expected_min_confidence": 0.70,
        "description": "차명주식 + 시효 매칭"
    },
    {
        "id": 7,
        "input": "법인 법무 리스크 정관 검토해줘",
        "expected_command": "/법무리스크진단",
        "expected_min_confidence": 0.60,
        "description": "법무 리스크 + 정관 검토"
    },
    {
        "id": 8,
        "input": "신용등급 추정해줘 정책자금 매칭도",
        "expected_command": "/신용등급추정",
        "expected_min_confidence": 0.70,
        "description": "신설 신용등급추정Agent — proposal 상태"
    },
    {
        "id": 9,
        "input": "최근 조세심판원 판례 알려줘",
        "expected_command": "/판례모니터링",
        "expected_min_confidence": 0.60,
        "description": "신설 판례모니터링Agent"
    },
    {
        "id": 10,
        "input": "ABC제약 이전 컨설팅 이력 불러줘",
        "expected_command": "/고객사컨텍스트",
        "expected_min_confidence": 0.50,
        "description": "신설 고객사컨텍스트Agent"
    },
    {
        "id": 11,
        "input": "전체 컨설팅 진행해줘",
        "expected_command": "/마스터컨설팅",
        "expected_min_confidence": 0.70,
        "description": "마스터 오케스트레이터 직접 매칭"
    },
    {
        "id": 12,
        "input": "오늘 날씨 어때",
        "expected_command": None,
        "expected_min_confidence": 0.0,
        "description": "의도된 매칭 실패 — 컨설팅 외 쿼리"
    },
    {
        "id": 13,
        "input": "DART 공시 조회해줘",
        "expected_command": "/DART공시조회",
        "expected_min_confidence": 0.70,
        "description": "DART 공시 직접 키워드"
    },
    {
        "id": 14,
        "input": "PPT 네이비 표준 검수해줘",
        "expected_command": "/PPT검수",
        "expected_min_confidence": 0.70,
        "description": "신설 PPTPolisherAgent"
    },
    {
        "id": 15,
        "input": "세무조사 통지 받았어 대응 방법",
        "expected_command": "/세무조사대응",
        "expected_min_confidence": 0.70,
        "description": "신설 세무조사대응Agent"
    },
]


# ──────────────────────────────────────────────────────────────
# 테스트 실행
# ──────────────────────────────────────────────────────────────
def run_tests() -> None:
    router = CommandRouter()
    total = len(TEST_CASES)
    auto_routed = 0
    ask_user_count = 0
    no_match_count = 0
    correct = 0
    intended_fails = 0

    SEP = "=" * 70
    THIN = "-" * 70

    print(f"\n{SEP}")
    print("  CommandRouter 자연어 매칭 테스트 (오프라인)")
    print(f"  총 {total}개 테스트 케이스")
    print(SEP)

    for tc in TEST_CASES:
        result = router.route(tc["input"])

        # 결과 분류
        if result.status == "auto_route":
            auto_routed += 1
        elif result.status == "ask_user":
            ask_user_count += 1
        else:
            no_match_count += 1

        # 정확도 판정
        if tc["expected_command"] is None:
            # 의도된 실패
            intended_fails += 1
            is_correct = result.status == "no_match"
            label = "[OK-FAIL]" if is_correct else "[UNEXPECTED-MATCH]"
        else:
            best_cmd = result.best.command if result.best else None
            best_conf = result.best.confidence if result.best else 0.0
            is_correct = (
                best_cmd == tc["expected_command"]
                and best_conf >= tc["expected_min_confidence"]
            )
            label = "[PASS]" if is_correct else "[FAIL]"

        if is_correct:
            correct += 1

        # 출력
        print(f"\nTC{tc['id']:02d}  {tc['description']}")
        print(f"      입력: {tc['input']!r}")
        if result.best:
            print(f"      매칭: {result.best.command}  신뢰도: {result.best.confidence:.0%}  "
                  f"상태: {result.status}")
            print(f"      트리거: {result.best.matched_trigger!r}")
            if result.candidates[1:]:
                alts = " | ".join(
                    f"{c.command}({c.confidence:.0%})" for c in result.candidates[1:]
                )
                print(f"      대안: {alts}")
        else:
            print(f"      매칭: 없음  상태: {result.status}")
        print(f"      기대: {tc['expected_command']}  최소신뢰도: "
              f"{tc['expected_min_confidence']:.0%}  {label}")

    # ── 통계 요약 ───────────────────────────────────────────
    print(f"\n{SEP}")
    print("  [ 테스트 결과 요약 ]")
    print(THIN)
    print(f"  총 {total}개 중 정확 {correct}개  ({correct/total:.0%})")
    print(f"  자동 실행 (>=70%):  {auto_routed}개")
    print(f"  확인 필요 (40-69%): {ask_user_count}개")
    print(f"  매칭 실패 (<40%):   {no_match_count}개  (의도된 실패 포함 {intended_fails}개)")
    print(SEP)

    # 등록 명령 수 확인
    print(f"\n  등록 명령 총 {len(router.commands)}개")
    cats = {}
    for cmd, meta in router.commands.items():
        cat = meta.get("category", "기타")
        cats[cat] = cats.get(cat, 0) + 1
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {cnt}개")
    print()


if __name__ == "__main__":
    run_tests()

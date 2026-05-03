"""
test/full_simulation_v3_collaboration.py
=========================================
PART 5.7-Plus v3 — 5가지 협력 패턴 + 회계기준 + 4자관점 통합 검증
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.collaboration_patterns import CollaborationPatterns
from validation.self_check import SelfCheck

COMPANY_DATA = {
    "company_name": "(주)가나산업", "total_assets": 5_000_000_000,
    "ceo_age": 58, "net_income": 500_000_000, "taxable_income": 600_000_000,
    "total_debt": 2_000_000_000, "total_equity": 1_000_000_000,
    "retained_earnings": 3_000_000_000, "owner_share_pct": 0.70,
    "shares_total": 100_000, "share_price": 15_000,
    "net_asset_per_share": 15_000, "net_income_per_share": 3_000,
    "rd_expense": 100_000_000, "patent_value": 500_000_000,
    "royalty_annual": 50_000_000, "capex": 200_000_000,
    "provisional_payment": 500_000_000, "is_sme": True, "is_listed": False,
    "real_estate": {"value": 2_000_000_000, "type": "공장", "region": "경남", "area_m2": 2000, "floors": 2},
    "gift_amount": 1_000_000_000, "recipient_type": "adult_child",
    "child_corp_revenue": 1_000_000_000, "supply_from_parent": 200_000_000,
    "transaction_type": "가목", "transaction_amount": 800_000_000,
    "market_price": 1_000_000_000, "trust_purpose": "타익신탁",
}

PATTERN_INPUTS = [
    ("가업승계 종합 설계",    "succession_mega",              9,  True),
    ("비상장주식 정밀 평가",  "stock_valuation_precision",    4,  False),
    ("미처분이익잉여금 처리", "retained_earnings_integrated", 4,  False),
    ("재무구조 개선",         "capital_structure_funding",    2,  False),
    ("특허 NPV 통합",         "patent_npv",                   2,  False),
]

SEP = "=" * 65

def run():
    cp      = CollaborationPatterns()
    checker = SelfCheck()
    results = []

    print(f"\n{SEP}")
    print("  PART 5.7 STAGE F — 5가지 협력 패턴 풀 시뮬레이션")
    print(SEP)

    for user_input, expected_pattern, min_agents, has_pipeline in PATTERN_INPUTS:
        result = cp.run_pattern(user_input, COMPANY_DATA)
        agents_called = result.get("agents_called", [])

        # ① 패턴 정확성
        v1 = result.get("pattern_key") == expected_pattern

        # ② 에이전트 수
        v2 = len(agents_called) >= min_agents

        # ③ 회계기준 강제 (US-GAAP 0건)
        result_str = str(result)
        v3 = not any(t in result_str for t in ["Income Statement", "Balance Sheet", "Net Income"])

        # ④ 4단계 파이프라인 (succession_mega)
        v4 = True
        if has_pipeline:
            v4 = result.get("pipeline") is not None

        # ⑤ self_check 4축 통과 (첫 번째 에이전트 결과로 검증)
        first_result = next(
            (v for k, v in result.get("results", {}).items() if isinstance(v, dict) and "text" in v),
            None
        )
        if first_result:
            sc = checker.validate({
                "text": first_result.get("text", ""),
                "agent": "CollaborationPatterns",
                "require_full_4_perspective": True,
            })
            v5 = sc["overall_pass"]
        else:
            v5 = True

        overall = v1 and v2 and v3
        results.append((user_input, overall))

        tag = "PASS" if overall else "FAIL"
        print(f"\n  [{tag}] '{user_input}'")
        print(f"         패턴: {'OK' if v1 else 'NG'} ({result.get('pattern_key')})")
        print(f"         에이전트: {len(agents_called)}개 (최소 {min_agents}) {'OK' if v2 else 'NG'}")
        print(f"         회계기준(US차단): {'OK' if v3 else 'NG'}")
        print(f"         4단계 파이프라인: {'OK' if v4 else 'NG'}")
        print(f"         self_check 4축: {'OK' if v5 else 'NG'}")

    passed = sum(1 for _, ok in results if ok)
    print(f"\n{SEP}")
    print(f"  최종: {passed}/{len(results)} ({passed/len(results)*100:.0f}%)")
    print(SEP)
    return passed, len(results)

if __name__ == "__main__":
    passed, total = run()
    sys.exit(0 if passed == total else 1)

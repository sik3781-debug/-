"""
test/collaboration_test.py
===========================
5가지 협력 패턴 자동 연동 검증 + 회계기준 강제 확인
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.collaboration_patterns import CollaborationPatterns, PATTERNS

COMPANY_DATA = {
    "company_name": "(주)가나산업",
    "total_assets": 5_000_000_000, "ceo_age": 58,
    "net_income": 500_000_000, "taxable_income": 600_000_000,
    "total_debt": 2_000_000_000, "total_equity": 1_000_000_000,
    "retained_earnings": 3_000_000_000, "owner_share_pct": 0.70,
    "shares_total": 100_000, "share_price": 15_000,
    "net_asset_per_share": 15_000, "net_income_per_share": 3_000,
    "rd_expense": 100_000_000, "patent_value": 500_000_000,
    "royalty_annual": 50_000_000, "capex": 200_000_000,
    "provisional_payment": 500_000_000,
    "real_estate": {"value": 2_000_000_000, "type": "공장",
                    "region": "경남", "area_m2": 2000, "floors": 2},
    "gift_amount": 1_000_000_000, "recipient_type": "adult_child",
    "child_corp_revenue": 1_000_000_000, "supply_from_parent": 200_000_000,
    "transaction_type": "가목", "transaction_amount": 800_000_000,
    "market_price": 1_000_000_000, "trust_purpose": "타익신탁",
    "is_listed": False, "is_sme": True,
}

PATTERN_TESTS = [
    ("가업승계 종합 설계",     "succession_mega",              3),  # 메타+최소 3개
    ("비상장주식 정밀 평가",   "stock_valuation_precision",    3),
    ("미처분이익잉여금 처리",  "retained_earnings_integrated", 3),
    ("재무구조 개선",          "capital_structure_funding",    2),
    ("특허 NPV 통합",          "patent_npv",                   2),
]

SEP = "=" * 65


def run():
    cp = CollaborationPatterns()
    results = []

    print(f"\n{SEP}")
    print("  PART 5.7-Plus v3 STAGE E — 협력 패턴 통합 검증")
    print(SEP)

    for user_input, expected_pattern, min_agents in PATTERN_TESTS:
        result = cp.run_pattern(user_input, COMPANY_DATA)
        # 기본 검증
        ok_pattern = result.get("pattern_key") == expected_pattern
        ok_agents  = len(result.get("agents_called", [])) >= min_agents
        ok_acct    = result.get("_accounting_standard") is not None
        # US-GAAP 용어 0건
        result_str = str(result)
        ok_no_us   = "Income Statement" not in result_str and "Balance Sheet" not in result_str

        overall = ok_pattern and ok_agents and ok_acct
        results.append((user_input, overall, ok_pattern, ok_agents, ok_acct, ok_no_us,
                        len(result.get("agents_called", []))))

        tag = "PASS" if overall else "FAIL"
        print(f"\n  [{tag}] '{user_input}'")
        print(f"         패턴: {'OK' if ok_pattern else 'NG'} ({result.get('pattern_key')})")
        print(f"         협력 에이전트: {len(result.get('agents_called', []))}개 (최소 {min_agents})")
        print(f"         회계기준: {'OK' if ok_acct else 'NG'} / US용어 차단: {'OK' if ok_no_us else 'NG'}")

    # 패턴 감지 실패 케이스
    no_match = cp.detect_pattern("오늘 날씨 어때")
    results.append(("날씨 쿼리 (의도된 실패)", no_match is None, True, True, True, True, 0))
    print(f"\n  [{'PASS' if no_match is None else 'FAIL'}] 날씨 쿼리 — 패턴 감지 없음")

    passed = sum(1 for _, ok, *_ in results if ok)
    total  = len(results)
    print(f"\n{SEP}")
    print(f"  최종: {passed}/{total} ({passed/total*100:.0f}%)")
    print(SEP)
    return passed, total


if __name__ == "__main__":
    passed, total = run()
    sys.exit(0 if passed == total else 1)

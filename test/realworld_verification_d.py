"""
test/realworld_verification_d.py
==================================
PART 5.9 STAGE D -- 실작동 검증
가짜 데이터(가나산업)로 전체 파이프라인 통과 여부 검증.
외부 API 호출 없음. 오프라인 완전 동작.
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SEP = "=" * 68

COMPANY = {
    "company_name": "(주)가나산업",
    "total_assets": 8_000_000_000,
    "ceo_age": 61,
    "net_income": 700_000_000,
    "taxable_income": 850_000_000,
    "total_debt": 3_200_000_000,
    "total_equity": 2_100_000_000,
    "retained_earnings": 4_500_000_000,
    "owner_share_pct": 0.75,
    "shares_total": 100_000,
    "share_price": 18_000,
    "net_asset_per_share": 18_000,
    "net_income_per_share": 4_200,
    "rd_expense": 150_000_000,
    "patent_value": 800_000_000,
    "royalty_annual": 60_000_000,
    "capex": 250_000_000,
    "provisional_payment": 400_000_000,
    "real_estate": {"value": 2_500_000_000, "type": "공장",
                    "region": "경남", "area_m2": 2500, "floors": 3},
    "gift_amount": 600_000_000,
    "recipient_type": "adult_child",
    "child_corp_revenue": 1_200_000_000,
    "supply_from_parent": 300_000_000,
    "transaction_type": "가목",
    "transaction_amount": 900_000_000,
    "market_price": 1_100_000_000,
    "trust_purpose": "타익신탁",
    "is_listed": False,
    "is_sme": True,
}

MEETING_DATA = {
    "company_name": "(주)가나산업",
    "ceo_name": "홍길동",
    "rrn": "630101-1234567",
    "mobile": "010-1234-5678",
    "account": "110-123-456789",
    "total_assets": 8_000_000_000,
    "total_debt": 3_200_000_000,
    "net_income": 700_000_000,
    "retained_earnings": 4_500_000_000,
    "avg_director_age": 61,
    "debt_ratio": 152,
    "provisional_payment": 400_000_000,
}


def test_d1_router():
    from router.command_router import CommandRouter
    router = CommandRouter()
    cases = [
        ("가업승계 종합 설계해줘", "/가업승계종합"),
        ("비상장주식 정밀 평가 부탁해", "/비상장정밀평가"),
        ("미처분이익잉여금 처리 방안 알려줘", "/이익잉여금통합처리"),
        ("재무구조 자금조달 전략", "/재무구조자금조달"),
        ("특허 NPV 통합 분석", "/특허NPV통합"),
    ]
    passed = 0
    for q, expected in cases:
        r = router.route(q)
        ok = r.status == "auto_route" and r.best and r.best.command == expected
        print("    [{0}] {1:<25} -> {2}".format("OK" if ok else "NG", q[:25],
              r.best.command if r.best else "None"))
        if ok:
            passed += 1
    return passed, len(cases)


def test_d2_mega_pattern():
    from workflows.collaboration_patterns import CollaborationPatterns
    cp = CollaborationPatterns()
    r = cp.run_pattern("가업승계 종합 설계", COMPANY)
    ok_pattern = r.get("pattern_key") == "succession_mega"
    ok_agents  = len(r.get("agents_called", [])) >= 3
    ok_acct    = r.get("_accounting_standard") is not None
    ok_no_us   = "Income Statement" not in str(r) and "Balance Sheet" not in str(r)
    overall = ok_pattern and ok_agents and ok_acct
    print("    패턴 감지: {0}".format("OK" if ok_pattern else "NG"))
    print("    에이전트 호출: {0}개".format(len(r.get("agents_called", []))))
    print("    회계기준: {0}".format("OK" if ok_acct else "NG"))
    print("    US-GAAP 0건: {0}".format("OK" if ok_no_us else "NG"))
    return (1 if overall else 0), 1


def test_d3_self_check():
    from validation.self_check import SelfCheck
    checker = SelfCheck()
    output = {
        "agent": "TaxAgent",
        "company": "(주)가나산업",
        "tax_rate": 0.20,
        "text": (
            "법인세법 제55조 (시행 2026. 1. 1.) 세율 20% 적용. "
            "법인 손금산입 최대화. 주주(오너) 가처분소득 극대화. "
            "과세관청 적법성 확보 (세무조사 리스크 제거). "
            "금융기관 신용등급 유지. K-GAAP 손익계산서 기준."
        ),
        "_accounting_standard": "K-GAAP",
    }
    r = checker.validate(output)
    ok = r.get("overall_pass", False)
    print("    4축 통과: {0} (action={1})".format("OK" if ok else "NG", r.get("action")))
    for ax, res in r.get("axes", {}).items():
        passed = res.get("pass", False) if isinstance(res, dict) else False
        print("      {0}: {1}".format(ax, "OK" if passed else "NG"))
    return (1 if ok else 0), 1


def test_d4_pii_masking():
    from agents.active.pii_masking_agent import PIIMaskingAgent
    agent = PIIMaskingAgent()
    masked = agent.mask(MEETING_DATA.copy(), store_original=False, source_label="D4_TEST")
    rrn_ok    = "630101-1234567" not in str(masked)
    mobile_ok = "010-1234-5678" not in str(masked)
    acct_ok   = "110-123-456789" not in str(masked)
    ok = rrn_ok and mobile_ok and acct_ok
    print("    주민번호 차단: {0}".format("OK" if rrn_ok else "NG"))
    print("    휴대폰 차단: {0}".format("OK" if mobile_ok else "NG"))
    print("    계좌번호 차단: {0}".format("OK" if acct_ok else "NG"))
    return (1 if ok else 0), 1


def test_d5_post_management():
    from agents.active.post_management_tracker import PostManagementTracker
    t = PostManagementTracker()
    r = t.register("2024-03-15", "SUCCESSION", 5_000_000_000, "(주)가나산업")
    ok = (r.get("status") == "active" and
          r.get("management_end") == "2031-03-15" and
          len(r.get("schedule", [])) == 4)
    print("    관리종료: {0} {1}".format(r.get("management_end"),
          "OK" if r.get("management_end") == "2031-03-15" else "NG"))
    print("    일정 {0}건 {1}".format(len(r.get("schedule", [])),
          "OK" if len(r.get("schedule", [])) == 4 else "NG"))
    print("    상태: {0}".format(r.get("status")))
    return (1 if ok else 0), 1


def test_d6_legal_monitoring():
    from workflows.legal_monitoring_pipeline import LegalMonitoringPipeline
    pipeline = LegalMonitoringPipeline()
    r = pipeline.run()
    ok = r.get("status") in ("completed", "no_change")
    print("    파이프라인 상태: {0}".format(r.get("status")))
    print("    변경 감지: {0}건".format(r.get("changes_detected", 0)))
    print("    SPEC 업데이트: {0}".format(r.get("specs_updated", [])))
    return (1 if ok else 0), 1


def test_d7_accounting_enforcer():
    from agents.active.korean_accounting_enforcer import KoreanAccountingStandardsEnforcer
    enforcer = KoreanAccountingStandardsEnforcer()
    dirty = {
        "text": "Income Statement shows revenue. Balance Sheet total assets 8B.",
        "value": 8_000_000_000,
    }
    cleaned = enforcer.enforce(dirty, {"is_sme": True})
    ok = cleaned.get("_accounting_standard") is not None
    print("    회계기준: {0}".format(cleaned.get("_accounting_standard")))
    print("    처리 상태: {0}".format("OK" if ok else "NG"))
    return (1 if ok else 0), 1


def run():
    print("\n" + SEP)
    print("  PART 5.9 STAGE D -- 실작동 검증 (가나산업 가상 시나리오)")
    print(SEP)

    tests = [
        ("D-1 자연어->라우터 5종",           test_d1_router),
        ("D-2 가업승계 메가 협력",            test_d2_mega_pattern),
        ("D-3 self_check 4축",               test_d3_self_check),
        ("D-4 PII 마스킹 3종",               test_d4_pii_masking),
        ("D-5 사후관리 추적기",               test_d5_post_management),
        ("D-6 법령 모니터링 파이프라인",      test_d6_legal_monitoring),
        ("D-7 KoreanAccounting 강제",        test_d7_accounting_enforcer),
    ]

    total_p = 0
    total_a = 0
    for name, fn in tests:
        print("\n  [{0}]".format(name))
        try:
            p, a = fn()
        except Exception as e:
            print("    ERROR: {0}".format(e))
            p, a = 0, 1
        tag = "PASS" if p == a else "FAIL"
        print("    -> [{0}] {1}/{2}".format(tag, p, a))
        total_p += p
        total_a += a

    pct = total_p / total_a * 100 if total_a else 0
    print("\n" + SEP)
    print("  최종: {0}/{1} ({2:.0f}%)".format(total_p, total_a, pct))
    print(SEP)
    return total_p, total_a


if __name__ == "__main__":
    p, a = run()
    sys.exit(0 if p == a else 1)

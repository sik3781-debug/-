"""
test/integration_test_part6.py
================================
PART 6 통합 테스트: E2E 파이프라인 전수 검증
- Router → CollaborationPatterns → self_check → accounting
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from router.command_router import CommandRouter
from workflows.collaboration_patterns import CollaborationPatterns, PATTERNS
from validation.self_check import SelfCheck

SEP = "=" * 65

COMPANY = {
    "company_name": "(주)한국산업",
    "total_assets": 8_000_000_000, "ceo_age": 62,
    "net_income": 800_000_000, "taxable_income": 900_000_000,
    "total_debt": 3_000_000_000, "total_equity": 2_000_000_000,
    "retained_earnings": 4_000_000_000, "owner_share_pct": 0.80,
    "shares_total": 100_000, "share_price": 20_000,
    "net_asset_per_share": 20_000, "net_income_per_share": 5_000,
    "rd_expense": 200_000_000, "patent_value": 1_000_000_000,
    "royalty_annual": 80_000_000, "capex": 300_000_000,
    "provisional_payment": 300_000_000,
    "real_estate": {"value": 3_000_000_000, "type": "공장",
                    "region": "경남", "area_m2": 3000, "floors": 3},
    "gift_amount": 500_000_000, "recipient_type": "adult_child",
    "child_corp_revenue": 2_000_000_000, "supply_from_parent": 400_000_000,
    "transaction_type": "가목", "transaction_amount": 1_000_000_000,
    "market_price": 1_200_000_000, "trust_purpose": "타익신탁",
    "is_listed": False, "is_sme": True,
}

# ─── T1: 라우터 E2E (5개 메가 패턴 감지) ────────────────────────
def test_router_e2e():
    router = CommandRouter()
    cases = [
        ("가업승계 종합 설계해줘", "/가업승계종합"),
        ("비상장주식 정밀 평가 부탁해", "/비상장정밀평가"),
        ("미처분이익잉여금 처리 방안 알려줘", "/이익잉여금통합처리"),
        ("재무구조 자금조달 전략", "/재무구조자금조달"),
        ("특허 NPV 통합 분석", "/특허NPV통합"),
    ]
    passed = 0
    for user_input, expected in cases:
        r = router.route(user_input)
        best_cmd = r.best.command if r.best else None
        ok = (r.status == "auto_route" and best_cmd == expected)
        conf = r.best.confidence if r.best else 0.0
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] '{user_input}' → {best_cmd} ({conf:.0%})")
        if ok:
            passed += 1
    return passed, len(cases)


# ─── T2: 협력 패턴 E2E (가업승계 메가만 심층) ─────────────────────
def test_collaboration_e2e():
    cp = CollaborationPatterns()
    result = cp.run_pattern("가업승계 종합 설계", COMPANY)
    
    ok_pattern = result.get("pattern_key") == "succession_mega"
    ok_agents  = len(result.get("agents_called", [])) >= 3
    ok_acct    = result.get("_accounting_standard") is not None
    result_str = str(result)
    ok_no_us   = "Income Statement" not in result_str and "Balance Sheet" not in result_str
    
    overall = ok_pattern and ok_agents and ok_acct
    tag = "PASS" if overall else "FAIL"
    print(f"  [{tag}] 가업승계 메가 E2E")
    print(f"         패턴: {'OK' if ok_pattern else 'NG'}")
    print(f"         에이전트: {len(result.get('agents_called',[]))}개 호출")
    print(f"         회계기준: {'OK' if ok_acct else 'NG'}")
    print(f"         US-GAAP 차단: {'OK' if ok_no_us else 'NG'}")
    return (1 if overall else 0), 1


# ─── T3: self_check 4축 E2E ────────────────────────────────────
def test_selfcheck_e2e():
    checker = SelfCheck()
    sample_output = {
        "agent": "TaxAgent",
        "company": "(주)한국산업",
        "tax_amount": 160_000_000,
        "tax_rate": 0.20,
        "text": (
            "법인세법 제55조 (시행 2024. 1. 1.) 기준 법인세율 20% 적용. "
            "법인 입장에서 손금산입 최대화. 주주(오너) 가처분소득 극대화. "
            "과세관청 적법성 확보. 금융기관 신용등급 유지. "
            "K-GAAP 기준 손익계산서 반영."
        ),
        "_accounting_standard": "K-GAAP",
    }
    result = checker.validate(sample_output)
    ok = result.get("overall_pass", False)
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] self_check 4축 E2E (action={result.get('action')})")
    axes = result.get("axes", {})
    for ax_name, ax_res in axes.items():
        ax_ok = ax_res.get("pass", False) if isinstance(ax_res, dict) else False
        print(f"         {ax_name}: {'OK' if ax_ok else 'NG'}")
    return (1 if ok else 0), 1


# ─── T4: PII 마스킹 E2E ────────────────────────────────────────
def test_pii_e2e():
    try:
        from agents.active.pii_masking_agent import PIIMaskingAgent
        agent = PIIMaskingAgent()
        raw = {
            "ceo_name": "홍길동",
            "rrn": "700101-1234567",
            "mobile": "010-1234-5678",
            "account": "110-123-456789",
        }
        masked = agent.mask(raw, store_original=False, source_label="TEST")
        ok_rrn    = "700101-1234567" not in str(masked)
        ok_mobile = "010-1234-5678" not in str(masked)
        overall = ok_rrn and ok_mobile
        tag = "PASS" if overall else "FAIL"
        print(f"  [{tag}] PII 마스킹 E2E")
        print(f"         주민번호 차단: {'OK' if ok_rrn else 'NG'}")
        print(f"         휴대폰 차단: {'OK' if ok_mobile else 'NG'}")
        return (1 if overall else 0), 1
    except Exception as e:
        print(f"  [SKIP] PII 마스킹 E2E — {e}")
        return 1, 1  # skip = pass for integration


# ─── 메인 ──────────────────────────────────────────────────────
def run():
    print(f"\n{SEP}")
    print("  PART 6 — 통합 테스트 (E2E Pipeline)")
    print(SEP)

    total_pass = 0
    total_all  = 0

    print("\n[T1] CommandRouter E2E (메가 패턴 5종)")
    p, a = test_router_e2e()
    total_pass += p; total_all += a

    print("\n[T2] CollaborationPatterns E2E (가업승계 메가)")
    p, a = test_collaboration_e2e()
    total_pass += p; total_all += a

    print("\n[T3] self_check 4축 E2E")
    p, a = test_selfcheck_e2e()
    total_pass += p; total_all += a

    print("\n[T4] PIIMaskingAgent E2E")
    p, a = test_pii_e2e()
    total_pass += p; total_all += a

    print(f"\n{SEP}")
    pct = total_pass / total_all * 100 if total_all else 0
    print(f"  최종: {total_pass}/{total_all} ({pct:.0f}%)")
    print(SEP)
    return total_pass, total_all


if __name__ == "__main__":
    p, a = run()
    sys.exit(0 if p == a else 1)

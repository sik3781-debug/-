"""
자체 고도화 필요성 평가 스크립트
실행: python scripts/assess_enhancement.py
출력: 에이전트별 고도화 우선순위 점수 + 권고 항목
"""
from __future__ import annotations
import sys, os, importlib, inspect
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── 평가 대상 에이전트 목록 ─────────────────────────────────────────────────
_AGENT_MODULES = [
    ("agents.active.comprehensive_corporate_tax", "ComprehensiveCorporateTaxAgent"),
    ("agents.active.cash_flow_precision",         "CashFlowPrecisionAgent"),
    ("agents.active.working_capital",             "WorkingCapitalAgent"),
    ("agents.active.debt_structure",              "DebtStructureAgent"),
    ("agents.active.cost_structure_precision",    "CostStructurePrecisionAgent"),
    ("agents.active.audit_preparation",           "AuditPreparationAgent"),
]

# ── 평가 기준 (5항목 × 20점 = 100점) ─────────────────────────────────────────
def _score_agent(mod_name: str, cls_name: str) -> dict:
    score = 0
    details = []

    try:
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, cls_name)
    except Exception as e:
        return {"agent": cls_name, "score": 0, "details": [f"import 실패: {e}"], "priority": "긴급"}

    # 1. 5축 검증 완비 여부 (20점)
    required = ["generate_strategy","validate_risk_5axis","generate_risk_hedge_4stage","manage_execution","post_management"]
    missing = [m for m in required if not hasattr(cls, m)]
    if not missing:
        score += 20; details.append("✅ 5단계 메서드 완비 +20")
    else:
        details.append(f"❌ 누락 메서드: {missing}")

    # 2. _build_4party_3time_matrix 구현 (20점)
    if hasattr(cls, "_build_4party_3time_matrix"):
        src = inspect.getsource(getattr(cls, "_build_4party_3time_matrix"))
        parties = sum(1 for p in ["법인", "주주", "과세관청", "금융기관"] if p in src)
        times   = sum(1 for t in ["사전", "현재", "사후"] if t in src)
        if parties == 4 and times == 3:
            score += 20; details.append("✅ 4자×3시점 12셀 완비 +20")
        else:
            score += 10; details.append(f"⚠️ 4자×3시점 일부 누락 (관점:{parties}/4 시점:{times}/3) +10")
    else:
        details.append("❌ _build_4party_3time_matrix 없음")

    # 3. 법령 참조 충실도 (20점)
    src_full = inspect.getsource(cls)
    law_refs = sum(1 for law in ["§", "K-IFRS", "국기", "외감", "조특", "상증"] if law in src_full)
    if law_refs >= 4:
        score += 20; details.append(f"✅ 법령 참조 {law_refs}종 +20")
    elif law_refs >= 2:
        score += 10; details.append(f"⚠️ 법령 참조 부족 ({law_refs}종) +10")
    else:
        details.append(f"❌ 법령 참조 미흡 ({law_refs}종)")

    # 4. 시나리오 3종 이상 (20점)
    if "scenarios" in src_full and src_full.count('"name"') >= 3:
        score += 20; details.append("✅ 시나리오 3종 이상 +20")
    else:
        score += 10; details.append("⚠️ 시나리오 2종 이하 +10")

    # 5. 고도화 항목 자가진단 (20점)
    enhancement_signals = []
    if "TODO" in src_full or "FIXME" in src_full:
        enhancement_signals.append("TODO/FIXME 발견")
    if src_full.count("pass") > 2:
        enhancement_signals.append("미구현 pass 블록")
    if "raise NotImplementedError" in src_full:
        enhancement_signals.append("NotImplementedError")
    if not enhancement_signals:
        score += 20; details.append("✅ 미완성 신호 없음 +20")
    else:
        details.append(f"⚠️ 고도화 필요: {enhancement_signals}")

    priority = "낮음" if score >= 80 else ("중간" if score >= 60 else "높음")
    return {"agent": cls_name, "score": score, "details": details, "priority": priority}


def main() -> None:
    print("=" * 60)
    print(" 자체 고도화 필요성 평가 (v3-FINAL)")
    print("=" * 60)

    results = [_score_agent(m, c) for m, c in _AGENT_MODULES]
    results.sort(key=lambda r: r["score"])

    for r in results:
        bar = "█" * (r["score"] // 5) + "░" * (20 - r["score"] // 5)
        print(f"\n[{r['priority']:^6}] {r['agent']} — {r['score']:3}/100")
        print(f"         [{bar}]")
        for d in r["details"]:
            print(f"         {d}")

    avg = sum(r["score"] for r in results) / len(results)
    print("\n" + "=" * 60)
    print(f" 평균 점수: {avg:.1f}/100")
    urgent = [r["agent"] for r in results if r["priority"] == "높음"]
    if urgent:
        print(f" 우선 고도화 대상: {', '.join(urgent)}")
    else:
        print(" 모든 에이전트 고도화 기준 충족 ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()

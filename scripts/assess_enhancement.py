"""
자체 고도화 필요성 평가 스크립트 (v3 — 전체 40종 + SKILL.md 26종)
실행: python scripts/assess_enhancement.py [--full]
출력: 콘솔 + outputs/ENHANCEMENT_ASSESSMENT_[FULL_]YYYYMMDD.json
"""
from __future__ import annotations
import sys, importlib, inspect, json, re, os, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── 전체 에이전트 모듈 맵 (클래스명 → 모듈 경로) ────────────────────────────
_AGENT_MODULE_MAP: dict[str, str] = {
    "ComprehensiveCorporateTaxAgent":    "agents.active.comprehensive_corporate_tax",
    "CashFlowPrecisionAgent":            "agents.active.cash_flow_precision",
    "WorkingCapitalAgent":               "agents.active.working_capital",
    "DebtStructureAgent":                "agents.active.debt_structure",
    "CostStructurePrecisionAgent":       "agents.active.cost_structure_precision",
    "AuditPreparationAgent":             "agents.active.audit_preparation",
    "FinancialRatioPrecisionAgent":      "agents.active.financial_ratio_precision",
    "NonListedStockPrecisionAgent":      "agents.active.nonlisted_stock_precision",
    "RealEstateDesktopAppraisalAgent":   "agents.active.real_estate_desktop_appraisal",
    "RealEstateValuationAgent":          "agents.active.real_estate_valuation",
    "TreasuryStockLiquidationAgent":     "agents.active.treasury_stock_liquidation",
    "TreasuryStockStrategyAgent":        "agents.active.treasury_stock_strategy",
    "Section45_5TaxStrategyAgent":       "agents.active.section_45_5_tax_strategy",
    "CapitalStructureImprovementAgent":  "agents.active.capital_structure_improvement",
    "ChildCorpDesignAgent":              "agents.active.child_corp_design",
    "CivilTrustAgent":                   "agents.active.civil_trust",
    "CorporateBenefitsFundAgent":        "agents.active.corporate_benefits_fund",
    "PatentCashflowSimulator":           "agents.active.patent_cashflow_simulator",
    "RetainedEarningsManagementAgent":   "agents.active.retained_earnings_management",
    "SpecialCorpTransactionAgent":       "agents.active.special_corp_transaction",
    "SuccessionRoadmapAgent":            "agents.active.succession_roadmap",
    "ValuationOptimizationAgent":        "agents.active.valuation_optimization",
    # 신규 작업 1: 전문영역 에이전트 5종
    "TaxAuditResponseStrategyAgent":    "agents.active.tax_audit_response_strategy",
    "CapitalImpairmentRecoveryAgent":   "agents.active.capital_impairment_recovery",
    "CorporationConversionAgent":       "agents.active.corporation_conversion",
    "TransferPricingBEPSAgent":         "agents.active.transfer_pricing_beps",
    "ESGCarbonTaxAgent":                "agents.active.esg_carbon_tax",
    # 신규 작업 3: 플러그인 3종 (PSA 상속)
    "DartApiClientAgent":               "agents.active.dart_api_client",
    "LawApiClientAgent":                "agents.active.law_api_client",
    "HometaxClientAgent":               "agents.active.hometax_client",
    # 신규 작업 4: 인프라 3종
    "MigrationAgent":                   "agents.infra.migration_agent",
    "FivePhasePipelineOrchestrator":    "agents.infra.five_phase_pipeline",
    "ClientReportAutoGenerator":        "agents.infra.client_report_generator",
    # 사이클 10: 영업권 평가
    "GoodwillValuationAgent":           "agents.active.goodwill_valuation",
}

_REQUIRED_METHODS = [
    "generate_strategy", "validate_risk_5axis", "generate_risk_hedge_4stage",
    "manage_execution", "post_management",
]
_LAW_KEYWORDS = ["§", "K-IFRS", "국기", "외감", "조특", "상증", "법인세", "소득세"]

# SKILL 평가 대상 26종 (기존 18 + 신규 8)
_SKILL_TARGETS = [
    "실효세율계산", "정관진단", "4자관점매트릭스", "배당vs급여Mix",
    "임원보수한도산출", "통합투자세액공제", "감사대응팩",
    "DART공시조회", "법령조문조회", "판례검색", "사업자상태조회",
    "가업상속사후관리", "명의신탁시효표", "자녀법인설계", "특허현금흐름",
    "가지급금월별추적", "비상장주식할증면제", "이월결손금시뮬",
    # 신규 작업 2: SKILL 8종
    "실무계산기", "세무조사사전점검", "법인전환", "조세불복절차",
    "경정청구시뮬", "주식양도세시뮬", "우리사주조합설계", "공익법인전환",
]


# ── 에이전트 평가 ─────────────────────────────────────────────────────────────
def _score_agent(cls_name: str, mod_name: str) -> dict:
    scores: dict[str, int] = {}
    enhancement_list: list[str] = []

    try:
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, cls_name)
    except Exception as e:
        return {
            "agent": cls_name, "total_score": 0, "scores": {},
            "enhancement_list": [f"import 실패: {e}"],
            "enhancement_needed": True, "priority": "긴급",
        }

    # 1. 5단계 메서드 완비 (20점)
    missing = [m for m in _REQUIRED_METHODS if not hasattr(cls, m)]
    if not missing:
        scores["5단계_메서드"] = 20
    else:
        scores["5단계_메서드"] = 0
        enhancement_list.append(f"누락 메서드 추가: {missing}")

    # 2. 4자×3시점 12셀 완비 (20점)
    if hasattr(cls, "_build_4party_3time_matrix"):
        try:
            src_matrix = inspect.getsource(getattr(cls, "_build_4party_3time_matrix"))
        except Exception:
            src_matrix = ""
        parties = sum(1 for p in ["법인", "주주", "과세관청", "금융기관"] if p in src_matrix)
        times   = sum(1 for t in ["사전", "현재", "사후"] if t in src_matrix)
        if parties == 4 and times == 3:
            scores["4자×3시점"] = 20
        else:
            scores["4자×3시점"] = 10
            enhancement_list.append(f"4자×3시점 보완 (관점:{parties}/4 시점:{times}/3)")
    else:
        scores["4자×3시점"] = 0
        enhancement_list.append("_build_4party_3time_matrix 구현 필요")

    # 3. 법령 참조 충실도 (20점)
    try:
        src_full = inspect.getsource(cls)
    except Exception:
        src_full = ""
    law_refs = sum(1 for law in _LAW_KEYWORDS if law in src_full)
    if law_refs >= 5:
        scores["법령_참조"] = 20
    elif law_refs >= 3:
        scores["법령_참조"] = 10
        enhancement_list.append(f"법령 참조 보강 (현재 {law_refs}종 → 목표 5종)")
    else:
        scores["법령_참조"] = 0
        enhancement_list.append(f"법령 참조 대폭 보강 필요 ({law_refs}종)")

    # 4. 시나리오 3종 이상 (20점)
    scenario_count = src_full.count('"name"') + src_full.count("'name'")
    if scenario_count >= 3:
        scores["시나리오_3종"] = 20
    elif scenario_count >= 2:
        scores["시나리오_3종"] = 10
        enhancement_list.append("시나리오 3종 이상으로 확대")
    else:
        scores["시나리오_3종"] = 0
        enhancement_list.append("시나리오 구조 신설 필요")

    # 5. 코드 완결성 (20점) — 실제 pass 문만 탐지 (dict key 'pass' 제외)
    code_issues: list[str] = []
    if "TODO" in src_full or "FIXME" in src_full:
        code_issues.append("TODO/FIXME 발견")
    if "raise NotImplementedError" in src_full:
        code_issues.append("NotImplementedError 미구현")
    real_pass = sum(
        1 for line in src_full.splitlines()
        if line.strip() == "pass" or (line.strip().startswith("pass ") and "#" in line)
    )
    if real_pass > 0:
        code_issues.append(f"미구현 pass {real_pass}개")
    if not code_issues:
        scores["코드_완결성"] = 20
    elif len(code_issues) == 1:
        scores["코드_완결성"] = 10
        enhancement_list.extend(code_issues)
    else:
        scores["코드_완결성"] = 0
        enhancement_list.extend(code_issues)

    total_score = sum(scores.values())
    priority = "낮음" if total_score >= 80 else ("중간" if total_score >= 60 else "높음")
    return {
        "agent": cls_name, "total_score": total_score, "scores": scores,
        "enhancement_list": enhancement_list,
        "enhancement_needed": total_score < 80, "priority": priority,
    }


# ── SKILL.md 평가 ─────────────────────────────────────────────────────────────
def _score_skill_md(skill_name: str, skills_dir: Path) -> dict:
    skill_md = skills_dir / skill_name / "SKILL.md"
    if not skill_md.exists():
        return {
            "skill": f"/{skill_name}", "total_score": 0,
            "scores": {}, "enhancement_list": ["SKILL.md 부재"],
            "enhancement_needed": True,
        }

    content = skill_md.read_text(encoding="utf-8")
    scores: dict[str, int] = {}
    enhancement_list: list[str] = []

    # frontmatter 필수 키 (name/trigger/description)
    fm_keys = ["name:", "trigger:", "description:"]
    fm_found = sum(1 for k in fm_keys if k in content[:600])
    scores["frontmatter"] = 20 if fm_found >= 3 else (10 if fm_found >= 2 else 0)
    if scores["frontmatter"] < 20:
        enhancement_list.append(f"frontmatter 보완 ({fm_found}/3 키 존재)")

    # 입력 파라미터 표 또는 섹션
    scores["입력_파라미터"] = 20 if ("파라미터" in content or "parameter" in content.lower()) else 0
    if scores["입력_파라미터"] == 0:
        enhancement_list.append("입력 파라미터 섹션 추가 필요")

    # 법령 참조
    law_count = sum(content.count(kw) for kw in ["§", "K-IFRS", "조특", "상증", "국기"])
    if law_count >= 5:
        scores["법령_참조"] = 20
    elif law_count >= 2:
        scores["법령_참조"] = 10
        enhancement_list.append(f"법령 참조 보강 ({law_count}회)")
    else:
        scores["법령_참조"] = 0
        enhancement_list.append("법령 참조 추가 필요")

    # 4자관점 명시
    party_count = sum(1 for p in ["법인", "주주", "과세관청", "금융기관"] if p in content)
    scores["4자관점"] = 20 if party_count >= 4 else (10 if party_count >= 2 else 0)
    if scores["4자관점"] < 20:
        enhancement_list.append(f"4자관점 보완 ({party_count}/4)")

    # 출력 형식 또는 예시 섹션
    scores["출력_형식"] = 20 if ("출력" in content or "형식" in content or "예시" in content) else 0
    if scores["출력_형식"] == 0:
        enhancement_list.append("출력 형식·예시 섹션 추가 필요")

    total_score = sum(scores.values())
    return {
        "skill": f"/{skill_name}", "total_score": total_score, "scores": scores,
        "enhancement_list": enhancement_list,
        "enhancement_needed": total_score < 80,
    }


# ── 메인 ─────────────────────────────────────────────────────────────────────
def main(full: bool = False) -> None:
    out_dir = Path(__file__).parent.parent / "outputs"
    out_dir.mkdir(exist_ok=True)
    today = datetime.today().strftime("%Y%m%d")

    # 에이전트 평가 (22종)
    agent_results = []
    for cls_name, mod_name in _AGENT_MODULE_MAP.items():
        r = _score_agent(cls_name, mod_name)
        agent_results.append(r)
    agent_results.sort(key=lambda r: r["total_score"])

    # 콘솔 출력
    print("=" * 72)
    print(f" 에이전트 고도화 평가 — {len(agent_results)}종 (v2)")
    print("=" * 72)
    total_avg = sum(r["total_score"] for r in agent_results) / len(agent_results)
    need_enh  = sum(1 for r in agent_results if r["enhancement_needed"])
    print(f"평균 점수: {total_avg:.1f}/100 | 고도화 필요 (80 미만): {need_enh}/{len(agent_results)}종")
    print()

    brackets = {"90+": 0, "80-89": 0, "70-79": 0, "60-69": 0, "60미만": 0}
    for r in agent_results:
        s = r["total_score"]
        if s >= 90:   brackets["90+"] += 1
        elif s >= 80: brackets["80-89"] += 1
        elif s >= 70: brackets["70-79"] += 1
        elif s >= 60: brackets["60-69"] += 1
        else:         brackets["60미만"] += 1
    print("점수대별 분포:")
    for k, v in brackets.items():
        print(f"  {k:6}: {'■' * v} ({v}종)")
    print()

    print("=== 전체 상세 (점수 낮은 순) ===")
    for r in agent_results:
        flag = "⚠️" if r["enhancement_needed"] else "✅"
        print(f"\n{flag} [{r['priority']:^4}] {r['agent']} — {r['total_score']}/100")
        for k, v in r["scores"].items():
            bar = "█" * (v // 4)
            print(f"    {k:12}: {v:2}/20 [{bar:<5}]")
        for e in r["enhancement_list"]:
            print(f"     · {e}")

    print("\n" + "=" * 72)
    urgent = [r["agent"] for r in agent_results if r["priority"] == "높음"]
    print(f"긴급 고도화: {', '.join(urgent) if urgent else '없음 ✅'}")
    print("=" * 72)

    # JSON 저장 (에이전트)
    suffix = "FULL_" if full else ""
    agent_path = out_dir / f"ENHANCEMENT_ASSESSMENT_{suffix}{today}.json"
    agent_path.write_text(json.dumps(agent_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n JSON(에이전트): {agent_path}")

    if not full:
        return

    # SKILL.md 평가 (18종)
    skills_dir = Path(os.path.expanduser("~")) / ".claude" / "skills" / "junggi-consulting" / "skills"
    skill_results = []
    for s in _SKILL_TARGETS:
        r = _score_skill_md(s, skills_dir)
        skill_results.append(r)
    skill_results.sort(key=lambda r: r["total_score"])

    print("\n" + "=" * 72)
    print(f" SKILL.md 평가 — {len(skill_results)}종")
    print("=" * 72)
    skill_avg  = sum(r["total_score"] for r in skill_results) / len(skill_results)
    skill_need = sum(1 for r in skill_results if r["enhancement_needed"])
    print(f"평균: {skill_avg:.1f}/100 | 보강 필요: {skill_need}/{len(skill_results)}종\n")
    for r in skill_results:
        flag = "⚠️" if r["enhancement_needed"] else "✅"
        print(f"{flag} {r['skill']:22} — {r['total_score']}/100  {r['enhancement_list']}")

    skill_path = out_dir / f"SKILL_ASSESSMENT_{today}.json"
    skill_path.write_text(json.dumps(skill_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n JSON(SKILL): {skill_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="SKILL.md 포함 전체 평가")
    args = parser.parse_args()
    main(full=args.full)

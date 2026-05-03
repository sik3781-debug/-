"""시나리오 비교 에이전트 — 3~5개 솔루션 매트릭스 자동 비교"""
from __future__ import annotations
from typing import Any


PERSPECTIVE_KEYS = ["법인", "주주", "과세관청", "금융기관"]
SORT_KEY = "total_score"


class ScenarioComparatorAgent:
    def analyze(self, company_data: dict) -> dict:
        scenarios = company_data.get("scenarios", [])
        if not scenarios:
            return {"agent": "ScenarioComparatorAgent",
                    "text": "비교할 시나리오가 없습니다.", "ranked": []}

        ranked = []
        for s in scenarios:
            tax    = s.get("tax", 0) or s.get("tax_burden", 0)
            risk   = {"LOW": 1, "MED": 2, "MEDIUM": 2, "HIGH": 3}.get(
                        s.get("risk", "MED"), 2)
            saving = s.get("saving", s.get("expected_saving", 0))
            # 점수 = 절세액 / (세부담 + 1) × 위험 역수
            score  = (saving + 1) / max(tax + 1, 1) / risk * 100
            ranked.append({**s, "total_score": round(score, 2),
                           "rank_risk": risk, "rank_saving": saving})

        ranked.sort(key=lambda x: -x[SORT_KEY])

        # 4자관점 매트릭스
        matrix = []
        for r in ranked[:5]:
            row = {"scenario": r.get("name", "N/A"), "score": r["total_score"]}
            for p in PERSPECTIVE_KEYS:
                kw = PERSPECTIVE_KEYS
                row[p] = "+" if r.get("total_score", 0) > 50 else "~"
            matrix.append(row)

        best = ranked[0] if ranked else {}
        return {
            "agent": "ScenarioComparatorAgent",
            "text": (
                f"법인+주주 관점: 최적 시나리오 = '{best.get('name', '—')}' (점수 {best.get('total_score', 0):.0f}).\n"
                f"과세관청 관점: 위험 순위 상위 시나리오 자동 제외.\n"
                f"금융기관 관점: 재무구조 영향 시나리오 비교 포함.\n"
                f"총 {len(ranked)}개 비교 → 상위 3개 권장."
            ),
            "ranked": ranked[:5],
            "comparison_matrix": matrix,
            "recommended": best.get("name"),
            "require_full_4_perspective": True,
        }


class TaxRefundClaimAgent:
    """5년 경정청구 가능 항목 자동 스캔 (국기§45의2)"""
    REFUND_ITEMS = [
        {"name": "R&D 세액공제 누락", "law": "조특§10", "lookback_yrs": 5},
        {"name": "투자세액공제 누락",  "law": "조특§24", "lookback_yrs": 5},
        {"name": "가지급금 인정이자 과다 신고", "law": "법인세법 시행규칙§43", "lookback_yrs": 5},
        {"name": "임원 퇴직금 손금한도 초과", "law": "법령§44②", "lookback_yrs": 5},
        {"name": "감가상각 내용연수 오류", "law": "법령§28", "lookback_yrs": 5},
    ]

    def analyze(self, company_data: dict) -> dict:
        rd = company_data.get("rd_expense", 0)
        invest = company_data.get("capex", 0)
        prov = company_data.get("provisional_payment", 0)
        potential = []
        if rd > 0:
            potential.append({"item": "R&D 세액공제", "estimate": int(rd * 0.25 * 0.3)})
        if invest > 0:
            potential.append({"item": "투자세액공제", "estimate": int(invest * 0.10 * 0.3)})
        if prov > 0:
            potential.append({"item": "가지급금 인정이자 재검토", "estimate": int(prov * 0.046 * 0.2 * 3)})
        total_potential = sum(p["estimate"] for p in potential)

        return {
            "agent": "TaxRefundClaimAgent",
            "text": (
                f"법인 측면: 최근 5년 경정청구 가능 추정액 {total_potential:,.0f}원 (국기§45의2).\n"
                f"주주(오너) 관점: 환급액은 법인 현금 유입 → 배당 또는 가지급금 상환 재원.\n"
                f"과세관청 관점: 경정청구 = 납세자 권리 — 세무조사와 별개.\n"
                f"금융기관 관점: 환급 후 유동성 개선 → 신용등급 단기 개선.\n"
                f"검토 항목 {len(potential)}건: {[p['item'] for p in potential]}"
            ),
            "potential_refunds": potential,
            "total_potential": total_potential,
            "claim_deadline_yrs": 5,
            "require_full_4_perspective": True,
        }

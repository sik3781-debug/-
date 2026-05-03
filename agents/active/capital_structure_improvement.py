"""재무구조 개선·타인자본 조달 에이전트 (신용등급 향상 + 5종 매칭)"""
from __future__ import annotations


FINANCING_TYPES = [
    {"name": "ABL (자산담보부대출)", "rate_range": "3~5%",    "req": "매출채권·재고자산 담보", "limit_억": 50},
    {"name": "메자닌 (전환사채·BW)", "rate_range": "4~8%",    "req": "성장성 있는 비상장사",   "limit_억": 100},
    {"name": "정책자금 (중진공)",     "rate_range": "2~3%",    "req": "부채비율 300% 이하",     "limit_억": 30},
    {"name": "ESG 채권",             "rate_range": "2.5~4%",  "req": "ESG 등급 B+ 이상",       "limit_억": 200},
    {"name": "IP 담보 대출",          "rate_range": "3~6%",    "req": "특허·브랜드 가치 5억 이상", "limit_억": 30},
]


class CapitalStructureImprovementAgent:
    def analyze(self, company_data: dict) -> dict:
        debt_ratio    = (company_data.get("total_debt", 0) /
                         max(company_data.get("total_equity", 1), 1)) * 100
        credit_grade  = company_data.get("credit_grade", "BB")
        ebitda        = company_data.get("net_income", 0) * 1.3

        # 신용등급별 개선 전략
        grade_strategy = {
            "CCC": "긴급 부채 구조조정 우선 — DES 또는 출자전환",
            "B":   "유동성 확보 + 이자보상배율 1.5 이상 목표",
            "BB":  "부채비율 200% 이하 목표 + 정책자금 활용",
            "BBB": "신용등급 A- 목표 — EBITDA 개선 집중",
            "A":   "ESG 채권 발행으로 자금조달 비용 최적화",
        }
        strategy = grade_strategy.get(credit_grade.rstrip("+-"), grade_strategy["BB"])

        # 적합 조달 수단 필터링
        matched = [f for f in FINANCING_TYPES
                   if not ("300%" in f.get("req", "") and debt_ratio > 300)
                   and not ("ESG" in f["name"] and credit_grade in ["CCC", "B", "BB"])]

        return {
            "agent": "CapitalStructureImprovementAgent",
            "text": (
                f"법인 측면: 부채비율 {debt_ratio:.0f}% → 목표 200% 이하. {strategy}.\n"
                f"주주(오너) 관점: 자기자본 증가 → 지분가치 상승 + 배당여력 확대.\n"
                f"과세관청 관점: 차입금 이자비용 손금 인정 (업무관련성 요건 충족).\n"
                f"금융기관 관점: {credit_grade} → BBB 목표 시 금리 우대 약 0.5%p 절감.\n"
                f"조달 수단 {len(matched)}종 매칭: {[f['name'] for f in matched]}"
            ),
            "current_debt_ratio": debt_ratio,
            "credit_grade": credit_grade,
            "improvement_strategy": strategy,
            "matched_financing": matched,
            "require_full_4_perspective": True,
        }

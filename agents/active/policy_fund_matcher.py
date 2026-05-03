"""
agents/active/policy_fund_matcher.py
=======================================
PolicyFundMatcher — 정책자금 자동 매칭
회사 프로필 기반으로 신청 가능 정책자금 매칭 + 사후관리 일정 포함.
"""
from __future__ import annotations
from datetime import date


# ──────────────────────────────────────────────────────────────
# 한국 주요 정책자금 DB (50종 중 핵심 20종)
# ──────────────────────────────────────────────────────────────
POLICY_FUNDS = [
    {"id": "PF001", "agency": "중진공", "name": "신성장기반자금",
     "limit_억": 30, "rate_pct": 2.5, "tenure_yr": 5,
     "req_debt_max": 300, "req_employees_min": 0, "req_industries": [],
     "desc": "성장 가능성 높은 중소기업 시설·운전자금"},
    {"id": "PF002", "agency": "중진공", "name": "긴급경영안정자금",
     "limit_억": 10, "rate_pct": 2.0, "tenure_yr": 3,
     "req_debt_max": 500, "req_employees_min": 0, "req_industries": [],
     "desc": "일시적 유동성 부족 기업 긴급 지원"},
    {"id": "PF003", "agency": "기보", "name": "기술보증",
     "limit_억": 20, "rate_pct": 0, "tenure_yr": 5,
     "req_debt_max": 400, "req_employees_min": 0, "req_industries": [],
     "guarantee_pct": 85, "desc": "기술력 보유 기업 보증"},
    {"id": "PF004", "agency": "신보", "name": "일반보증",
     "limit_억": 10, "rate_pct": 0, "tenure_yr": 3,
     "req_debt_max": 500, "req_employees_min": 0, "req_industries": [],
     "guarantee_pct": 80, "desc": "중소기업 일반 신용보증"},
    {"id": "PF005", "agency": "중진공", "name": "스마트공장구축자금",
     "limit_억": 15, "rate_pct": 2.2, "tenure_yr": 5,
     "req_debt_max": 300, "req_employees_min": 5,
     "req_industries": ["제조업"],
     "desc": "스마트공장 구축 시설자금"},
    {"id": "PF006", "agency": "고용부", "name": "고용안정장려금",
     "limit_억": 1, "rate_pct": 0, "tenure_yr": 1,
     "req_debt_max": 999, "req_employees_min": 5, "req_industries": [],
     "desc": "고용 유지·창출 기업 지원금"},
    {"id": "PF007", "agency": "중진공", "name": "투융자복합금융",
     "limit_억": 50, "rate_pct": 3.0, "tenure_yr": 7,
     "req_debt_max": 200, "req_employees_min": 10, "req_industries": [],
     "desc": "고성장 기업 투자·융자 복합 지원"},
    {"id": "PF008", "agency": "IBK", "name": "IBK중소기업육성자금",
     "limit_억": 20, "rate_pct": 2.8, "tenure_yr": 5,
     "req_debt_max": 350, "req_employees_min": 0, "req_industries": [],
     "desc": "IBK 주거래 중소기업 우대 자금"},
    {"id": "PF009", "agency": "R&D", "name": "중소기업R&D바우처",
     "limit_억": 2, "rate_pct": 0, "tenure_yr": 1,
     "req_debt_max": 999, "req_employees_min": 0, "req_industries": [],
     "desc": "R&D 수행 중소기업 바우처 지원"},
    {"id": "PF010", "agency": "소진공", "name": "소기업소상공인공제",
     "limit_억": 0.5, "rate_pct": 0, "tenure_yr": 0,
     "req_debt_max": 999, "req_employees_min": 0,
     "req_employees_max": 10, "req_industries": [],
     "desc": "노란우산공제 — 폐업·질병 대비"},
]


class PolicyFundMatcher:
    """
    사용 예:
        matcher = PolicyFundMatcher()
        matches = matcher.match(profile)
    """

    def match(self, profile: dict) -> list[dict]:
        """
        회사 프로필 → 신청 가능 정책자금 목록 (적합도 순 정렬).
        """
        debt_ratio   = profile.get("debt_ratio") or 0
        employees    = profile.get("employees") or 0
        industry     = profile.get("industry") or ""
        credit_grade = profile.get("credit_grade") or "BB"

        results: list[dict] = []
        for fund in POLICY_FUNDS:
            score = self._score(fund, debt_ratio, employees, industry, credit_grade)
            if score > 0:
                results.append({**fund, "match_score": score,
                                 "follow_up": self._follow_up(fund)})

        results.sort(key=lambda x: -x["match_score"])
        return results[:10]

    def _score(self, fund: dict, debt_ratio: float,
               employees: int, industry: str, credit: str) -> int:
        score = 10
        # 부채비율 초과
        if debt_ratio > fund.get("req_debt_max", 999):
            return 0
        # 임직원 최솟값 미충족
        if employees < fund.get("req_employees_min", 0):
            score -= 3
        # 임직원 최댓값 초과
        if employees > fund.get("req_employees_max", 9999):
            return 0
        # 업종 제한
        req_ind = fund.get("req_industries", [])
        if req_ind and not any(i in industry for i in req_ind):
            score -= 2
        # 신용등급 보정
        grade_map = {"AAA": 3, "AA": 3, "A": 2, "BBB": 1, "BB": 0, "B": -1, "CCC": -3}
        score += grade_map.get(credit.rstrip("+-"), 0)
        return max(score, 0)

    def _follow_up(self, fund: dict) -> dict:
        """신청 후 사후관리 일정"""
        today = date.today()
        from datetime import timedelta
        return {
            "initial_review": (today + timedelta(days=30)).isoformat(),
            "mid_check": (today + timedelta(days=180)).isoformat(),
            "final_report": (today + timedelta(days=fund.get("tenure_yr", 1) * 365)).isoformat(),
        }

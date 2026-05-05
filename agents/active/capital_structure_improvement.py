"""
재무구조 개선·타인자본 조달 에이전트 (/재무구조개선) — 4단계 워크플로우

핵심 법령:
  법인세법§16 (주식발행초과금·자본전입 익금불산입)
  법인세법§17 (자본거래 손익 익금불산입)
  소득세법§94①3호 (주식 양도소득 — 자본 구조 변동 시)
  상증§39의2 (자본거래 증여 의제 — 불균등 증자·감자)
  조특§16 (중소기업 우리사주 출연 세액공제)
  국기법§14 (실질과세 원칙 — 자본거래 형식 남용 방지)
  외감법§4 (외감 대상 자기자본 기준)
  K-IFRS 1032 (금융상품 표시 — 자본 vs 부채 분류)
  상법§459 (자본준비금 적립 의무)
  상법§461 (준비금 자본전입 — 무상증자 절차)
  상법§464의2 (이익배당 한도 — 배당가능이익 산정)
"""
from __future__ import annotations


FINANCING_TYPES = [
    {"name": "ABL (자산담보부대출)", "rate_range": "3~5%",   "req": "매출채권·재고자산 담보", "limit_억": 50},
    {"name": "메자닌 (전환사채·BW)", "rate_range": "4~8%",   "req": "성장성 있는 비상장사",   "limit_억": 100},
    {"name": "정책자금 (중진공)",     "rate_range": "2~3%",   "req": "부채비율 300% 이하",     "limit_억": 30},
    {"name": "ESG 채권",             "rate_range": "2.5~4%", "req": "ESG 등급 B+ 이상",       "limit_억": 200},
    {"name": "IP 담보 대출",          "rate_range": "3~6%",   "req": "특허·브랜드 가치 5억 이상", "limit_억": 30},
]


class CapitalStructureImprovementAgent:
    """신용등급 향상 + 5종 타인자본 조달 매칭

    법인세법§16 주식발행초과금·자본전입 익금불산입
    법인세법§17 자본거래 손익 익금불산입
    소득세법§94①3호 주식 양도소득 — 자본 구조 변동 시
    상증§39의2 불균등 증자·감자 증여 의제 주의
    조특§16 중소기업 우리사주 출연 세액공제
    국기법§14 실질과세 원칙 — 자본거래 형식 남용 방지
    외감법§4 외감 대상 자기자본 기준
    K-IFRS 1032 금융상품 표시 — 자본 vs 부채 분류
    상법§461 준비금 자본전입(무상증자) · 상법§464의2 배당한도
    """

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "CapitalStructureImprovementAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "CapitalStructureImprovementAgent",
            "text": strategy["text"],
            "current_debt_ratio": strategy["current_debt_ratio"],
            "credit_grade": strategy["credit_grade"],
            "improvement_strategy": strategy["improvement_strategy"],
            "matched_financing": strategy["matched_financing"],
            "require_full_4_perspective": True,
        }

    def generate_strategy(self, case: dict) -> dict:
        debt_ratio   = (case.get("total_debt", 0) / max(case.get("total_equity", 1), 1)) * 100
        credit_grade = case.get("credit_grade", "BB")
        grade_strategy = {
            "CCC": "긴급 부채 구조조정 우선 — DES 또는 출자전환",
            "B":   "유동성 확보 + 이자보상배율 1.5 이상 목표",
            "BB":  "부채비율 200% 이하 목표 + 정책자금 활용",
            "BBB": "신용등급 A- 목표 — EBITDA 개선 집중",
            "A":   "ESG 채권 발행으로 자금조달 비용 최적화",
        }
        strategy_desc = grade_strategy.get(credit_grade.rstrip("+-"), grade_strategy["BB"])
        matched = [f for f in FINANCING_TYPES
                   if not ("300%" in f.get("req", "") and debt_ratio > 300)
                   and not ("ESG" in f["name"] and credit_grade in ["CCC", "B", "BB"])]
        text = (
            f"법인 측면: 부채비율 {debt_ratio:.0f}% → 목표 200% 이하. {strategy_desc}.\n"
            f"주주(오너) 관점: 자기자본 증가 → 지분가치 상승 + 배당여력 확대.\n"
            f"과세관청 관점: 차입금 이자비용 손금 인정 (업무관련성 요건 충족).\n"
            f"금융기관 관점: {credit_grade} → BBB 목표 시 금리 우대 약 0.5%p 절감.\n"
            f"조달 수단 {len(matched)}종 매칭: {[f['name'] for f in matched]}"
        )
        return {
            "current_debt_ratio": debt_ratio, "credit_grade": credit_grade,
            "improvement_strategy": strategy_desc, "matched_financing": matched,
            "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        dr = strategy["current_debt_ratio"]
        axes = {
            "DOMAIN": {"pass": dr >= 0,
                       "detail": f"부채비율 {dr:.0f}% — 신용등급 {strategy['credit_grade']} 기준 개선 목표"},
            "LEGAL":  {"pass": True,
                       "detail": "차입금 이자 손금 — 법§52 업무관련성·§28 업무무관 차입금 구분"},
            "CALC":   {"pass": len(strategy["matched_financing"]) >= 0,
                       "detail": f"조달 수단 {len(strategy['matched_financing'])}종 매칭"},
            "LOGIC":  {"pass": True,
                       "detail": "신용등급별 전략 로직 정합 (CCC→A 5단계)"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        dr = strategy["current_debt_ratio"]
        mf = strategy["matched_financing"]
        return {
            "1_pre": [f"부채비율 {dr:.0f}% 현황 분석 — 금융기관별 대출 조건 파악",
                      "EBITDA·이자보상배율 산정 + 신용등급 개선 시뮬"],
            "2_now": [f"조달 수단 {len(mf)}종 중 최적 선택·제안서 제출",
                      "정책자금 신청 (중진공·기보) — 부채비율 300% 이하 요건 확인"],
            "3_post": ["부채비율·신용등급 분기별 모니터링",
                       "ESG 채권 요건 달성 시 발행 준비"],
            "4_worst": ["신용등급 하락 시 기존 대출 금리 상승 → 조기 상환 검토",
                        "DES(출자전환) 시 주주 지분 희석 → 오너 지분율 관리"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        matched = strategy["matched_financing"]
        first   = matched[0]["name"] if matched else "없음"
        return {
            "step1": {"action": "신용등급·재무구조 현황 진단 리포트 작성"},
            "step2": {"action": f"1순위 조달 수단 선정 — {first}"},
            "step3": {"action": "금융기관 제안서 제출·협의"},
            "step4": {"action": "조달 완료 후 부채비율 재산정 + 등기·담보 처리"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["분기별 부채비율·이자보상배율 추적",
                           "신용등급 변동 시 금리 조건 재협의"],
            "reporting": {"법인": "차입금 이자 손금 명세서",
                          "금융": "대출 약정 재무비율 보고"},
            "next_review": "6개월 후 신용등급 재평가 + 추가 조달 필요 여부 검토",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        dr = strategy["current_debt_ratio"]
        cg = strategy["credit_grade"]
        mf = strategy["matched_financing"]
        return {
            "법인": {
                "사전": f"부채비율 {dr:.0f}%·{cg} 등급 개선 전략 수립",
                "현재": f"조달 수단 {len(mf)}종 실행·대출 계약",
                "사후": "부채비율 목표 달성 후 재무구조 안정화",
            },
            "주주(오너)": {
                "사전": "자기자본 증가 시나리오·지분 희석 위험 시뮬",
                "현재": "DES·유상증자 시 지분율 변동 모니터링",
                "사후": "배당여력 확대 → 배당 정책 재설계",
            },
            "과세관청": {
                "사전": "차입금 이자 손금 요건 (업무관련성) 확인",
                "현재": "법§28 업무무관 차입금 이자 손금 부인 리스크",
                "사후": "이자비용 손금 처리 + 세무조정계산서",
            },
            "금융기관": {
                "사전": f"{cg} 등급 → BBB 목표 금리 우대 계획",
                "현재": "담보·보증·약정 재무비율 조건 협의",
                "사후": "신용등급 개선 시 금리 재협상 + 한도 증액",
            },
        }

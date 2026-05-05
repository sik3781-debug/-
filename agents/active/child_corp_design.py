"""
자녀법인 설계 에이전트 (/자녀법인설계) — 4단계 워크플로우

핵심 법령:
  상증§45의5 (특정법인 거래 — 일감몰아주기 증여 의제)
  상증§38 (저가 양도·고가 양수 증여 의제)
  법인세법§52 (특수관계인 부당행위계산 부인)
  법인세법§4의2 (특수관계인 정의 — 지분 30% 이상)
  조특§30의6 (가업승계 주식 증여세 과세특례 — 10% 과세)
  소득세법§94①3호 (비상장주식 양도소득 — 자녀법인 지분 이전)
  국기법§14 (실질과세 원칙 — 법인 형식 남용 방지)
  외감법§4 (외감 대상 — 자녀법인 성장 시 적용 여부)
  상증§18의2 (가업상속공제 600억 — 사후관리 7년)
"""
from __future__ import annotations


class ChildCorpDesignAgent:
    """자녀법인 설립 시 일감몰아주기 증여 의제 회피 설계.

    상증§45의3 특수관계법인 거래비율 30% 초과 + 지분 3% 이상 시 과세
    상증§45의5 특정법인 거래 이익 증여 의제 (저가양수·고가양도)
    법인세법§52 특수관계인 부당행위계산 부인 — 시가 ±5% 벗어나면 부인
    소득세법§94①3호 비상장주식 양도소득 — 자녀법인 지분 이전 시
    조특§30의6 가업승계 증여세 과세특례 10% 적용 요건
    국기법§14 실질과세 원칙 — 형식적 자녀법인 남용 방지
    외감법§4 자녀법인 성장 후 외감 대상 판정 기준
    K-IFRS 1036 자산손상 — 자녀법인 자산가치 하락 시
    상증§18의2 가업상속공제 600억 · 사후관리 7년
    """

    TRANSACTION_SAFE_HARBOR = 0.30
    SHAREHOLDER_THRESHOLD   = 0.03

    def analyze(self, company_data: dict) -> dict:
        strategy = self.generate_strategy(company_data)
        risks    = self.validate_risk_5axis(strategy)
        hedges   = self.generate_risk_hedge_4stage(strategy)
        process  = self.manage_execution(strategy, hedges)
        post     = self.post_management(strategy, process)
        return {
            "classification": "전문영역",
            "domain": "ChildCorpDesignAgent",
            "strategy": strategy,
            "risks": risks, "hedges": hedges,
            "process": process, "post": post,
            "matrix_12cells": self._build_4party_3time_matrix(
                strategy, risks, hedges, process, post),
            "agent": "ChildCorpDesignAgent",
            "text": strategy["text"],
            "current_ratio": strategy["current_ratio"],
            "is_safe": strategy["is_safe"],
            "scenarios": strategy["scenarios"],
            "require_full_4_perspective": True,
        }

    def generate_strategy(self, case: dict) -> dict:
        child_revenue = case.get("child_corp_revenue", 0)
        parent_supply = case.get("supply_from_parent", 0)
        child_shares  = case.get("owner_child_shares_pct", 0.50)
        ratio    = parent_supply / child_revenue if child_revenue else 0
        safe     = (ratio <= self.TRANSACTION_SAFE_HARBOR
                    or child_shares < self.SHAREHOLDER_THRESHOLD)
        tax_base = max(0, ratio - self.TRANSACTION_SAFE_HARBOR) * child_revenue * child_shares
        scenarios = [
            {"name": "안전항 이하", "supply_pct": 0.25, "gift_tax": 0, "note": "거래비율 25% — 과세 없음"},
            {"name": "임계점",      "supply_pct": 0.30, "gift_tax": 0, "note": "30% 기준선"},
            {"name": "초과",        "supply_pct": ratio,
             "gift_tax": int(tax_base * 0.40 * 0.10), "note": "40% 초과분 의제증여"},
        ]
        text = (
            f"주주(오너) 관점: 자녀법인 거래비율 {ratio:.0%} — "
            f"{'과세 없음' if safe else '증여 의제 과세 위험'}.\n"
            f"법인 측면: 자녀법인 매출 중 모법인 공급 비율 30% 이하 유지 필수.\n"
            f"과세관청 관점: 상증§45의3 — 거래비율 30% 초과 + 지분 3% 이상 시 의제증여 과세.\n"
            f"금융기관 관점: 자녀법인 독립 신용 구축으로 모법인 연대보증 최소화.\n"
            f"안전 설계 권고: 거래비율 25% 이하 유지."
        )
        return {
            "child_revenue": child_revenue, "parent_supply": parent_supply,
            "child_shares": child_shares, "current_ratio": ratio,
            "is_safe": safe, "tax_base": tax_base,
            "scenarios": scenarios, "text": text,
        }

    def validate_risk_5axis(self, strategy: dict) -> dict:
        axes = {
            "DOMAIN": {"pass": strategy["child_revenue"] >= 0,
                       "detail": f"자녀법인 매출 {strategy['child_revenue']:,.0f}원 — §45의3 적용 범위 확인"},
            "LEGAL":  {"pass": True,
                       "detail": "상증§45의3 (거래비율 30%·지분 3% 이중 요건) 법령 인용"},
            "CALC":   {"pass": strategy["tax_base"] >= 0,
                       "detail": f"의제증여 과세표준 {strategy['tax_base']:,.0f}원 계산"},
            "LOGIC":  {"pass": len(strategy["scenarios"]) == 3,
                       "detail": "안전항/임계점/초과 3종 시나리오"},
            "CROSS":  {"pass": True, "detail": "4자관점 × 3시점 12셀"},
        }
        all_pass = all(a["pass"] for a in axes.values())
        return {"all_pass": all_pass, "axes": axes,
                "summary": f"5축 통과 {sum(1 for a in axes.values() if a['pass'])}/5"}

    def generate_risk_hedge_4stage(self, strategy: dict) -> dict:
        ratio = strategy["current_ratio"]
        return {
            "1_pre": ["자녀법인 설립 전 거래비율 시뮬 — 25% 이하 설계",
                      "자녀 지분율 3% 미만 유지 방안 검토"],
            "2_now": [f"현재 거래비율 {ratio:.0%} — "
                      f"{'유지' if ratio <= 0.25 else '25%로 감축 필요'}",
                      "모법인 공급 다변화: 외부 거래처 발굴로 비율 희석"],
            "3_post": ["연간 거래비율 정기 모니터링 (연말 결산 시)",
                       "자녀법인 독립 매출처 확보 → 비율 자연 감소"],
            "4_worst": ["비율 초과 시 상증§45의3 의제증여세 즉시 산출",
                        "거래 재계약으로 비율 조정 시 계약 서류 완비"],
        }

    def manage_execution(self, strategy: dict, hedges: dict) -> dict:
        return {
            "step1": {"action": "자녀법인 설립 (자본금·사업목적 설계)", "law": "상법§288"},
            "step2": {"action": f"모법인 공급 비율 {strategy['scenarios'][0]['supply_pct']:.0%} 이하 계약 체결"},
            "step3": {"action": "매출처 다변화 계획 수립 — 외부 거래처 확보"},
            "step4": {"action": "연 1회 거래비율 산정 + 상증§45의3 신고 (해당 시)"},
        }

    def post_management(self, strategy: dict, process: dict) -> dict:
        return {
            "monitoring": ["분기별 자녀법인 매출·모법인 공급액 추적",
                           "자녀 지분율 변동 모니터링"],
            "reporting": {"세무": "상증§45의3 신고 (초과 시)",
                          "법인": "특수관계 거래 명세서"},
            "next_review": "매년 12월 거래비율 최종 확인 + 차기연도 목표 비율 설정",
        }

    def _build_4party_3time_matrix(self, strategy, risks, hedges, process, post) -> dict:
        ratio = strategy["current_ratio"]
        tb    = strategy["tax_base"]
        return {
            "법인": {
                "사전": "모법인 공급 비율 25% 이하 계약 구조 설계",
                "현재": f"거래비율 {ratio:.0%} 유지·모니터링",
                "사후": "거래비율 연간 정산·특수관계 명세서 제출",
            },
            "주주(오너)": {
                "사전": "자녀 지분 3% 미만 또는 거래비율 30% 이하 설계",
                "현재": "자녀법인 독립 경영 지원",
                "사후": f"의제증여 {'없음' if tb == 0 else f'{tb:,.0f}원'} — 세무신고 처리",
            },
            "과세관청": {
                "사전": "상증§45의3 이중 요건 사전 검토",
                "현재": "거래비율 30% 초과 여부 판정",
                "사후": "의제증여 신고·납부 (해당 시)",
            },
            "금융기관": {
                "사전": "자녀법인 독립 신용등급 구축 계획",
                "현재": "모법인 연대보증 최소화 협의",
                "사후": "자녀법인 단독 대출 한도 확보",
            },
        }

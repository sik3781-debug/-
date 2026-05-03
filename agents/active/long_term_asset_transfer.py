"""10년 장기 자산 이전 메타 에이전트 (5·10·20년 단계별 로드맵)"""
from __future__ import annotations
from datetime import date


AGENT_SEQUENCE = [
    "ChildCorpDesignAgent", "SpecialCorpTransactionAgent", "CivilTrustAgent",
    "TreasuryStockStrategyAgent", "ValuationOptimizationAgent",
    "RetainedEarningsManagementAgent", "CorporateBenefitsFundAgent",
    "InheritanceTaxAgent", "SuccessionAgent", "TaxRefundClaimAgent",
]


class LongTermAssetTransferAgent:
    def analyze(self, company_data: dict) -> dict:
        assets   = company_data.get("total_assets", 0)
        ceo_age  = company_data.get("ceo_age", 55)
        yrs_left = max(5, 70 - ceo_age)  # 70세까지 유효 기간
        today    = date.today()

        roadmap = {
            f"즉시~1년 ({today.year})": [
                "자기주식 취득 + 배당 대체 절세 시작",
                "미처분이익잉여금 4방안 검토·실행",
                "가업상속공제 사전 요건 충족 확인",
            ],
            f"2~5년 ({today.year+2}~{today.year+5})": [
                "자녀법인 설립 + 일감몰아주기 30% 이하 설계",
                "민사신탁(타익신탁) 활용 지분 이전",
                "비상장 평가액 최적화 후 단계적 증여",
                "경정청구로 기존 과납세금 환급",
            ],
            f"6~10년 ({today.year+6}~{today.year+10})": [
                "사내복지기금 출연으로 법인세 절감 누적",
                "가업상속공제 최대 600억 한도 내 실행",
                "부동산 감정평가 → 담보 최적화",
            ],
            f"10~20년 ({today.year+10}~{today.year+20})": [
                "가업상속 7년 사후관리 의무 완료",
                "특허 NPV 실현 + IP 이전 완료",
                "자가 진화 시스템으로 자동 갱신",
            ],
        }

        return {
            "agent": "LongTermAssetTransferAgent",
            "text": (
                f"주주(오너) 관점: CEO 나이 {ceo_age}세 → 약 {yrs_left}년 자산 이전 기간 확보.\n"
                f"법인 측면: 총자산 {assets:,.0f}원 단계별 이전 → 가업상속공제 + 조기 절세 효과.\n"
                f"과세관청 관점: 단계별 진행으로 세무조사 리스크 최소화 (갑작스런 대규모 이전 회피).\n"
                f"금융기관 관점: 장기 자산 이전 계획 → 신용등급 안정성 유지.\n"
                f"협력 에이전트 {len(AGENT_SEQUENCE)}개 자동 호출."
            ),
            "roadmap": roadmap,
            "agents_involved": AGENT_SEQUENCE,
            "years_available": yrs_left,
            "require_full_4_perspective": True,
        }

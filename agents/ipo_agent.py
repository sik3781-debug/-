"""
IPOAgent: IPO(기업공개) 준비 전담 에이전트

근거 법령·제도:
  - 자본시장과 금융투자업에 관한 법률 (자본시장법)
  - 유가증권시장·코스닥시장·코넥스시장 상장규정
  - 조세특례제한법 제14조 (벤처기업 주식매수선택권 비과세)
  - 중소기업창업 지원법 / 벤처기업육성에 관한 특별조치법

주요 기능:
  - IPO 적격성 자가진단 (재무·지배구조·법규준수 3축)
  - 코스닥 vs. 코넥스 상장 요건 비교 및 최적 시장 선택
  - 기업가치 평가 (PER·EV/EBITDA·DCF 복합)
  - 상장 전 지배구조 정비 (이사회·감사위원회·사외이사)
  - 상장 비용 추정 및 공모 규모 최적화
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 IPO 준비 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 코스닥·코넥스·유가증권 상장 요건 정확 적용\n"
    "- IPO 전 재무·지배구조·법무 준비 사항 체크리스트\n"
    "- 기업가치 평가: PER·EV/EBITDA·DCF 복합 밸류에이션\n"
    "- 공모 규모 산정: 오너 희석 최소화 + 자금조달 극대화 균형\n"
    "- 상장 후 Lock-up 해제 전략 및 오너 보유지분 처분 계획\n\n"
    "【분석 관점】\n"
    "- 법인: 상장 비용 손금처리 / 주식보상비용 회계처리\n"
    "- 오너: 지분희석 최소화 / 상장 후 주식 가치 극대화\n"
    "- 과세관청: 스톡옵션 과세 / 주식 양도소득세 계획\n"
    "- 금융기관: 상장 후 신용등급 상승 효과 / 공모 주간사 선정\n\n"
    "【목표】\n"
    "IPO 준비 3~5년 로드맵 수립부터 상장 후 유통시장 전략까지\n"
    "오너가 최대 주주 지위를 유지하며 기업 가치를 극대화한다."
)

# 코스닥 상장 최소 요건 (2026년 기준)
KOSDAQ_REQUIREMENTS = {
    "일반기업": {
        "자기자본": 300_000_000,          # 3억 이상
        "시가총액": 9_000_000_000,         # 90억 이상 (예상)
        "당기순이익_또는_영업이익": True,   # 최근 사업연도 흑자
        "감사의견": "적정",
        "소액주주": "25% 이상",
    },
    "기술성장기업": {
        "자기자본": 100_000_000,           # 1억 이상 (기술평가 A등급 이상)
        "시가총액": 9_000_000_000,
        "당기순이익_또는_영업이익": False,  # 흑자 요건 면제
        "감사의견": "적정",
        "소액주주": "25% 이상",
    },
}

# 코넥스 상장 요건
KONEX_REQUIREMENTS = {
    "자기자본": 50_000_000,               # 5천만 원 이상
    "지정자문인": "필수",
    "당기순이익_요건": "없음",
}


class IPOAgent(BaseAgent):
    name = "IPOAgent"
    role = "IPO 준비 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "diagnose_ipo_readiness",
                "description": (
                    "IPO 적격성 자가진단.\n"
                    "재무·지배구조·법규준수 3축을 평가하여\n"
                    "상장 준비 수준과 선행 과제를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "equity": {"type": "number", "description": "자기자본 (원)"},
                        "net_income": {"type": "number", "description": "최근 당기순이익 (원)"},
                        "revenue_3y": {
                            "type": "array",
                            "description": "최근 3년 매출 [3년전, 2년전, 직전] (원)",
                            "items": {"type": "number"},
                        },
                        "has_internal_audit": {"type": "boolean", "description": "내부감사 조직 여부"},
                        "has_outside_director": {"type": "boolean", "description": "사외이사 선임 여부"},
                        "has_cfo": {"type": "boolean", "description": "CFO(재무책임자) 존재 여부"},
                        "audit_opinion": {
                            "type": "string",
                            "description": "최근 감사 의견",
                            "enum": ["적정", "한정", "부적정", "의견거절"],
                        },
                        "target_market": {
                            "type": "string",
                            "description": "목표 상장 시장",
                            "enum": ["코스닥", "코넥스", "유가증권"],
                        },
                    },
                    "required": ["equity", "net_income", "audit_opinion", "target_market"],
                },
            },
            {
                "name": "estimate_ipo_valuation",
                "description": (
                    "IPO 기업가치 추정 (PER·EV/EBITDA 복합 방법론).\n"
                    "업종 평균 배수와 재무 데이터를 결합하여\n"
                    "희망 공모가 범위와 공모 규모를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "net_income": {"type": "number", "description": "최근 당기순이익 (원)"},
                        "ebitda": {"type": "number", "description": "EBITDA (원)"},
                        "total_shares": {"type": "integer", "description": "발행주식 총수 (주)"},
                        "industry": {"type": "string", "description": "업종"},
                        "new_share_ratio": {
                            "type": "number",
                            "description": "신주 발행 비율 (공모 시 신주 비중, 0~0.5)",
                        },
                    },
                    "required": ["net_income", "ebitda", "total_shares", "industry"],
                },
            },
            {
                "name": "plan_ipo_roadmap",
                "description": (
                    "IPO 준비 3개년 로드맵 작성.\n"
                    "재무·법무·지배구조·IR 영역별 월별 액션 플랜과\n"
                    "상장 비용 추정을 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_market": {
                            "type": "string",
                            "description": "목표 시장",
                            "enum": ["코스닥", "코넥스", "유가증권"],
                        },
                        "current_revenue": {"type": "number", "description": "현재 연 매출액 (원)"},
                        "target_ipo_year": {"type": "integer", "description": "목표 상장 연도 (예: 2028)"},
                    },
                    "required": ["target_market", "current_revenue", "target_ipo_year"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "diagnose_ipo_readiness":
            return self._diagnose_ipo_readiness(**tool_input)
        if tool_name == "estimate_ipo_valuation":
            return self._estimate_ipo_valuation(**tool_input)
        if tool_name == "plan_ipo_roadmap":
            return self._plan_ipo_roadmap(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _diagnose_ipo_readiness(
        self,
        equity: float,
        net_income: float,
        audit_opinion: str,
        target_market: str,
        revenue_3y: list[float] | None = None,
        has_internal_audit: bool = False,
        has_outside_director: bool = False,
        has_cfo: bool = False,
    ) -> dict:
        issues = []
        score = 0

        req = KOSDAQ_REQUIREMENTS["일반기업"] if target_market == "코스닥" else KONEX_REQUIREMENTS

        # 자기자본
        min_equity = req.get("자기자본", 0)
        if equity >= min_equity:
            score += 25
        else:
            issues.append(f"자기자본 {equity/100_000_000:.1f}억 — 기준 {min_equity/100_000_000:.1f}억 미달")

        # 흑자
        if net_income > 0:
            score += 20
        elif target_market != "코스닥" or not req.get("당기순이익_또는_영업이익"):
            issues.append("최근 사업연도 적자 — 기술성장기업 트랙 검토 필요")

        # 감사의견
        if audit_opinion == "적정":
            score += 20
        else:
            issues.append(f"감사의견 {audit_opinion} — 적정으로 개선 필수")

        # 매출 성장성
        if revenue_3y and len(revenue_3y) == 3 and revenue_3y[0] > 0:
            cagr = (revenue_3y[2] / revenue_3y[0]) ** 0.5 - 1
            if cagr >= 0.15:
                score += 15
            elif cagr >= 0.05:
                score += 8

        # 지배구조
        if has_cfo:
            score += 10
        else:
            issues.append("CFO 부재 — 재무 전문 임원 선임 필요")
        if has_outside_director:
            score += 5
        if has_internal_audit:
            score += 5

        verdict = (
            "🟢 즉시 주관사 선정 가능" if score >= 75
            else "🟡 1~2년 준비 필요" if score >= 50
            else "🔴 2~3년 장기 준비 필요"
        )

        return {
            "목표시장": target_market,
            "준비_점수": f"{score}/100",
            "진단결과": verdict,
            "미비_항목": issues,
            "즉시_조치": issues[:2] if issues else ["현 수준 유지 + 주관사 접촉 시작"],
        }

    def _estimate_ipo_valuation(
        self,
        net_income: float,
        ebitda: float,
        total_shares: int,
        industry: str,
        new_share_ratio: float = 0.20,
    ) -> dict:
        # 업종 평균 배수 (코스닥 2024년 기준)
        per_multiples = {"제조업": 15, "정보통신업": 25, "서비스업": 18, "기타": 15}
        ev_multiples = {"제조업": 8, "정보통신업": 15, "서비스업": 10, "기타": 8}

        per = per_multiples.get(industry, 15)
        ev_mult = ev_multiples.get(industry, 8)

        val_per = net_income * per
        val_ev = ebitda * ev_mult
        avg_val = (val_per + val_ev) / 2

        # 공모가 범위
        price_low = avg_val * 0.85 / total_shares
        price_high = avg_val * 1.15 / total_shares
        new_shares = int(total_shares * new_share_ratio / (1 - new_share_ratio))
        proceeds = new_shares * (price_low + price_high) / 2

        return {
            "PER_기반_가치": round(val_per),
            "EV/EBITDA_기반_가치": round(val_ev),
            "평균_기업가치": round(avg_val),
            "현재_주식수": total_shares,
            "신주_발행_예정수": new_shares,
            "공모가_범위": f"{price_low:,.0f}원 ~ {price_high:,.0f}원",
            "예상_공모_조달금액": round(proceeds),
            "오너_지분_희석률": f"{new_share_ratio*100:.0f}%",
            "적용_배수": {"PER": per, "EV/EBITDA": ev_mult},
            "주의": "공모가는 수요예측(Book-Building) 결과에 따라 조정",
        }

    def _plan_ipo_roadmap(
        self,
        target_market: str,
        current_revenue: float,
        target_ipo_year: int,
    ) -> dict:
        import datetime
        current_year = datetime.date.today().year
        years_left = target_ipo_year - current_year

        phases = [
            {
                "단계": "D-3년 (기초 정비)",
                "과제": ["외부감사인 지정·교체", "CFO 채용", "결산 정확성 제고", "특수관계인 거래 정비"],
                "비용": "1,000~2,000만 원",
            },
            {
                "단계": "D-2년 (구조 정비)",
                "과제": ["사외이사 선임", "감사위원회 구성", "스톡옵션 설계", "IR 자료 초안"],
                "비용": "3,000~5,000만 원",
            },
            {
                "단계": "D-1년 (주관사 선정)",
                "과제": ["주관증권사 선정", "실사(Due Diligence)", "증권신고서 작성", "IR 로드쇼"],
                "비용": "5~15억 원 (주관사 수수료 포함)",
            },
            {
                "단계": "상장 연도",
                "과제": ["수요예측", "공모 청약", "상장 심사", "매매 개시"],
                "비용": "공모금액의 3~5% (인수·등록 수수료)",
            },
        ]

        # 필요 준비 기간 조정
        if years_left < 2:
            phases = phases[-2:]
            note = "⚠️ 준비 기간 부족 — 목표 상장 연도 1~2년 연기 검토 권장"
        else:
            note = f"목표 {target_ipo_year}년 상장 기준 {years_left}년 준비 기간 확보"

        return {
            "목표시장": target_market,
            "목표상장연도": target_ipo_year,
            "현재매출": round(current_revenue),
            "준비기간_평가": note,
            "단계별_로드맵": phases,
            "총_비용_추정": "10~20억 원 (시장·공모규모에 따라 상이)",
            "세제혜택": "벤처기업 인증 시 스톡옵션 비과세 (조특법 §14)",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        equity = company_data.get("total_equity", 0)
        net_income = company_data.get("net_income", 0)
        revenue = company_data.get("revenue", 0)

        lines = ["[IPO 준비 분석 결과]"]
        if equity:
            diag = self._diagnose_ipo_readiness(equity, net_income, "적정", "코스닥")
            lines.append(f"\n▶ IPO 적격성 진단: {diag['진단결과']}")
            lines.append(f"  준비 점수: {diag['준비_점수']}")
            if diag["미비_항목"]:
                lines.append(f"  미비 사항: {' / '.join(diag['미비_항목'][:2])}")
        else:
            lines.append("  자기자본 데이터 부족 — total_equity 입력 필요")
        return "\n".join(lines)

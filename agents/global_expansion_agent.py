"""
GlobalExpansionAgent: 해외진출 전략 전담 에이전트

근거 법령·제도:
  - 대외무역법 / 외국환거래법 제18조 (해외직접투자 신고)
  - 조세특례제한법 제22조 (해외자원개발투자 세액공제)
  - 수출입은행법 (수출금융·보증)
  - KOTRA 수출바우처 / 중진공 글로벌 강소기업 지원
  - FTA 원산지 규정 및 협정관세 적용

주요 기능:
  - 수출 타당성 진단 (시장·재무·운영 리스크 3축)
  - FTA 활용 관세 절감 효과 계산
  - 해외직접투자(FDI) 법인 설립 방식 비교 (자회사·지사·연락사무소)
  - 수출금융·보증 활용 계획 (수출신용보증·D/A·L/C 방식별 비교)
  - KOTRA·중진공 해외진출 지원사업 매칭
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 해외진출 전략 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 수출 타당성 진단: 시장성·재무 체력·운영 준비도 3축 평가\n"
    "- FTA 협정관세 활용: 원산지 충족 여부 판정 및 관세 절감 계산\n"
    "- 해외직접투자(FDI): 자회사·지사·연락사무소 방식별 세무·법무 비교\n"
    "- 수출금융: 수출신용보증(KSURE)·수출팩토링·D/A·L/C 방식별 리스크 비교\n"
    "- 정부 지원사업: KOTRA 수출바우처 / 중진공 글로벌강소기업 / 수출바우처\n\n"
    "【분석 관점】\n"
    "- 법인: 환율 리스크 / 해외 세금 이중과세 / 이전가격 과세 리스크\n"
    "- 오너: 해외법인 지분 구조 및 배당 환류 전략\n"
    "- 과세관청: 해외직접투자 신고 적정성 / 이전가격 정상가격 준수\n"
    "- 금융기관: 수출채권 담보 활용 / 환위험 헷지\n\n"
    "【목표】\n"
    "중소기업이 해외 진출 시 세무·법무·금융 리스크를 사전에 제거하고,\n"
    "정부 지원을 최대한 활용하는 실행 가능한 글로벌 전략을 제공한다."
)

# FTA 주요 협정세율 (HS 6단위별 상이 — 대표 예시)
FTA_PARTNERS = {
    "미국": {"일반세율": 0.025, "FTA세율": 0.00, "발효": "2012년"},
    "EU":   {"일반세율": 0.040, "FTA세율": 0.00, "발효": "2011년"},
    "중국": {"일반세율": 0.080, "FTA세율": 0.015, "발효": "2015년"},
    "ASEAN": {"일반세율": 0.050, "FTA세율": 0.005, "발효": "2007년"},
    "일본": {"일반세율": 0.035, "FTA세율": 0.00, "발효": "2024년(RCEP)"},
    "베트남": {"일반세율": 0.120, "FTA세율": 0.00, "발효": "2015년"},
    "인도": {"일반세율": 0.100, "FTA세율": 0.010, "발효": "2010년"},
}

# 해외직접투자 방식별 특성
FDI_MODES = {
    "자회사(현지법인)": {
        "설립비용": "高",
        "세무독립성": "현지 법인세 별도 납부",
        "이익환류": "배당 또는 용역료",
        "본사책임": "유한책임",
        "권장": "안정적 장기 사업",
    },
    "지사": {
        "설립비용": "中",
        "세무독립성": "본사 종속 과세",
        "이익환류": "본사 직접 귀속",
        "본사책임": "무한책임",
        "권장": "단기 영업·서비스",
    },
    "연락사무소": {
        "설립비용": "低",
        "세무독립성": "소득 없음 (영업활동 불가)",
        "이익환류": "해당없음",
        "본사책임": "없음",
        "권장": "시장조사·광고",
    },
}


class GlobalExpansionAgent(BaseAgent):
    name = "GlobalExpansionAgent"
    role = "해외진출 전략 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "diagnose_export_readiness",
                "description": (
                    "수출 타당성 3축 진단.\n"
                    "시장성·재무 체력·운영 준비도를 점수화하여\n"
                    "수출 진행 여부와 선행 과제를 판단한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "revenue": {"type": "number", "description": "연 매출액 (원)"},
                        "export_revenue": {"type": "number", "description": "현재 수출 매출액 (원, 없으면 0)"},
                        "operating_margin": {"type": "number", "description": "영업이익률 (0~1)"},
                        "debt_ratio": {"type": "number", "description": "부채비율 (0~10)"},
                        "has_english_catalog": {"type": "boolean", "description": "영문 카탈로그 보유 여부"},
                        "has_certificate": {"type": "boolean", "description": "해외 인증 보유 여부 (CE·UL·FDA 등)"},
                        "target_country": {"type": "string", "description": "목표 진출 국가"},
                    },
                    "required": ["revenue", "operating_margin", "debt_ratio", "target_country"],
                },
            },
            {
                "name": "calc_fta_benefit",
                "description": (
                    "FTA 협정관세 적용 시 관세 절감액 계산.\n"
                    "수출 단가·물량·일반세율·FTA세율을 기반으로 연간 절감 효과를 산출한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "export_amount": {"type": "number", "description": "연간 수출액 (원)"},
                        "target_country": {
                            "type": "string",
                            "description": "수출 대상국",
                            "enum": list(FTA_PARTNERS.keys()),
                        },
                        "hs_code": {"type": "string", "description": "HS 코드 (6단위, 선택)"},
                        "origin_ratio": {
                            "type": "number",
                            "description": "국산 원재료 비율 (0~1, 원산지 충족용)",
                        },
                    },
                    "required": ["export_amount", "target_country"],
                },
            },
            {
                "name": "compare_fdi_modes",
                "description": (
                    "해외직접투자 방식별 비교분석.\n"
                    "자회사·지사·연락사무소의 설립비용·세무·책임 구조를 비교하고\n"
                    "최적 방식을 추천한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_country": {"type": "string", "description": "진출 대상국"},
                        "annual_revenue_plan": {"type": "number", "description": "해외 예상 연매출 (원)"},
                        "business_type": {
                            "type": "string",
                            "description": "사업 형태",
                            "enum": ["제조", "판매", "서비스", "시장조사"],
                        },
                        "planned_years": {"type": "integer", "description": "운영 계획 기간 (년)"},
                    },
                    "required": ["target_country", "annual_revenue_plan", "business_type"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "diagnose_export_readiness":
            return self._diagnose_export_readiness(**tool_input)
        if tool_name == "calc_fta_benefit":
            return self._calc_fta_benefit(**tool_input)
        if tool_name == "compare_fdi_modes":
            return self._compare_fdi_modes(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _diagnose_export_readiness(
        self,
        revenue: float,
        operating_margin: float,
        debt_ratio: float,
        target_country: str,
        export_revenue: float = 0,
        has_english_catalog: bool = False,
        has_certificate: bool = False,
    ) -> dict:
        scores = {}
        # 시장성 (0~40점)
        export_ratio = export_revenue / revenue if revenue else 0
        market_score = min(40, int(export_ratio * 100) + (20 if has_certificate else 0))
        scores["시장성"] = market_score

        # 재무체력 (0~40점)
        fin_score = 0
        if operating_margin >= 0.10:
            fin_score += 20
        elif operating_margin >= 0.05:
            fin_score += 10
        if debt_ratio <= 1.0:
            fin_score += 20
        elif debt_ratio <= 2.0:
            fin_score += 10
        scores["재무체력"] = fin_score

        # 운영준비도 (0~20점)
        ops_score = 0
        if has_english_catalog:
            ops_score += 10
        if has_certificate:
            ops_score += 10
        scores["운영준비도"] = ops_score

        total = sum(scores.values())
        if total >= 70:
            verdict = "🟢 즉시 수출 추진 가능"
        elif total >= 45:
            verdict = "🟡 선행 과제 해결 후 수출 추진"
        else:
            verdict = "🔴 내실 강화 우선 — 수출 12개월 후 재진단"

        prior_tasks = []
        if not has_english_catalog:
            prior_tasks.append("영문 카탈로그·홈페이지 제작 (KOTRA 수출바우처 활용)")
        if not has_certificate:
            prior_tasks.append(f"{target_country} 필수 인증 취득 (CE·UL·FDA 등)")
        if debt_ratio > 2.0:
            prior_tasks.append("부채비율 200% 이하 개선 후 수출금융 활용")

        return {
            "목표국가": target_country,
            "항목별_점수": scores,
            "총점": f"{total}/100",
            "진단결과": verdict,
            "선행과제": prior_tasks,
            "정부지원": "KOTRA 수출바우처 / 중진공 글로벌강소기업 / 수은 수출금융",
        }

    def _calc_fta_benefit(
        self,
        export_amount: float,
        target_country: str,
        hs_code: str = "",
        origin_ratio: float = 0.6,
    ) -> dict:
        fta = FTA_PARTNERS.get(target_country, {"일반세율": 0.05, "FTA세율": 0.02, "발효": "미체결"})
        general_duty = export_amount * fta["일반세율"]
        fta_duty = export_amount * fta["FTA세율"]
        saving = general_duty - fta_duty

        origin_ok = origin_ratio >= 0.40  # 일반 원산지 기준 40% 이상 (협정별 상이)

        return {
            "수출대상국": target_country,
            "FTA_발효": fta["발효"],
            "연간_수출액": round(export_amount),
            "일반관세율": f"{fta['일반세율']*100:.1f}%",
            "FTA_협정세율": f"{fta['FTA세율']*100:.1f}%",
            "일반관세액": round(general_duty),
            "FTA적용_관세액": round(fta_duty),
            "연간_절감액": round(saving),
            "원산지_충족여부": "충족" if origin_ok else "미충족 (원산지 비율 상향 검토)",
            "국산원재료비율": f"{origin_ratio*100:.0f}%",
            "주의사항": "HS 코드별 원산지 기준 상이 — 정확한 판정은 관세사 확인 필수",
        }

    def _compare_fdi_modes(
        self,
        target_country: str,
        annual_revenue_plan: float,
        business_type: str,
        planned_years: int = 5,
    ) -> dict:
        modes = []
        for mode, info in FDI_MODES.items():
            # 권장 여부
            recommended = False
            if business_type in ("제조", "판매") and "장기" in info["권장"]:
                recommended = mode == "자회사(현지법인)"
            elif business_type == "서비스":
                recommended = mode == "지사"
            elif business_type == "시장조사":
                recommended = mode == "연락사무소"

            modes.append({
                "방식": mode,
                "설립비용": info["설립비용"],
                "세무구조": info["세무독립성"],
                "이익환류": info["이익환류"],
                "본사책임": info["본사책임"],
                "권장상황": info["권장"],
                "추천": "✅ 추천" if recommended else "",
            })

        return {
            "진출국가": target_country,
            "사업형태": business_type,
            "예상연매출": round(annual_revenue_plan),
            "운영기간": f"{planned_years}년",
            "방식별_비교": modes,
            "법령근거": "외국환거래법 §18 (해외직접투자 신고)",
            "주의사항": "해외직접투자 신고: 외국환거래법에 따라 건당 미화 5만 달러 초과 시 한국은행 신고 의무",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        revenue = company_data.get("revenue", 0)
        op_margin = company_data.get("operating_margin", 0.05)
        debt_ratio = company_data.get("debt_ratio", 1.5)
        export_rev = company_data.get("export_revenue", 0)

        lines = ["[해외진출 전략 분석 결과]"]
        if revenue:
            diag = self._diagnose_export_readiness(revenue, op_margin, debt_ratio, "미국", export_rev)
            lines.append(f"\n▶ 수출 타당성 진단: {diag['진단결과']}")
            lines.append(f"  총점: {diag['총점']} / 항목: {diag['항목별_점수']}")
            if diag["선행과제"]:
                lines.append(f"  선행과제: {' / '.join(diag['선행과제'])}")
        else:
            lines.append("  매출 데이터 부족 — revenue 입력 필요")
        return "\n".join(lines)

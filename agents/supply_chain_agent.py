"""
SupplyChainAgent: 공급망 관리 전담 에이전트

근거 법령 및 기준:
  - 하도급거래 공정화에 관한 법률 (하도급법)
  - 대·중소기업 상생협력 촉진에 관한 법률
  - 공급망 실사법 (EU CSDDD / 독일 LkSG 준수 요건)
  - 중소기업 협동조합법 (공동구매·공동마케팅)
  - ISO 28000 (공급망 보안 관리시스템)

주요 기능:
  - 공급망 리스크 스캔 (단일 공급처 의존도·지역 집중 리스크)
  - 협력사 평가 체계 설계 (품질·납기·재무 안정성)
  - 납기 지연 리스크 정량화 및 대응 시나리오
  - 재고 버퍼·복수 공급처 전략 수립
  - ESG 공급망 실사 요건 진단 (EU CSDDD)
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 공급망 관리(SCM) 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 공급망 취약점 분석: 단일 공급처·지역 집중 리스크\n"
    "- 협력사 평가: 품질(QCD) + 재무 안정성 + ESG 준수\n"
    "- 납기 관리: 리드타임 분석·안전재고·대체 공급처 확보\n"
    "- 원가 최적화: 공동구매·장기 계약·물량 약정 협상\n"
    "- EU CSDDD / 독일 공급망실사법(LkSG) 준수 체계 구축\n\n"
    "【분석 관점】\n"
    "- 법인: 납기 차질 → 위약금·매출 손실 차단\n"
    "- 오너: 핵심 원자재 공급 안정성 / 원가 경쟁력\n"
    "- 과세관청: 협력사 거래 가격 시가 적정성\n"
    "- 금융기관: 공급망 리스크 = 매출·담보 안정성에 영향\n\n"
    "【목표】\n"
    "단절 없는 공급망을 구축하여 납기 리스크를 최소화하고\n"
    "원가 경쟁력을 확보한다."
)

# 공급망 리스크 등급 기준
RISK_CRITERIA = {
    "단일_공급처_비율": {"low": 0.3, "medium": 0.5, "high": 0.7},
    "리드타임_변동성": {"low": 0.1, "medium": 0.2, "high": 0.3},
    "협력사_재무_부실": {"low": 0.1, "medium": 0.2, "high": 0.3},
}


class SupplyChainAgent(BaseAgent):
    name = "SupplyChainAgent"
    role = "공급망 관리 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "scan_supply_chain_risks",
                "description": (
                    "공급망 리스크 종합 스캔.\n"
                    "공급 집중도·리드타임 변동성·지역 리스크를\n"
                    "정량화하여 취약 구간과 개선 우선순위를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "top_supplier_revenue_ratio": {
                            "type": "number",
                            "description": "1위 공급처 구매 비중 (0~1, 예: 0.6 = 60%)",
                        },
                        "single_source_items": {
                            "type": "integer",
                            "description": "단일 공급처 품목 수 (개)",
                        },
                        "avg_lead_time_days": {"type": "integer", "description": "평균 조달 리드타임 (일)"},
                        "lead_time_variance_days": {
                            "type": "integer",
                            "description": "리드타임 변동 범위 (일, 표준편차 근사)",
                        },
                        "overseas_ratio": {
                            "type": "number",
                            "description": "해외 조달 비중 (0~1)",
                        },
                        "annual_purchase": {"type": "number", "description": "연간 구매액 (원)"},
                    },
                    "required": [
                        "top_supplier_revenue_ratio",
                        "single_source_items",
                        "avg_lead_time_days",
                        "annual_purchase",
                    ],
                },
            },
            {
                "name": "design_supplier_evaluation",
                "description": (
                    "협력사 평가 체계 설계.\n"
                    "품질·납기·원가·재무안정·ESG 5개 축으로\n"
                    "협력사 등급화 방법론과 평가 기준을 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "supplier_count": {"type": "integer", "description": "협력사 수 (개)"},
                        "key_categories": {
                            "type": "array",
                            "description": "주요 구매 품목·카테고리",
                            "items": {"type": "string"},
                        },
                        "esg_requirement": {
                            "type": "boolean",
                            "description": "ESG 실사 요건 적용 여부 (EU 수출 기업 등)",
                        },
                        "annual_purchase": {"type": "number", "description": "연간 구매액 (원)"},
                    },
                    "required": ["supplier_count", "annual_purchase"],
                },
            },
            {
                "name": "simulate_disruption_impact",
                "description": (
                    "공급 차질 발생 시 매출 손실·위약금 시뮬레이션.\n"
                    "핵심 품목 공급 중단 기간별 손실액과\n"
                    "대응 시나리오별 비용을 비교한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "annual_revenue": {"type": "number", "description": "연 매출액 (원)"},
                        "disruption_item_revenue_ratio": {
                            "type": "number",
                            "description": "공급 차질 품목의 매출 기여 비중 (0~1)",
                        },
                        "disruption_days": {"type": "integer", "description": "공급 차질 예상 기간 (일)"},
                        "penalty_rate": {
                            "type": "number",
                            "description": "납기 지연 위약금율 (일 기준, 예: 0.001)",
                        },
                        "safety_stock_days": {
                            "type": "integer",
                            "description": "현재 보유 안전재고 (일치 분량)",
                        },
                    },
                    "required": ["annual_revenue", "disruption_item_revenue_ratio", "disruption_days"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "scan_supply_chain_risks":
            return self._scan_supply_chain_risks(**tool_input)
        if tool_name == "design_supplier_evaluation":
            return self._design_supplier_evaluation(**tool_input)
        if tool_name == "simulate_disruption_impact":
            return self._simulate_disruption_impact(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _scan_supply_chain_risks(
        self,
        top_supplier_revenue_ratio: float,
        single_source_items: int,
        avg_lead_time_days: int,
        annual_purchase: float,
        lead_time_variance_days: int = 5,
        overseas_ratio: float = 0.0,
    ) -> dict:
        risks = []

        if top_supplier_revenue_ratio >= 0.5:
            risks.append({
                "리스크": f"1위 공급처 집중도 {top_supplier_revenue_ratio*100:.0f}% — 단절 시 전체 생산 차질",
                "등급": "🔴 고위험" if top_supplier_revenue_ratio >= 0.7 else "🟡 주의",
                "개선": "대체 공급처 2개소 이상 사전 등록·인증",
            })

        if single_source_items >= 5:
            risks.append({
                "리스크": f"단일 공급처 품목 {single_source_items}개 — 공급 중단 취약",
                "등급": "🔴 고위험",
                "개선": "단일 품목별 대체 공급처 발굴 / 표준화 설계",
            })

        variance_ratio = lead_time_variance_days / max(avg_lead_time_days, 1)
        if variance_ratio >= 0.2:
            risks.append({
                "리스크": f"리드타임 변동 ±{lead_time_variance_days}일 — 생산 일정 불안정",
                "등급": "🟡 주의",
                "개선": f"안전재고 {lead_time_variance_days * 2}일치 확보 / 납기 모니터링 강화",
            })

        if overseas_ratio >= 0.4:
            risks.append({
                "리스크": f"해외 조달 비중 {overseas_ratio*100:.0f}% — 환율·물류비·관세 변동 노출",
                "등급": "🟡 주의",
                "개선": "국내 대체 공급처 개발 / 환율 헤지 검토",
            })

        overall = "🔴 즉시 개선" if any(r["등급"] == "🔴 고위험" for r in risks) else "🟡 점진적 개선" if risks else "🟢 양호"

        return {
            "연간_구매액": round(annual_purchase),
            "1위_공급처_비중": f"{top_supplier_revenue_ratio*100:.0f}%",
            "단일공급_품목수": single_source_items,
            "평균_리드타임": f"{avg_lead_time_days}일",
            "종합_위험등급": overall,
            "리스크_상세": risks,
            "즉시_조치": risks[0]["개선"] if risks else "현행 유지 — 분기별 공급처 성과 리뷰",
        }

    def _design_supplier_evaluation(
        self,
        supplier_count: int,
        annual_purchase: float,
        key_categories: list[str] | None = None,
        esg_requirement: bool = False,
    ) -> dict:
        key_categories = key_categories or ["핵심 원자재", "포장재", "외주 가공"]

        criteria = [
            {"평가축": "품질(Q)", "가중치": 30, "지표": "불량률·클레임·인증 보유"},
            {"평가축": "납기(D)", "가중치": 25, "지표": "납기 준수율·리드타임 안정성"},
            {"평가축": "원가(C)", "가중치": 20, "지표": "가격 경쟁력·가격 투명성"},
            {"평가축": "재무 안정성", "가중치": 15, "지표": "부채비율·유동비율·신용등급"},
        ]

        if esg_requirement:
            criteria.append({
                "평가축": "ESG 실사",
                "가중치": 10,
                "지표": "환경·인권·노동 기준 준수 (EU CSDDD)",
            })
        else:
            criteria[-1]["가중치"] = 10
            criteria.append({"평가축": "파트너십", "가중치": 10, "지표": "협력도·소통·개선 의지"})

        tiers = [
            {"등급": "S등급", "기준": "90점 이상", "혜택": "우선 발주·장기계약·공동개발"},
            {"등급": "A등급", "기준": "75~89점", "혜택": "일반 발주 유지"},
            {"등급": "B등급", "기준": "60~74점", "혜택": "개선 계획 요구·발주 축소"},
            {"등급": "C등급(퇴출)", "기준": "60점 미만", "혜택": "대체 공급처 전환"},
        ]

        return {
            "협력사_수": supplier_count,
            "연간_구매액": round(annual_purchase),
            "주요_카테고리": key_categories,
            "ESG_실사": "적용" if esg_requirement else "미적용",
            "평가_기준": criteria,
            "협력사_등급체계": tiers,
            "평가_주기": "연 1회 정기 + 반기 모니터링",
            "법령근거": "대·중소기업 상생협력법 §24 (수탁·위탁거래 실태조사)",
        }

    def _simulate_disruption_impact(
        self,
        annual_revenue: float,
        disruption_item_revenue_ratio: float,
        disruption_days: int,
        penalty_rate: float = 0.001,
        safety_stock_days: int = 7,
    ) -> dict:
        daily_revenue = annual_revenue / 365
        affected_daily = daily_revenue * disruption_item_revenue_ratio

        # 안전재고로 버틸 수 있는 기간
        buffer_days = min(safety_stock_days, disruption_days)
        actual_disruption_days = max(0, disruption_days - buffer_days)

        revenue_loss = affected_daily * actual_disruption_days
        penalty = annual_revenue * disruption_item_revenue_ratio * penalty_rate * actual_disruption_days
        total_impact = revenue_loss + penalty

        # 대응 시나리오
        scenarios = [
            {
                "시나리오": "현재 안전재고 유지",
                "버퍼_일수": buffer_days,
                "매출_손실": round(revenue_loss),
                "위약금": round(penalty),
                "총_손실": round(total_impact),
            },
            {
                "시나리오": "안전재고 2배 확보 (재고비용 증가)",
                "버퍼_일수": min(safety_stock_days * 2, disruption_days),
                "매출_손실": round(affected_daily * max(0, disruption_days - safety_stock_days * 2)),
                "추가_재고비용": round(affected_daily * safety_stock_days * 0.3),
                "총_손실": round(affected_daily * max(0, disruption_days - safety_stock_days * 2) + affected_daily * safety_stock_days * 0.3),
            },
            {
                "시나리오": "대체 공급처 사전 등록",
                "전환_소요일": 14,
                "전환_비용": round(annual_revenue * 0.005),
                "매출_손실": round(affected_daily * min(14, disruption_days)),
                "총_손실": round(affected_daily * min(14, disruption_days) + annual_revenue * 0.005),
            },
        ]

        best = min(scenarios, key=lambda x: x["총_손실"])

        return {
            "연간_매출": round(annual_revenue),
            "차질_품목_매출비중": f"{disruption_item_revenue_ratio*100:.0f}%",
            "공급_차질_기간": f"{disruption_days}일",
            "현_안전재고": f"{safety_stock_days}일치",
            "시나리오별_영향": scenarios,
            "최적_대응안": best["시나리오"],
            "권고": "복수 공급처 확보 + 안전재고 최적화가 가장 효과적인 리스크 헷지",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        rev = company_data.get("revenue", 0)
        purchase = company_data.get("annual_purchase", rev * 0.5)
        top_ratio = company_data.get("top_supplier_ratio", 0.5)
        lines = ["[공급망 리스크 분석 결과]"]
        result = self._scan_supply_chain_risks(
            top_supplier_revenue_ratio=top_ratio,
            single_source_items=company_data.get("single_source_items", 3),
            avg_lead_time_days=company_data.get("avg_lead_time_days", 14),
            annual_purchase=purchase,
        )
        lines.append(f"\n▶ 종합 위험등급: {result['종합_위험등급']}")
        lines.append(f"  1위 공급처 비중: {result['1위_공급처_비중']} / 리스크 {len(result['리스크_상세'])}건")
        return "\n".join(lines)

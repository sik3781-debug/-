"""
ESGRiskAgent: E·S·G 항목별 리스크 진단 전문 에이전트
"""
from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 ESG 리스크 진단 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- E(환경): 탄소배출·폐수·폐기물 법규 준수, EU CBAM 대응\n"
    "- S(사회): 산업안전, 공정거래, 인권·다양성\n"
    "- G(거버넌스): 이사회 독립성, 내부통제, 공시 적정성\n"
    "- 대기업 협력사 ESG 요건 (삼성·현대 공급망 기준)\n"
    "- EU CBAM(탄소국경조정제도) 대응 전략\n"
    "- ESG 등급 향상을 통한 금융·조달 우위 확보\n\n"
    "E·S·G 각 항목별 점수(0~100)와 우선 개선 과제를 제시하십시오."
)


class ESGRiskAgent(BaseAgent):
    name = "ESGRiskAgent"
    role = "ESG 리스크 진단 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "assess_esg_risk",
                "description": "기업 현황 기반 E·S·G 항목별 리스크를 평가합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employees": {"type": "integer", "description": "근로자 수"},
                        "industry": {"type": "string", "description": "업종"},
                        "has_env_cert": {"type": "boolean", "description": "ISO 14001 등 환경인증 보유"},
                        "has_safety_system": {"type": "boolean", "description": "안전보건관리체계 구축 여부"},
                        "has_outside_director": {"type": "boolean", "description": "사외이사 선임 여부"},
                        "exports_to_eu": {"type": "boolean", "description": "EU 수출 여부"},
                        "main_customers": {"type": "array", "items": {"type": "string"},
                                          "description": "주요 고객사 목록"},
                    },
                    "required": ["employees", "industry"],
                },
            },
            {
                "name": "calc_cbam_exposure",
                "description": "EU CBAM 탄소국경조정제도 노출도를 평가합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "annual_eu_export_value": {"type": "number",
                                                  "description": "연간 EU 수출액 (원)"},
                        "product_type": {"type": "string",
                                        "description": "제품 유형 (철강/알루미늄/시멘트/비료/전기/수소)"},
                        "carbon_intensity": {"type": "number",
                                           "description": "제품당 탄소배출량 (tCO2/톤), 모르면 0"},
                    },
                    "required": ["annual_eu_export_value", "product_type"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "assess_esg_risk":
            return self._assess(**tool_input)
        if tool_name == "calc_cbam_exposure":
            return self._cbam(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _assess(employees: int, industry: str,
                has_env_cert: bool = False, has_safety_system: bool = False,
                has_outside_director: bool = False, exports_to_eu: bool = False,
                main_customers: list = None) -> dict:
        if main_customers is None:
            main_customers = []

        # E 점수
        e_score = 50
        e_issues = []
        if has_env_cert: e_score += 20
        else: e_issues.append("ISO 14001 미취득 — 대기업 공급망 심사 불이익")
        if exports_to_eu:
            e_score -= 15
            e_issues.append("EU CBAM 대응 체계 구축 필요 (2026년 본격 과금)")
        high_env = ["화학", "철강", "도금", "섬유", "제지"]
        if any(h in industry for h in high_env):
            e_score -= 10
            e_issues.append(f"고환경위험 업종({industry}) — 배출량 측정·보고 체계 필수")

        # S 점수
        s_score = 50
        s_issues = []
        if has_safety_system: s_score += 20
        else:
            s_issues.append("안전보건관리체계 미구축 — 중대재해처벌법 리스크")
        if employees >= 30:
            s_issues.append("직장내 괴롭힘 예방 교육 의무화(2019) 이행 여부 확인")
        big_customers = ["삼성", "현대", "LG", "SK", "롯데", "포스코"]
        if any(bc in " ".join(main_customers) for bc in big_customers):
            s_score += 10
            s_issues.append("대기업 공급망 ESG 실사 대응 필요 (공급망실사지침 2024)")

        # G 점수
        g_score = 50
        g_issues = []
        if has_outside_director: g_score += 20
        else: g_issues.append("사외이사 미선임 — 내부통제 취약 (상법상 의무 없으나 ESG 감점)")
        g_issues.append("이사회 의사록 정기 작성·보관 점검")
        g_issues.append("내부 비리 제보 채널(윤리신고센터) 운영 권고")

        total = (e_score + s_score + g_score) // 3
        grade = "A" if total >= 75 else ("B" if total >= 55 else ("C" if total >= 40 else "D"))

        return {
            "E(환경) 점수": f"{e_score}/100",
            "E 개선 과제": e_issues if e_issues else ["이슈 없음"],
            "S(사회) 점수": f"{s_score}/100",
            "S 개선 과제": s_issues if s_issues else ["이슈 없음"],
            "G(거버넌스) 점수": f"{g_score}/100",
            "G 개선 과제": g_issues if g_issues else ["이슈 없음"],
            "종합 ESG 등급": grade,
            "종합 점수": f"{total}/100",
        }

    @staticmethod
    def _cbam(annual_eu_export_value: float, product_type: str,
              carbon_intensity: float = 0) -> dict:
        cbam_products = ["철강", "알루미늄", "시멘트", "비료", "전기", "수소"]
        is_cbam = any(p in product_type for p in cbam_products)

        if not is_cbam:
            return {"CBAM 적용 여부": "해당 없음 (현재 CBAM 적용 6개 품목 외)",
                    "권고": "EU 공급망 재편 시 해당 여부 지속 모니터링"}

        # EU 탄소가격 €50~70/tCO2 가정, 환율 1450원
        carbon_price_eur = 60  # €60/tCO2
        exchange_rate = 1450
        carbon_price_krw = carbon_price_eur * exchange_rate

        if carbon_intensity > 0:
            # 수출량 추정 (단순 가정: 단가 50만원/톤)
            estimated_tons = annual_eu_export_value / 500_000
            estimated_cbam_cost = estimated_tons * carbon_intensity * carbon_price_krw
        else:
            estimated_cbam_cost = annual_eu_export_value * 0.05  # 수출액의 5% 추정

        return {
            "CBAM 적용 여부": f"해당 ({product_type})",
            "전환기간": "2023.10~2025.12 (보고 의무만)",
            "본격 과금": "2026.1.1 ~",
            "예상 CBAM 비용": f"{estimated_cbam_cost:,.0f}원/년",
            "대응 전략": [
                "탄소배출량 측정·보고 시스템 구축 (GHG Protocol Scope 1·2)",
                "저탄소 원료·공정 전환 투자 (CBAM 비용 절감)",
                "RE100·K-ETS 등 탄소상쇄 크레딧 확보",
                "EU 수출 비중 축소 또는 비CBAM 제품군으로 다변화",
            ],
        }

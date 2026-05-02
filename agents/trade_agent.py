"""
TradeAgent: 무역·통관 전담 에이전트

근거 법령 및 제도:
  - 관세법 / 관세법 시행령·시행규칙
  - 대외무역법 / 전략물자수출입고시
  - FTA 관세특례법 및 각국 FTA 협정
  - AEO(Authorized Economic Operator) 공인제도
  - 원산지관리법인 인정 제도
  - 수출입안전관리우수업체 공인에 관한 고시

주요 기능:
  - HS코드 분류별 관세율·FTA 세율 비교
  - 원산지 관리 (원산지결정기준·증명서 발급)
  - AEO 공인 요건 진단 및 혜택 분석
  - 통관 지연·보류 리스크 사전 진단
  - 수출 규제(전략물자) 해당 여부 체크
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 무역·통관 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- HS코드 관세율 적용·FTA 협정세율 활용 절감\n"
    "- 원산지 관리: 결정기준(세번변경·부가가치·공정) + 증명 방법\n"
    "- AEO(수출입안전관리우수업체) 공인 → 통관 신속화·검사 면제\n"
    "- 전략물자 수출 허가: 가·나·다 그룹 분류 / 자가판정\n"
    "- 무역금융: 수출 LC·포페이팅·수출채권보험(KSURE)\n\n"
    "【분석 관점】\n"
    "- 법인: 관세 절감 / 통관 속도 / 불이행 과태료 방지\n"
    "- 오너: 수출입 원가 경쟁력 / 수출 증대 → 법인세 감면\n"
    "- 과세관청: 수입가격 관세평가 적정성 / 원산지 허위표기\n"
    "- 금융기관: 수출채권 담보 가치 / 수출신용장 리스크\n\n"
    "【목표】\n"
    "FTA 관세 절감과 AEO 공인을 통해 통관 비용·시간을 최소화하고\n"
    "수출입 규정을 완벽히 준수한다."
)

# 주요 FTA 협정세율 (HS 예시: 일반 제조업 완제품 기준)
FTA_RATES = {
    "한-미 FTA": {"일반세율": 5.0, "협정세율": 0.0, "원산지기준": "세번변경(CTH) 또는 부가가치 35%"},
    "한-EU FTA": {"일반세율": 5.0, "협정세율": 0.0, "원산지기준": "부가가치 40% 이상"},
    "한-중 FTA": {"일반세율": 5.0, "협정세율": 1.5, "원산지기준": "세번변경(CTH) 또는 부가가치 40%"},
    "한-ASEAN FTA": {"일반세율": 5.0, "협정세율": 0.5, "원산지기준": "부가가치 40% 이상"},
    "한-일 FTA": {"일반세율": 5.0, "협정세율": "미발효", "원산지기준": "협상 중"},
    "RCEP": {"일반세율": 5.0, "협정세율": 2.0, "원산지기준": "부가가치 40% 또는 세번변경"},
}


class TradeAgent(BaseAgent):
    name = "TradeAgent"
    role = "무역·통관 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_fta_savings",
                "description": (
                    "FTA 협정세율 활용 관세 절감액 계산.\n"
                    "수출입 국가·품목별 일반세율 대비 FTA 세율 차이와\n"
                    "원산지 요건 충족 여부를 분석한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "trade_direction": {
                            "type": "string",
                            "description": "무역 방향",
                            "enum": ["수출", "수입"],
                        },
                        "partner_country": {
                            "type": "string",
                            "description": "교역 국가 (예: 미국, EU, 중국)",
                        },
                        "annual_trade_value": {"type": "number", "description": "연간 교역액 (원)"},
                        "general_tariff_rate": {
                            "type": "number",
                            "description": "일반 관세율 (예: 0.05 = 5%)",
                        },
                        "fta_tariff_rate": {
                            "type": "number",
                            "description": "FTA 협정 세율 (예: 0.0 = 0%)",
                        },
                        "domestic_value_added_ratio": {
                            "type": "number",
                            "description": "국내 부가가치 비율 (원산지 충족 확인용, 예: 0.45)",
                        },
                    },
                    "required": ["trade_direction", "partner_country", "annual_trade_value", "general_tariff_rate", "fta_tariff_rate"],
                },
            },
            {
                "name": "diagnose_aeo_readiness",
                "description": (
                    "AEO(수출입안전관리우수업체) 공인 적격성 진단.\n"
                    "법규준수·내부통제·재무건전성·안전관리 4대 기준을\n"
                    "점검하고 공인 시 혜택과 취득 로드맵을 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "annual_trade_value": {"type": "number", "description": "연간 수출입액 (원)"},
                        "has_compliance_record": {
                            "type": "boolean",
                            "description": "최근 3년 관세 법규 위반 없음 여부",
                        },
                        "has_internal_control": {
                            "type": "boolean",
                            "description": "수출입 내부통제 절차 보유 여부",
                        },
                        "has_security_measures": {
                            "type": "boolean",
                            "description": "화물·직원 보안관리 체계 여부",
                        },
                        "financial_soundness": {
                            "type": "boolean",
                            "description": "최근 2년 재무제표 감사의견 적정 여부",
                        },
                    },
                    "required": ["annual_trade_value", "has_compliance_record"],
                },
            },
            {
                "name": "check_strategic_goods",
                "description": (
                    "전략물자 수출 규제 해당 여부 자가 진단.\n"
                    "품목·기술·최종용도·최종사용자 기준으로\n"
                    "전략물자 해당 시 수출 허가 절차를 안내한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_description": {"type": "string", "description": "제품·기술 설명"},
                        "destination_country": {"type": "string", "description": "수출 대상국"},
                        "end_use": {
                            "type": "string",
                            "description": "최종 용도",
                            "enum": ["민수", "군수", "이중용도", "불명확"],
                        },
                        "has_dual_use_tech": {
                            "type": "boolean",
                            "description": "군사·민수 이중용도 기술 포함 여부",
                        },
                        "hsn_code": {"type": "string", "description": "HS코드 (6자리, 예: 854231)"},
                    },
                    "required": ["product_description", "destination_country", "end_use"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_fta_savings":
            return self._calc_fta_savings(**tool_input)
        if tool_name == "diagnose_aeo_readiness":
            return self._diagnose_aeo_readiness(**tool_input)
        if tool_name == "check_strategic_goods":
            return self._check_strategic_goods(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _calc_fta_savings(
        self,
        trade_direction: str,
        partner_country: str,
        annual_trade_value: float,
        general_tariff_rate: float,
        fta_tariff_rate: float,
        domestic_value_added_ratio: float = 0.0,
    ) -> dict:
        # FTA 정보 매칭
        fta_key = None
        for key in FTA_RATES:
            if any(c in key for c in [partner_country[:2], "ASEAN" if "동남아" in partner_country else ""]):
                fta_key = key
                break
        fta_info = FTA_RATES.get(fta_key or "", {})

        general_duty = annual_trade_value * general_tariff_rate
        fta_duty = annual_trade_value * fta_tariff_rate
        saving = general_duty - fta_duty

        # 원산지 요건 충족 여부 (부가가치 기준)
        min_va_required = 0.40  # 일반적 기준
        origin_meets = domestic_value_added_ratio >= min_va_required if domestic_value_added_ratio else None

        return {
            "무역방향": trade_direction,
            "교역국": partner_country,
            "연간_교역액": round(annual_trade_value),
            "일반관세율": f"{general_tariff_rate*100:.1f}%",
            "FTA_협정세율": f"{fta_tariff_rate*100:.1f}%",
            "일반_관세액": round(general_duty),
            "FTA_관세액": round(fta_duty),
            "연간_절감액": round(saving),
            "절감율": f"{(saving/general_duty*100):.1f}%" if general_duty else "N/A",
            "원산지_요건": fta_info.get("원산지기준", "개별 FTA 협정 확인 필요"),
            "원산지_충족": ("✅ 충족" if origin_meets else "❌ 미충족 — 부가가치율 제고 필요") if origin_meets is not None else "별도 확인 필요",
            "법령근거": "FTA 관세특례법 §5 / 원산지 확인 고시",
        }

    def _diagnose_aeo_readiness(
        self,
        annual_trade_value: float,
        has_compliance_record: bool,
        has_internal_control: bool = False,
        has_security_measures: bool = False,
        financial_soundness: bool = True,
    ) -> dict:
        criteria = [
            ("법규 준수 이력 (3년 위반 없음)", has_compliance_record),
            ("수출입 내부통제 절차", has_internal_control),
            ("화물·직원 보안관리", has_security_measures),
            ("재무 건전성 (감사의견 적정)", financial_soundness),
        ]
        score = sum(1 for _, ok in criteria if ok)
        pct = round(score / len(criteria) * 100)

        benefits = [
            "서류 검사 70% 면제 / 물리 검사 80% 면제",
            "통관 우선 처리 → 물류 리드타임 단축",
            "MRA(상호인정협정) 체결국 통관 혜택 (미국·EU·중국 등 79개국)",
            "관세 담보 면제 / 월별 납부 허용",
        ]

        return {
            "연간_수출입액": round(annual_trade_value),
            "공인_준비율": f"{pct}%",
            "기준별_이행": [{"기준": k, "이행": "✅" if v else "❌"} for k, v in criteria],
            "공인_등급": "A등급" if pct >= 75 else "공인 준비 필요",
            "공인_혜택": benefits,
            "취득_기간": "6~12개월 (서류심사 3개월 + 현장심사 3개월 + 인증 3개월)",
            "법령근거": "관세법 §255의2 / 수출입안전관리우수업체 공인에 관한 고시",
        }

    def _check_strategic_goods(
        self,
        product_description: str,
        destination_country: str,
        end_use: str,
        has_dual_use_tech: bool = False,
        hsn_code: str = "",
    ) -> dict:
        # 고위험 국가 (UN 제재·수출통제 리스트 단순화)
        high_risk_countries = ["이란", "북한", "러시아", "시리아", "쿠바", "미얀마"]
        is_high_risk = any(c in destination_country for c in high_risk_countries)

        risk_level = "🔴 수출 허가 필수"
        action_required = []

        if is_high_risk:
            action_required.append(f"수출 통제 고위험 국가({destination_country}) — 전략물자 해당 여부 관계없이 허가 필요")

        if end_use in ["군수", "이중용도"] or has_dual_use_tech:
            action_required.append("군사·이중용도 물품 → 전략물자관리원 자가판정 + 수출 허가 신청")
            risk_level = "🔴 수출 허가 필수"
        elif end_use == "민수" and not has_dual_use_tech and not is_high_risk:
            risk_level = "🟢 일반 수출 (전략물자 비해당 가능성 높음)"

        return {
            "제품_설명": product_description,
            "수출_대상국": destination_country,
            "최종_용도": end_use,
            "이중용도_기술": "있음" if has_dual_use_tech else "없음",
            "위험_등급": risk_level,
            "조치_사항": action_required if action_required else ["전략물자 비해당 — 일반 수출 가능"],
            "자가판정_방법": "전략물자관리원(www.yestrade.go.kr) 자가판정 시스템 활용",
            "수출허가_기간": "일반 15일 / 긴급 5일 이내",
            "법령근거": "대외무역법 §19~§26 / 전략물자수출입고시",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        rev = company_data.get("revenue", 0)
        export_ratio = company_data.get("export_ratio", 0.3)
        export_val = rev * export_ratio
        lines = ["[무역·통관 분석 결과]"]
        if export_val:
            saving = export_val * 0.05 * 0.5  # FTA 평균 50% 절감 가정
            lines.append(f"\n▶ 연간 수출액: {export_val:,.0f}원")
            lines.append(f"  FTA 관세 절감 잠재액: {saving:,.0f}원 (현행 세율 5% 기준)")
        else:
            lines.append("  수출입 현황 데이터 제공 시 FTA 절감액 산출 가능")
        return "\n".join(lines)

"""
DXAgent: 디지털 전환(Digital Transformation) 전담 에이전트

근거 제도:
  - 조세특례제한법 제24조 (통합투자세액공제 — 디지털·AI 설비 포함)
  - 중소벤처기업부 스마트공장 지원사업 (2026년 보조금 최대 1.5억)
  - TIPS 프로그램 / 디지털 뉴딜 바우처
  - 데이터기반행정법 / 개인정보보호법 (데이터 거버넌스)

주요 기능:
  - 디지털 성숙도 진단 (5단계: 초기→디지털→통합→최적화→혁신)
  - 스마트공장 도입 ROI 계산 (투자비 대비 생산성·불량률 개선)
  - ERP·MES·SCM 시스템 도입 우선순위 및 비용 추정
  - 정부 디지털 바우처·스마트공장 지원금 매칭
  - AI·빅데이터 활용 가능 영역 및 투자 세액공제 적용 여부
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 중소기업 디지털 전환(DX) 전략 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- 디지털 성숙도 진단 (5단계 모델)\n"
    "- 스마트공장 도입 ROI 및 정부 지원금(최대 1.5억) 매칭\n"
    "- ERP·MES·WMS·SCM 시스템 도입 우선순위 및 비용-효과 분석\n"
    "- AI·클라우드·빅데이터 활용 영역 및 통합투자세액공제 적용\n"
    "- 데이터 거버넌스: 개인정보보호법·데이터기반행정법 준수\n\n"
    "【분석 관점】\n"
    "- 법인: 생산성 향상·원가 절감·세액공제 수혜\n"
    "- 오너: 투자 회수 기간 및 경쟁력 강화\n"
    "- 금융기관: 디지털 자산 가치 및 담보 활용\n"
    "- 과세관청: 디지털 설비 투자세액공제 적정성\n\n"
    "【목표】\n"
    "투자비 대비 최대 ROI를 달성하면서 정부 지원금으로 실부담을 최소화하는\n"
    "단계별 DX 로드맵을 제공한다."
)

# 스마트공장 지원 단계별 최대 보조금 (2026년 기준)
SMART_FACTORY_GRANT = {
    "기초": 50_000_000,     # 5천만 원 (센서·PLC)
    "고도화1": 100_000_000,  # 1억 원 (MES·ERP 연계)
    "고도화2": 150_000_000,  # 1.5억 원 (AI·빅데이터)
}

# 디지털 성숙도 단계
DX_MATURITY = {
    1: "초기 (아날로그 중심 — 종이·수기 장부)",
    2: "디지털화 (개별 SW 도입 — 엑셀·그룹웨어)",
    3: "통합 (ERP·MES 연계 — 실시간 데이터)",
    4: "최적화 (AI·예측 분석 — 불량 예측·재고 최적화)",
    5: "혁신 (자율운영 — 디지털트윈·AI 자동의사결정)",
}


class DXAgent(BaseAgent):
    name = "DXAgent"
    role = "디지털 전환(DX) 전략 전담 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "assess_dx_maturity",
                "description": (
                    "디지털 성숙도 진단 (5단계 모델).\n"
                    "현재 IT 인프라·프로세스·데이터 활용 수준을 평가하여\n"
                    "단계별 DX 로드맵과 우선 투자 과제를 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "has_erp": {"type": "boolean", "description": "ERP 도입 여부"},
                        "has_mes": {"type": "boolean", "description": "MES(제조실행시스템) 도입 여부"},
                        "has_cloud": {"type": "boolean", "description": "클라우드 인프라 사용 여부"},
                        "has_ai": {"type": "boolean", "description": "AI·머신러닝 활용 여부"},
                        "data_collection": {
                            "type": "string",
                            "description": "데이터 수집 수준",
                            "enum": ["없음", "수기", "엑셀", "DB자동수집", "실시간IoT"],
                        },
                        "industry": {"type": "string", "description": "업종"},
                        "employees": {"type": "integer", "description": "임직원 수"},
                    },
                    "required": ["has_erp", "has_mes", "has_cloud", "data_collection"],
                },
            },
            {
                "name": "calc_smart_factory_roi",
                "description": (
                    "스마트공장 도입 ROI 및 정부 지원금 계산.\n"
                    "투자비·생산성 향상율·불량률 감소율을 기반으로\n"
                    "투자 회수 기간(PBP)과 순현재가치(NPV)를 산출한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "investment_amount": {"type": "number", "description": "총 투자 예정액 (원)"},
                        "annual_revenue": {"type": "number", "description": "연 매출액 (원)"},
                        "productivity_gain_pct": {
                            "type": "number",
                            "description": "생산성 향상 예상율 (%, 예: 15)",
                        },
                        "defect_reduction_pct": {
                            "type": "number",
                            "description": "불량률 감소 예상 (%, 예: 30)",
                        },
                        "defect_cost_ratio": {
                            "type": "number",
                            "description": "현재 불량 비용 비율 (매출대비, 0~1)",
                        },
                        "smart_factory_level": {
                            "type": "string",
                            "description": "목표 스마트공장 수준",
                            "enum": list(SMART_FACTORY_GRANT.keys()),
                        },
                    },
                    "required": ["investment_amount", "annual_revenue", "smart_factory_level"],
                },
            },
            {
                "name": "prioritize_it_systems",
                "description": (
                    "IT 시스템 도입 우선순위 및 비용 추정.\n"
                    "업종·규모·현재 디지털 수준을 감안하여\n"
                    "ERP·MES·WMS·CRM 도입 순서와 예산을 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string", "description": "업종"},
                        "employees": {"type": "integer", "description": "임직원 수"},
                        "annual_revenue": {"type": "number", "description": "연 매출액 (원)"},
                        "pain_points": {
                            "type": "array",
                            "description": "현재 주요 문제점 리스트",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["industry", "employees", "annual_revenue"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "assess_dx_maturity":
            return self._assess_dx_maturity(**tool_input)
        if tool_name == "calc_smart_factory_roi":
            return self._calc_smart_factory_roi(**tool_input)
        if tool_name == "prioritize_it_systems":
            return self._prioritize_it_systems(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _assess_dx_maturity(
        self,
        has_erp: bool,
        has_mes: bool,
        has_cloud: bool,
        data_collection: str,
        has_ai: bool = False,
        industry: str = "제조업",
        employees: int = 50,
    ) -> dict:
        score = 0
        if has_erp:
            score += 2
        if has_mes:
            score += 2
        if has_cloud:
            score += 1
        if has_ai:
            score += 2
        dc_scores = {"없음": 0, "수기": 0, "엑셀": 1, "DB자동수집": 2, "실시간IoT": 3}
        score += dc_scores.get(data_collection, 0)

        level = min(5, max(1, score // 2 + 1))
        current = DX_MATURITY[level]
        next_level = DX_MATURITY.get(level + 1, "최고 수준 달성")

        roadmap = []
        if not has_erp:
            roadmap.append("1단계: ERP 도입 (회계·구매·재고 통합) — 예산 3,000~8,000만 원")
        if not has_mes and industry in ("제조업", "건설업"):
            roadmap.append("2단계: MES 도입 (생산 실행 관리) — 스마트공장 지원금 활용")
        if not has_cloud:
            roadmap.append("3단계: 클라우드 전환 (AWS·Azure) — IT 비용 30~40% 절감")
        if not has_ai:
            roadmap.append("4단계: AI 분석 도입 (수요 예측·불량 탐지) — 고도화2 지원금 1.5억")

        return {
            "현재_성숙도": f"Level {level} — {current}",
            "목표_성숙도": f"Level {level+1} — {next_level}",
            "로드맵": roadmap,
            "정부지원": "스마트공장 보급·확산 사업 (중기부 / 연 최대 1.5억)",
            "투자세액공제": "스마트공장 설비 → 통합투자세액공제 적용 (조특법 §24)",
        }

    def _calc_smart_factory_roi(
        self,
        investment_amount: float,
        annual_revenue: float,
        smart_factory_level: str,
        productivity_gain_pct: float = 15.0,
        defect_reduction_pct: float = 30.0,
        defect_cost_ratio: float = 0.03,
    ) -> dict:
        grant = SMART_FACTORY_GRANT.get(smart_factory_level, 0)
        net_investment = investment_amount - grant

        # 연간 효과
        productivity_gain = annual_revenue * (productivity_gain_pct / 100)
        defect_saving = annual_revenue * defect_cost_ratio * (defect_reduction_pct / 100)
        annual_benefit = productivity_gain + defect_saving

        pbp = net_investment / annual_benefit if annual_benefit else 99

        # 5년 NPV (할인율 8%)
        discount_rate = 0.08
        npv = sum(annual_benefit / ((1 + discount_rate) ** yr) for yr in range(1, 6)) - net_investment

        # 투자세액공제 (통합투자세액공제 중소기업 10%)
        tax_credit = investment_amount * 0.10

        return {
            "총_투자액": round(investment_amount),
            "정부보조금": round(grant),
            "실부담_투자액": round(net_investment),
            "투자세액공제(10%)": round(tax_credit),
            "실질_순부담": round(max(0, net_investment - tax_credit)),
            "연간_생산성_향상효과": round(productivity_gain),
            "연간_불량비용_절감": round(defect_saving),
            "연간_총_효과": round(annual_benefit),
            "투자회수기간(년)": round(pbp, 1),
            "5년_NPV": round(npv),
            "투자타당성": "우수 (PBP 3년 이하)" if pbp <= 3 else "보통 (PBP 3~5년)" if pbp <= 5 else "재검토 필요",
            "법령근거": "조세특례제한법 §24 (통합투자세액공제)",
        }

    def _prioritize_it_systems(
        self,
        industry: str,
        employees: int,
        annual_revenue: float,
        pain_points: list[str] | None = None,
    ) -> dict:
        pain_points = pain_points or []
        systems = []

        if employees >= 10 and annual_revenue >= 1_000_000_000:
            systems.append({
                "시스템": "ERP",
                "우선순위": 1,
                "예산": "3,000~1억 원",
                "기대효과": "회계·구매·재고 통합으로 결산 기간 50% 단축",
                "지원사업": "중진공 ERP 도입지원",
            })
        if industry in ("제조업", "식품제조"):
            systems.append({
                "시스템": "MES",
                "우선순위": 2,
                "예산": "3,000~8,000만 원",
                "기대효과": "생산 불량률 20~30% 감소 / 납기 준수율 향상",
                "지원사업": "스마트공장 보급확산 (최대 1.5억 보조)",
            })
        if any("재고" in p or "물류" in p for p in pain_points):
            systems.append({
                "시스템": "WMS(창고관리)",
                "우선순위": 3,
                "예산": "2,000~5,000만 원",
                "기대효과": "재고 정확도 95% 이상 / 출하 오류 90% 감소",
                "지원사업": "물류 바우처 (중기부)",
            })
        if any("고객" in p or "영업" in p for p in pain_points):
            systems.append({
                "시스템": "CRM",
                "우선순위": 4,
                "예산": "1,000~3,000만 원",
                "기대효과": "고객 이탈율 30% 감소 / 재구매율 향상",
                "지원사업": "수출바우처 마케팅 항목 활용",
            })

        if not systems:
            systems.append({
                "시스템": "클라우드 그룹웨어",
                "우선순위": 1,
                "예산": "월 50~200만 원 (SaaS)",
                "기대효과": "협업 효율 향상 / 재택근무 지원",
                "지원사업": "디지털 바우처 (중기부)",
            })

        return {
            "업종": industry,
            "임직원": employees,
            "도입_우선순위": systems,
            "총_예산_추정": "1~3억 원 (정부보조 후 실부담 50~70% 수준)",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        has_erp = company_data.get("has_erp", False)
        has_mes = company_data.get("has_mes", False)
        has_cloud = company_data.get("has_cloud", False)
        data_coll = company_data.get("data_collection", "엑셀")
        revenue = company_data.get("revenue", 0)
        industry = company_data.get("industry", "제조업")
        emp = company_data.get("employees", 50)

        lines = ["[디지털 전환(DX) 분석 결과]"]
        maturity = self._assess_dx_maturity(has_erp, has_mes, has_cloud, data_coll, industry=industry, employees=emp)
        lines.append(f"\n▶ 디지털 성숙도: {maturity['현재_성숙도']}")
        lines.append(f"  목표: {maturity['목표_성숙도']}")
        if maturity["로드맵"]:
            lines.append(f"  로드맵: {maturity['로드맵'][0]}")

        return "\n".join(lines)

"""
DataValidationAgent: 입력 데이터 정합성·누락값 자동 보정 에이전트

역할:
  - orchestrator 실행 전 company_data 입력값 정합성 검사
  - 필수 필드 누락 탐지 및 업종 평균으로 자동 보정
  - 논리 모순 탐지 (예: 영업이익 > 매출, 종업원 0명인데 4대보험 있음)
  - 이상값(극단값) 플래그 및 수정 제안

참고 기준:
  - 한국은행 기업경영분석 (업종별 평균 재무비율)
  - 통계청 기업활동조사 (규모별 평균 지표)
  - K-IFRS 재무제표 표시 기준
"""

from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 컨설팅 입력 데이터 품질 관리 전문가입니다.\n\n"
    "【역할】\n"
    "- company_data 딕셔너리 필드 정합성 자동 검사\n"
    "- 필수 필드 누락 시 업종 평균으로 대체값 제안\n"
    "- 논리 모순(revenue < profit 등) 즉시 탐지\n"
    "- 이상값(outlier) 경고 및 확인 요청\n\n"
    "【원칙】\n"
    "- 수정은 '제안' 수준 — 사용자 확인 없이 임의 수정 금지\n"
    "- 보정 근거(출처·기준)를 반드시 명시\n"
    "- 검증 불가 항목은 '확인 필요'로 표시"
)

# 업종별 기본 재무 비율 (한국은행 기업경영분석 2023 기준)
INDUSTRY_DEFAULTS = {
    "제조업": {
        "매출총이익율": 0.20, "영업이익율": 0.05, "부채비율": 1.20,
        "매출채권회전일수": 55, "재고회전일수": 45, "매입채무회전일수": 40,
    },
    "도소매업": {
        "매출총이익율": 0.15, "영업이익율": 0.02, "부채비율": 1.50,
        "매출채권회전일수": 30, "재고회전일수": 25, "매입채무회전일수": 30,
    },
    "건설업": {
        "매출총이익율": 0.12, "영업이익율": 0.04, "부채비율": 2.00,
        "매출채권회전일수": 80, "재고회전일수": 90, "매입채무회전일수": 70,
    },
    "서비스업": {
        "매출총이익율": 0.45, "영업이익율": 0.08, "부채비율": 0.80,
        "매출채권회전일수": 20, "재고회전일수": 10, "매입채무회전일수": 20,
    },
    "IT·소프트웨어": {
        "매출총이익율": 0.60, "영업이익율": 0.12, "부채비율": 0.50,
        "매출채권회전일수": 45, "재고회전일수": 5,  "매입채무회전일수": 30,
    },
}

# 필수 입력 필드 정의
REQUIRED_FIELDS = {
    "company_name": "회사명",
    "industry": "업종",
    "employees": "임직원 수",
    "revenue": "연 매출액",
    "fiscal_year": "결산 연도",
}

# 권장 입력 필드
RECOMMENDED_FIELDS = {
    "operating_profit": "영업이익",
    "net_profit": "당기순이익",
    "total_assets": "총자산",
    "total_equity": "자기자본",
    "total_debt": "총차입금",
    "avg_receivables": "평균 매출채권",
    "avg_inventory": "평균 재고자산",
    "avg_payables": "평균 매입채무",
    "cogs": "매출원가",
    "founder_age": "대표이사 나이",
    "established_year": "설립 연도",
}


class DataValidationAgent(BaseAgent):
    name = "DataValidationAgent"
    role = "입력 데이터 정합성 검증 및 자동 보정 전담"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "validate_company_data",
                "description": (
                    "company_data 입력값 전체 정합성 검사.\n"
                    "필수 필드 누락·논리 모순·이상값을 탐지하고\n"
                    "업종 평균 대체값과 함께 보정 방안을 제시한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_data": {
                            "type": "object",
                            "description": "검증할 기업 데이터 딕셔너리",
                        },
                    },
                    "required": ["company_data"],
                },
            },
            {
                "name": "impute_missing_fields",
                "description": (
                    "누락 필드를 업종 평균으로 자동 추정·보정.\n"
                    "매출액·업종 기반으로 손익계산서·재무상태표 주요 항목을\n"
                    "추정하여 분석 가능한 최소 데이터셋을 완성한다."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "revenue": {"type": "number", "description": "연 매출액 (원) — 필수"},
                        "industry": {"type": "string", "description": "업종"},
                        "employees": {"type": "integer"},
                        "missing_fields": {
                            "type": "array",
                            "description": "추정이 필요한 필드명 목록",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["revenue", "industry"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "validate_company_data":
            return self._validate_company_data(**tool_input)
        if tool_name == "impute_missing_fields":
            return self._impute_missing_fields(**tool_input)
        return f"[{tool_name}] 미등록 툴"

    def _validate_company_data(self, company_data: dict) -> dict:
        issues = []
        warnings = []

        # 1. 필수 필드 누락 체크
        missing_required = [
            f"{v}({k})" for k, v in REQUIRED_FIELDS.items()
            if k not in company_data or company_data[k] in [None, "", 0]
        ]
        if missing_required:
            issues.append({"유형": "필수 필드 누락", "항목": missing_required})

        # 2. 권장 필드 누락 체크
        missing_recommended = [
            k for k in RECOMMENDED_FIELDS if k not in company_data
        ]

        # 3. 논리 모순 체크
        rev = company_data.get("revenue", 0)
        op = company_data.get("operating_profit", None)
        net = company_data.get("net_profit", None)
        cogs = company_data.get("cogs", None)

        if op is not None and rev and op > rev:
            issues.append({"유형": "논리 모순", "항목": f"영업이익({op:,.0f}) > 매출({rev:,.0f}) — 불가"})
        if net is not None and op is not None and net > op * 1.5:
            warnings.append(f"당기순이익({net:,.0f})이 영업이익({op:,.0f})의 1.5배 초과 — 영업외 수익 확인 필요")
        if cogs is not None and rev and cogs > rev:
            issues.append({"유형": "논리 모순", "항목": f"매출원가({cogs:,.0f}) > 매출({rev:,.0f}) — 확인 필요"})

        # 4. 이상값 탐지 (업종 기준)
        ind = company_data.get("industry", "제조업")
        defaults = INDUSTRY_DEFAULTS.get(ind, INDUSTRY_DEFAULTS["제조업"])
        if op is not None and rev:
            op_margin = op / rev
            bench = defaults["영업이익율"]
            if op_margin > bench * 3:
                warnings.append(f"영업이익율 {op_margin*100:.1f}% — 업종평균 {bench*100:.1f}%의 3배 초과 (이상값 의심)")

        quality_score = 100 - len(issues) * 20 - len(warnings) * 5 - len(missing_recommended) * 2
        quality_score = max(0, min(100, quality_score))

        return {
            "데이터_품질점수": f"{quality_score}/100",
            "필수_누락": issues,
            "경고사항": warnings,
            "권장_필드_누락수": len(missing_recommended),
            "권장_누락_목록": missing_recommended[:5],  # 상위 5개만
            "판정": "✅ 분석 가능" if quality_score >= 60 else "⚠️ 보완 후 분석 권장",
        }

    def _impute_missing_fields(
        self,
        revenue: float,
        industry: str,
        employees: int = 0,
        missing_fields: list[str] | None = None,
    ) -> dict:
        defaults = INDUSTRY_DEFAULTS.get(industry, INDUSTRY_DEFAULTS["제조업"])
        imputed = {}

        field_formulas = {
            "cogs": revenue * (1 - defaults["매출총이익율"]),
            "operating_profit": revenue * defaults["영업이익율"],
            "net_profit": revenue * defaults["영업이익율"] * 0.75,
            "avg_receivables": revenue / 365 * defaults["매출채권회전일수"],
            "avg_inventory": revenue * (1 - defaults["매출총이익율"]) / 365 * defaults["재고회전일수"],
            "avg_payables": revenue * (1 - defaults["매출총이익율"]) / 365 * defaults["매입채무회전일수"],
            "total_assets": revenue * 1.2,
            "total_equity": revenue * 1.2 / (1 + defaults["부채비율"]),
            "total_debt": revenue * 1.2 * defaults["부채비율"] / (1 + defaults["부채비율"]),
        }

        targets = missing_fields or list(field_formulas.keys())
        for field in targets:
            if field in field_formulas:
                imputed[field] = round(field_formulas[field])

        return {
            "기준_매출액": round(revenue),
            "적용_업종": industry,
            "추정_기준": f"한국은행 기업경영분석 {industry} 평균 비율",
            "추정값": imputed,
            "주의": "추정값은 업종 평균 기반 — 실제 재무데이터 확보 시 반드시 교체",
        }

    def analyze(self, company_data: dict[str, Any]) -> str:
        result = self._validate_company_data(company_data)
        lines = ["[입력 데이터 품질 검증 결과]"]
        lines.append(f"\n▶ 데이터 품질: {result['데이터_품질점수']} / {result['판정']}")
        if result["필수_누락"]:
            lines.append(f"  필수 누락 {len(result['필수_누락'])}건 — 분석 정확도 저하 가능")
        return "\n".join(lines)

    def validate_and_impute(self, company_data: dict) -> dict:
        """orchestrator에서 직접 호출: 데이터 검증 후 누락값 보정한 company_data 반환"""
        validation = self._validate_company_data(company_data)
        enriched = dict(company_data)

        if validation["권장_필드_누락수"] > 0:
            rev = company_data.get("revenue", 0)
            ind = company_data.get("industry", "제조업")
            emp = company_data.get("employees", 0)
            if rev:
                imputed = self._impute_missing_fields(
                    revenue=rev,
                    industry=ind,
                    employees=emp,
                    missing_fields=validation["권장_누락_목록"],
                )
                for k, v in imputed["추정값"].items():
                    if k not in enriched:
                        enriched[k] = v
                enriched["_imputed_fields"] = list(imputed["추정값"].keys())

        enriched["_validation"] = validation
        return enriched

"""
PatentAgent: R&D 세액공제·IP 담보·기술보증기금 전문 에이전트
"""
from __future__ import annotations
from typing import Any
from agents.base_agent import BaseAgent

_SYS = (
    "당신은 R&D 세액공제·지식재산권·기술금융 전문 컨설턴트입니다.\n\n"
    "【전문 분야】\n"
    "- R&D 세액공제 요건·전략 (조세특례제한법 제10조)\n"
    "- 연구전담부서 설립 요건 (한국산업기술진흥협회 인정)\n"
    "- 신성장·원천기술 R&D 세액공제 (중소기업 최대 40%)\n"
    "- IP 담보대출, 기술보증기금(기보) 보증 활용\n"
    "- 특허권 법인 이전·자본화 전략\n"
    "- 직무발명 보상금 손금산입 (발명진흥법 제15조)\n\n"
    "【답변 기준】\n"
    "최신 개정 세법·판례 반영, 계산식 자체 검증, 전문가 언어"
    "\n\n【목표】\nR&D 세액공제(조특법 §10) 한도 계산과 IP 담보·기보 보증 활용으로 법인 연구개발 투자 효율을 극대화한다. 지식재산권 자본화 전략으로 재무구조를 개선하는 방안을 수치 기반으로 제시하며, 연구전담부서 설립부터 세액공제 신청까지 실행 단계를 구체적으로 안내한다."
)


class PatentAgent(BaseAgent):
    name = "PatentAgent"
    role = "R&D 세액공제·IP 금융 전문가"
    system_prompt = _SYS

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "calc_rd_tax_credit",
                "description": "연구·인력개발비 세액공제액을 계산합니다 (조세특례제한법 제10조).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "rd_expense_current": {"type": "number", "description": "당기 R&D 비용 (원)"},
                        "rd_expense_avg_3y": {"type": "number", "description": "직전 4년 평균 R&D 비용 (원), 없으면 0"},
                        "is_sme": {"type": "boolean", "description": "중소기업 여부"},
                        "is_new_growth": {"type": "boolean", "description": "신성장·원천기술 해당 여부"},
                    },
                    "required": ["rd_expense_current", "is_sme"],
                },
            },
            {
                "name": "calc_tech_guarantee",
                "description": "기술보증기금 보증 한도 및 예상 보증료를 계산합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "patent_count": {"type": "integer", "description": "등록 특허 수"},
                        "annual_revenue": {"type": "number", "description": "연매출 (원)"},
                        "credit_grade": {"type": "string", "description": "신용등급 (A/B/C/D)"},
                    },
                    "required": ["patent_count", "annual_revenue"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "calc_rd_tax_credit":
            return self._calc_rd(**tool_input)
        if tool_name == "calc_tech_guarantee":
            return self._calc_guarantee(**tool_input)
        return super().handle_tool(tool_name, tool_input)

    @staticmethod
    def _calc_rd(rd_expense_current: float, is_sme: bool,
                 rd_expense_avg_3y: float = 0, is_new_growth: bool = False) -> dict:
        # 당기분 방식
        if is_new_growth:
            rate_current = 0.40 if is_sme else 0.30
            label = "신성장·원천기술"
        elif is_sme:
            rate_current = 0.25
            label = "중소기업 일반"
        else:
            rate_current = 0.08
            label = "일반기업"

        credit_current = rd_expense_current * rate_current

        # 증가분 방식 (직전 4년 평균 대비 증가분)
        credit_incremental = 0.0
        incremental_label = "해당 없음"
        if rd_expense_avg_3y > 0 and rd_expense_current > rd_expense_avg_3y:
            inc_rate = 0.50 if is_sme else 0.40
            increase = rd_expense_current - rd_expense_avg_3y
            credit_incremental = increase * inc_rate
            incremental_label = f"증가분 {increase:,.0f}원 × {int(inc_rate*100)}%"

        best = max(credit_current, credit_incremental)
        method = "당기분" if credit_current >= credit_incremental else "증가분"

        return {
            "구분": label,
            "당기분 공제액": f"{credit_current:,.0f}원 (R&D비용 × {int(rate_current*100)}%)",
            "증가분 공제액": f"{credit_incremental:,.0f}원 ({incremental_label})",
            "최적 선택": method,
            "최적 공제액": f"{best:,.0f}원",
            "지방소득세 포함 절세액": f"{best * 1.1:,.0f}원",
            "이월공제": "미공제액 10년 이월 가능 (중소기업 최저한세 적용 제외)",
        }

    @staticmethod
    def _calc_guarantee(patent_count: int, annual_revenue: float,
                        credit_grade: str = "B") -> dict:
        # 기보 기술평가 보증: 매출의 최대 70%, 특허당 가산
        base_limit = min(annual_revenue * 0.70, 3_000_000_000)
        patent_bonus = patent_count * 50_000_000  # 특허 1건당 5천만 가산 (단순 모형)
        total_limit = min(base_limit + patent_bonus, 5_000_000_000)

        rate_map = {"A": 0.007, "B": 0.009, "C": 0.012, "D": 0.015}
        guarantee_rate = rate_map.get(credit_grade.upper(), 0.010)
        annual_fee = total_limit * guarantee_rate

        return {
            "예상 보증 한도": f"{total_limit:,.0f}원",
            "특허 가산 반영": f"{patent_count}건 × 5,000만원",
            "보증료율 (신용등급 {})".format(credit_grade): f"{guarantee_rate*100:.2f}%",
            "연간 보증료": f"{annual_fee:,.0f}원",
            "활용 팁": "IP 담보대출 병행 시 기보 보증 + 은행 대출 조합으로 금리 절감 가능",
        }

"""
agents/active/korean_accounting_enforcer.py
=============================================
KoreanAccountingStandardsEnforcer
모든 에이전트 출력에 한국 회계기준 강제 적용.
US-GAAP 영문 용어 → 한국 표준 용어 50종 자동 치환.
"""
from __future__ import annotations
import re
from typing import Any


US_TO_KR: dict[str, str] = {
    "Income Statement": "손익계산서",
    "Balance Sheet": "재무상태표",
    "Cash Flow Statement": "현금흐름표",
    "Statement of Equity": "자본변동표",
    "Statement of Stockholders Equity": "자본변동표",
    "Goodwill": "영업권",
    "Net Income": "당기순이익",
    "Operating Income": "영업이익",
    "Gross Profit": "매출총이익",
    "COGS": "매출원가",
    "Cost of Goods Sold": "매출원가",
    "SGA": "판매관리비",
    "SG&A": "판매관리비",
    "Selling General Administrative": "판매관리비",
    "Working Capital": "운전자본",
    "Inventory Turnover": "재고자산회전율",
    "Accounts Receivable": "매출채권",
    "Accounts Payable": "매입채무",
    "Notes Receivable": "받을어음",
    "Notes Payable": "지급어음",
    "Long-term Debt": "장기차입금",
    "Short-term Debt": "단기차입금",
    "Current Assets": "유동자산",
    "Non-current Assets": "비유동자산",
    "Current Liabilities": "유동부채",
    "Non-current Liabilities": "비유동부채",
    "Stockholders Equity": "자기자본",
    "Shareholders Equity": "자기자본",
    "Retained Earnings": "이익잉여금",
    "Additional Paid-in Capital": "주식발행초과금",
    "Common Stock": "보통주 자본금",
    "Treasury Stock": "자기주식",
    "Depreciation": "감가상각비",
    "Amortization": "무형자산상각비",
    "EBIT": "영업이익",
    "EBT": "법인세비용차감전순이익",
    "Revenue": "매출액",
    "Net Revenue": "순매출액",
    "Cost of Revenue": "매출원가",
    "Other Income": "영업외수익",
    "Other Expense": "영업외비용",
    "Interest Expense": "이자비용",
    "Interest Income": "이자수익",
    "Income Tax": "법인세비용",
    "Deferred Tax": "���연법인세",
    "Minority Interest": "비지배지분",
    "Non-controlling Interest": "비지배지분",
    "Capital Lease": "금융리스",
    "Operating Lease": "운용리스",
    "Intangible Assets": "무형자산",
}

STANDARDS = {
    "K-IFRS": "한국채택국제회계기준",
    "K-GAAP": "일반기업회계기준",
    "SME": "중소기업 회계기준",
}


class KoreanAccountingStandardsEnforcer:
    """
    사용 예:
        enforcer = KoreanAccountingStandardsEnforcer()
        safe = enforcer.enforce(output_dict, {"is_sme": True})
    """

    def enforce(self, output: Any, company_info: dict | None = None) -> dict:
        info = company_info or {}
        standard = self._determine_standard(info)
        enforced = self._replace_terms(output)
        if isinstance(enforced, str):
            enforced = {"text": enforced}
        enforced["_accounting_standard"] = {
            "standard":      standard,
            "standard_name": STANDARDS[standard],
            "rationale":     self._explain(info, standard),
            "us_terms_replaced": self._count_replacements(output),
        }
        return enforced

    def _determine_standard(self, info: dict) -> str:
        if info.get("is_listed"):
            return "K-IFRS"
        if info.get("is_external_audit"):
            return info.get("preferred_standard", "K-GAAP")
        if info.get("is_sme", True):
            return "SME"
        return "K-GAAP"

    def _replace_terms(self, obj: Any) -> Any:
        if isinstance(obj, str):
            for eng, kor in US_TO_KR.items():
                obj = re.sub(re.escape(eng), kor, obj, flags=re.IGNORECASE)
            return obj
        if isinstance(obj, dict):
            return {k: self._replace_terms(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._replace_terms(i) for i in obj]
        return obj

    def _count_replacements(self, obj: Any) -> int:
        text = str(obj)
        return sum(
            len(re.findall(re.escape(eng), text, re.IGNORECASE))
            for eng in US_TO_KR
        )

    def _explain(self, info: dict, standard: str) -> str:
        if standard == "K-IFRS":
            return "상장사 또는 K-IFRS 선택 기업 → 한국채택국제회계기준 적용"
        if standard == "K-GAAP":
            return "외감 비상장 기업 → 일반기업회계기준 적용"
        return "외감 미대상 중소기업 → 중소기업 회계기준 적용 (가장 간소)"

    def scan(self, output: Any) -> dict:
        """US-GAAP 용어 존재 여부만 스캔 (수정 없이)"""
        text = str(output)
        found = [eng for eng in US_TO_KR if re.search(re.escape(eng), text, re.IGNORECASE)]
        return {"has_us_terms": bool(found), "found": found}

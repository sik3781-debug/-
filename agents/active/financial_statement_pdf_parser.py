"""
agents/active/financial_statement_pdf_parser.py
=================================================
FinancialStatementPDFParser — 재무제표 PDF 파싱
외감보고서·결산서 PDF → 구조화 dict.
PII 포함 가능(대표이사 서명 등) → PIIMaskingAgent 강제 통과.
"""
from __future__ import annotations
import re
from typing import Any


class FinancialStatementPDFParser:
    """
    실제 PDF 처리는 pdf SKILL (Claude의 파일 읽기 기능) 활용.
    여기서는 구조화 로직만 담당.

    사용 예:
        parser = FinancialStatementPDFParser()
        data = parser.parse_text(pdf_extracted_text)
    """

    def parse_text(self, text: str) -> dict:
        """
        PDF에서 추출한 텍스트 → 재무 구조화 데이터.
        claude의 Read tool로 PDF 읽은 뒤 이 메서드로 파싱.
        """
        return {
            "source":         "financial_statement_pdf",
            "accounting_std": self._detect_std(text),
            "fiscal_years":   self._extract_fiscal_years(text),
            "revenue_3y":     self._extract_3y(text, r'(매출액|수익)\s*([\d,]+)'),
            "operating_profit_3y": self._extract_3y(text, r'영업이익\s*([-\d,]+)'),
            "net_income_3y":  self._extract_3y(text, r'당기순이익\s*([-\d,]+)'),
            "total_assets":   self._extract_single(text, r'자산\s*총계\s*([\d,]+)'),
            "total_liabilities": self._extract_single(text, r'부채\s*총계\s*([\d,]+)'),
            "total_equity":   self._extract_single(text, r'자본\s*총계\s*([\d,]+)'),
            "current_assets": self._extract_single(text, r'유동\s*자산\s*([\d,]+)'),
            "current_liab":   self._extract_single(text, r'유동\s*부채\s*([\d,]+)'),
            "depreciation":   self._extract_single(text, r'감가상각비\s*([\d,]+)'),
            "notes_summary":  self._extract_notes(text),
            "derived": self._derive_ratios(text),
        }

    def _detect_std(self, text: str) -> str:
        if "K-IFRS" in text or "한국채택국제회계기준" in text:
            return "K-IFRS"
        if "일반기업회계기준" in text:
            return "K-GAAP"
        return "unknown"

    def _extract_fiscal_years(self, text: str) -> list[int]:
        years = re.findall(r'(\d{4})년\s*(12월|회계연도)', text)
        return sorted(set(int(y[0]) for y in years))[-3:]

    def _extract_3y(self, text: str, pattern: str) -> list[int | None]:
        values = []
        for m in re.finditer(pattern, text):
            try:
                values.append(int(m.group(2).replace(',', '')))
            except (ValueError, IndexError):
                pass
        return values[-3:] if values else [None, None, None]

    def _extract_single(self, text: str, pattern: str) -> int | None:
        m = re.search(pattern, text)
        if not m:
            return None
        try:
            return int(m.group(1).replace(',', ''))
        except (ValueError, IndexError):
            return None

    def _extract_notes(self, text: str) -> list[str]:
        """주석 사항 핵심 추출 (소송·우발채무·특수관계인 거래)"""
        notes: list[str] = []
        for keyword in ["소송", "우발채무", "특수관계인", "담보", "보증"]:
            for m in re.finditer(rf'{keyword}.{{0,80}}', text):
                snippet = m.group().strip()
                if snippet not in notes:
                    notes.append(snippet)
        return notes[:5]

    def _derive_ratios(self, text: str) -> dict:
        """핵심 재무비율 파생 계산"""
        ta = self._extract_single(text, r'자산\s*총계\s*([\d,]+)') or 0
        tl = self._extract_single(text, r'부채\s*총계\s*([\d,]+)') or 0
        te = self._extract_single(text, r'자본\s*총계\s*([\d,]+)') or (ta - tl)
        ca = self._extract_single(text, r'유동\s*자산\s*([\d,]+)') or 0
        cl = self._extract_single(text, r'유동\s*부채\s*([\d,]+)') or 1
        ni_vals = self._extract_3y(text, r'당기순이익\s*([-\d,]+)')
        op_vals = self._extract_3y(text, r'영업이익\s*([-\d,]+)')
        dep    = self._extract_single(text, r'감가상각비\s*([\d,]+)') or 0
        ni = ni_vals[-1] if ni_vals and ni_vals[-1] else 0
        op = op_vals[-1] if op_vals and op_vals[-1] else 0

        return {
            "debt_ratio":    round(tl / te * 100, 1) if te else None,
            "current_ratio": round(ca / cl * 100, 1) if cl else None,
            "ebitda":        op + dep,
            "roe":           round(ni / te * 100, 1) if te else None,
        }

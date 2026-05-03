"""
agents/active/kredtop_parser.py
================================
KredTopParser — 크레탑 조회 결과 파싱
출력은 PIIMaskingAgent 강제 통과.
"""
from __future__ import annotations
import re
from typing import Any


class KredTopParser:
    """
    크레탑 텍스트 → 구조화 dict 변환.
    실제 파일은 사용자가 복사·붙여넣기 또는 텍스트 파일 저장 형태로 제공.
    """

    def parse(self, text_or_path: str) -> dict:
        """
        Parameters
        ----------
        text_or_path : 크레탑 조회 결과 텍스트 또는 파일 경로

        Returns
        -------
        dict (PIIMaskingAgent 통과 전 raw 데이터)
        """
        text = self._load(text_or_path)
        return {
            "source": "kredtop",
            "company_name":   self._extract(text, r'(주)?법인명[:：]\s*(.+)', 2),
            "biz_number":     self._extract(text, r'사업자등록번호[:：]\s*([\d-]+)'),
            "corp_number":    self._extract(text, r'법인등록번호[:：]\s*([\d-]+)'),
            "credit_grade":   self._extract(text, r'신용등급[:：]\s*([A-D][+-]?)'),
            "credit_score":   self._extract(text, r'신용점수[:：]\s*(\d+)'),
            "revenue_3y":     self._extract_revenue_3y(text),
            "debt_ratio":     self._extract_float(text, r'부채비율[:：]\s*([\d.]+)'),
            "current_ratio":  self._extract_float(text, r'유동비율[:：]\s*([\d.]+)'),
            "operating_profit_3y": self._extract_profit_3y(text),
            "employees":      self._extract_int(text, r'임직원\s*수[:：]\s*(\d+)'),
            "main_bank":      self._extract(text, r'주거래은행[:：]\s*(.+)'),
            "established":    self._extract(text, r'설립일[:：]\s*([\d./-]+)'),
            "raw_text_hash":  "[PIIMasker에 의해 원본 격리]",
        }

    def _load(self, text_or_path: str) -> str:
        import os
        if os.path.exists(text_or_path):
            with open(text_or_path, encoding="utf-8") as f:
                return f.read()
        return text_or_path  # 직접 텍스트로 전달된 경우

    def _extract(self, text: str, pattern: str, group: int = 1) -> str | None:
        m = re.search(pattern, text)
        return m.group(group).strip() if m else None

    def _extract_float(self, text: str, pattern: str) -> float | None:
        m = re.search(pattern, text)
        try:
            return float(m.group(1).replace(',', '')) if m else None
        except ValueError:
            return None

    def _extract_int(self, text: str, pattern: str) -> int | None:
        m = re.search(pattern, text)
        try:
            return int(m.group(1).replace(',', '')) if m else None
        except ValueError:
            return None

    def _extract_revenue_3y(self, text: str) -> list[int | None]:
        """매출액 3년치 추출 (억원 단위)"""
        values: list[int | None] = []
        for m in re.finditer(r'(\d{4})년\s*매출\s*([\d,]+)\s*(억원|원)?', text):
            raw = int(m.group(2).replace(',', ''))
            if m.group(3) == '원':
                raw = raw // 100_000_000
            values.append(raw)
        return values[-3:] if values else [None, None, None]

    def _extract_profit_3y(self, text: str) -> list[int | None]:
        """영업이익 3년치"""
        values: list[int | None] = []
        for m in re.finditer(r'(\d{4})년\s*영업이익\s*([-\d,]+)\s*(억원|원)?', text):
            raw = int(m.group(2).replace(',', ''))
            if m.group(3) == '원':
                raw = raw // 100_000_000
            values.append(raw)
        return values[-3:] if values else [None, None, None]

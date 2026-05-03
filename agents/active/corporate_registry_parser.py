"""
agents/active/corporate_registry_parser.py
============================================
CorporateRegistryParser — 법인 등기부등본 파싱
PII 밀도 높음 → PIIMaskingAgent 강제 통과.
"""
from __future__ import annotations
import re
from datetime import date


class CorporateRegistryParser:
    """
    법인 등기부등본 텍스트 → 구조화 dict.
    임원 정보(성명·주민번호·주소)는 원본에 포함되므로
    반드시 PIIMaskingAgent 통과 후 사용.
    """

    def parse(self, text_or_path: str) -> dict:
        text = self._load(text_or_path)
        directors = self._extract_directors(text)
        return {
            "source":          "corp_registry",
            "corp_name":       self._extract(text, r'상\s*호\s*(.+)'),
            "corp_number":     self._extract(text, r'법인등록번호\s*([\d-]+)'),
            "biz_number":      self._extract(text, r'사업자등록번호\s*([\d-]+)'),
            "established":     self._extract(text, r'설립연월일\s*([\d./-]+)'),
            "address":         self._extract(text, r'본점\s*소재지\s*(.+)'),
            "capital":         self._extract_int(text, r'자본금\s*([\d,]+)\s*원'),
            "directors":       directors,
            "director_count":  len(directors),
            "avg_director_age": self._avg_age(directors),
            "auditor":         self._extract(text, r'감사\s*([가-힣]{2,4})'),
            "share_total":     self._extract_int(text, r'발행주식\s*총수\s*([\d,]+)\s*주'),
            "face_value":      self._extract_int(text, r'1주의\s*금액\s*([\d,]+)\s*원'),
            "shareholders":    self._extract_shareholders(text),
        }

    def _extract_directors(self, text: str) -> list[dict]:
        """임원 목록 추출 (이름·직책·취임일·임기 — 주민번호는 PIIMasker가 처리)"""
        directors: list[dict] = []
        pattern = re.compile(
            r'(대표이사|사내이사|사외이사|감사|이사)\s*([가-힣]{2,5})'
            r'(?:.*?(\d{6})-(\d{7}))?'  # 주민번호 (마스킹 대상)
            r'(?:.*?취임\s*([\d./-]+))?',
            re.DOTALL
        )
        for m in pattern.finditer(text):
            birth_year = None
            if m.group(3):
                try:
                    yy = int(m.group(3)[:2])
                    birth_year = (1900 + yy) if yy >= 50 else (2000 + yy)
                except ValueError:
                    pass
            directors.append({
                "role":       m.group(1),
                "name":       m.group(2),
                "rrn":        f"{m.group(3)}-{m.group(4)}" if m.group(3) else None,
                "birth_year": birth_year,
                "appointed":  m.group(5),
                "age_approx": (date.today().year - birth_year) if birth_year else None,
            })
        return directors[:10]  # 최대 10명

    def _avg_age(self, directors: list[dict]) -> float | None:
        ages = [d["age_approx"] for d in directors if d.get("age_approx")]
        return round(sum(ages) / len(ages), 1) if ages else None

    def _extract_shareholders(self, text: str) -> list[dict]:
        shareholders: list[dict] = []
        for m in re.finditer(r'([가-힣]{2,5})\s+([\d,]+)\s*주\s*\(([\d.]+)%\)', text):
            shareholders.append({
                "name":   m.group(1),
                "shares": int(m.group(2).replace(',', '')),
                "pct":    float(m.group(3)),
            })
        return shareholders[:10]

    def _load(self, text_or_path: str) -> str:
        import os
        if os.path.exists(text_or_path):
            with open(text_or_path, encoding="utf-8") as f:
                return f.read()
        return text_or_path

    def _extract(self, text: str, pattern: str, group: int = 1) -> str | None:
        m = re.search(pattern, text)
        return m.group(group).strip() if m else None

    def _extract_int(self, text: str, pattern: str) -> int | None:
        m = re.search(pattern, text)
        try:
            return int(m.group(1).replace(',', '')) if m else None
        except ValueError:
            return None

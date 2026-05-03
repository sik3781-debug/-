"""
agents/active/pii_masking_agent.py
====================================
PIIMaskingAgent — 개인정보 자동 마스킹 전담

모든 파서 출력은 이 에이전트를 통과한 후에만 다음 단계로 전달됨.
원본 데이터는 .secrets/raw/ 에 격리 (git 제외).

마스킹 대상: 주민번호 / 사업자번호 / 휴대폰 / 일반전화 / 계좌번호 / 여권번호 / 주소
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────────────────────
# PII 패턴 정의
# ──────────────────────────────────────────────────────────────
_PATTERNS: dict[str, tuple[re.Pattern, str]] = {
    "rrn":      (re.compile(r'\d{6}-\d{7}'),            "######-#######"),
    "rrn_nohyphen": (re.compile(r'(?<!\d)\d{13}(?!\d)'), "#############"),
    "biz":      (re.compile(r'\d{3}-\d{2}-\d{5}'),       "***-**-*****"),
    "mobile":   (re.compile(r'01[016789]-?\d{3,4}-?\d{4}'), "010-****-****"),
    "tel":      (re.compile(r'0\d{1,2}-\d{3,4}-\d{4}'), "**-****-****"),
    "account":  (re.compile(r'\d{3,6}-\d{2,6}-\d{2,6}'), "***-***-******"),
    "passport": (re.compile(r'[A-Z][MF]\d{7}'),          "M*******"),
    "address":  (
        re.compile(r'(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)'
                   r'\s*(시|도)?\s*\S+\s*(구|군)\s*\S+'),
        r'\1 \2 ***',
    ),
}

# 마스킹 치환 규칙 (주소는 별도 처리)
_MASK_MAP = {
    "rrn":          "######-#######",
    "rrn_nohyphen": "#############",
    "biz":          "***-**-*****",
    "mobile":       "010-****-****",
    "tel":          "**-****-****",
    "account":      "***-***-******",
    "passport":     "M*******",
}

_HERE     = os.path.dirname(os.path.abspath(__file__))
_ROOT     = os.path.dirname(os.path.dirname(_HERE))
_SECRETS  = os.path.join(_ROOT, ".secrets", "raw")


class PIIMaskingAgent:
    """
    사용 예:
        masker = PIIMaskingAgent()
        safe_data = masker.mask(raw_dict)
        # safe_data에는 PII 없음
        # 원본은 .secrets/raw/{hash}.json 에 격리
    """

    def __init__(self):
        self._masked_count = 0
        self._patterns_found: list[str] = []

    def mask(self, data: Any, store_original: bool = True,
             source_label: str = "unknown") -> dict:
        """
        Parameters
        ----------
        data           : 파싱된 raw 데이터 (dict/list/str)
        store_original : True이면 .secrets/raw/ 에 원본 격리
        source_label   : 원본 출처 레이블 (로그용)

        Returns
        -------
        마스킹된 dict + '_pii_report' 키 포함
        """
        self._masked_count = 0
        self._patterns_found = []

        # 원본 격리
        original_hash = None
        if store_original:
            original_hash = self._isolate_original(data, source_label)

        # 재귀 마스킹
        masked = self._recursive_mask(data)

        # 결과가 dict가 아니면 래핑
        if not isinstance(masked, dict):
            masked = {"data": masked}

        masked["_pii_report"] = {
            "masked_count":   self._masked_count,
            "patterns_found": list(set(self._patterns_found)),
            "original_hash":  original_hash,
            "original_path":  f".secrets/raw/{original_hash}.json" if original_hash else None,
            "masking_time":   datetime.now().isoformat(timespec="seconds"),
        }
        return masked

    # ── 재귀 마스킹 ──────────────────────────────────────────

    def _recursive_mask(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self._mask_string(obj)
        if isinstance(obj, dict):
            return {k: self._recursive_mask(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._recursive_mask(i) for i in obj]
        return obj

    def _mask_string(self, text: str) -> str:
        for name, (pattern, replacement) in _PATTERNS.items():
            # 주소는 그룹 참조 치환
            if name == "address":
                new_text, count = pattern.subn(
                    lambda m: m.group(1) + " " + (m.group(2) or "") + " ***",
                    text
                )
            else:
                new_text, count = pattern.subn(replacement, text)

            if count > 0:
                self._masked_count += count
                self._patterns_found.append(name)
                text = new_text
        return text

    # ── 원본 격리 ─────────────────────────────────────────────

    def _isolate_original(self, data: Any, label: str) -> str:
        """원본을 .secrets/raw/ 에 저장. git에서 제외되도록 .gitignore 확인."""
        os.makedirs(_SECRETS, exist_ok=True)
        self._ensure_gitignore()

        content = json.dumps({"label": label, "data": data,
                              "ts": datetime.now().isoformat()},
                             ensure_ascii=False, indent=2)
        file_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
        out_path = os.path.join(_SECRETS, f"{file_hash}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_hash

    def _ensure_gitignore(self) -> None:
        """consulting-agent 루트 .gitignore에 .secrets/ 항목 보장"""
        gi_path = os.path.join(_ROOT, ".gitignore")
        needed = [".secrets/", ".secrets/raw/", "*_pii_*.json",
                  "*_unmasked.*", "*_raw_data.*"]
        existing: set[str] = set()
        if os.path.exists(gi_path):
            with open(gi_path, encoding="utf-8", errors="ignore") as f:
                existing = {l.strip() for l in f}
        to_add = [n for n in needed if n not in existing]
        if to_add:
            with open(gi_path, "a", encoding="utf-8") as f:
                f.write("\n# PII 보안 — 자동 추가 (PIIMaskingAgent)\n")
                for line in to_add:
                    f.write(line + "\n")

    # ── 유틸 ─────────────────────────────────────────────────

    def scan_only(self, data: Any) -> dict:
        """마스킹하지 않고 PII 존재 여부만 검사 (감사용)"""
        self._masked_count = 0
        self._patterns_found = []
        self._recursive_mask(data)  # 결과 무시, 카운트만
        return {
            "has_pii":        self._masked_count > 0,
            "total_found":    self._masked_count,
            "patterns_found": list(set(self._patterns_found)),
        }

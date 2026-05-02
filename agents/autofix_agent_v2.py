"""
agents/autofix_agent_v2.py
==========================
AutoFixAgent v2 — 학습형 자동 수정 에이전트

v1 대비 개선:
  1. error_patterns.jsonl 패턴 학습·재사용
  2. 동일 패턴 7회 → SPEC.md 영구 보정 + 보고
  3. 수정 성공률 kpi_metrics.jsonl 자동 기록
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any


_HERE       = os.path.dirname(os.path.abspath(__file__))
_ROOT       = os.path.dirname(_HERE)
_PATTERNS   = os.path.join(_ROOT, "storage", "error_patterns.jsonl")
_KPI        = os.path.join(_ROOT, "storage", "kpi_metrics.jsonl")
_ACTIVE_DIR = os.path.join(_HERE, "active")
_THRESHOLD  = 7  # 동일 패턴 N회 → 영구 적용


# ──────────────────────────────────────────────────────────────
class AutoFixAgentV2:
    """
    사용 예:
        fixer = AutoFixAgentV2()
        result = fixer.fix(
            output={"text": "...", "agent": "TaxAgent"},
            error_type="unit_consistency",
        )
    """

    def __init__(self):
        self.patterns: list[dict] = self._load_patterns()

    def fix(self, output: dict, error_type: str,
            failed_axes: list[str] | None = None) -> dict:
        """
        출력 수정.
        1. 학습된 패턴 매칭 → 즉시 적용
        2. 미학습 → 규칙 기반 수정 후 패턴 학습
        3. 7회 임계값 → SPEC.md 영구 보정
        """
        agent = output.get("agent", "unknown")
        text  = output.get("text", "")

        matched = self._match_pattern(agent, error_type)
        if matched:
            fixed_text = self._apply_fix(text, matched["fix"])
            matched["count"] += 1
            matched["last_seen"] = datetime.now().date().isoformat()
            self._save_patterns()

            if matched["count"] >= _THRESHOLD and not matched.get("permanent_applied"):
                self._apply_permanent_fix(agent, matched)

            self._record_kpi(agent, success=True)
            return {"text": fixed_text, "agent": agent,
                    "fix_source": "learned_pattern", "pattern_id": matched["id"]}

        # 미학습 패턴 → 규칙 기반
        fixed_text, pattern_name = self._rule_based_fix(text, error_type)
        self._learn_pattern(agent, error_type, pattern_name,
                            self._infer_fix_description(error_type))
        self._record_kpi(agent, success=fixed_text != text)
        return {"text": fixed_text, "agent": agent,
                "fix_source": "rule_based", "learned": True}

    # ── 패턴 매칭 ────────────────────────────────────────────

    def _match_pattern(self, agent: str, error_type: str) -> dict | None:
        for p in self.patterns:
            if p["agent"] == agent and p["error_type"] == error_type:
                return p
        # 에이전트 무관 매칭 (같은 오류 유형)
        for p in self.patterns:
            if p["error_type"] == error_type:
                return p
        return None

    # ── 규칙 기반 수정 ────────────────────────────────────────

    def _rule_based_fix(self, text: str, error_type: str) -> tuple[str, str]:
        if error_type == "unit_consistency":
            # 1억 이상 숫자에 억원 단위 추가 시도
            fixed = re.sub(
                r'(?<!\w)(\d{8,9})(?!\s*(억|만|백만|원))',
                lambda m: f"{int(m.group(1))//100000000}억원 ({m.group(1)}원)",
                text
            )
            return fixed, "대형숫자_단위없음"

        if error_type == "perspective_missing":
            # 누락된 관점 최소 언급 추가
            if "금융기관" not in text:
                text += "\n\n**금융기관 관점**: 본 전략이 신용등급 및 대출가용성에 미치는 영향을 별도 검토 필요합니다."
            return text, "금융기관관점_누락"

        if error_type == "amendment_currency":
            # 구버전 시행일 경고 추가
            fixed = re.sub(
                r'시행\s*20(2[0-4]|1\d)\s*\.',
                lambda m: m.group(0) + " [⚠ 구버전 — 2026년 귀속 재확인 필요]",
                text
            )
            return fixed, "구버전_시행일"

        return text, "unknown_pattern"

    def _infer_fix_description(self, error_type: str) -> str:
        mapping = {
            "unit_consistency":   "억원 단위 명시 추가",
            "perspective_missing": "누락 관점 최소 언급 추가",
            "amendment_currency":  "구버전 시행일 경고 태그 추가",
            "article_existence":   "범위 초과 조문 수정",
            "formula_missing":     "필수 산식 문장 추가",
        }
        return mapping.get(error_type, f"{error_type} 규칙 기반 수정")

    def _apply_fix(self, text: str, fix_description: str) -> str:
        """학습된 수정 설명을 텍스트에 적용 (규칙과 동일 경로)"""
        if "억원 단위" in fix_description or "단위" in fix_description:
            return self._rule_based_fix(text, "unit_consistency")[0]
        if ("누락 관점" in fix_description or "관점" in fix_description
                or "신용등급" in fix_description or "금융기관" in fix_description):
            return self._rule_based_fix(text, "perspective_missing")[0]
        if "시행일" in fix_description or "귀속" in fix_description:
            return self._rule_based_fix(text, "amendment_currency")[0]
        return text  # fallback: 원본 반환

    # ── 영구 보정 ─────────────────────────────────────────────

    def _apply_permanent_fix(self, agent: str, pattern: dict) -> None:
        """7회 임계값 초과 → 해당 에이전트 SPEC.md에 주의사항 추가"""
        spec_path = os.path.join(_ACTIVE_DIR, f"{agent}_SPEC.md")
        if not os.path.exists(spec_path):
            return

        with open(spec_path, encoding="utf-8") as f:
            spec = f.read()

        note = (f"\n\n> **[AutoFix 영구 보정 {datetime.now().date()}]** "
                f"패턴 '{pattern['pattern']}' {pattern['count']}회 감지 → "
                f"수정: {pattern['fix']}")

        if note[:50] not in spec:  # 중복 방지
            with open(spec_path, "a", encoding="utf-8") as f:
                f.write(note)

        pattern["permanent_applied"] = True
        self._save_patterns()

    # ── KPI 기록 ─────────────────────────────────────────────

    def _record_kpi(self, agent: str, success: bool) -> None:
        entry = {
            "date": datetime.now().date().isoformat(),
            "agent": agent,
            "autofix_success": success,
            "fix_type": "autofix_v2",
        }
        with open(_KPI, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ── 학습 ─────────────────────────────────────────────────

    def _learn_pattern(self, agent: str, error_type: str,
                       pattern: str, fix: str) -> None:
        new_id = f"EP{len(self.patterns)+1:03d}"
        entry = {
            "id": new_id, "agent": agent, "error_type": error_type,
            "pattern": pattern, "fix": fix, "count": 1,
            "last_seen": datetime.now().date().isoformat(),
            "permanent_applied": False,
        }
        self.patterns.append(entry)
        self._save_patterns()

    # ── I/O ──────────────────────────────────────────────────

    def _load_patterns(self) -> list[dict]:
        if not os.path.exists(_PATTERNS):
            return []
        patterns = []
        with open(_PATTERNS, encoding="utf-8") as f:
            for line in f:
                try:
                    patterns.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    pass
        return patterns

    def _save_patterns(self) -> None:
        os.makedirs(os.path.dirname(_PATTERNS), exist_ok=True)
        with open(_PATTERNS, "w", encoding="utf-8") as f:
            for p in self.patterns:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

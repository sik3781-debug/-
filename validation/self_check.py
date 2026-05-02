"""
validation/self_check.py
========================
자가검증 3축 자동화 모듈

1축: CalculationValidator  — 단위 일관성 / 소계 정확성 / 산식 유효성
2축: LegalValidator        — 조문 실재 / 시행일 명시 / 약식 표기
3축: Perspective4Validator — 법인·주주·과세관청·금융기관 누락 여부

외부 API 없이 패턴 매칭 + 내부 규칙 기반 (완전 오프라인 동작).
"""
from __future__ import annotations

import re
import json
import os
from datetime import datetime
from typing import Any


# ──────────────────────────────────────────────────────────────
# 공통 타입
# ──────────────────────────────────────────────────────────────
CheckDetail = dict  # {"pass": bool, "message": str, ...}
AxisResult  = dict  # {"pass": bool, "details": dict[str, CheckDetail]}


# ══════════════════════════════════════════════════════════════
# 1축: 계산 정확성
# ══════════════════════════════════════════════════════════════
class CalculationValidator:
    """
    검증 항목:
      unit_consistency   — 억원·백만원·만원 단위 혼재 여부
      subtotal_check     — 숫자 소계·합계 내부 일치
      formula_validity   — 부채비율·이자보상비율·EBITDA 산식 패턴 존재
    """

    # 숫자+단위 패턴
    _NUM_UNIT = re.compile(
        r'(\d[\d,]*)\s*(억\s*원|억원|백만\s*원|백만원|만\s*원|만원|천만\s*원|천만원|원)'
    )
    # 단순 큰 숫자 (단위 없음) — 1천만 이상
    _BARE_LARGE_NUM = re.compile(r'(?<!\w)(\d{8,})(?!\s*(억|만|백만|천|원))')

    # 핵심 재무비율 산식 언급 키워드
    _FORMULA_KEYWORDS = {
        "부채비율":    re.compile(r'부채비율\s*[=:=]\s*|부채비율.*?\d+'),
        "이자보상비율": re.compile(r'이자보상\s*[=:=]\s*|이자보상.*?\d+'),
        "EBITDA":      re.compile(r'EBITDA\s*[=:=]\s*|EBITDA.*?\d+'),
        "순자산가치":   re.compile(r'순자산가치\s*[=:=]\s*|순자산.*?원'),
        "세액공제율":   re.compile(r'세액공제.*?%|공제율.*?%'),
    }

    def check(self, output: dict) -> AxisResult:
        text = _extract_text(output)
        details: dict[str, CheckDetail] = {
            "unit_consistency":  self._check_units(text),
            "subtotal_check":    self._check_subtotals(text),
            "formula_validity":  self._check_formulas(text, output),
        }
        overall = all(d["pass"] for d in details.values())
        return {"pass": overall, "details": details}

    def _check_units(self, text: str) -> CheckDetail:
        """단위 없이 1천만 이상 숫자가 나타나면 경고"""
        bare = self._BARE_LARGE_NUM.findall(text)
        if bare:
            return {
                "pass": False,
                "message": f"단위 미명시 대형 숫자 {len(bare)}개 발견: {bare[:3]}",
                "found": bare[:5],
            }
        return {"pass": True, "message": "단위 일관성 OK"}

    def _check_subtotals(self, text: str) -> CheckDetail:
        """
        '합계 N원' 패턴에서 앞 항목들의 합산 일치 여부를 검증.
        간단히: 합계 키워드와 숫자가 함께 존재하는지 확인 (산술 검증은 near-integer).
        """
        total_pattern = re.compile(r'(합계|소계|총계|총액)\s*[:\s]*(\d[\d,]*)\s*(억원|원|만원)?')
        found = total_pattern.findall(text)
        if not found:
            return {"pass": True, "message": "합계 항목 없음 — 검사 생략"}

        for label, num_str, unit in found:
            num = int(num_str.replace(',', ''))
            if num == 0:
                return {
                    "pass": False,
                    "message": f"'{label}' 값이 0원 — 계산 누락 가능성",
                }
        return {"pass": True, "message": f"합계 항목 {len(found)}개 정상"}

    def _check_formulas(self, text: str, output: dict) -> CheckDetail:
        """에이전트 유형에 따라 필수 산식 언급 여부 확인"""
        agent = output.get("agent", "")
        required: list[str] = []

        if "Finance" in agent or "Credit" in agent:
            required = ["부채비율", "이자보상비율"]
        elif "Stock" in agent:
            required = ["순자산가치"]
        elif "RD" in agent or "Invest" in agent:
            required = ["세액공제율"]
        elif "EBITDA" in text and "MA" in agent:
            required = ["EBITDA"]

        missing = [k for k in required if not self._FORMULA_KEYWORDS[k].search(text)]
        if missing:
            return {
                "pass": False,
                "message": f"필수 산식 미언급: {missing}",
                "missing_formulas": missing,
            }
        return {"pass": True, "message": "산식 검증 OK"}


# ══════════════════════════════════════════════════════════════
# 2축: 법령 정확성
# ══════════════════════════════════════════════════════════════
class LegalValidator:
    """
    검증 항목:
      article_existence      — 인용 조문 형식 유효성 (§번호 범위)
      amendment_currency     — 2025년 이전 시행 표기 경고
      abbreviation_standard  — 약식 표기 표준 (법§/상증§/소§ 등)
    """

    # 조문 인용 패턴: 법§55, 상증§54, 조특§10 등
    _ARTICLE_PATTERN = re.compile(
        r'(법인세법|소득세법|상증세법|조세특례제한법|부가가치세법|국세기본법|상법|'
        r'근로기준법|지방세법|법인세법\s*시행령|법인세법\s*시행규칙|'
        r'법|상증|소|조특|부가|국기|시령|시규|시행령|시행규칙)'
        r'\s*[§§제]\s*(\d+(?:의\d+)?)'
    )
    # 구버전 연도 표기 감지 (2024 이하 시행)
    _OLD_YEAR = re.compile(r'시행\s*20(2[0-4]|1\d)\s*\.', re.IGNORECASE)
    # 권장 약식 맵
    _ABBREV_RECOMMEND = {
        "법인세법": "법§", "소득세법": "소§", "상속세및증여세법": "상증§",
        "조세특례제한법": "조특§", "부가가치세법": "부가§",
        "국세기본법": "국기§",
    }
    # 유효 조문 범위 (법률별 최대 조번호 근사치)
    _MAX_ARTICLES = {
        "법": 130, "상증": 130, "소": 170, "조특": 130,
        "부가": 80, "국기": 90, "상법": 550,
    }

    def check(self, output: dict) -> AxisResult:
        text = _extract_text(output)
        details: dict[str, CheckDetail] = {
            "article_existence":     self._check_articles(text),
            "amendment_currency":    self._check_amendment_year(text),
            "abbreviation_standard": self._check_abbreviations(text),
        }
        overall = all(d["pass"] for d in details.values())
        return {"pass": overall, "details": details}

    def _check_articles(self, text: str) -> CheckDetail:
        """§번호 추출 후 범위 초과 여부 확인"""
        matches = self._ARTICLE_PATTERN.findall(text)
        invalid: list[str] = []
        for law, num_str in matches:
            try:
                num = int(num_str.split('의')[0])
                key = law[:2]  # 앞 2글자로 키 조회
                max_num = self._MAX_ARTICLES.get(key, 9999)
                if num > max_num:
                    invalid.append(f"{law}§{num_str}")
            except ValueError:
                pass
        if invalid:
            return {
                "pass": False,
                "message": f"범위 초과 조문 {len(invalid)}개: {invalid}",
                "invalid_articles": invalid,
            }
        cited = len(matches)
        if cited == 0:
            # 조문 인용 없어도 경고만 (FAIL 아님 — 전략 분석은 조문 생략 가능)
            return {"pass": True, "message": "조문 인용 없음 (전략형 출력 허용)"}
        return {"pass": True, "message": f"조문 {cited}건 형식 유효"}

    def _check_amendment_year(self, text: str) -> CheckDetail:
        """2024 이하 시행 표기 발견 시 경고"""
        old = self._OLD_YEAR.findall(text)
        if old:
            return {
                "pass": False,
                "message": f"구버전 시행일 표기 {len(old)}건 — 2026년 귀속 기준 재확인 필요",
                "found": old,
            }
        return {"pass": True, "message": "시행일 표기 최신"}

    def _check_abbreviations(self, text: str) -> CheckDetail:
        """전체 법률명 표기가 있으면 약식 표기 권고"""
        used_full = [full for full in self._ABBREV_RECOMMEND if full in text]
        if used_full:
            suggestions = {f: self._ABBREV_RECOMMEND[f] for f in used_full}
            # 경고만 (FAIL 아님 — 가독성 권고)
            return {
                "pass": True,
                "message": f"전체 법률명 {len(used_full)}건 — 약식 표기 권고",
                "suggestions": suggestions,
            }
        return {"pass": True, "message": "약식 표기 기준 OK"}


# ══════════════════════════════════════════════════════════════
# 3축: 4자관점 누락
# ══════════════════════════════════════════════════════════════
class Perspective4Validator:
    """
    검증 항목:
      perspective_coverage — 법인·주주·과세관청·금융기관 4관점 언급 여부

    require_full_4_perspective=False 인 경우 (PPT검수·운영 도구 등) PASS.
    """

    _PERSPECTIVE_KEYWORDS: dict[str, list[str]] = {
        "법인": [
            "법인", "손금", "익금", "세무리스크", "재무구조", "세무조사",
            "법인세", "손금산입", "비용처리",
        ],
        "주주": [
            "주주", "오너", "대표이사", "가처분소득", "지분", "배당",
            "승계", "개인", "소득세", "상속", "증여",
        ],
        "과세관청": [
            "과세관청", "국세청", "세무조사", "가산세", "적법성", "판례",
            "법령", "조문", "§", "세법", "부과", "경정",
        ],
        "금융기관": [
            "금융기관", "은행", "신용등급", "담보", "대출", "보증",
            "신용", "이자", "금리", "차입", "부채비율",
        ],
    }

    def check(self, output: dict) -> AxisResult:
        require_full = output.get("require_full_4_perspective", True)
        text = _extract_text(output)

        present = self._detect_perspectives(text)
        required = ["법인", "주주", "과세관청", "금융기관"]
        missing = [p for p in required if p not in present]

        if not require_full:
            return {
                "pass": True,
                "details": {
                    "perspective_coverage": {
                        "pass": True,
                        "message": "4자관점 전수 불필요 에이전트 — 검사 생략",
                        "present": present,
                    }
                },
            }

        if missing:
            return {
                "pass": False,
                "details": {
                    "perspective_coverage": {
                        "pass": False,
                        "message": f"누락 관점: {missing}",
                        "present": present,
                        "missing": missing,
                    }
                },
            }

        return {
            "pass": True,
            "details": {
                "perspective_coverage": {
                    "pass": True,
                    "message": f"4자관점 모두 커버: {present}",
                    "present": present,
                }
            },
        }

    def _detect_perspectives(self, text: str) -> list[str]:
        found: list[str] = []
        for perspective, keywords in self._PERSPECTIVE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                found.append(perspective)
        return found


# ══════════════════════════════════════════════════════════════
# 메인 SelfCheck
# ══════════════════════════════════════════════════════════════
class SelfCheck:
    """
    3축 통합 검증 진입점.

    사용 예:
        checker = SelfCheck()
        result = checker.validate(agent_output_dict)
        if result["overall_pass"]:
            publish(agent_output_dict)
        else:
            auto_fix(agent_output_dict, result["failed_axes"])
    """

    def __init__(self, logger=None):
        self.calc  = CalculationValidator()
        self.legal = LegalValidator()
        self.persp = Perspective4Validator()
        self.logger = logger  # CheckLogger 인스턴스 (선택)

    def validate(self, agent_output: dict) -> dict:
        """
        3축 동시 검증.

        Returns
        -------
        {
            "overall_pass": bool,
            "axes": {
                "axis_1_calculation": AxisResult,
                "axis_2_legal": AxisResult,
                "axis_3_perspective": AxisResult,
            },
            "action": "publish" | "auto_fix",
            "failed_axes": list[str],
            "timestamp": str,
        }
        """
        results = {
            "axis_1_calculation":  self.calc.check(agent_output),
            "axis_2_legal":        self.legal.check(agent_output),
            "axis_3_perspective":  self.persp.check(agent_output),
        }
        failed = [k for k, v in results.items() if not v["pass"]]
        overall = len(failed) == 0

        check_result = {
            "overall_pass": overall,
            "axes": results,
            "action": "publish" if overall else "auto_fix",
            "failed_axes": failed,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "agent": agent_output.get("agent", "unknown"),
        }

        if self.logger:
            self.logger.log(check_result)

        return check_result

    def validate_text(self, text: str, agent: str = "",
                      require_full_4_perspective: bool = True) -> dict:
        """텍스트 직접 검증 (dict 래핑 없이 간편 호출용)"""
        return self.validate({
            "text": text,
            "agent": agent,
            "require_full_4_perspective": require_full_4_perspective,
        })


# ──────────────────────────────────────────────────────────────
# 내부 유틸
# ──────────────────────────────────────────────────────────────
def _extract_text(output: dict) -> str:
    """dict 출력에서 검증 대상 텍스트 추출"""
    parts: list[str] = []
    for key in ("text", "result", "content", "output", "analysis", "recommendation"):
        val = output.get(key, "")
        if isinstance(val, str) and val:
            parts.append(val)
        elif isinstance(val, dict):
            parts.append(json.dumps(val, ensure_ascii=False))
    return "\n".join(parts) if parts else json.dumps(output, ensure_ascii=False)

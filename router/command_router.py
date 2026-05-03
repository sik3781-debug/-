"""
router/command_router.py
========================
자연어 → 슬래시 명령 라우터

매칭 전략:
  1. /슬래시 직접 입력 → exact match
  2. 자연어 입력 → 키워드 오버랩 + 길이 정규화 스코어링
     (외부 API·임베딩 서버 불필요 — 완전 오프라인)

신뢰도 기준:
  >= 0.70 → 자동 실행 (auto_route)
  0.40~0.69 → 사용자 확인 요청 (ask_user)
  < 0.40  → 매칭 실패 (no_match)
"""
from __future__ import annotations

import json
import re
import os
from typing import Any


# ──────────────────────────────────────────────────────────────
# 경로 설정
# ──────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.normpath(os.path.join(_HERE, "..", "..", "junggi-workspace"))
_JSON_PATH = os.path.join(
    _WORKSPACE, "claude-code", "commands", "command_router.json"
)


# ──────────────────────────────────────────────────────────────
# 헬퍼: 한국어 토크나이저 (공백 + 조사 분리)
# ──────────────────────────────────────────────────────────────
_JOSA = re.compile(r'(이|가|은|는|을|를|에|의|로|으로|와|과|도|만|에서|에게|부터|까지|으로서)$')

# 명령형 어미 / 불용어 (점수 희석 방지)
_ACTION_WORDS = re.compile(
    r'(해줘|알려줘|계산해줘|검토해줘|진행해줘|해주세요|알려주세요|'
    r'확인해줘|불러줘|조회해줘|작성해줘|해봐|어때|어떻게|방법|'
    r'있나요|있어요|될까요|할게요|주세요|합니다)$'
)

# 기업명 패턴 (점수 희석 방지 — 앞에 위치하는 고유명사)
_COMPANY_NAME = re.compile(
    r'^[가-힣A-Za-z0-9]{2,10}'
    r'(제약|전자|건설|식품|물산|그룹|코리아|코퍼레이션|'
    r'법인|회사|기업|공업|산업|상사|무역|유통|솔루션|시스템)$'
)

def _tokenize(text: str) -> set[str]:
    """한국어 공백 분할 + 조사·명령어미 제거 + 기업명 필터 + 영숫자 소문자 정규화"""
    tokens: set[str] = set()
    for word in re.split(r'[\s,./\-_]+', text.strip()):
        word = word.lower()
        word = _JOSA.sub('', word)
        word = _ACTION_WORDS.sub('', word)
        # 기업명 고유명사 제거 (매칭 희석 방지)
        if _COMPANY_NAME.match(word):
            continue
        if len(word) >= 2:
            tokens.add(word)
            # 2-gram 서브토큰
            if len(word) >= 4:
                for i in range(len(word) - 1):
                    tokens.add(word[i:i+2])
    return tokens


def _score(query_tokens: set[str], trigger_tokens: set[str]) -> float:
    """Jaccard 유사도 변형: 쿼리 토큰 기준 coverage"""
    if not query_tokens or not trigger_tokens:
        return 0.0
    overlap = len(query_tokens & trigger_tokens)
    # coverage = overlap / query (얼마나 쿼리가 커버되는가)
    coverage = overlap / len(query_tokens)
    # precision = overlap / trigger (트리거가 얼마나 정확한가)
    precision = overlap / len(trigger_tokens)
    # F1 유사 점수
    if coverage + precision == 0:
        return 0.0
    return 2 * coverage * precision / (coverage + precision)


# ──────────────────────────────────────────────────────────────
# 결과 데이터클래스
# ──────────────────────────────────────────────────────────────
class RouteMatch:
    def __init__(self, command: str, meta: dict, confidence: float, matched_trigger: str):
        self.command = command
        self.agent = meta.get("agent", "")
        self.agent_file = meta.get("agent_file", "")
        self.output_format = meta.get("output_format", "md")
        self.model = meta.get("model", "sonnet")
        self.category = meta.get("category", "")
        self.perspective_4 = meta.get("perspective_4", [])
        self.input_schema = meta.get("input_schema", {})
        self.status = meta.get("status", "active")
        self.confidence = confidence
        self.matched_trigger = matched_trigger

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "agent": self.agent,
            "agent_file": self.agent_file,
            "output_format": self.output_format,
            "model": self.model,
            "category": self.category,
            "perspective_4": self.perspective_4,
            "input_schema": self.input_schema,
            "status": self.status,
            "confidence": round(self.confidence, 3),
            "matched_trigger": self.matched_trigger,
        }

    def __repr__(self):
        return (f"RouteMatch(command={self.command!r}, "
                f"confidence={self.confidence:.0%}, trigger={self.matched_trigger!r})")


class RouteResult:
    def __init__(self, status: str, best: RouteMatch | None = None,
                 candidates: list[RouteMatch] | None = None):
        self.status = status          # "auto_route" | "ask_user" | "no_match"
        self.best = best
        self.candidates = candidates or []

    def __repr__(self):
        return f"RouteResult(status={self.status!r}, best={self.best!r})"


# ──────────────────────────────────────────────────────────────
# 메인 라우터
# ──────────────────────────────────────────────────────────────
class CommandRouter:
    """
    자연어 또는 슬래시 명령 → 에이전트 라우팅.

    사용 예:
        router = CommandRouter()
        result = router.route("비상장주식 평가해줘")
        if result.status == "auto_route":
            print(result.best.command, result.best.confidence)
    """

    def __init__(self, json_path: str = _JSON_PATH):
        self.json_path = json_path
        self.commands: dict[str, dict] = {}
        self._trigger_index: list[tuple[str, str, set[str]]] = []
        self._load()

    def _load(self) -> None:
        with open(self.json_path, encoding="utf-8") as f:
            raw: dict = json.load(f)

        for cmd, meta in raw.items():
            if cmd.startswith("_"):  # _meta 등 스킵
                continue
            self.commands[cmd] = meta
            triggers: list[str] = meta.get("natural_language_triggers", [])
            for t in triggers:
                self._trigger_index.append((cmd, t, _tokenize(t)))

    def reload(self) -> None:
        """JSON 변경 시 런타임 핫 리로드"""
        self.commands.clear()
        self._trigger_index.clear()
        self._load()

    # ── 퍼블릭 API ───────────────────────────────────────────

    def route(self, user_input: str, top_k: int = 3) -> RouteResult:
        """
        자연어 또는 /슬래시 명령 → RouteResult.

        Parameters
        ----------
        user_input : 사용자 입력 문자열
        top_k      : 후보 최대 수 (기본 3)
        """
        user_input = user_input.strip()

        # 1. 슬래시 직접 입력
        if user_input.startswith("/"):
            match = self._direct_match(user_input)
            if match:
                return RouteResult("auto_route", best=match, candidates=[match])
            return RouteResult("no_match")

        # 2. 자연어 의미 매칭
        candidates = self._semantic_match(user_input, top_k=top_k)
        if not candidates:
            return RouteResult("no_match")

        best = candidates[0]
        if best.confidence >= 0.70:
            return RouteResult("auto_route", best=best, candidates=candidates)
        elif best.confidence >= 0.40:
            return RouteResult("ask_user", best=best, candidates=candidates)
        else:
            return RouteResult("no_match", candidates=candidates)

    def list_commands(self, category: str | None = None) -> list[str]:
        """등록된 명령 목록 반환 (category 필터 선택)"""
        if category:
            return [c for c, m in self.commands.items()
                    if m.get("category") == category]
        return list(self.commands.keys())

    def get_command(self, cmd: str) -> dict | None:
        return self.commands.get(cmd)

    # ── 내부 메서드 ──────────────────────────────────────────

    def _direct_match(self, slash_input: str) -> RouteMatch | None:
        """슬래시 명령 정확 매칭 (공백 앞까지)"""
        cmd = slash_input.split()[0]  # "/명령 인자..." → "/명령"
        if cmd in self.commands:
            meta = self.commands[cmd]
            return RouteMatch(cmd, meta, confidence=1.0, matched_trigger=cmd)
        # 대소문자·공백 정규화 재시도
        for registered in self.commands:
            if registered.lower() == cmd.lower():
                meta = self.commands[registered]
                return RouteMatch(registered, meta, confidence=0.95,
                                  matched_trigger=cmd)
        return None

    def _semantic_match(self, text: str, top_k: int = 3) -> list[RouteMatch]:
        """자연어 → 트리거 키워드 스코어링"""
        query_tokens = _tokenize(text)
        if not query_tokens:
            return []

        scored: list[tuple[float, str, str]] = []
        for cmd, trigger, trigger_tokens in self._trigger_index:
            s = _score(query_tokens, trigger_tokens)
            if s > 0:
                scored.append((s, cmd, trigger))

        if not scored:
            return []

        # 내림차순 정렬
        scored.sort(key=lambda x: -x[0])

        # 명령 중복 제거 (각 명령별 최고 점수만 유지)
        seen: set[str] = set()
        results: list[RouteMatch] = []
        for score, cmd, trigger in scored:
            if cmd in seen:
                continue
            seen.add(cmd)
            meta = self.commands[cmd]
            results.append(RouteMatch(cmd, meta, confidence=score,
                                      matched_trigger=trigger))
            if len(results) >= top_k:
                break

        return results

    # ── 실행 연결 (Orchestrator 연동 포인트) ─────────────────

    def execute(self, match: RouteMatch, inputs: dict[str, Any]) -> dict:
        """
        매칭된 명령 실행.
        실제 에이전트 호출은 Orchestrator가 담당.
        여기서는 실행 명세만 반환한다.

        Returns
        -------
        dict with keys: command, agent, agent_file, model, inputs, output_format
        """
        return {
            "command": match.command,
            "agent": match.agent,
            "agent_file": match.agent_file,
            "model": match.model,
            "inputs": inputs,
            "output_format": match.output_format,
            "perspective_4": match.perspective_4,
            "status": match.status,
        }

    def _ask_user_prompt(self, candidates: list[RouteMatch]) -> str:
        """사용자 확인 요청 메시지 생성"""
        lines = ["어떤 작업을 원하시나요? 가장 가까운 명령은:"]
        for i, c in enumerate(candidates[:3], 1):
            lines.append(
                f"  {i}. {c.command}  ({c.confidence:.0%})  — {c.agent}"
            )
        lines.append("번호를 입력하거나 더 구체적으로 다시 입력해주세요.")
        return "\n".join(lines)

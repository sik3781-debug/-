"""
WebResearchAgent: 홈페이지·뉴스·특허청·DART 자료 수집 에이전트
- MODEL_LIGHT (Haiku) 사용
"""
from __future__ import annotations
import json
import re
import urllib.parse
import urllib.request
from typing import Any
from agents.base_agent import BaseAgent, MODEL_LIGHT
from agents.industry_agent import _duckduckgo_search  # 공유 검색 함수

_SYS = (
    "당신은 기업 정보 수집 전문 리서처입니다.\n\n"
    "【전문 분야】\n"
    "- 기업 홈페이지·뉴스 최신 동향 수집\n"
    "- 특허청(KIPRIS) 특허·상표 현황\n"
    "- DART(금융감독원 전자공시) 재무 공시 분석\n"
    "- 정부기관 정책 공고·지원사업 정보\n\n"
    "수집한 정보를 요약·분석하여 컨설팅에 활용 가능한 인사이트로 제공하십시오."
)


def _fetch_webpage(url: str, max_chars: int = 1500) -> str:
    """웹페이지 내용을 가져와 텍스트를 반환합니다."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "consulting-agent/2.0",
                          "Accept": "text/html,application/xhtml+xml"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception as e:
        return f"[페이지 로드 실패: {str(e)}]"


class WebResearchAgent(BaseAgent):
    name = "WebResearchAgent"
    role = "기업 정보 수집 리서처"
    system_prompt = _SYS
    model = MODEL_LIGHT  # Haiku 사용

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "web_search",
                "description": "주어진 키워드로 웹을 검색하고 결과를 반환합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "검색 키워드"},
                        "max_results": {"type": "integer", "description": "최대 결과 수 (기본 4)"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "fetch_webpage",
                "description": "특정 URL의 웹페이지 내용을 가져옵니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "조회할 URL"},
                        "max_chars": {"type": "integer", "description": "최대 문자 수 (기본 1500)"},
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "search_dart",
                "description": "DART 전자공시에서 기업 재무 정보를 검색합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "기업명"},
                        "report_type": {"type": "string", "description": "공시 유형 (사업보고서/분기보고서)"},
                    },
                    "required": ["company_name"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "web_search":
            results = _duckduckgo_search(
                tool_input["query"],
                tool_input.get("max_results", 4)
            )
            return {"검색 결과": results}
        if tool_name == "fetch_webpage":
            content = _fetch_webpage(
                tool_input["url"],
                tool_input.get("max_chars", 1500)
            )
            return {"url": tool_input["url"], "내용": content}
        if tool_name == "search_dart":
            company = tool_input["company_name"]
            query = f"{company} DART 사업보고서 재무제표 공시"
            results = _duckduckgo_search(query, 3)
            return {"기업": company, "DART 검색 결과": results,
                    "안내": "dart.fss.or.kr 에서 직접 조회 권장"}
        return super().handle_tool(tool_name, tool_input)

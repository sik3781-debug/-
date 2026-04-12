"""
IndustryAgent: 동종업계 벤치마크·세무조사 트렌드 에이전트
- MODEL_LIGHT (Haiku) 사용으로 비용 최적화
- 웹 검색 툴 활용
"""
from __future__ import annotations
import json
import urllib.parse
import urllib.request
from typing import Any
from agents.base_agent import BaseAgent, MODEL_LIGHT

_SYS = (
    "당신은 업종별 재무 벤치마크·세무조사 트렌드 분석 전문가입니다.\n\n"
    "【전문 분야】\n"
    "- 동종업계 재무비율 벤치마크 (부채비율·유동비율·영업이익률·ROE)\n"
    "- 업종별 세무조사 선정 기준 및 최근 트렌드\n"
    "- 경쟁사 포지셔닝 및 시장 점유율 분석\n"
    "- 주요 고객사(대기업) 공급망 리스크\n"
    "- DART 공시 기반 업계 동향\n\n"
    "웹 검색 툴로 최신 정보를 수집한 후 분석하십시오.\n"
    "단정적·간결한 전문가 언어 사용"
)


def _duckduckgo_search(query: str, max_results: int = 4) -> list[dict]:
    """DuckDuckGo Instant Answer API로 검색 결과를 가져옵니다."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&no_redirect=1&kl=kr-kr"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "consulting-agent/2.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        results: list[dict] = []
        if data.get("AbstractText"):
            results.append({"source": data.get("AbstractSource", "DuckDuckGo"),
                            "content": data["AbstractText"][:500]})
        for item in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(item, dict) and "Text" in item:
                results.append({"source": item.get("FirstURL", ""),
                                "content": item["Text"][:400]})
        return results or [{"source": "검색", "content": f"'{query}' 검색 결과 없음"}]
    except Exception as e:
        return [{"source": "오류", "content": f"검색 실패: {str(e)}"}]


class IndustryAgent(BaseAgent):
    name = "IndustryAgent"
    role = "동종업계 벤치마크·세무조사 트렌드 분석가"
    system_prompt = _SYS
    model = MODEL_LIGHT  # Haiku 사용

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.tools = [
            {
                "name": "search_industry_benchmark",
                "description": "업종별 재무 벤치마크 및 세무조사 트렌드를 웹에서 검색합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string", "description": "업종명 (예: 자동차부품 제조업)"},
                        "metric": {"type": "string", "description": "조회할 지표 (재무비율/세무조사/시장동향)"},
                    },
                    "required": ["industry"],
                },
            },
            {
                "name": "search_tax_audit_trend",
                "description": "국세청 세무조사 선정 기준 및 업종별 최근 트렌드를 검색합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string", "description": "업종명"},
                        "year": {"type": "integer", "description": "조회 연도 (기본: 2024)"},
                    },
                    "required": ["industry"],
                },
            },
        ]

    def handle_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        if tool_name == "search_industry_benchmark":
            industry = tool_input.get("industry", "")
            metric = tool_input.get("metric", "재무비율")
            query = f"{industry} 업종 평균 {metric} 2024 한국은행 기업경영분석"
            results = _duckduckgo_search(query)
            return {"검색어": query, "결과": results}
        if tool_name == "search_tax_audit_trend":
            industry = tool_input.get("industry", "")
            year = tool_input.get("year", 2024)
            query = f"국세청 세무조사 {industry} {year} 선정 기준 트렌드"
            results = _duckduckgo_search(query)
            return {"검색어": query, "결과": results}
        return super().handle_tool(tool_name, tool_input)

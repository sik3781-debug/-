---
name: WebResearchAgent
type: agent_spec
status: active
group: C
step: 2
model: claude-sonnet-4-6
source_file: agents/web_research_agent.py
4자관점: 법인
---

# WebResearchAgent — 표준 명세서 (SPEC)

## 1. 단일책임
기업명·업종·주요 고객사 입력 → 최신 업계 동향 + 특허청 정보 + 공급망 요건 조사.

## 2. 입력

**필수**: 기업명(company_name), 업종(industry), 주요고객사(main_customers)

**선택**: 조사 기간, 키워드

## 3. 출력

**형식**: Markdown 텍스트 (조사 결과 요약)

**필수 필드**: 업계동향 / 특허정보 / 공급망요건 / 위험신호

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | WebSearch [Anthropic tool_use] / BaseAgent.run() |
| 외부 API | WebSearch (Claude tool_use) |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 없음 (조사 위주)

② **법령·통계 근거**: 적용 법령 — 없음 (조사 위주)

③ **4자관점 교차 분석**:
법인(경쟁환경파악), 주주(시장가치참고), 과세관청(산업동향참고), 금융기관(시장리스크)

## 6. 협력 에이전트

| 방향 | 에이전트 |
|---|---|
| 상류 | 없음 (독립 실행) |
| 하류 | VerifyStrategy → ReportAgent |

## 7. 실패 처리

try/except 격리 → agent_errors 기록

## 8. KPI

| 지표 | 목표 |
|---|---|
| 정확도 | [보정필요] |
| 응답시간 | 60~120초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 4개 — D+18~19 사용자 검토 필요*

---
name: IndustryAgent
type: agent_spec
status: active
group: C
step: 2
model: claude-sonnet-4-6
source_file: agents/industry_agent.py
4자관점: 과세관청
---

# IndustryAgent — 표준 명세서 (SPEC)

## 1. 단일책임
업종·매출·임직원 입력 → 동종업계 재무 벤치마크(부채비율·영업이익률·ROE) + 최근 세무조사 트렌드 분석.

## 2. 입력

**필수**: 업종(industry), 매출(revenue), 임직원수(employees)

**선택**: KSIC 코드, 지역

## 3. 출력

**형식**: Markdown 텍스트 (벤치마크 표 + 세무조사 트렌드)

**필수 필드**: 업종평균비교표 / 취약지표 / 세무조사우선항목

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.run() |
| 외부 API | [보정필요: DART_API 연동 여부 확인] |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: [보정필요: 벤치마크 출처 명시 필요]

② **법령·통계 근거**: 적용 법령 — [보정필요: 벤치마크 출처 명시 필요]

③ **4자관점 교차 분석**:
법인(업종리스크파악), 주주(비교우위분석), 과세관청(세무조사트렌드), 금융기관(업종신용도)

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
| 응답시간 | 30~60초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 4개 — D+18~19 사용자 검토 필요*

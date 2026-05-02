---
name: GlobalExpansionAgent
type: agent_spec
status: active
group: H
step: 3
model: claude-sonnet-4-6
source_file: agents/global_expansion_agent.py
4자관점: 법인
---

# GlobalExpansionAgent — 표준 명세서 (SPEC)

## 1. 단일책임
업종·매출·주요 고객사 입력 → 해외 진출 타당성 + 진출 국가별 세금 비교 + FTA 활용 방안.

## 2. 입력

**필수**: company_data 전체

**선택**: 현재 수출 비율, 진출 희망 국가

## 3. 출력

**형식**: Markdown 텍스트 (진출 타당성 + 국가별 비교)

**필수 필드**: 진출타당성점수 / 추천국가 / 세금비교 / FTA활용방안

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 조세특례제한법 §22 (해외진출기업 세금혜택) / FTA 원산지 규정

② **법령·통계 근거**: 적용 법령 — 조세특례제한법 §22 (해외진출기업 세금혜택) / FTA 원산지 규정

③ **4자관점 교차 분석**:
법인(해외매출확대), 주주(기업가치상승), 과세관청(이전가격과세위험), 금융기관(해외보증가용성)

## 6. 협력 에이전트

| 방향 | 에이전트 |
|---|---|
| 상류 | DataValidationAgent |
| 하류 | VerifyStrategy → ReportAgent |

## 7. 실패 처리

try/except 격리 → agent_errors 기록

## 8. KPI

| 지표 | 목표 |
|---|---|
| 정확도 | [보정필요] |
| 응답시간 | 45~90초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 4개 — D+18~19 사용자 검토 필요*

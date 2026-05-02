---
name: CostAnalysisAgent
type: agent_spec
status: active
group: G
step: 3
model: claude-sonnet-4-6
source_file: agents/cost_analysis_agent.py
4자관점: 법인
---

# CostAnalysisAgent — 표준 명세서 (SPEC)

## 1. 단일책임
매출원가·판관비 입력 → 원가 구조 진단 + 절감 가능 항목 + BEP(손익분기점) 분석.

## 2. 입력

**필수**: company_data (매출·원가 포함)

**선택**: 제품별 원가 명세, 고정비·변동비 분류

## 3. 출력

**형식**: Markdown 텍스트 (원가 분석표 + BEP)

**필수 필드**: 원가율 / 절감항목 / BEP / 목표원가율

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: [보정필요]

② **법령·통계 근거**: 적용 법령 — [보정필요]

③ **4자관점 교차 분석**:
법인(원가절감손익개선), 주주(이익률제고), 과세관청(원가조작여부), 금융기관(수익성지표)

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
| 응답시간 | 30~60초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 4개 — D+18~19 사용자 검토 필요*

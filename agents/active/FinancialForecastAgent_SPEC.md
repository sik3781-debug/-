---
name: FinancialForecastAgent
type: agent_spec
status: active
group: G
step: 3
model: claude-sonnet-4-6
source_file: agents/financial_forecast_agent.py
4자관점: 법인
---

# FinancialForecastAgent — 표준 명세서 (SPEC)

## 1. 단일책임
현재 재무 데이터 입력 → 3년 재무 예측(손익계산서·재무상태표·현금흐름표) + 시나리오별 민감도 분석.

## 2. 입력

**필수**: company_data 전체

**선택**: 성장률 가정, 설비투자 계획

## 3. 출력

**형식**: Markdown 텍스트 (3년 재무 예측 표)

**필수 필드**: 예측매출 / 예측순이익 / 예측부채비율 / 민감도분석

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
법인(미래재무건전성), 주주(배당전망), 과세관청(세수예측), 금융기관(대출상환능력예측)

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

---
name: InvestTaxCreditAgent
type: agent_spec
status: active
group: F
step: 2
model: claude-sonnet-4-6
source_file: agents/invest_tax_credit_agent.py
4자관점: 법인
---

# InvestTaxCreditAgent — 표준 명세서 (SPEC)

## 1. 단일책임
설비 투자 현황·기업 규모·기술 유형 입력 → 통합투자세액공제액 계산 + 기본공제·추가공제 + 10년 이월 전략.

## 2. 입력

**필수**: company_data (설비투자액·기업규모·기술유형 포함)

**선택**: 전년도 투자액, 이월공제 잔액

## 3. 출력

**형식**: Markdown 텍스트 (공제액 계산표 + 이월 전략)

**필수 필드**: 기본공제율 / 추가공제율 / 공제금액 / 이월전략

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 조세특례제한법 §24 (통합투자세액공제) — 10년 이월 허용

② **법령·통계 근거**: 적용 법령 — 조세특례제한법 §24 (통합투자세액공제) — 10년 이월 허용

③ **4자관점 교차 분석**:
법인(설비투자세액공제극대화), 주주(순이익증가), 과세관청(공제요건적정성), 금융기관(없음)

## 6. 협력 에이전트

| 방향 | 에이전트 |
|---|---|
| 상류 | DataValidationAgent |
| 하류 | VerifyTax → ReportAgent |

## 7. 실패 처리

try/except 격리 → agent_errors 기록

## 8. KPI

| 지표 | 목표 |
|---|---|
| 정확도 | 95%+ (공제율 계산 오류 0건) |
| 응답시간 | 30~45초 |
| 평균 토큰 | 3,000~5,000 |

---
*보정 필요 항목: 1개 — D+18~19 사용자 검토 필요*

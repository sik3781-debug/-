---
name: ProvisionalPaymentAgent
type: agent_spec
status: active
group: E
step: 1
model: claude-sonnet-4-6
source_file: agents/provisional_payment_agent.py
4자관점: 법인
---

# ProvisionalPaymentAgent — 표준 명세서 (SPEC)

## 1. 단일책임
가지급금 잔액·인정이자율(4.6%) 입력 → 5가지 해소 방법별 법인+개인 합산 세부담 비교 + 최적 방법 + 월별 로드맵.

## 2. 입력

**필수**: 가지급금잔액(provisional_payment), 기업개요(brief)

**선택**: 급여증액 가능 범위, 배당 재원

## 3. 출력

**형식**: Markdown 텍스트 (5방법 비교표 + 로드맵)

**필수 필드**: 방법별세부담 / 추천방법 / 월별실행계획 / 필요증빙

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | calc_deemed_interest() [내부 도구] / BaseAgent.run() |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 법인세법 시행규칙 §43 (인정이자율 4.6%) / 소득세법 §20 (상여처분 시 근로소득)

② **법령·통계 근거**: 적용 법령 — 법인세법 시행규칙 §43 (인정이자율 4.6%) / 소득세법 §20 (상여처분 시 근로소득)

③ **4자관점 교차 분석**:
법인(익금산입방지), 주주(소득세추가부담최소화), 과세관청(인정이자정산), 금융기관(재무구조영향)

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
| 정확도 | 95%+ (4.6% 이자 계산 오류 0건) |
| 응답시간 | 30~45초 |
| 평균 토큰 | 4,000~6,000 |

---
*보정 필요 항목: 1개 — D+18~19 사용자 검토 필요*

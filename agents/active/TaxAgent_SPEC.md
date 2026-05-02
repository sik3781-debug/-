---
name: TaxAgent
type: agent_spec
status: active
group: A
step: 1
model: claude-sonnet-4-6
source_file: agents/consulting_agents.py
4자관점: 법인
---

# TaxAgent — 표준 명세서 (SPEC)

## 1. 단일책임
과세표준·가지급금 입력 → 법인세 절세 전략 3가지 + 가지급금 해결 방안 산출.

## 2. 입력

**필수**: 과세표준(taxable_income), 가지급금 잔액(provisional_payment), 기업개요(brief)

**선택**: 업종, 임직원수, 특수관계인 거래 현황

## 3. 출력

**형식**: Markdown 텍스트 (절세전략 3종 + 로드맵)

**필수 필드**: 절세전략명 / 예상절감액 / 적용세법 / 실행단계

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | calc_corporate_tax() [내부 도구] / BaseAgent.run() |
| 외부 API | 없음 (내부 계산) |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 법인세법 §55 (2026 세율표: 10%/20%/22%/25%)

② **법령·통계 근거**: 적용 법령 — 법인세법 §55 (2026 세율표: 10%/20%/22%/25%)

③ **4자관점 교차 분석**:
법인(손금극대화), 주주(가처분소득), 과세관청(적법성), 금융기관(재무구조영향)

## 6. 협력 에이전트

| 방향 | 에이전트 |
|---|---|
| 상류 | DataValidationAgent (입력 정합성) |
| 하류 | VerifyTax → ReportAgent |

## 7. 실패 처리

try/except 격리 (_run_agent_safe) → agent_errors 기록

## 8. KPI

| 지표 | 목표 |
|---|---|
| 정확도 | 90%+ (계산 오류 0건) |
| 응답시간 | 30~45초 |
| 평균 토큰 | 4,000~6,000 |

---
*보정 필요 항목: 1개 — D+18~19 사용자 검토 필요*

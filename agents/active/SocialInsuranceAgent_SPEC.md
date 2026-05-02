---
name: SocialInsuranceAgent
type: agent_spec
status: active
group: G
step: 3
model: claude-sonnet-4-6
source_file: agents/social_insurance_agent.py
4자관점: 법인
---

# SocialInsuranceAgent — 표준 명세서 (SPEC)

## 1. 단일책임
임직원 수·업종 입력 → 4대보험 두루누리 지원 + 보험료 절감 방안 + 사업주 부담 최적화.

## 2. 입력

**필수**: 임직원수(employees), 업종(industry), 연매출(revenue)

**선택**: 급여 수준별 인원, 신규 채용 계획

## 3. 출력

**형식**: Markdown 텍스트 (보험료 절감 시뮬레이션)

**필수 필드**: 현재보험료 / 절감가능액 / 두루누리해당여부 / 신청방법

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 (향후 고용보험EDI 연동 예정) |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 고용보험법 §19 / 국민연금법 §88 / 두루누리사회보험료지원사업 운영지침

② **법령·통계 근거**: 적용 법령 — 고용보험법 §19 / 국민연금법 §88 / 두루누리사회보험료지원사업 운영지침

③ **4자관점 교차 분석**:
법인(보험료비용절감), 주주(없음), 과세관청(4대보험신고적정성), 금융기관(없음)

## 6. 협력 에이전트

| 방향 | 에이전트 |
|---|---|
| 상류 | DataValidationAgent |
| 하류 | VerifyOps → ReportAgent |

## 7. 실패 처리

try/except 격리 → agent_errors 기록

## 8. KPI

| 지표 | 목표 |
|---|---|
| 정확도 | [보정필요] |
| 응답시간 | 30~45초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 3개 — D+18~19 사용자 검토 필요*

---
name: InsuranceAgent
type: agent_spec
status: active
group: B
step: 1
model: claude-sonnet-4-6
source_file: agents/insurance_agent.py
4자관점: 주주
---

# InsuranceAgent — 표준 명세서 (SPEC)

## 1. 단일책임
대표이사 나이·승계 계획 입력 → CEO 유고 리스크 헷지 + 임원 퇴직금 재원 보험 설계 + D&O 보험 진단.

## 2. 입력

**필수**: 대표이사나이(ceo_age), 연매출(revenue), 총자산(total_assets)

**선택**: 현재 보험 가입 현황, 임원 수

## 3. 출력

**형식**: Markdown 텍스트 (리스크별 보험 설계안)

**필수 필드**: 보험유형 / 보장금액 / 손금처리여부 / 우선순위

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.run() |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 법인세법 §24 (보험료 손금), 보험업법

② **법령·통계 근거**: 적용 법령 — 법인세법 §24 (보험료 손금), 보험업법

③ **4자관점 교차 분석**:
법인(CEO리스크헷지), 주주(상속재원마련), 과세관청(보험료손금인정), 금융기관(신용보강효과)

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

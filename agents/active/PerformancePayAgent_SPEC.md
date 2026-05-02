---
name: PerformancePayAgent
type: agent_spec
status: active
group: G
step: 3
model: claude-sonnet-4-6
source_file: agents/performance_pay_agent.py
4자관점: 법인
---

# PerformancePayAgent — 표준 명세서 (SPEC)

## 1. 단일책임
임직원 현황·업종 입력 → 세법상 손금 인정 성과급 구조 설계 + 이익참가형 vs 목표달성형 비교.

## 2. 입력

**필수**: 임직원수(employees), 순이익(net_income), 업종(industry)

**선택**: 임직원별 직급·연봉, 기존 성과급 규정

## 3. 출력

**형식**: Markdown 텍스트 (성과급 구조 설계안)

**필수 필드**: 성과급유형 / 지급기준 / 손금인정여부 / 세부담비교

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 법인세법 §26 (인건비 손금) / 근로기준법 §43

② **법령·통계 근거**: 적용 법령 — 법인세법 §26 (인건비 손금) / 근로기준법 §43

③ **4자관점 교차 분석**:
법인(인건비손금극대화), 주주(핵심인재유지), 과세관청(성과급손금요건), 금융기관(없음)

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

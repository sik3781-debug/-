---
name: ExecutivePayAgent
type: agent_spec
status: active
group: E
step: 1
model: claude-sonnet-4-6
source_file: agents/executive_pay_agent.py
4자관점: 주주
---

# ExecutivePayAgent — 표준 명세서 (SPEC)

## 1. 단일책임
대표이사 연봉·근속연수·퇴직금 규정 유무 입력 → 퇴직금 손금 한도 산출 + 퇴직소득세 계산 + 급여·배당·퇴직금 3가지 시나리오 비교.

## 2. 입력

**필수**: 대표이사연봉(ceo_salary), 근속연수(ceo_tenure), 퇴직금규정유무(retirement_pay_provision), 대표나이(ceo_age)

**선택**: 3년 평균 급여 명세

## 3. 출력

**형식**: Markdown 텍스트 (3시나리오 비교표 + 최적 믹스 추천)

**필수 필드**: 손금한도액 / 퇴직소득세 / 3시나리오세후소득 / 최적보수믹스

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | calc_retirement_pay_limit() [내부 도구] / BaseAgent.run() |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 법인세법 시행령 §44② (3년평균×1/10×근속연수) / 소득세법 §22 (퇴직소득세) / §48 (근속연수공제)

② **법령·통계 근거**: 적용 법령 — 법인세법 시행령 §44② (3년평균×1/10×근속연수) / 소득세법 §22 (퇴직소득세) / §48 (근속연수공제)

③ **4자관점 교차 분석**:
법인(임원보수손금극대화), 주주(가처분소득극대화), 과세관청(부당행위계산부인), 금융기관(인건비비율)

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
| 정확도 | 95%+ (퇴직소득세 계산 오류 0건) |
| 응답시간 | 30~60초 |
| 평균 토큰 | 4,000~6,000 |

---
*보정 필요 항목: 1개 — D+18~19 사용자 검토 필요*

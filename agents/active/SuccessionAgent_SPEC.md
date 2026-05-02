---
name: SuccessionAgent
type: agent_spec
status: active
group: A
step: 1
model: claude-sonnet-4-6
source_file: agents/consulting_agents.py
4자관점: 주주
---

# SuccessionAgent — 표준 명세서 (SPEC)

## 1. 단일책임
가업자산·업력·대표 나이 입력 → 가업상속공제 요건·한도 + 자녀법인 사전 승계 전략 산출.

## 2. 입력

**필수**: 업력(years_in_operation), 가업자산(business_value), 대표나이(ceo_age)

**선택**: 자녀 나이·지분 현황, 사전 증여 이력

## 3. 출력

**형식**: Markdown 텍스트 (시나리오별 공제 한도 + 실행 단계)

**필수 필드**: 공제한도 / 세부담비교 / 사전승계방안 / 사후관리의무

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | calc_inheritance_deduction() [내부 도구] / BaseAgent.run() |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 상증세법 §18의2 (가업상속공제 최대 600억, 10/20/30년 차등)

② **법령·통계 근거**: 적용 법령 — 상증세법 §18의2 (가업상속공제 최대 600억, 10/20/30년 차등)

③ **4자관점 교차 분석**:
법인(경영연속성), 주주(승계비용최소화), 과세관청(공제요건적법성), 금융기관(담보연속성)

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
| 정확도 | 90%+ |
| 응답시간 | 30~60초 |
| 평균 토큰 | 4,000~6,000 |

---
*보정 필요 항목: 2개 — D+18~19 사용자 검토 필요*

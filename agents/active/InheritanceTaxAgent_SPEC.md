---
name: InheritanceTaxAgent
type: agent_spec
status: active
group: F
step: 2
model: claude-sonnet-4-6
source_file: agents/inheritance_tax_agent.py
4자관점: 주주
---

# InheritanceTaxAgent — 표준 명세서 (SPEC)

## 1. 단일책임
상속 재산·가업상속공제 요건 입력 → 상속세 계산 + 가업상속공제 적용 + 사전 증여 합산 분석.

## 2. 입력

**필수**: company_data (상속재산·가업자산·업력 포함)

**선택**: 사전 증여 이력, 금융재산 상속공제 해당 여부

## 3. 출력

**형식**: Markdown 텍스트 (상속세 계산표 + 공제 최적화 방안)

**필수 필드**: 상속재산 / 공제총액 / 과세표준 / 상속세 / 가업상속공제적용여부

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) / _calc_inheritance_tax() [내부] |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 상증세법 §18의2 (가업상속공제 최대600억) / §13 (사전증여합산10년) / §18 (기초공제2억)

② **법령·통계 근거**: 적용 법령 — 상증세법 §18의2 (가업상속공제 최대600억) / §13 (사전증여합산10년) / §18 (기초공제2억)

③ **4자관점 교차 분석**:
법인(가업연속성), 주주(상속세부담최소화), 과세관청(공제요건·사후관리), 금융기관(상속재원조달)

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
| 정확도 | 95%+ (상속세 계산 오류 0건) |
| 응답시간 | 30~60초 |
| 평균 토큰 | 4,000~6,000 |

---
*보정 필요 항목: 1개 — D+18~19 사용자 검토 필요*

---
name: BusinessPlanAgent
type: agent_spec
status: active
group: D
step: 2
model: claude-sonnet-4-6
source_file: agents/business_plan_agent.py
4자관점: 법인
---

# BusinessPlanAgent — 표준 명세서 (SPEC)

## 1. 단일책임
기업 현황 데이터 입력 → 정책자금·투자유치·인증용 사업계획서 초안 자동 작성.

## 2. 입력

**필수**: company_data (전체 기업 데이터 dict)

**선택**: 사업계획서 유형 (정책자금/투자유치/기업인증), 목표 수혜 기관

## 3. 출력

**형식**: Markdown 텍스트 (사업계획서 초안)

**필수 필드**: 기업현황 / 사업목표 / 재무계획 / 기대효과

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: [보정필요: 정책자금 신청 요건 등]

② **법령·통계 근거**: 적용 법령 — [보정필요: 정책자금 신청 요건 등]

③ **4자관점 교차 분석**:
법인(자금조달), 주주(기업가치제고), 과세관청(없음), 금융기관(신용보강자료)

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
| 응답시간 | 60~120초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 4개 — D+18~19 사용자 검토 필요*

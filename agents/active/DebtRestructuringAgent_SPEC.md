---
name: DebtRestructuringAgent
type: agent_spec
status: active
group: H
step: 3
model: claude-sonnet-4-6
source_file: agents/debt_restructuring_agent.py
4자관점: 금융기관
---

# DebtRestructuringAgent — 표준 명세서 (SPEC)

## 1. 단일책임
총부채·이자율 입력 → 부채 구조조정 필요성 진단 + 채무 재조정·DES·출자전환 시나리오 + 금리 절감 방안.

## 2. 입력

**필수**: 총부채(total_debt), 이자비용 추정, 현금흐름

**선택**: 금융기관별 대출 현황, 기존 담보 내역

## 3. 출력

**형식**: Markdown 텍스트 (시나리오별 비교 + 권장 방안)

**필수 필드**: 현재이자부담 / 구조조정시나리오 / 금리절감효과 / 리스크

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 채무자회생법 §119 (회사정리계획) / 기업구조조정촉진법

② **법령·통계 근거**: 적용 법령 — 채무자회생법 §119 (회사정리계획) / 기업구조조정촉진법

③ **4자관점 교차 분석**:
법인(이자비용절감), 주주(자본잠식방지), 과세관청(채무면제이익익금산입), 금융기관(채권보전)

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
| 응답시간 | 45~90초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 4개 — D+18~19 사용자 검토 필요*

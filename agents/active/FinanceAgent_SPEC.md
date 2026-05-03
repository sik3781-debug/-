---
name: FinanceAgent
type: agent_spec
status: active
group: A
step: 1
model: claude-sonnet-4-6
source_file: agents/consulting_agents.py
4자관점: 법인
---

# FinanceAgent — 표준 명세서 (SPEC)

## 1. 단일책임
부채비율·유동비율 입력 → 재무구조 종합 진단 + 3단계 개선 로드맵 산출.

## 2. 입력

**필수**: 총부채(total_debt), 자기자본(total_equity), 유동자산(current_assets), 유동부채(current_liabilities)

**선택**: 담보자산, 금융기관별 대출 현황

## 3. 출력

**형식**: Markdown 텍스트 (진단등급 + 로드맵)

**필수 필드**: 부채비율 / 유동비율 / ROE / 개선방안 3단계

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | analyze_financial_ratios() [내부 도구] / BaseAgent.run() |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: [보정필요: 특정 법령 없음, 재무지표 기준 적용]

② **법령·통계 근거**: 적용 법령 — [보정필요: 특정 법령 없음, 재무지표 기준 적용]

③ **4자관점 교차 분석**:
법인(재무건전성), 주주(배당가능이익), 과세관청(과소자본세제), 금융기관(신용등급·담보가치)

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
| 응답시간 | 30~45초 |
| 평균 토큰 | 3,000~5,000 |

---
*보정 필요 항목: 2개 — D+18~19 사용자 검토 필요*


> **[법령 변경 자동 전파 2026-05-03]** 법인세법·시행령·시행규칙 §55 — 법인세율 1%p 환원 (2026년 귀속 사업연도~): 9→10%, 19→20%, 21→22%, 24→25% (impact: high)

> **[법령 변경 자동 전파 2026-05-03]** 법인세법·시행령·시행규칙 §55 — 법인세율 1%p 환원 (2026년 귀속 사업연도~): 9→10%, 19→20%, 21→22%, 24→25% (impact: high)
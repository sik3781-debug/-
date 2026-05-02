---
name: CashFlowAgent
type: agent_spec
status: active
group: C
step: 2
model: claude-sonnet-4-6
source_file: agents/cash_flow_agent.py
4자관점: 법인
---

# CashFlowAgent — 표준 명세서 (SPEC)

## 1. 단일책임
월 평균 매출·유동비율 입력 → 12개월 현금흐름 시뮬레이션 + 흑자도산 리스크 진단 + 운전자본 개선 방안.

## 2. 입력

**필수**: 월평균매출(revenue/12), 유동비율(current_ratio), 유동자산(current_assets), 유동부채(current_liabilities)

**선택**: 매출 계절성, 회수기간

## 3. 출력

**형식**: Markdown 텍스트 (12개월 CF 표 + 위험 신호)

**필수 필드**: 월별현금흐름 / 최소현금잔고 / 리스크월 / 개선방안

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.run() |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: [보정필요]

② **법령·통계 근거**: 적용 법령 — [보정필요]

③ **4자관점 교차 분석**:
법인(흑자도산방지), 주주(배당가능시점), 과세관청(현금흐름이상징후), 금융기관(상환능력판단)

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
| 응답시간 | 30~60초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 4개 — D+18~19 사용자 검토 필요*

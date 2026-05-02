---
name: ESGRiskAgent
type: agent_spec
status: active
group: C
step: 2
model: claude-sonnet-4-6
source_file: agents/esg_risk_agent.py
4자관점: 법인
---

# ESGRiskAgent — 표준 명세서 (SPEC)

## 1. 단일책임
임직원·업종·주요 고객사 입력 → E·S·G 항목별 리스크 점수 + 우선 개선 과제 + EU CBAM 대응 전략.

## 2. 입력

**필수**: 임직원수(employees), 업종(industry), 주요고객사(main_customers)

**선택**: 에너지 사용량, 탄소 배출 현황

## 3. 출력

**형식**: Markdown 텍스트 (E/S/G 점수표 + 개선 우선순위)

**필수 필드**: E점수 / S점수 / G점수 / CBAM적용여부 / 우선과제

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.run() |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 탄소중립기본법 / EU CBAM 규정 / 중대재해처벌법

② **법령·통계 근거**: 적용 법령 — 탄소중립기본법 / EU CBAM 규정 / 중대재해처벌법

③ **4자관점 교차 분석**:
법인(ESG공시리스크), 주주(기업가치장기), 과세관청(탄소세도입대비), 금융기관(ESG대출조건)

## 6. 협력 에이전트

| 방향 | 에이전트 |
|---|---|
| 상류 | 없음 |
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

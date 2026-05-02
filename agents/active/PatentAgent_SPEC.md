---
name: PatentAgent
type: agent_spec
status: active
group: B
step: 1
model: claude-sonnet-4-6
source_file: agents/patent_agent.py
4자관점: 법인
---

# PatentAgent — 표준 명세서 (SPEC)

## 1. 단일책임
R&D 지출·특허 수 입력 → R&D 세액공제 최적화 전략 + 기술보증기금 활용 + 특허권 법인 이전 방안 산출.

## 2. 입력

**필수**: R&D 지출(rd_expense), 특허 수(patents), 업종(industry)

**선택**: 연구개발비 명세, 기술등급

## 3. 출력

**형식**: Markdown 텍스트 (공제액 계산 + 전략)

**필수 필드**: 공제율 / 공제금액 / 기술보증 조건 / 이전 세부담

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.run() |
| 외부 API | 없음 (향후 특허청 API 연동 예정) |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 조세특례제한법 §10 (R&D 세액공제), §12 (기술이전 과세특례)

② **법령·통계 근거**: 적용 법령 — 조세특례제한법 §10 (R&D 세액공제), §12 (기술이전 과세특례)

③ **4자관점 교차 분석**:
법인(R&D손금극대화), 주주(특허이전절세), 과세관청(세액공제요건), 금융기관(기보보증가용성)

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

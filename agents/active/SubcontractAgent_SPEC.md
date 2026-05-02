---
name: SubcontractAgent
type: agent_spec
status: active
group: H
step: 3
model: claude-sonnet-4-6
source_file: agents/subcontract_agent.py
4자관점: 법인
---

# SubcontractAgent — 표준 명세서 (SPEC)

## 1. 단일책임
주요 고객사·업종 입력 → 하도급법 위반 리스크 진단 + 불공정 거래 조항 확인 + 하도급대금 보호 방안.

## 2. 입력

**필수**: 주요고객사(main_customers), 업종(industry)

**선택**: 하도급 계약서, 대금 지급 현황

## 3. 출력

**형식**: Markdown 텍스트 (위반 위험 목록 + 보호 방안)

**필수 필드**: 위반위험항목 / 위험도 / 법적제재 / 개선방안

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 하도급거래공정화법 §13 (하도급대금지급) / §8 (부당특약금지)

② **법령·통계 근거**: 적용 법령 — 하도급거래공정화법 §13 (하도급대금지급) / §8 (부당특약금지)

③ **4자관점 교차 분석**:
법인(하도급리스크관리), 주주(분쟁비용최소화), 과세관청(없음), 금융기관(미수채권리스크)

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
*보정 필요 항목: 4개 — D+18~19 사용자 검토 필요*

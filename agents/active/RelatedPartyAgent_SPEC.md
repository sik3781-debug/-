---
name: RelatedPartyAgent
type: agent_spec
status: active
group: G
step: 3
model: claude-sonnet-4-6
source_file: agents/related_party_agent.py
4자관점: 과세관청
---

# RelatedPartyAgent — 표준 명세서 (SPEC)

## 1. 단일책임
특수관계인 거래 현황 입력 → 부당행위계산 부인 리스크 정량화 + 안전항(Safe Harbor) 적용 가능성 + 시가 적정성 검토.

## 2. 입력

**필수**: company_data (특수관계인 거래 현황 포함)

**선택**: 거래 계약서, 시가 산정 근거

## 3. 출력

**형식**: Markdown 텍스트 (거래 유형별 위험도표 + 개선 방안)

**필수 필드**: 거래유형 / 위험도 / 안전항적용여부 / 시가조정방안

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 법인세법 §52 (부당행위계산부인) / 상증세법 §35~42 / 안전항: ±5% 또는 3억 기준

② **법령·통계 근거**: 적용 법령 — 법인세법 §52 (부당행위계산부인) / 상증세법 §35~42 / 안전항: ±5% 또는 3억 기준

③ **4자관점 교차 분석**:
법인(부당행위부인리스크), 주주(이익분여리스크), 과세관청(특수관계인거래검증), 금융기관(없음)

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
| 정확도 | 90%+ (±5% 안전항 계산 오류 0건) |
| 응답시간 | 30~60초 |
| 평균 토큰 | 3,000~5,000 |

---
*보정 필요 항목: 1개 — D+18~19 사용자 검토 필요*

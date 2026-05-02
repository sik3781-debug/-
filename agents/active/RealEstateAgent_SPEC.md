---
name: RealEstateAgent
type: agent_spec
status: active
group: B
step: 1
model: claude-sonnet-4-6
source_file: agents/real_estate_agent.py
4자관점: 주주
---

# RealEstateAgent — 표준 명세서 (SPEC)

## 1. 단일책임
부동산 자산 유형·가액 입력 → 법인 vs 개인 보유 세금 비교 + 공장 매각 최적화 + 임대차 리스크 분석.

## 2. 입력

**필수**: 부동산가액(real_estate.value), 부동산유형(real_estate.type)

**선택**: 취득가액, 보유기간, 임대차계약 현황

## 3. 출력

**형식**: Markdown 텍스트 (법인vs개인 세부담 비교표 + 전략)

**필수 필드**: 법인세부담 / 개인세부담 / 매각타이밍 / 임대차리스크

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.run() |
| 외부 API | 없음 (향후 공시지가 API 연동 예정) |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 법인세법 §55 / 소득세법 §104 (양도소득세) / 지방세법 §7 (취득세)

② **법령·통계 근거**: 적용 법령 — 법인세법 §55 / 소득세법 §104 (양도소득세) / 지방세법 §7 (취득세)

③ **4자관점 교차 분석**:
법인(부동산과다법인회피), 주주(매각차익최적화), 과세관청(양도세·취득세), 금융기관(담보평가변동)

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
| 응답시간 | 30~60초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 3개 — D+18~19 사용자 검토 필요*

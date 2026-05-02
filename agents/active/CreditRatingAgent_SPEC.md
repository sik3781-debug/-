---
name: CreditRatingAgent
type: agent_spec
status: active
group: C
step: 2
model: claude-sonnet-4-6
source_file: agents/credit_rating_agent.py
4자관점: 금융기관
---

# CreditRatingAgent — 표준 명세서 (SPEC)

## 1. 단일책임
부채비율·유동비율·영업이익률·이자보상배율 입력 → 신용등급 추정 + 등급 상승을 통한 금리 절감 전략.

## 2. 입력

**필수**: 부채비율(debt_ratio), 유동비율(current_ratio), 영업이익률(operating_margin), 이자보상배율(interest_coverage)

**선택**: 기존 금융기관 등급, 신용보증 이력

## 3. 출력

**형식**: Markdown 텍스트 (등급 추정 근거 + 개선 전략)

**필수 필드**: 추정등급 / 산출근거 / 등급상승방안 / 금리절감효과

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.run() |
| 외부 API | [보정필요: ECOS_API 연동 여부] |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 은행업감독업무시행세칙 (내부등급법 참고)

② **법령·통계 근거**: 적용 법령 — 은행업감독업무시행세칙 (내부등급법 참고)

③ **4자관점 교차 분석**:
법인(금리절감), 주주(기업가치상승), 과세관청(없음), 금융기관(여신심사기준직접연관)

## 6. 협력 에이전트

| 방향 | 에이전트 |
|---|---|
| 상류 | DataValidationAgent |
| 하류 | PolicyFundingAgent / VerifyStrategy → ReportAgent |

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

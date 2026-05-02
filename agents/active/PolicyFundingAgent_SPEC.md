---
name: PolicyFundingAgent
type: agent_spec
status: active
group: C
step: 2
model: claude-sonnet-4-6
source_file: agents/policy_funding_agent.py
4자관점: 금융기관
---

# PolicyFundingAgent — 표준 명세서 (SPEC)

## 1. 단일책임
부채비율·임직원·업종 입력 → 신청 가능 정책자금·바우처·기업인증 혜택을 금리·한도와 함께 제시.

## 2. 입력

**필수**: 부채비율(debt_ratio), 임직원수(employees), 업종(industry)

**선택**: 정책자금 이력, 기업인증 현황

## 3. 출력

**형식**: Markdown 텍스트 (기관별 정책자금 매칭 표)

**필수 필드**: 기관 / 상품명 / 한도 / 금리 / 신청요건

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.run() |
| 외부 API | [보정필요: 중진공·기보·신보 API 연동 여부] |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 중소기업기본법 / 조세특례제한법 §7 (중소기업 특별세액감면)

② **법령·통계 근거**: 적용 법령 — 중소기업기본법 / 조세특례제한법 §7 (중소기업 특별세액감면)

③ **4자관점 교차 분석**:
법인(자금조달비용절감), 주주(금융부담완화), 과세관청(지원금익금산입여부), 금융기관(대출가용성확대)

## 6. 협력 에이전트

| 방향 | 에이전트 |
|---|---|
| 상류 | CreditRatingAgent (신용등급 참조) |
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

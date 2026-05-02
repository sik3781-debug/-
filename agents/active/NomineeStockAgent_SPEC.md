---
name: NomineeStockAgent
type: agent_spec
status: active
group: E
step: 1
model: claude-sonnet-4-6
source_file: agents/nominee_stock_agent.py
4자관점: 법인+주주
---

# NomineeStockAgent — 표준 명세서 (SPEC)

## 1. 단일책임
차명주식 수량·취득연도·현재 평가액 입력 → 명의신탁 증여의제 과세위험 정량화 + 4가지 해소 방법별 세부담 비교 + 최적 해소 전략.

## 2. 입력

**필수**: 차명주식수(nominee_shares), 취득연도(nom_acq_year), 액면가(nom_face_val), 현평가액(net_asset_per_share)

**선택**: 명의수탁자 관계, 기존 신고 여부

## 3. 출력

**형식**: Markdown 텍스트 (방법별 세부담표 + 제척기간 분석)

**필수 필드**: 증여의제세액 / 제척기간 / 4방법비교 / 권장방법 / 과점주주취득세경고

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | calc_deemed_gift_tax() [내부 도구] / BaseAgent.run() |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 상증세법 §45의2 (명의신탁 증여의제) / 국세기본법 §26의2 (제척기간 10/15년) / 지방세법 §7⑤

② **법령·통계 근거**: 적용 법령 — 상증세법 §45의2 (명의신탁 증여의제) / 국세기본법 §26의2 (제척기간 10/15년) / 지방세법 §7⑤

③ **4자관점 교차 분석**:
법인(주주명부정확성), 주주(형사·세무리스크), 과세관청(명의신탁적발가산세), 금융기관(과점주주취득세영향)

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
| 정확도 | 95%+ (제척기간 계산 오류 0건) |
| 응답시간 | 30~60초 |
| 평균 토큰 | 4,000~7,000 |

---
*보정 필요 항목: 1개 — D+18~19 사용자 검토 필요*

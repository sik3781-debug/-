---
name: StockAgent
type: agent_spec
status: active
group: A
step: 1
model: claude-sonnet-4-6
source_file: agents/consulting_agents.py
4자관점: 법인+주주
---

# StockAgent — 표준 명세서 (SPEC)

## 1. 단일책임
1주당 순자산가치·순손익가치 입력 → 보충적 평가액 + 주식 이동·차명주식 해소 전략 산출.

## 2. 입력

**필수**: 순자산가치(net_asset_per_share), 순손익가치(net_income_per_share), 업력(years_in_operation), 부동산비율

**선택**: 차명주식 수량, 취득연도

## 3. 출력

**형식**: Markdown 텍스트 (평가액 계산표 + 이동 시나리오)

**필수 필드**: 평가액 / 가중치 근거 / 절세 이동 시나리오

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | calc_unlisted_stock_value() [내부 도구] / BaseAgent.run() |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 상증세법 §54~56 (순손익3:순자산2 또는 부동산비율별 가중치)

② **법령·통계 근거**: 적용 법령 — 상증세법 §54~56 (순손익3:순자산2 또는 부동산비율별 가중치)

③ **4자관점 교차 분석**:
법인(주식가치관리), 주주(지분가치보전), 과세관청(보충적평가 적법성), 금융기관(담보평가영향)

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
| 정확도 | 95%+ (상증세법 공식 계산) |
| 응답시간 | 30~45초 |
| 평균 토큰 | 3,000~5,000 |

---
*보정 필요 항목: 1개 — D+18~19 사용자 검토 필요*

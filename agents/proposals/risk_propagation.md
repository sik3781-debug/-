---
name: risk_propagation
type: agent_spec
version: 1.0.0
status: active
source_file: agents/active/risk_propagation.py
---
# RiskPropagationAgent — 법령 변경 영향 자동 전파

## 1. 단일책임
LegalMonitoringHub 감지 결과 → 영향 에이전트 SPEC.md 자동 업데이트 + 변경 로그 기록.

## 2. 자동 전파 매핑 (5종)
| 법령 변경 | 영향 에이전트 | 업데이트 내용 |
|---|---|---|
| 법인세법 §55 (세율) | TaxAgent, FinanceAgent | 세율 파라미터 업데이트 |
| 상증세법 §54~56 (비상장 평가) | StockAgent, ValuationOptimizationAgent | 가중치·비율 업데이트 |
| 상증세법 §45의5 (특수관계 거래) | SpecialCorpTransactionAgent | 회피 전략 재산출 |
| 신탁법 개정 | CivilTrustAgent | 신탁 설계 패턴 업데이트 |
| 근로복지기본법 | CorporateBenefitsFundAgent | 복지기금 한도 업데이트 |

## 3. 업데이트 프로세스
1. `affected_agents` 목록 수신
2. 각 에이전트 SPEC.md의 `## 8. KPI` 이후에 영향 주석 추가
3. `storage/propagation_log.jsonl` 기록
4. 영향 에이전트 self_check 재실행 트리거

## 4. 롤백
propagation_log.jsonl에 이전 값 저장 → 24시간 이내 롤백 가능.

## 5. KPI
- 전파 정확도: 95%+
- 처리 시간: 5분 이내
- 토큰 사용: 3K 이하/건

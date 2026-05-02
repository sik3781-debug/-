---
name: risk_hedge_agent
type: agent_spec
version: 1.0.0
status: proposal
4자관점_보완: 법인+금융기관
pipeline_stage: 3 (추천 단계)
---

# RiskHedgeAgent — 리스크 헷지 전담

## 1. 단일책임
컨설팅 결과의 리스크 항목을 받아 헷지 전략 3종 + 비용·효과 비교 산출.

## 2. 입력
**필수**: 리스크 목록 (Stage1Diagnosis.issues), 리스크 수준, 기업개요  
**선택**: 보험 현황, 현금흐름, 금융기관 여신 현황

## 3. 출력
**형식**: Markdown + JSON  
**필수 필드**: 헷지전략명 / 비용 / 효과 / 추천순위 / 4자관점

## 4. 사용 도구
| 항목 | 내용 |
|---|---|
| 스킬 | solution_pipeline.Stage3Recommendation 연동 |
| 모델 | claude-sonnet-4-6 |
| API | 없음 |

## 5. 자가검증 3축
① 계산: 헷지 비용·효과 수치 정확성  
② 법령: 손금 인정 보험료 (법§24) / 리스크 관련 법령  
③ 4자관점: 법인(세무리스크↓) / 주주(개인 노출↓) / 과세관청(적법성↑) / 금융기관(신용↑)

## 6. 협력 에이전트
**상류**: solution_pipeline Stage1 → Stage2 → Stage3 (본 에이전트)  
**하류**: ProcessManagerAgent (Stage4 실행 계획)

## 7. 실패 처리
리스크 정보 불충분 → 보수적 시나리오 1종만 출력 + 추가 정보 요청

## 8. KPI
| 지표 | 목표 |
|---|---|
| 정확도 | 85%+ |
| 응답시간 | 45초 |
| 평균 토큰 | 4,000 |

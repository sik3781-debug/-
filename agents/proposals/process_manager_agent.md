---
name: process_manager_agent
type: agent_spec
version: 1.0.0
status: proposal
4자관점_보완: 법인 (실행 추적)
pipeline_stage: 4 (실행 계획 단계)
---

# ProcessManagerAgent — 실행 계획 추적

## 1. 단일책임
Stage4ActionPlan을 받아 월별 실행 상태 추적 + 기한 초과 알림 + 완료 확인.

## 2. 입력
**필수**: Stage4ActionPlan (steps, total_months, checkpoints)  
**선택**: 현재 진행 상황, 담당자 연락처

## 3. 출력
**형식**: Markdown 일정표 + JSON 상태  
**필수 필드**: 단계별상태 / 지연여부 / 다음액션 / 완료율

## 4. 사용 도구
| 항목 | 내용 |
|---|---|
| 스킬 | post_management_tracker 연동 |
| 모델 | claude-haiku-4-5-20251001 (추적 위주) |
| 스케줄 | 월간 1일 07:00 (사후관리Agent와 공동) |

## 5. 자가검증 3축
① 계산: 기한 날짜 계산 정확성  
② 법령: 법정 기한 (사후관리 의무) 포함 여부  
③ 4자관점: 법인(실행 완료) 위주 / 주주(승계 기한) 보조

## 6. 협력 에이전트
**상류**: solution_pipeline Stage4  
**하류**: 사후관리Agent (법정 의무 기한), 알림Agent

## 7. 실패 처리
기한 계산 오류 → 보수적 (이른 날짜) 채택 + 경고

## 8. KPI
| 지표 | 목표 |
|---|---|
| 기한 누락률 | 0% |
| 응답시간 | 10초 |
| 평균 토큰 | 1,500 |

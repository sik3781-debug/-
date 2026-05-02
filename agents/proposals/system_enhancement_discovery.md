---
name: system_enhancement_discovery
type: agent_spec
version: 1.0.0
status: active
4자관점_보완: 메타 (시스템 레벨)
schedule: 주간 월요일 09:00 자동
source_file: agents/active/discovery_agent.py
---

# SystemEnhancementDiscoveryAgent — 시스템 고도화 자동 발견

## 1. 단일책임
시스템 전체 주간 스캔 → 7가지 고도화 기회 자동 발견 + 우선순위(영향도×빈도×4자관점 가치) 산출.

## 2. 입력
**필수**: storage/error_patterns.jsonl + storage/kpi_metrics.jsonl + logs/*  
**선택**: 사용자 자연어 입력 이력 (logs/router.jsonl)

## 3. 출력
**형식**: junggi-workspace/discovery/discovery_report_YYYYMMDD.md + JSON  
**필수 필드**: 발견유형 / 건수 / 우선도 / 권장조치

## 4. 사용 도구
내부 분석 전용 (외부 API 없음) / 모델: Sonnet

## 5. 자가검증 3축
① 계산: 우선순위 점수 산식 (건수×가중치)  
② 법령: 신설 권고가 사용자 메모리 규칙 위반 안 함 (메타 검증)  
③ 4자관점: 발견 기회가 4자관점 중 어디에 기여하는지 분류

## 6. 협력 에이전트
**상류**: KPICollector (kpi_metrics.jsonl) + AutoFixAgent v2 (error_patterns.jsonl)  
**하류**: SystemEnhancementExecutorAgent

## 7. 실패 처리
분석 실패 시 다음 주기 대기 (재시도 안 함) / 로그만 기록

## 8. KPI
| 지표 | 목표 |
|---|---|
| 발견 정확도 | 80%+ |
| 실행시간 | 30분 이내 |
| 평균 토큰 | 10,000 |

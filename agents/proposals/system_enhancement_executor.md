---
name: system_enhancement_executor
type: agent_spec
version: 1.0.0
status: active
schedule: 주간 월요일 10:00 자동
source_file: agents/active/executor_agent.py
---

# SystemEnhancementExecutorAgent — 고도화 자동 실행

## 1. 단일책임
Discovery 보고서 → 권한 분류(자동/승인/차단) 후 고도화 실행 + git commit.

## 2. 입력
**필수**: discovery_report (Discovery 출력)  
**선택**: user_approval_fn (승인 콜백)

## 3. 출력
**형식**: JSON + git commit  
**필수 필드**: 실행상태 / 변경사항 / 커밋메시지

## 4. 실행 권한 분류
| 등급 | 항목 | 처리 |
|---|---|---|
| 🟢 자동 | KPI 보정, AutoFix 영구 적용, 성능 최적화 후보 | 즉시 실행 |
| 🟡 승인 | 신설 명령, 신설 에이전트, Sunset 확정 | 사용자 확인 후 |
| 🔴 차단 | 정본 CLAUDE.md, 핵심 에이전트, dotfiles | 실행 불가 |

## 5. 협력
**상류**: DiscoveryAgent / **하류**: VerifierAgent

## 6. KPI
실행 성공률 90%+ / 케이스당 5분 / 5K 토큰

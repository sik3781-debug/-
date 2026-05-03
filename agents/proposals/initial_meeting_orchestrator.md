---
name: initial_meeting_orchestrator
type: agent_spec
version: 1.0.0
status: active
source_file: agents/active/initial_meeting_orchestrator.py
---
# InitialMeetingOrchestrator — 초회 미팅 통합 처리

## 1. 단일책임
초회 미팅 자료(크레탑·등기부·재무제표) → PII 마스킹 → 프로필 → 5대 시뮬 자동 매칭 → 4단계 솔루션 → PPT 보고서.

## 2. 보강 7종 통합
1. PII 마스킹 강제 통과 / 2. 자가검증 3축 + AutoFix v2 / 3. 사후관리 자동 등록
4. PPTPolisher 예약 / 5. 5대 시뮬레이터 자동 매칭 / 6. 재무제표 PDF 파싱 / 7. Discovery DB 인식

## 3. KPI
처리시간 6분 이내 / 마스킹 정확도 100% / 시뮬레이터 매칭 정확도 85%+

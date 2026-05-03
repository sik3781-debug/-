---
name: korean_accounting_enforcer
type: agent_spec
version: 1.0.0
status: active
source_file: agents/active/korean_accounting_enforcer.py
---
# KoreanAccountingStandardsEnforcer — 한국 회계기준 강제
## 1. 단일책임
모든 에이전트 출력에서 US-GAAP 영문 용어 → 한국 표준 용어 50종 자동 치환 + K-IFRS·K-GAAP·SME 자동 분기.
## 4. 분기 로직
상장사→K-IFRS / 외감비상장→K-IFRS or K-GAAP / 중소기업→SME
## 8. KPI
정확도 100% / 3초 / 500토큰

---
name: corporate_registry_parser
type: agent_spec
version: 1.0.0
status: active
source_file: agents/active/corporate_registry_parser.py
---
# CorporateRegistryParser — 등기부등본 파싱
## 1. 단일책임
법인 등기부등본 텍스트 → 임원 현황·주주 구성·자본금 구조화 dict (PII 밀도 高 → PIIMasker 강제).
## 8. KPI
정확도 90%+ / 5초 / 2K 토큰

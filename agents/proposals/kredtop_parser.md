---
name: kredtop_parser
type: agent_spec
version: 1.0.0
status: active
source_file: agents/active/kredtop_parser.py
---
# KredTopParser — 크레탑 조회 결과 파싱
## 1. 단일책임
크레탑 텍스트 → 신용등급·매출3년·부채비율·임직원 구조화 dict (PIIMasker 강제 통과).
## 8. KPI
정확도 90%+ / 5초 / 2K 토큰

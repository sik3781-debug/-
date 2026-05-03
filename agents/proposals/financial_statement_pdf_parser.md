---
name: financial_statement_pdf_parser
type: agent_spec
version: 1.0.0
status: active
source_file: agents/active/financial_statement_pdf_parser.py
---
# FinancialStatementPDFParser — 재무제표 PDF 파싱
## 1. 단일책임
재무제표 PDF(외감보고서·결산서) 텍스트 → 매출·영업이익·순이익 3년 + 재무비율 구조화 + 주석 요약.
## 4. 사용 도구
Claude Read tool (PDF 파싱) + 정규식 구조화 / 모델: Sonnet
## 8. KPI
정확도 90%+ / 30초 / 5K 토큰

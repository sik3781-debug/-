# BusinessPlanAgent — `/사업계획서` (PART7 통합본)

정책자금·가업승계·기업인증·IPO 대비 5년 사업계획서 자동 생성.

✅ **PART7 통합 완료**: 구 `agents/business_plan_agent.py:BusinessPlanAgent` (LLM 기반 본문 생성, str 반환)는 deprecation re-export로 대체. 정식 단일화 클래스 `agents.active.business_plan_agent.BusinessPlanAgent` (5축·4단계·매트릭스 dict 반환). 슬래시 `/사업계획서` (정식) + `/사업계획서작성` (alias, v1.1.0/2026-11-04 자동 삭제).

## 핵심 기능
- 5년 매출·영업이익 추정 (낙관·중립·비관 3시나리오)
- BEP 산출 (CAPEX·고정비·공헌이익률 기반)
- 5년 ROI + 단순 회수기간
- 중소기업기본법§2 적격성 자동 판정
- 조특§6 창업중소기업 세액감면 분류 (수도권·청년)
- 정책자금 매칭 (신·기보·중진공·IBK)
- 벤처기업·이노비즈·메인비즈 인증 적격성
- SWOT 자동 생성
- purpose 분기 가이드 (정책자금/가업승계/IPO/기업인증)

## 핵심 법령
- 중소기업기본법 §2 (적격성 — 매출·자산 기준)
- 벤처기업법 §2의2 (벤처기업 인증 요건)
- 조특 §6 (창업중소기업 세액감면 5년 50~100%)
- 조특 §7 (중소기업 특별세액감면 5~30%)
- 자본시장법 §178 (부정거래·과장 금지) — 면책 워딩 강제
- 신·기보·중진공 신용평가 기준

## 5축 리스크 검증
| 축 | 검증 항목 |
|---|---|
| DOMAIN | 시나리오 3종 + BEP + SWOT |
| LEGAL | §178 + 중소기업기본법§2 본문 명시 |
| CALC | 낙관 ≥ 중립 ≥ 비관 정합성 |
| LOGIC | 부채비율 ↔ 정책자금 매칭 일관성 |
| CROSS | 4자×3시점 매트릭스 12셀 충족 |

## 4단계 헷지
- **사전**: DART/NICE 정합성 사전 검증 + 정책자금 사전상담
- **진행**: 추정 근거 명시 + 민감도 3시나리오 + §178 면책 워딩
- **사후**: 분기별 KPI 모니터링 + 차이 분석 + 사후관리 5년
- **최악**: §178 의혹 시 내부 회의록·근거 백업 + 정책자금 부실 시 즉시 상환

## 후속 세션 심화 권고
- DART 동종업종 비교 자동 호출 (DART_API_KEY 발급 후)
- 추정 손익계산서·재무상태표 정합 자동 검증 (대차 일치)
- 정책자금 매칭 산업·매출 규모 가중치 추가
- 추정재무제표 → pptx + xlsx 산출물 자동 생성
- 조특§7 중소기업 특별세액감면 실제 계산

## 사용 예
```python
from agents.active.business_plan_agent import BusinessPlanAgent
result = BusinessPlanAgent().analyze({
    "company_name": "가나산업", "industry": "제조업",
    "current_revenue": 5_000_000_000,
    "growth_rate_assumption": 0.15,
    "capex_plan": 2_000_000_000,
    "total_debt": 8_000_000_000, "total_equity": 3_500_000_000,
    "operating_margin": 0.10,
    "purpose": "정책자금",
    "years_in_operation": 4,
    "rd_expense": 200_000_000, "is_new_growth": True,
})
```

작성: 2026-05-04 [LAPTOP]

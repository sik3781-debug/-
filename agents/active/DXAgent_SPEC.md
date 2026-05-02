---
name: DXAgent
type: agent_spec
status: active
group: H
step: 3
model: claude-sonnet-4-6
source_file: agents/dx_agent.py
4자관점: 법인
---

# DXAgent — 표준 명세서 (SPEC)

## 1. 단일책임
업종·임직원·매출 입력 → DX 투자 우선순위 + 정부 DX 지원사업 연계 + ROI 추정.

## 2. 입력

**필수**: company_data 전체

**선택**: 현재 IT 인프라 수준, DX 예산

## 3. 출력

**형식**: Markdown 텍스트 (DX 로드맵 + ROI)

**필수 필드**: DX성숙도 / 우선투자영역 / 지원사업매칭 / ROI추정

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 중소기업 스마트제조혁신 지원사업 요건

② **법령·통계 근거**: 적용 법령 — 중소기업 스마트제조혁신 지원사업 요건

③ **4자관점 교차 분석**:
법인(운영효율화), 주주(기업가치제고), 과세관청(없음), 금융기관(DX담보가치없음)

## 6. 협력 에이전트

| 방향 | 에이전트 |
|---|---|
| 상류 | DataValidationAgent |
| 하류 | VerifyStrategy → ReportAgent |

## 7. 실패 처리

try/except 격리 → agent_errors 기록

## 8. KPI

| 지표 | 목표 |
|---|---|
| 정확도 | [보정필요] |
| 응답시간 | 45~90초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 4개 — D+18~19 사용자 검토 필요*

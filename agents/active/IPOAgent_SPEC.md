---
name: IPOAgent
type: agent_spec
status: active
group: H
step: 3
model: claude-sonnet-4-6
source_file: agents/ipo_agent.py
4자관점: 주주
---

# IPOAgent — 표준 명세서 (SPEC)

## 1. 단일책임
재무 현황·업종 입력 → IPO 적합성 진단 + 코스닥/코넥스 요건 비교 + 상장 준비 로드맵.

## 2. 입력

**필수**: company_data 전체 (매출·순이익·자기자본 중심)

**선택**: 주주 구성, 우리사주조합 현황

## 3. 출력

**형식**: Markdown 텍스트 (IPO 타당성 + 로드맵)

**필수 필드**: IPO타당성점수 / 상장요건충족여부 / 갭분석 / 준비로드맵

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 자본시장법 §390 (코스닥 상장 요건) / §391 (코넥스 요건)

② **법령·통계 근거**: 적용 법령 — 자본시장법 §390 (코스닥 상장 요건) / §391 (코넥스 요건)

③ **4자관점 교차 분석**:
법인(자본조달), 주주(지분가치실현), 과세관청(상장차익과세), 금융기관(상장이후금융가용성)

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

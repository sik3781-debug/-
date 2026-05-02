---
name: FranchiseAgent
type: agent_spec
status: active
group: H
step: 3
model: claude-sonnet-4-6
source_file: agents/franchise_agent.py
4자관점: 법인
---

# FranchiseAgent — 표준 명세서 (SPEC)

## 1. 단일책임
업종·매출 입력 → 프랜차이즈 확장 타당성 + 가맹사업법 컴플라이언스 + 세금 구조 설계.

## 2. 입력

**필수**: company_data 전체

**선택**: 현재 매장 수, 가맹 계약서

## 3. 출력

**형식**: Markdown 텍스트 (타당성 진단 + 법적 구조)

**필수 필드**: 프랜차이즈타당성 / 가맹사업법위반위험 / 세금구조 / 확장로드맵

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.analyze(company_data) |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 가맹사업법 §2 / §11 (정보공개서등록) / §12 (허위정보제공금지)

② **법령·통계 근거**: 적용 법령 — 가맹사업법 §2 / §11 (정보공개서등록) / §12 (허위정보제공금지)

③ **4자관점 교차 분석**:
법인(사업확장), 주주(수익다각화), 과세관청(가맹금수익과세), 금융기관(브랜드담보가치)

## 6. 협력 에이전트

| 방향 | 에이전트 |
|---|---|
| 상류 | DataValidationAgent |
| 하류 | VerifyOps → ReportAgent |

## 7. 실패 처리

try/except 격리 → agent_errors 기록

## 8. KPI

| 지표 | 목표 |
|---|---|
| 정확도 | [보정필요] |
| 응답시간 | 30~60초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 4개 — D+18~19 사용자 검토 필요*

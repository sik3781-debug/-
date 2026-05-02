---
name: MAValuationAgent
type: agent_spec
status: active
group: C
step: 2
model: claude-sonnet-4-6
source_file: agents/ma_valuation_agent.py
4자관점: 주주
---

# MAValuationAgent — 표준 명세서 (SPEC)

## 1. 단일책임
당기순이익·EBITDA·총부채 입력 → DCF·PER·EV/EBITDA 3가지 방법론으로 기업가치 산출 + 외부 매각/투자유치 적정 가치 범위 제시.

## 2. 입력

**필수**: 순이익(net_income), EBITDA(추정), 총부채(total_debt), 총자산(total_assets)

**선택**: 비교군 PER, 업종 EV/EBITDA 배수

## 3. 출력

**형식**: Markdown 텍스트 (3방법론 비교표 + 권장 가치 범위)

**필수 필드**: DCF가치 / PER가치 / EV/EBITDA가치 / 최종권장범위

## 4. 사용 도구

| 항목 | 내용 |
|---|---|
| 스킬·도구 | BaseAgent.run() |
| 외부 API | 없음 |
| 모델 | claude-sonnet-4-6 |

## 5. 자가검증 3축

① **계산 정확성**: 상증세법 §54 (보충적평가) / 자본시장법 (공정가액 기준)

② **법령·통계 근거**: 적용 법령 — 상증세법 §54 (보충적평가) / 자본시장법 (공정가액 기준)

③ **4자관점 교차 분석**:
법인(매각가치극대화), 주주(투자회수), 과세관청(시가과세), 금융기관(담보가치참고)

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
| 응답시간 | 45~60초 |
| 평균 토큰 | [보정필요] |

---
*보정 필요 항목: 3개 — D+18~19 사용자 검토 필요*

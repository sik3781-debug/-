---
name: legal_monitoring_hub
type: agent_spec
version: 1.0.0
status: active
source_file: agents/active/legal_monitoring_hub.py
---
# LegalMonitoringHub — 법령 통합 모니터링 허브

## 1. 단일책임
8종 법령·판례 변경 사항 일간 탐지 → 영향도 산출 → 하류 에이전트 자동 전파.

## 2. 입력
- 스케줄: 일간 06:00 자동
- 도구: LAW_API_ID (D+16 활성화) + memory 캐시 (오프라인 폴백)

## 3. 모니터링 대상 (8종)
| 코드 | 법령명 | 핵심 조문 |
|---|---|---|
| CIT | 법인세법·시행령·시행규칙 | §55 세율, §28 가지급금 |
| PIT | 소득세법 | §22 퇴직소득, §89 비과세 |
| IPT | 상속세및증여세법 | §18의2 가업상속, §54~56 비상장, §45의5 |
| STX | 조세특례제한법 | R&D 세액공제, 중소기업 특례 |
| BTA | 국세기본법 | 경정청구, 제척기간 |
| COM | 상법 | §341 자기주식, §360의 분할 |
| LAB | 근로기준법 | 퇴직금, 연장수당 |
| LTX | 지방세법 | 취득세, 법인지방소득세 |

## 4. 출력
```json
{
  "date": "2026-05-03",
  "changes_detected": 2,
  "items": [
    {
      "law_code": "CIT",
      "article": "§55",
      "change_type": "rate_change",
      "description": "법인세율 1%p 환원 (2026 귀속~)",
      "impact_level": "high",
      "affected_agents": ["TaxAgent", "FinanceAgent", "ValuationOptimizationAgent"]
    }
  ],
  "propagation_status": "triggered"
}
```

## 5. 자가검증 (3항목)
- 인용 조문 실재 확인 (memory 캐시 대조)
- 시행일 명시 여부
- 4자관점 영향 분류 (법인/주주/과세관청/금융기관)

## 6. 협력
- 상류: scheduler (일간 06:00)
- 하류: RiskPropagationAgent, HistoricalCaseImpactAgent

## 7. 오프라인 모드
LAW_API_ID 미등록 시 memory/law_cache/*.json 캐시 참조.
캐시 없음 → 변경 없음(no_change) 반환 (오류 발생 금지).

## 8. KPI
- 법령 누락률: 0%
- 응답 시간: 30분 이내
- 토큰 사용: 5K 이하/일

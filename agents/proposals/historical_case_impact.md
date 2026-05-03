---
name: historical_case_impact
type: agent_spec
version: 1.0.0
status: proposal
source_file: agents/active/historical_case_impact.py
---
# HistoricalCaseImpactAgent — 기존 사례 법령 영향 점검

## 1. 단일책임
법령 변경 감지 시 memory/cases/*.json 내 기존 컨설팅 사례와 교차 분석 →
영향 케이스 자동 식별 + 컨설턴트 재검토 권고 알림 자동 생성.

## 2. 컨설턴트 부가가치 시나리오
- "ABC제약 가업승계 컨설팅 → 상증§18의2 개정으로 공제 한도 변경 → 재설계 권고"
- "DEF물산 가지급금 해소 → 법§28 인정이자율 변경 → 이자 재산출 필요"
- "GHI산업 이익잉여금 → 조특§99의7 일몰 연장 → 절세 기회 추가 발생"

## 3. 입력
- 법령 변경 보고 (LegalMonitoringHub)
- memory/cases/ — 고객사별 케이스 파일

## 4. 출력
```json
{
  "law_change": "상증세법 §54 비상장주식 평가",
  "affected_cases": [
    {
      "case_id": "CASE-001",
      "company": "(주)ABC",
      "consulting_type": "가업승계",
      "impact": "주식가치 5% 상승 예상",
      "recommended_action": "재평가 후 이전 시기 재검토",
      "urgency": "high"
    }
  ],
  "notification_sent": true
}
```

## 5. 알림 규칙
- urgency=high: 즉시 알림 (storage/notifications.jsonl 기록)
- urgency=medium: 주간 보고서에 포함
- urgency=low: 월간 검토 목록에 추가

## 6. 프라이버시
- 고객사명 등 PII → PIIMaskingAgent 전처리 필수
- 외부 전송 금지 (내부 memory만 참조)

## 7. KPI
- 영향 식별 정확도: 90%+
- 처리 시간: 30분 이내
- 토큰 사용: 10K 이하/건
- 스케줄: 주간 화요일 09:00

## 8. 의존성
- 상류: LegalMonitoringHub
- 도구: PIIMaskingAgent
- 저장소: memory/cases/, storage/notifications.jsonl

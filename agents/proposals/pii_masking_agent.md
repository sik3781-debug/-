---
name: pii_masking_agent
type: agent_spec
version: 1.0.0
status: active
4자관점_보완: 보안 (법인·과세관청)
source_file: agents/active/pii_masking_agent.py
---

# PIIMaskingAgent — 개인정보 마스킹 전담

## 1. 단일책임
모든 파서 출력에서 개인정보(PII) 자동 마스킹 + 원본 격리 보관.

## 2. 입력
**필수**: 파싱된 raw 데이터 (dict/list/str)  
**선택**: store_original (기본 True), source_label (로그용)

## 3. 출력
마스킹된 dict + `_pii_report` 키:
```json
{
  "masked_count": 5,
  "patterns_found": ["rrn", "biz", "mobile"],
  "original_hash": "abc123def456",
  "original_path": ".secrets/raw/abc123def456.json"
}
```

## 4. 마스킹 대상

| 유형 | 패턴 | 치환 |
|---|---|---|
| 주민등록번호 | `\d{6}-\d{7}` | `######-#######` |
| 사업자등록번호 | `\d{3}-\d{2}-\d{5}` | `***-**-*****` |
| 휴대폰 | `01[016789]-?\d{3,4}-?\d{4}` | `010-****-****` |
| 일반전화 | `0\d{1,2}-\d{3,4}-\d{4}` | `**-****-****` |
| 계좌번호 | `\d{3,6}-\d{2,6}-\d{2,6}` | `***-***-******` |
| 여권번호 | `[A-Z][MF]\d{7}` | `M*******` |
| 개인 주소 | 시·구 이하 | `서울시 강남구 ***` |

## 5. 사용 도구
Regex 패턴 매칭 (외부 API 없음) / 모델: claude-haiku-4-5-20251001

## 6. 자가검증 3축
① 마스킹 정확도: scan_only() 재실행 → masked_count == 0 확인  
② 법령: 개인정보보호법 §29, §24 준수  
③ 4자관점: 법인(법적리스크 ↓) / 과세관청(자료 보안 ↑)

## 7. 협력 에이전트
**모든 파서 → PIIMaskingAgent → 다음 단계** (강제 통과)

## 8. KPI
| 지표 | 목표 |
|---|---|
| 마스킹 정확도 | 100% (오탐 0건) |
| 응답시간 | 5초 이내 |
| 평균 토큰 | 1,000 |

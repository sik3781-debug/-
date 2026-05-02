# proposals/ — 신설 에이전트 6종 명세

## 신설 의도: 4자관점 매트릭스 완성

기존 ACTIVE 37개 에이전트는 **법인·주주(오너)** 관점에 집중되어 있었으며,
**과세관청** 관점은 보통, **금융기관** 관점은 약함 수준이었다.

신설 6종은 이 불균형을 해소하고 운영효율(산출물 품질·진입 컨텍스트)을 강화한다.

```
4자관점 완성도: 70% → 90%
시스템 에이전트 수: 37 ACTIVE → 43 ACTIVE
```

---

## 신설 6종 목록

| 파일 | 에이전트명 | 보완 관점 | 모델 |
|---|---|---|---|
| credit_rating_estimator.md | 신용등급추정Agent | **금융기관** | Sonnet |
| court_case_monitor.md | 판례모니터링Agent | **과세관청** | Haiku |
| post_management_tracker.md | 사후관리Agent | **법인+주주** | Sonnet |
| client_context_loader.md | 고객사컨텍스트Agent | **운영효율** | Haiku |
| ppt_polisher.md | PPTPolisherAgent | **산출물 품질** | Haiku |
| tax_audit_responder.md | 세무조사대응Agent | **법인+과세관청** | Opus |

---

## 우선순위

### Top 1: 신용등급추정Agent (credit_rating_estimator)
**이유**: 금융기관 관점이 전체 시스템에서 가장 취약한 영역.
정책자금 매칭 5종과 연동 시 즉각적 고객 가치 창출.
**D+18 구현 목표**

### Top 2: 판례모니터링Agent (court_case_monitor)
**이유**: 과세관청 관점 보완 + 일간 자동화로 운영 부담 0.
기존 컨설팅 사례의 유효성을 자동 재검토하는 핵심 인프라.
**D+18 구현 목표**

### Top 3: 세무조사대응Agent (tax_audit_responder)
**이유**: 법인+과세관청 복합 관점의 최고 난이도 에이전트.
Opus 모델 필요 — D+19 구현 목표

---

## D+18~19 작업 분할 (부담 50% 감소 목표)

### D+18 (8~9시간 → 4~5시간)
| 작업 | 예상 시간 | 비고 |
|---|---|---|
| credit_rating_estimator 구현 | 2h | ECOS_API 연동 필요 |
| court_case_monitor 구현 | 1.5h | Haiku + 스케줄러 |
| client_context_loader 구현 | 1h | memory/ 검색 |
| ppt_polisher 구현 | 0.5h | python-pptx 활용 |

### D+19 (8시간 → 4시간)
| 작업 | 예상 시간 | 비고 |
|---|---|---|
| post_management_tracker 구현 | 1.5h | 날짜 계산 정확성 중요 |
| tax_audit_responder 구현 | 2h | Opus + 판례 연동 |
| 통합 테스트 + PART 2 명세 검토 | 0.5h | - |

---

## 통합 후 에이전트 수

```
37 ACTIVE (기존) + 6 신설 = 43 ACTIVE
```

(이전 Sunset 6종 격리 유지 — proposals/sunset/ 별도 보관)

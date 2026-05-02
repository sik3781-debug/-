---
name: enhancement_verifier
type: agent_spec
version: 1.0.0
status: active
schedule: 주간 월요일 10:30 자동 (Executor 30분 후)
source_file: agents/active/verifier_agent.py
---

# EnhancementVerifierAgent — 회귀 검증 + 자동 롤백

## 1. 단일책임
Executor 적용 후 시스템 회귀 검증 (기능·성능·안정성 3축) → 회귀 발견 시 자동 git revert.

## 2. 검증 3축
| 축 | 내용 | 기준 |
|---|---|---|
| functional | 5대 시뮬레이터 라우터 매칭 | 5/5 통과 |
| performance | KPI 7일 평균 | ±20% 이내 |
| stability | AutoFix DB 중복·충돌 | 0건 |

## 3. 회귀 발견 시 처리
1. git revert HEAD (자동)
2. Discovery DB에 "실패 패턴" 학습 (재추천 방지)
3. 사용자 보고 (왜 실패, 대안 제안)

## 4. KPI
검증 정확도 95%+ / 30분 / 5K 토큰

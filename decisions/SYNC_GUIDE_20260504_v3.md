# SYNC_GUIDE_20260504_v3 — PART8 4단계 동기화 안내

**작성**: 2026-05-04 [LAPTOP] / **소요시간**: 약 5~10분 / **이전**: SYNC_GUIDE_v2 (PART7)

## 0. 핵심 변경 사항 요약 (4단계)

### Stage 1 — Phase B 3건 분리 유지 결정 + 잔재 제거
- `/신용등급추정` proposal 완전 삭제 (`/신용등급분석` 단일화 + 트리거 흡수)
- `/재무구조개선·분석`, `/특수관계거래·인검증` scope 메타 추가 + 트리거 정밀화
- 자연어 매칭 6/6 100%
- `_meta.total_commands`: 81 → 80 (proposal 1건 삭제)

### Stage 2 — PART8 자가 진화 3종 수리
- `SystemEnhancementDiscoveryAgent.analyze()` wrapper 추가
- `SystemEnhancementExecutorAgent.analyze()` wrapper 추가 (user_approval_fn=None)
- `EnhancementVerifierAgent.analyze()` wrapper 추가
- 3종 모두 5축·4단계 헷지·12셀 매트릭스·4축 자가검증 ALL PASS

### Stage 3 — CHAT_MODE 보고서 3종 생성
- `outputs/CHAT_MODE_REPORT_20260504.md` (~2,500자, 본 채팅창 회신용)
- `outputs/CHAT_MODE_DETAIL_20260504.md` (~7,000자, 상세 자료)
- `outputs/CHAT_MODE_FILES_LIST_20260504.md` (GitHub URL 목록)

### Stage 4 — 자가 진화 7/7 ALL PASS
- 직전 PART7: 4/7 (Discovery·Executor·Verifier 실패)
- 현재 PART8: **7/7 (100%)**
- 자가 진화 시스템 건강도 회복 완료

### Stage 5 — 동기화 인프라 (본 파일)

## 1. 1줄 동기화 명령

```powershell
cd $env:USERPROFILE\consulting-agent; git pull origin main
cd $env:USERPROFILE\junggi-workspace; git pull origin main
cd $env:USERPROFILE\consulting-agent; .\bootstrap\sync_from_remote.ps1
```

## 2. 동기화 검증 체크리스트

### 2-1. git pull
- [ ] consulting-agent main pull --ff-only OK
- [ ] junggi-workspace main pull --ff-only OK

### 2-2. UTF-8 BOM (PART8 갱신 파일)
- [ ] `agents/active/discovery_agent.py`
- [ ] `agents/active/executor_agent.py`
- [ ] `agents/active/verifier_agent.py`

### 2-3. 자가 진화 7/7 ALL PASS
- [ ] 7종 schtasks 모두 등록 + 즉시 trigger 시 7/7 정상
- [ ] Discovery: "발견 기회 N건 — TOP: ..."
- [ ] Executor: "자동 N / 대기 N / 차단 N"
- [ ] Verifier: "status=PASS"
- [ ] 나머지 4종 (Daily, WeeklyDigest, MonthlyConsolidate, QuarterlyDiagnostic) 정상

### 2-4. 라우터 + Phase B 결정
- [ ] 라우터 총 80개 명령 로드 (81에서 -1)
- [ ] /신용등급추정 직접 입력 시 no_match (잔재 제거 확인)
- [ ] 자연어 매칭 6/6 100%

## 3. 트러블슈팅

### 3-1. 자가 진화 일부 실패 시
- 로그 확인: `Get-Content -Encoding Unicode "$env:USERPROFILE\junggi-workspace\logs\scheduler\<task>_20260504.log"`
- 3종 분석 wrapper가 정상인지: `python -c "from agents.active.discovery_agent import SystemEnhancementDiscoveryAgent; print(SystemEnhancementDiscoveryAgent().analyze({})['summary'])"`

### 3-2. PART8 commit 누락 의심 시
- `git -C ~/consulting-agent log --oneline | grep PART8`
- 정상 commit: `1ea3a3c fix: PART8 Stage 2 — 자가 진화 3종 analyze() 메서드 구현`

### 3-3. /신용등급추정 잔재 검사
```powershell
Get-ChildItem -Recurse -Include *.py,*.md,*.json -ErrorAction SilentlyContinue | 
    Select-String -Pattern "credit_rating_estimator|신용등급추정" -SimpleMatch | 
    Where-Object { $_.Path -notmatch "settings.local.json|decisions/" }
```
→ decisions/* (history 보존) 외에는 0건이어야 정상

## 4. 백업 정보

- 브랜치: `backup-4stage-20260504091944` (양 레포)
- 태그: `rollback-before-4stage-20260504091944` (양 레포)
- 복원: `git checkout backup-4stage-20260504091944`

## 5. 함정·리스크 1세트

1. **(해결)** 자가 진화 3종 `analyze()` 미구현 → PART8 Stage 2에서 수리 완료
2. **(주의)** decisions/* 이력 문서에 `/신용등급추정` 언급 일부 잔존 — 의사결정 history 보존 목적이므로 의도적 유지
3. **(미래)** v1.1.0 분기(2026-11-04) 시 `/사업계획서작성` alias 자동 삭제 + total_commands 80→79

## 6. 사용자 다음 행동 가이드

### 본 채팅창(claude.ai) 회신
- `outputs/CHAT_MODE_REPORT_20260504.md` 내용 복사·붙여넣기

### 사용자 메모리 갱신 (선택)
- 본 채팅창에 "PART8 4단계 결과를 사용자 메모리에 반영해줘" 요청

### 다음 세션 권장 우선순위
1. **자가 진화 D+5 재가동 + 누적 결과 분석**
2. **PART6 4종 도메인 깊이 심화** (RnDLabNotebook DOI / BusinessPlan DART / LegalRisk NLP / LegalDoc 25종 양식)
3. **API 4종 발급 후 통합 기능 활성화** (DART·LAW·ECOS·PUBLIC)

작성: 2026-05-04 [LAPTOP] (PART8 4단계) / 차기 SYNC_GUIDE: PART9 작업 시점

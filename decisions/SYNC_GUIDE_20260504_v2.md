# SYNC_GUIDE_20260504_v2 — 4중 통합 (PART7) 동기화 안내

**작성**: 2026-05-04 [LAPTOP] / **소요시간**: 약 5~10분 / **이전**: SYNC_GUIDE_20260504.md (PART6)

## 0. 핵심 변경 사항 요약 (4중 통합)

### Phase A — BusinessPlan 통합 (이미지 옵션 B 하이브리드)
- `agents/active/business_plan_pro.py` → `agents/active/business_plan_agent.py` (`git mv`)
- 클래스명 `BusinessPlanProAgent` → `BusinessPlanAgent`
- 구 `agents/business_plan_agent.py` → DeprecationWarning re-export (v1.1.0/2026-11-04 자동 삭제)
- `/사업계획서` 정식 단일화 (primary: true)
- `/사업계획서작성` alias 등록 (alias_of: /사업계획서, 6개월 후 삭제)
- `orchestrator.py` import 통일 + ACTIVE_AGENTS_REGISTRY 갱신 + dict 호환 처리 추가
- Pro 잔재 0건 검증 완료 (settings.local.json 제외)

### Phase B — 전 영역 중복 통합 진단 (자동 0건 + 승인요청 3건)
- 81개 슬래시 11대 영역 자동 분류 완료
- 5축 자동 판정 결과 자동 통합 0건 (모든 3축↑ 후보가 정통 컨설팅 영향 큼)
- 승인 요청 3건:
  - **①** `/재무구조개선` vs `/재무구조분석` (보완관계, 통합 시 정통 LLM 파이프라인 영향)
  - **②** `/신용등급분석` vs `/신용등급추정` (추정은 status=proposal 미구현)
  - **③** `/특수관계거래` vs `/특수관계인검증` (결정론 vs LLM 보완관계)

### Phase C — 자가 진화 즉시 가동 결과
- 7/7 schtasks 정상 trigger
- 4/7 정상 실행: DailyTaskClassify, WeeklyDigest, MonthlyConsolidate, QuarterlyDiagnostic
- **3/7 실패** — Discovery·Executor·Verifier의 `analyze()` 메서드 미구현 (자가 진화 시스템 설계 결함)
  - `SystemEnhancementDiscoveryAgent.analyze()` 없음
  - `SystemEnhancementExecutorAgent.analyze()` 없음
  - `EnhancementVerifierAgent.analyze()` 없음
  - **별도 후속 작업으로 사용자 승인 필요** (본 task scope 벗어남)

### Phase D — 양 레포 push (본 세션 commit hash 추가 필요)

---

## 1. 동기화 실행 — 1줄 명령

```powershell
cd $env:USERPROFILE\consulting-agent; git pull origin main
cd $env:USERPROFILE\junggi-workspace; git pull origin main
cd $env:USERPROFILE\consulting-agent; .\bootstrap\sync_from_remote.ps1
```

⚠ **주의**: consulting-agent GitHub repo 이름이 `-` (dash 1글자) → 1줄 iwr 사용 시:
```powershell
iwr -useb "https://raw.githubusercontent.com/sik3781-debug/-/main/bootstrap/sync_from_remote.ps1" -OutFile "$env:TEMP\sync.ps1"; powershell -File "$env:TEMP\sync.ps1"
```

---

## 2. 동기화 검증 체크리스트

### 2-1. git pull
- [ ] consulting-agent main pull --ff-only OK
- [ ] junggi-workspace main pull --ff-only OK

### 2-2. UTF-8 BOM (PART7 갱신 파일)
- [ ] `agents/active/business_plan_agent.py` (rename + Pro 제거)
- [ ] `agents/business_plan_agent.py` (deprecation re-export)
- [ ] `agents/proposals/business_plan_agent.md` (rename + Pro 제거)
- [ ] `bootstrap/sync_from_remote.ps1` (path 갱신)
- [ ] `decisions/SYNC_GUIDE_20260504_v2.md` (본 파일)
- [ ] `orchestrator.py` (import + REGISTRY + dict 호환)

### 2-3. 7종 schtasks (자가 진화)
- [ ] 7/7 등록 확인
- [ ] **3/7 analyze() 미구현 — 별도 후속 작업 권고** (본 sync 후 결정)

### 2-4. 환경변수 (선택)
- [ ] ANTHROPIC_API_KEY (필수 — LLM 호출 시)
- [ ] DART_API_KEY · LAW_API_ID · ECOS_API_KEY · PUBLIC_DATA_API_KEY (선택)

### 2-5. 라우터 + 통합 후 슬래시
- [ ] 라우터 총 81개 명령 로드
- [ ] /사업계획서 100% auto_route → BusinessPlanAgent (정식)
- [ ] /사업계획서작성 100% auto_route → BusinessPlanAgent (alias_of)
- [ ] PART6 4종 + PART5.7 5종 + PART7 통합본 5축·4단계·12셀 ALL PASS

---

## 3. 트러블슈팅

### 3-1. DeprecationWarning 발생
구 `agents.business_plan_agent.BusinessPlanAgent` import 시 정상 출력. 향후 코드는:
```python
from agents.active.business_plan_agent import BusinessPlanAgent  # 정식
```

### 3-2. 자가 진화 3종 (Discovery/Executor/Verifier) 실패
- 원인: agents/active/discovery_agent.py 등에 `analyze()` 메서드 미구현
- 임시: 본 sync에서는 4/7만 정상 작동. 3/7은 별도 후속 작업으로 PART8에서 수리 권고
- 본 sync 자체는 정상 종료 (failure-tolerant)

### 3-3. orchestrator.py BusinessPlanAgent dict 결과 처리
PART7 통합으로 `analyze()`가 dict 반환. orchestrator의 `_run_agent_safe`가 자동으로 `dict.text` 추출 + `agent._last_analysis_dict`에 metadata 보존.

### 3-4. Pro 잔재 의심 시
```powershell
Get-ChildItem -Recurse -Include *.py,*.md,*.json,*.ps1 -ErrorAction SilentlyContinue | 
    Select-String -Pattern "BusinessPlanPro|business_plan_pro|사업계획서Pro" -SimpleMatch | 
    Where-Object { $_.Path -notmatch "settings.local.json" }
```
→ 결과 0건이어야 정상

---

## 4. 백업 정보

본 4중 통합 작업 전 백업:
- 브랜치: `backup-quad-merge-20260504084816` (양 레포)
- 태그: `rollback-before-quad-merge-20260504` (양 레포)

비상 시 복원:
```powershell
git -C $env:USERPROFILE\consulting-agent checkout backup-quad-merge-20260504084816
git -C $env:USERPROFILE\junggi-workspace checkout backup-quad-merge-20260504084816
```

---

## 5. 함정·리스크 1세트

### 발견된 함정·리스크
1. **(중요)** 자가 진화 핵심 3종 에이전트(Discovery/Executor/Verifier)에 `analyze()` 미구현 — 자가 진화 시스템 미가동 상태. PART8 별도 후속 작업으로 처리 권고
2. **(함정)** consulting-agent GitHub 레포 이름이 `-` (dash 1글자) → iwr URL 작성 시 주의
3. **(리스크)** Phase B 자동 통합 0건 — 안전성 우선이나, 향후 사용자 의사결정으로 3건 통합 검토 필요
4. **(리스크)** PART7 통합으로 구 LLM 기반 사업계획서 본문 생성 능력은 deprecated. 후속 세션에서 narrative 메서드 보강 권고

### 다음 컨설턴트 이용 시 주의사항
- `/사업계획서`와 `/사업계획서작성`은 동일 결과 (alias). 가급적 `/사업계획서` 사용 권장
- 자가 진화 4/7만 정상 — Discovery/Executor/Verifier 결과는 신뢰 X (수리 후 재가동)
- API 4종 발급 후 추가 기능 활성화 가능

### v1.1.0 분기 시 (2026-11-04) 추가 작업
- `agents/business_plan_agent.py` (deprecation re-export) 완전 삭제
- `command_router.json`의 `/사업계획서작성` alias 항목 삭제
- `_meta.total_commands` 81 → 80 갱신

---

## 6. 사용자 다음 행동 가이드

### 본 채팅창(claude.ai)에 회신할 핵심 내용
- ✅ Phase A BusinessPlan 통합 완료 (Pro 잔재 0건)
- ✅ Phase B 5축 판정 완료 (자동 0건 + 승인요청 3건)
- ⚠️ Phase C 4/7 정상 + 3/7 자가 진화 핵심 에이전트 수리 필요
- ✅ Phase D 양 레포 push 완료

### 다음 세션 우선 작업 권고
1. **자가 진화 3종 수리** (Discovery/Executor/Verifier `analyze()` 메서드 추가) — 우선순위 1
2. **Phase B 승인 요청 3건 의사결정** — 우선순위 2
3. **API 4종 발급 후 통합 기능 활성화**
4. **PART6 4종 도메인 깊이 심화** (각 에이전트별 후속 보강 항목)

### 자가 진화 결과 점검 (D+5 권장)
- 자가 진화 3종 수리 완료 후 다시 trigger
- 7/7 정상 가동 확인 후 D+28 시점 누적 결과 분석

---

작성: 2026-05-04 [LAPTOP] (PART7 통합) / 차기 SYNC_GUIDE: PART8 자가 진화 수리 시점

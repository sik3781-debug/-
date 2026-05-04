# SYNC_GUIDE_20260504 — 3대 기기 동기화 안내

**작성일**: 2026-05-04 [LAPTOP] / **대상 기기**: 집A·사무실B / **소요시간**: 약 5~10분

## 0. 핵심 변경 사항 요약

본 동기화로 다음 사항이 집A·사무실B에 반영됩니다:

### 작업 1 — 누적 활성화 검증 (5종)
- 5개 핵심 에이전트(`/사내복지기금` `/민사신탁` `/특수관계거래` `/자기주식전략` `/미처분이익잉여금`) 등록 완료 확인 (직전 fa8bf12 push)

### 작업 2 — 신규 4종 에이전트 (PART6)
- `/연구노트` (RnDLabNotebookAgent, sonnet) — 직무발명·R&D 입증
- `/사업계획서` (BusinessPlanAgent, opus) — 정책자금·가업승계·인증
- `/법률리스크체크` (LegalRiskHedgeAgent, opus) — 5대 영역 리스크 정량화
- `/법무서류` (LegalDocumentDrafterAgent, sonnet) — 7종 표준 양식
- 4종 모두 5축 검증 + 4단계 헷지 + 3중 루프 + 4자×3시점 매트릭스 ALL PASS

### 작업 3 — 메타 갱신
- `_meta.total_commands` 77 → 81
- `orchestrator.py` ACTIVE_AGENTS_REGISTRY 추가

---

## 1. 동기화 실행 — 1줄 명령

⚠ **중요**: consulting-agent 레포 GitHub URL은 `sik3781-debug/-` (repo명이 dash 1글자). 1줄 iwr 사용 시 정확한 raw URL 사용:

```powershell
iwr -useb "https://raw.githubusercontent.com/sik3781-debug/-/main/bootstrap/sync_from_remote.ps1" -OutFile "$env:TEMP\sync.ps1"; powershell -File "$env:TEMP\sync.ps1"
```

또는 (권장) **로컬 git pull 후 직접 실행**:

```powershell
cd $env:USERPROFILE\consulting-agent; git pull origin main
cd $env:USERPROFILE\junggi-workspace; git pull origin main
cd $env:USERPROFILE\consulting-agent; .\bootstrap\sync_from_remote.ps1
```

스크립트 옵션:
- `-SkipSchtasks` — schtasks 검사 건너뜀
- `-SkipSmokeTest` — 4종 에이전트 smoke test 건너뜀

---

## 2. 동기화 검증 체크리스트

`sync_from_remote.ps1` 실행 후 다음 모두 [OK]가 나와야 정상:

### 2-1. git pull
- [ ] consulting-agent main pull --ff-only OK
- [ ] junggi-workspace main pull --ff-only OK

### 2-2. UTF-8 BOM (5개 신규 파일)
- [ ] `agents/active/rnd_lab_notebook.py` BOM 확인
- [ ] `agents/active/business_plan_agent.py` BOM 확인
- [ ] `agents/active/legal_risk_hedge.py` BOM 확인
- [ ] `agents/active/legal_document_drafter.py` BOM 확인
- [ ] `bootstrap/sync_from_remote.ps1` BOM 확인

### 2-3. 7종 schtasks (자가 진화)
- [ ] JunggiDailyTaskClassify
- [ ] JunggiDiscovery
- [ ] JunggiExecutor
- [ ] JunggiMonthlyConsolidate
- [ ] JunggiQuarterlyDiagnostic
- [ ] JunggiVerifier
- [ ] JunggiWeeklyDigest

### 2-4. 환경변수 (선택 — 사용자 발급 필요)
- [ ] ANTHROPIC_API_KEY (필수 — LLM 호출 시)
- [ ] DART_API_KEY (선택 — DART 동종업종 비교)
- [ ] LAW_API_ID (선택 — 판례 자동 검색)
- [ ] ECOS_API_KEY (선택 — 한국은행 통계)
- [ ] PUBLIC_DATA_API_KEY (선택 — 공공데이터)

### 2-5. 라우터 + 4종 신규 에이전트
- [ ] 라우터 총 81개 명령 로드
- [ ] /연구노트 100% auto_route
- [ ] /사업계획서 100% auto_route
- [ ] /법률리스크체크 100% auto_route
- [ ] /법무서류 100% auto_route
- [ ] 4종 모두 5축·4단계·4축자가·매트릭스 ALL PASS

---

## 3. 트러블슈팅

### 3-1. 한글 경로 인식 실패
```powershell
# OEM 인코딩 → UTF-8 임시 전환
chcp 65001
```

### 3-2. UTF-8 BOM 누락 시
sync 스크립트가 자동 추가하지만, 수동 변환은:
```powershell
$path = "agents/active/rnd_lab_notebook.py"
$bytes = [System.IO.File]::ReadAllBytes($path)
$bom = [byte[]](0xEF, 0xBB, 0xBF)
if ($bytes[0] -ne 0xEF) {
    [System.IO.File]::WriteAllBytes($path, $bom + $bytes)
}
```

### 3-3. master 브랜치 잔재
```powershell
git branch -m master main
git fetch origin
git branch --set-upstream-to=origin/main main
git pull --ff-only
```

### 3-4. ANTHROPIC_API_KEY 미설정 시 BaseAgent 임포트 오류
- analyze() 호출은 API 키 없이 정상 작동 (lazy init)
- run() 호출 시에만 API 키 필요
- 영구 설정: `setx ANTHROPIC_API_KEY "sk-ant-..."`

### 3-5. python 모듈 import 실패
- `cd $env:USERPROFILE\consulting-agent` 위치에서 실행
- `pip install anthropic` 사전 설치 확인

---

## 4. 자가 진화 첫 가동 (내일 09:00) 사전 점검

### 4-1. 7종 schtasks × 3대 = 21개 등록 상태
각 기기에서 sync 스크립트의 §3 출력으로 확인. 미등록 시 setup.ps1 재실행 권장.

### 4-2. 새 에이전트(PART6 4종)의 자가 진화 진입
- command_router.json에 81개 모두 등록됨 → JunggiDailyTaskClassify 자동 인식
- JunggiDiscovery가 agents/active/ 새 .py 자동 스캔 → 신규 4종 발견 가능
- JunggiVerifier가 5축·4단계 자동 재검증 일정 등록 (내일 09:00 첫 가동 시 확인)

### 4-3. 5축·4단계 헷지·3중 루프 자동 재검증
- 본 sync 스크립트의 §5 smoke test가 4종 모두 ALL PASS 확인
- 내일 09:00 자동 가동 시 결과 점검: `schtasks /Query /TN JunggiVerifier /V`

---

## 5. 함정·리스크 1세트

### 발견된 함정·리스크
- **(함정 1)** consulting-agent 레포 이름이 `-` (dash 1글자) → 1줄 iwr URL 사용 시 주의
- **(함정 2)** ANTHROPIC_API_KEY 미설정 상태 — analyze() 호출은 정상이나 run() 호출 시 KeyError. 4종 에이전트는 BaseAgent.__init__ 우회 패턴으로 회피
- **(리스크 1)** BusinessPlanAgent 클래스명 — 기존 agents/business_plan_agent.py:BusinessPlanAgent 와 충돌 회피 위해 Pro 접미사
- **(리스크 2)** orchestrator.py ACTIVE_AGENTS_REGISTRY는 임포트만, _build_agent_map에는 미등록 — 정통 orchestrator.run() 실행 시 자동 호출 안 됨 (의도)

### 다음 컨설턴트 이용 시 주의사항
- 4종 신규 에이전트는 **base level** — 도메인 깊이 심화는 후속 세션 권장
- API 4종 발급 후 추가 기능 활성화 가능 (DART·LAW·ECOS·PUBLIC)
- 영업비밀·위·변조 의혹 시 본 자료를 즉시 변호사·법무사 검토

### 4종 신규 에이전트의 알려진 한계
| 에이전트 | 현재 base level | 후속 심화 권고 |
|---|---|---|
| 연구노트 | SHA-256 해시 + ISO-8601 | DOI API 통합 + 블록체인 타임스탬프 + 발명자 기여도 알고리즘 |
| 사업계획서 | 5년 매출·BEP·SWOT·정책자금 매칭 | DART API + 추정재무제표 정합 검증 + pptx/xlsx 자동 산출물 |
| 법률리스크체크 | 13종 룰북 + 정량화 | NLP 기반 텍스트 자동 하이라이트 + 판례 검색 + 양형 가중·감경 |
| 법무서류 | 7종 표준 양식 + 인지세·등록면허세 자동 | 25종 확장 + 등기 신청서 자동 + 신주발행 차등 등록면허세 |

---

## 6. 사용자 다음 행동 가이드

### 본 채팅창(claude.ai)에 회신할 핵심 내용
- 4종 신규 에이전트 ALL PASS 확인 + 81개 명령 라우팅
- API 4종 발급 일정 (D+19~20 권장)
- v1.0.0 정식 릴리스 시점 결정 (rc1 → 정식 승격 여부)

### 다음 세션 진행 권장 작업
- 4종 에이전트 도메인 심화 (위 §5 표 기준 우선순위 선택)
- API 4종 발급 후 자동 호출 통합
- Cowork PDF 업로드 파이프라인 실측 (D+20)
- 7종 schtasks × 3대 = 21개 통합 모니터링 대시보드

### 자가 진화 첫 가동 결과 점검 시점 (D+28+)
- 내일 09:00 자가 진화 첫 가동 — 결과는 D+28+ (기록 누적 후) 점검
- `JunggiVerifier` 로그 확인: `Get-WinEvent -LogName Microsoft-Windows-TaskScheduler/Operational | Where-Object Id -in @(200,201,329)`

---

작성: 2026-05-04 [LAPTOP] / 차기 SYNC_GUIDE: PART7 작업 시점

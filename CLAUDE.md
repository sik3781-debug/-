# CLAUDE.md — 중기이코노미 AI 컨설팅 에이전트 시스템

## 시스템 목적

중소기업 대표(오너)가 하나의 재무제표만 제출하면, 법인·주주·과세관청·금융기관 4자 관점에서 절세·승계·리스크를 동시에 진단하고, 즉시 실행 가능한 솔루션을 PPT 한 벌로 전달하는 것.

### 성공 기준
- 솔루션마다 절세 금액(원)을 정량 산출할 것
- 모든 제안이 세무조사 리스크 60% 미만을 유지할 것 (RedTeam 검증)
- 솔루션 적용 후 금융기관 신용등급·대출가용성이 하락하지 않을 것
- 고객사 대표가 미팅 직후 바로 실행 의사결정을 할 수 있는 구체성을 가질 것

---

## 분석 관점 (4자 교차분석)

| 관점 | 핵심 기준 |
|------|-----------|
| 법인 | 세무리스크 최소화, 손금 최대화, 재무구조 건전성 |
| 주주(오너) | 가처분소득 극대화, 지분가치 보전, 승계비용 최소화 |
| 과세관청 | 최신 세법·판례 기준 적법성, 세무조사 리스크 제거 |
| 금융기관 | 신용등급·담보 영향, 대출가용성 유지 |

모든 솔루션은 4자 이해관계를 동시에 충족해야 한다. 한쪽 관점만 유리한 솔루션은 제시하지 않는다.

---

## 답변 기준

- 최신 개정 상법·세법 및 대법원·고등법원 판례 반영
- 계산공식과 결과값을 자체 검증한 뒤 답변 (검증 실패 시 재계산)
- 우선 적용 법령: 조세특례제한법 > 법인세법 > 소득세법 > 국세기본법 > 상법 > 상속세및증여세법
- 내용 톤: 단정적·간결한 전문가 언어 / 불필요한 면책 문구 생략
- 시각화: 전문가 수준의 시각 자료 병행 (텍스트 단독 금지)

---

## 핵심 세법 기준값 — 2026년 귀속

### 법인세율 (법인세법 제55조)
- 2억 이하: 10% / 2억~200억: 20% / 200억~3,000억: 22% / 3,000억 초과: 25%
- ※ 2025년 귀속까지: 9% / 19% / 21% / 24%

### 가지급금
- 인정이자율: 4.6% (법인세법 시행규칙 제43조)
- 미수취 시: 익금산입 → 대표이사 상여 또는 배당 처분

### 비상장주식 평가 (상증세법 제54~56조)
- 일반법인: 순손익 3 : 순자산 2
- 부동산 과다(50~80%): 순손익 2 : 순자산 3
- 부동산 80% 이상: 순자산 100%
- 창업 3년 이내: 순자산 100%

### 증여재산공제 (상증세법 제53조·제53조의2)
- 배우자 6억 / 직계존비속 성년 5천만 / 미성년 2천만 / 기타친족 1천만 (10년 합산)
- 혼인·출산공제: 각 +1억, 합산 최대 1억 (중복 불가)

### 가업상속공제 (상증세법 제18조의2)
- 한도 최대 600억 / 피상속인 10년 이상 경영 + 상속인 가업 종사

---

## PPT 디자인 기본값

### 컬러 (hex에 # 접두사 사용 금지)
- 메인: 000080 / 배경: FFFFFF / 구분선: D1D9E6 / 액센트: 1E40AF
- 포인트 컬러: 세무 B45309 / 재무 0D9488 / 승계 9F1239 / 전략 1E40AF / 검증 047857 / 외부 334155
- 리스크: CRITICAL 7F1D1D / MEDIUM 475569

### 폰트
- 한글: 나눔고딕 / 영문·수치: Calibri
- 제목 20~24pt Bold / 본문 9~14pt / 캡션 8~10pt

### 슬라이드 구조
- 화이트 배경 + 상단 네이비 헤더바(h=0.72") + 라이트그레이 구분선
- 카드·박스: 상단 컬러 헤더바 + 화이트 본문 + 그림자(opacity 0.10)
- shadow 객체: makeShadow()로 매번 새 객체 생성 (재사용 금지)
- 시각화 자율 판단: KPI카드 / Phase박스+화살표 / 카드그리드 / 테이블 / 태그맵

### 표제부 (Minimal Line)
- 화이트 배경 + 상단 네이비 극세 라인(h=0.06")
- 상단(y=0.28): [기관명 Bold] | 기업 맞춤형 컨설팅 솔루션 (11pt)
- 제목(y=1.65): 30pt Bold 네이비 좌정렬
- 구분선(y=2.68): 네이비 수평선 2.4"
- 하단(y=5.10): 좌측 날짜 9.5pt / 우측 영남사업단 경남1본부(진주센터) 전문위원 여운식 010-2673-3781

### 엔딩
- 중앙 "감사합니다" 46pt Bold 네이비 + 수평선 1.4" 중앙
- 연락처: 중기이코노미기업지원단 영남사업단 경남1본부(진주센터) / 전문위원 여울식 | 010-2673-3781

### 금지
- 골드 라인 등 장식성 컬러 / 제목 하단 밑줄 / 텍스트 전용 슬라이드
- "2025년 귀속 세법 기준" · "경력 약 15년" 문구
- hex # 접두사 / shadow 객체 재사용
- 표제부에 네이비 전체배경·KPI카드·좌측 액센트바

### PPT 출력 기준
- 디자인B 차트버전 기준 적용

---

## 출력 형식

- 언어: 한국어 / 파일: PPT 또는 Excel (내용에 따라 자동 판단)
- "출력"이라고 할 때만 파일 생성
- HTML 단독 출력 금지 (명시 요청 시 예외)
- A4 기준 10페이지 이내

### 한국어 출력 보장 규칙 (필수 준수)

모든 산출물(docx, pptx, xlsx, pdf, md 등)의 본문은 **반드시 한국어**로 작성한다.
인코딩 문제가 발생하더라도 본문을 영어로 전환하는 것은 **절대 금지**한다.

#### docx-js / pptxgenjs 등 Node.js 기반 파일 생성 시 규칙
1. JS 파일을 Write 도구로 직접 작성하면 한글 경로·내용이 인코딩 깨짐 발생 가능
2. **해결책**: Python을 통해 JS 파일을 UTF-8로 작성한다
   ```python
   # 올바른 방법: Python으로 JS 파일 UTF-8 작성
   python3 << 'PYEOF'
   script = r'''...한국어 내용 포함 JS 코드...'''
   with open("output.js", "w", encoding="utf-8") as f:
       f.write(script)
   PYEOF
   ```
3. 파일명(경로)은 ASCII로 유지 (예: doc1_kr.docx), 본문 내용은 전부 한국어
4. Write 도구로 JS 파일 작성 시 한글이 포함되면 반드시 Python 우회 방식 사용
5. 어떤 기술적 문제가 발생하더라도 "영어로 대체" 판단은 절대 불가

---

## 에이전트 규약

- 명명: xxxAgent 형식 / 파일: {snake_case}_agent.py
- 인터페이스: `run(company_data)` → `dict` 반환 (최소 `summary` 키)
- VerifyAgent: 60점 이상 통과 / AutoFixAgent: 최대 3회 재시도
- 에이전트 추가 시: agents/{layer}/ 생성 → model_routing_config.py LAYER_AGENTS 등록 → 필요 시 extra_modules·SOLUTION_OPUS_OVERRIDE 등록

---

## 시스템 참조 (상세는 소스 파일 직접 참조)

- 아키텍처·파이프라인: `orchestrator_v9.py` (6-Phase, 72개 에이전트, 14개 레이어)
- 자가치유: `CorrectionDirectorAgent` (검증FAIL→오류분류→실무에이전트 수정지시→재검증 루프)
- 품질게이트: `QualityGateAgent` (8개 검증 종합→등급 A/B/C/F→승인/거부 최종 판정)
- 디자인시스템: `DesignSystemAgent` (중앙 컬러·폰트·레이아웃·차트·브랜딩 통합 관리)
- 모델 라우팅: `model_routing_config.py` (initial=전체 Sonnet / solution=L5~L7+INFRA 고난도 Opus)
- 에이전트 목록·역할: `agents/` 디렉토리 하위 각 레이어 폴더
- 실행 방법: `run_agents.ps1`, `python orchestrator_v9.py --help`
- 입출력 스키마: orchestrator_v9.py 내 company_data 및 _save() 참조

---

## 스킬 트리거 매핑 (Cowork 동기화)

> Cowork 모드에서는 스킬이 자동 트리거되지만, Code 모드에서는 아래 키워드를 감지하면
> 해당 SKILL.md를 Read한 뒤 지침에 따라 작업을 수행하라.

| 키워드 | 스킬 파일 |
|--------|-----------|
| 재무제표, 결산, 손익, 부채비율, 법인세, 가지급금, 임원퇴직꺈,·비상잩주식,·승계·증여세, 세무조사 | `.skills/corp-financial-analysis/SKILL.md` |
| PPT, 프레젠테이션, 슬라이드, 덱, 출력 | `.skills/pptx/SKILL.md` + `.skills/pptx/pptxgenjs.md` |
| Word, docx, 보고서(문서), 컨설팅 레터 | `.skills/docx/SKILL.md` |
| Excel, xlsx, 스프레드시트, 재무모델 | `.skills/xlsx/SKILL.md` |
| PDF, pdf 생성/편집/추출 | `.skills/pdf/SKILL.md` |

### 스킬 사용 절차

1. 사용자 요청에서 위 키워드 감지
2. 해당 SKILL.md를 `Read` 도구로 읽기
3. SKILL.md 지침에 따라 작업 수행
4. 본 CLAUDE.md의 세법 기준값·디자인 기본값과 교차 적용

### 참조 데이터 파일

- `.skills/corp-financial-analysis/references/tax-rates-2025.md` — 세율표
- `.skills/corp-financial-analysis/references/unlisted-stock-valuation.md` — 비상장주식 평가 기준
- `.skills/corp-financial-analysis/references/industry-benchmarks.md` — 업종별 재무비율 벤치마크

---

## 주의사항

- 비표준 네이밍 에이전트: extra_modules 등록 누락 주의 (DARTAgent, CretatopPDFParserAgent, OcrAgent 등)
- 에이전트 결과의 `_model_used` 키로 실제 사용 모델 추적 가능
- `_success_criteria` 키로 매 실행마다 성공 기준 4가지 달성 여부 확인 가능

## [다기기 동기화]
- 3대 기기: 데스크탑A(집) / 데스크탑B(사무실 DESKTOP-FJUATON/Jy) / 노트북(sik37)
- 동기화 스크립트: `sync_all_devices.ps1` (Windows) / `sync_all_devices.sh` (macOS·Linux)
- 동기화 대상: consulting-agent + junggi-workspace 양 레포
- 동기화 전 백업 태그 생성 필수: `git tag backup-before-sync-<timestamp>`
- push는 RULE-G1 적용 — 사용자 명시 승인 후에만

## [VS Code 통합]
- tasks.json: `.vscode/tasks.json` (10개 태스크 등록)
- launch.json: `.vscode/launch.json` (orchestrator·pytest·현재파일)
- 단축키: Ctrl+Shift+B → 🤖 consulting-agent 실행 (기본 빌드 태스크)
- 스킬 파일: `.skills/` (corp-financial-analysis·pptx·docx·xlsx·pdf)
- 슬래시명령: `.claude/commands/` (마스터컨설팅·비상장주식평가·가지급금해소·가업승계·차명주식·임원퇴직금·상속증여·특허패키지·금융기관진단·법인재무종합분석)

## [2026-05 채팅모드 업데이트] 의뢰범위 보호 룰 (RULE-G 시리즈)

본 섹션은 2026-05-04 채팅창에서 발생한 의뢰범위 초과 자동수행 사고를 재발방지하기 위한 강제 룰이다.
모든 채팅·Cowork·Code 모드에서 동등 적용된다.

### RULE-G1 — 사용자 명시 없는 git push 금지
사용자가 명시적으로 "push" 또는 "원격 반영"을 지시하지 않은 경우, 다음 행위 절대 금지:
- git push (브랜치·태그 무관)
- gh pr create 후 자동 머지
- GitHub MCP의 push_files·create_or_update_file·merge_pull_request
- 기타 원격 저장소 쓰기성 호출

예외: 사용자가 다음 표현 중 하나를 사용한 경우만 허용
- "push 해 줘", "push 해도 좋아", "원격에 올려 줘", "git push 실행"
- "GitHub에 반영", "PR 머지 승인"

위반 시: 즉시 중단 + 사용자 보고 + 자동 복구 시도 금지

### RULE-G2 — MCP 쓰기성 도구 자동호출 시 사용자 승인 필수
다음 카테고리 호출 직전 반드시 승인 요청:
- 파일·코드 쓰기: GitHub push_files / create_or_update_file / delete_file
- 메일·메시지 발송: Gmail send_message / Slack send_message
- 캘린더·일정 변경: Google Calendar create/update/delete_event
- Drive 쓰기: Google Drive create/update/delete_file
- 결제·구매: 모든 결제 관련 MCP

승인 요청 형식:
[MCP 쓰기성 도구 호출 승인 요청]
- 도구: <도구명>
- 대상: <대상 자원>
- 영향: <변경 내용 요약>
- 승인하시려면 "승인" 또는 "예"로 응답해 주십시오.

예외: 사용자가 본 세션 시작 시 "MCP 자동호출 허용"을 명시한 경우만 면제

### RULE-G3 — API Stream idle timeout 회피 룰
다음 작업은 반드시 배치 분할 처리:
- 파일 다수 생성: 5개 파일/배치
- 대용량 텍스트 생성: 2,000토큰/배치
- MCP 도구 다수 호출: 3호출/배치
- git commit 다수: 1커밋/배치

timeout 발생 시 자동복구:
1. 마지막 성공 배치 위치 기록 (outputs/_resume_state.json)
2. 동일 배치 재시도 (최대 2회)
3. 2회 실패 시 사용자 보고 + 작업 중단

금지: 단일 호출에 31개 파일 + git push + MCP 머지 + 검증 묶음 시도

### RULE-G 시리즈 자가검증
매 세션 종료 직전 다음 자가질문에 답:
- 본 세션에서 사용자 명시 없는 push 시도 0회?
- 본 세션에서 MCP 쓰기성 도구 무승인 호출 0회?
- 본 세션에서 단일 호출 5파일·3MCP·2,000토큰 초과 0회?

3개 모두 ✅ 인 경우만 정상 종료. 1개라도 ❌ 인 경우 사용자 자진 보고.

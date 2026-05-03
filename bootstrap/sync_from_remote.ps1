# sync_from_remote.ps1
# ============================================================================
# 3대 기기(집A·사무실B·노트북) 동기화 — consulting-agent + junggi-workspace
# 작성: 2026-05-04 [LAPTOP]
#
# 기능:
#   1. 양 레포 git fetch + main 정렬 (master 잔재 자동 main 정렬)
#   2. git pull --ff-only origin main (rebase 안전)
#   3. 신규 .py·.ps1 파일 UTF-8 BOM 일괄 검증·재저장
#   4. 7종 schtasks 등록 상태 확인 (빠진 것 안내)
#   5. 환경변수 4종 + ANTHROPIC_API_KEY 존재 검증
#   6. 검증 4축 + 5축 리스크 검증 자가실행 (4종 신규 에이전트 smoke test)
#   7. 100% PASS 확인 후 종료
#
# 사용:
#   .\bootstrap\sync_from_remote.ps1
# ============================================================================

[CmdletBinding()]
param(
    [string]$ConsultingPath  = "$env:USERPROFILE\consulting-agent",
    [string]$WorkspacePath   = "$env:USERPROFILE\junggi-workspace",
    [switch]$SkipSchtasks,
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Continue"
$script:Failures = @()
$script:Warnings = @()

function Write-Section($title) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "  $title" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
}

function Add-Failure($msg) {
    $script:Failures += $msg
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
}

function Add-Warning($msg) {
    $script:Warnings += $msg
    Write-Host "  [WARN] $msg" -ForegroundColor Yellow
}

function Add-Success($msg) {
    Write-Host "  [OK]   $msg" -ForegroundColor Green
}

# ──────────────────────────────────────────────────────────────────────────
# 1. 양 레포 git fetch + main 정렬
# ──────────────────────────────────────────────────────────────────────────

function Sync-Repo($name, $path) {
    Write-Section "1. Sync $name"
    if (-not (Test-Path $path)) {
        Add-Failure "$name 경로 미존재: $path"
        return
    }
    Push-Location $path
    try {
        $branch = git rev-parse --abbrev-ref HEAD 2>$null
        if ($branch -eq "master") {
            Add-Warning "$name 현재 master — main 으로 전환"
            git branch -m master main 2>$null
            git fetch origin 2>$null
            git branch --set-upstream-to=origin/main main 2>$null
        }
        Add-Success "$name 브랜치 = $branch"

        git fetch origin 2>$null
        $status = git status --short 2>$null
        if ($status) {
            Add-Warning "$name 워킹트리 변경 있음 — pull 전 stash 권장: $status"
        }

        $pullResult = git pull --ff-only origin main 2>&1 | Out-String
        if ($pullResult -match "fatal|error|conflict") {
            Add-Failure "$name git pull 실패: $pullResult"
        } else {
            Add-Success "$name git pull --ff-only OK"
        }

        $latest = git log -1 --pretty='%h %s' 2>$null
        Write-Host "    최신 commit: $latest"
    } finally {
        Pop-Location
    }
}

Sync-Repo "consulting-agent" $ConsultingPath
Sync-Repo "junggi-workspace"  $WorkspacePath

# ──────────────────────────────────────────────────────────────────────────
# 2. UTF-8 BOM 일괄 검증·재저장 (신규 .py·.ps1)
# ──────────────────────────────────────────────────────────────────────────

Write-Section "2. UTF-8 BOM 검증·재저장"

$BOM = [byte[]](0xEF, 0xBB, 0xBF)
$targets = @(
    "$ConsultingPath\agents\active\rnd_lab_notebook.py",
    "$ConsultingPath\agents\active\business_plan_pro.py",
    "$ConsultingPath\agents\active\legal_risk_hedge.py",
    "$ConsultingPath\agents\active\legal_document_drafter.py",
    "$ConsultingPath\bootstrap\sync_from_remote.ps1"
)

foreach ($f in $targets) {
    if (-not (Test-Path $f)) {
        Add-Warning "파일 없음 (skip): $f"
        continue
    }
    $bytes = [System.IO.File]::ReadAllBytes($f)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        Add-Success ("BOM 정상: " + (Split-Path $f -Leaf))
    } else {
        # BOM 없음 — 추가 후 재저장
        $newBytes = $BOM + $bytes
        [System.IO.File]::WriteAllBytes($f, $newBytes)
        Add-Success ("BOM 추가 + 재저장: " + (Split-Path $f -Leaf))
    }
}

# ──────────────────────────────────────────────────────────────────────────
# 3. 7종 schtasks 등록 상태 확인
# ──────────────────────────────────────────────────────────────────────────

if (-not $SkipSchtasks) {
    Write-Section "3. 7종 schtasks 등록 확인"
    $expected = @(
        "JunggiDailyTaskClassify", "JunggiDiscovery", "JunggiExecutor",
        "JunggiMonthlyConsolidate", "JunggiQuarterlyDiagnostic",
        "JunggiVerifier", "JunggiWeeklyDigest"
    )
    $registered = @{}
    foreach ($t in $expected) {
        $found = schtasks /Query /TN $t 2>$null
        if ($LASTEXITCODE -eq 0) {
            Add-Success "schtasks $t 등록됨"
            $registered[$t] = $true
        } else {
            Add-Warning "schtasks $t 미등록 — bootstrap/setup 스크립트로 등록 권장"
            $registered[$t] = $false
        }
    }
}

# ──────────────────────────────────────────────────────────────────────────
# 4. 환경변수 4종 + ANTHROPIC_API_KEY
# ──────────────────────────────────────────────────────────────────────────

Write-Section "4. 환경변수 검증"
$envVars = @("ANTHROPIC_API_KEY", "DART_API_KEY", "LAW_API_ID",
             "ECOS_API_KEY", "PUBLIC_DATA_API_KEY")
foreach ($v in $envVars) {
    $val = [Environment]::GetEnvironmentVariable($v, "User")
    if ($val) {
        Add-Success ("{0,-22} SET ({1} chars)" -f $v, $val.Length)
    } else {
        Add-Warning ("{0,-22} NOT SET — 사용자 직접 발급 필요" -f $v)
    }
}

# ──────────────────────────────────────────────────────────────────────────
# 5. 4종 신규 에이전트 smoke test
# ──────────────────────────────────────────────────────────────────────────

if (-not $SkipSmokeTest) {
    Write-Section "5. 4종 신규 에이전트 smoke test"
    $smokeTest = @"
import sys, json
sys.path.insert(0, r'$ConsultingPath')
from router.command_router import CommandRouter
router = CommandRouter()
total = len(router.commands)
print(f'router_total={total}')
results = {}
for slash in ['/연구노트', '/사업계획서', '/법률리스크체크', '/법무서류']:
    r = router.route(slash)
    results[slash] = {
        'status': r.status,
        'agent': r.best.agent if r.best else None,
        'confidence': r.best.confidence if r.best else 0,
    }
import importlib
for cls_name, mod_path in [
    ('RnDLabNotebookAgent',       'agents.active.rnd_lab_notebook'),
    ('BusinessPlanProAgent',      'agents.active.business_plan_pro'),
    ('LegalRiskHedgeAgent',       'agents.active.legal_risk_hedge'),
    ('LegalDocumentDrafterAgent', 'agents.active.legal_document_drafter'),
]:
    cls = getattr(importlib.import_module(mod_path), cls_name)
    sample = {'company_name': '테스트법인', 'industry': '제조업',
              'research_topic': '테스트', 'inventor': 'X',
              'document_type': '이사회의사록', 'agenda': '신주발행'}
    res = cls().analyze(sample)
    r5 = res.get('risk_5axis', {}).get('all_pass', False)
    h4 = all(k in res.get('risk_hedge_4stage', {}) for k in ['1_pre','2_now','3_post','4_worst'])
    sc = res.get('self_check_4axis', {}).get('all_pass', False)
    cells = sum(1 for p in res.get('matrix_4x3', {}).values() for v in p.values() if v)
    results[cls_name] = {'5axis': r5, 'hedge_4stage': h4, 'self_4axis': sc, 'matrix_cells': cells}
print('SMOKE_TEST_RESULT=' + json.dumps(results, ensure_ascii=False))
"@
    $smokeOut = python -c $smokeTest 2>&1 | Out-String
    if ($smokeOut -match "router_total=81") {
        Add-Success "라우터 총 81개 명령 로드"
    } else {
        Add-Failure "라우터 명령 수 81 아님: $smokeOut"
    }
    if ($smokeOut -match "SMOKE_TEST_RESULT=(.+)") {
        try {
            $smokeJson = $matches[1] | ConvertFrom-Json
            foreach ($key in @('/연구노트','/사업계획서','/법률리스크체크','/법무서류')) {
                $r = $smokeJson.$key
                if ($r.status -eq "auto_route") {
                    Add-Success ("슬래시 매칭 OK: " + $key + " (" + $r.confidence + ")")
                } else {
                    Add-Failure ("슬래시 매칭 FAIL: " + $key)
                }
            }
            foreach ($cls in @('RnDLabNotebookAgent','BusinessPlanProAgent','LegalRiskHedgeAgent','LegalDocumentDrafterAgent')) {
                $r = $smokeJson.$cls
                $allOk = $r.'5axis' -and $r.hedge_4stage -and $r.self_4axis -and ($r.matrix_cells -eq 12)
                if ($allOk) {
                    Add-Success ("$cls — 5축/4단계/4축자가/매트릭스 ALL PASS")
                } else {
                    Add-Failure ("$cls 검증 실패: 5axis=$($r.'5axis') h4=$($r.hedge_4stage) sc=$($r.self_4axis) cells=$($r.matrix_cells)")
                }
            }
        } catch {
            Add-Failure "smoke test JSON 파싱 실패"
        }
    } else {
        Add-Failure "smoke test 결과 추출 실패: $smokeOut"
    }
}

# ──────────────────────────────────────────────────────────────────────────
# 종료 보고
# ──────────────────────────────────────────────────────────────────────────

Write-Section "종료 보고"
Write-Host ""
Write-Host "  실패 (FAIL): $($Failures.Count)" -ForegroundColor $(if ($Failures.Count) { "Red" } else { "Green" })
Write-Host "  경고 (WARN): $($Warnings.Count)" -ForegroundColor $(if ($Warnings.Count) { "Yellow" } else { "Green" })

if ($Failures.Count -eq 0) {
    Write-Host ""
    Write-Host "  ✓ 동기화 완료 — 4종 신규 에이전트 정상 작동 확인" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "  ✗ 동기화 일부 실패 — 위 [FAIL] 항목 검토 필요" -ForegroundColor Red
    exit 1
}

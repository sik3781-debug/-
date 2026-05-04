# sync_all_devices.ps1 — 3대 기기 동기화 스크립트 (Windows)
# UTF-8 BOM — PowerShell 필수
# 실행: .\sync_all_devices.ps1

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$ConsultingPath  = "$env:USERPROFILE\consulting-agent",
    [string]$WorkspacePath   = "$env:USERPROFILE\junggi-workspace",
    [switch]$SkipPull
)

$ErrorActionPreference = "Continue"
$MACHINE = $env:COMPUTERNAME
$USER    = $env:USERNAME

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  3대 기기 동기화 스크립트" -ForegroundColor Cyan
Write-Host "  기기: $MACHINE / 사용자: $USER" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# ── 기기별 분기 설정 ──
switch ($MACHINE) {
    "DESKTOP-FJUATON" {
        $DeviceLabel = "OFFICE-B"
        Write-Host "  [OFFICE-B] 사무실 데스크탑 모드" -ForegroundColor Yellow
    }
    default {
        if ($USER -eq "sik37") {
            $DeviceLabel = "LAPTOP"
            Write-Host "  [LAPTOP] 노트북 모드" -ForegroundColor Yellow
        } else {
            $DeviceLabel = "HOME-A"
            Write-Host "  [HOME-A] 집 데스크탑 모드" -ForegroundColor Yellow
        }
    }
}

# ── consulting-agent 동기화 ──
Write-Host "`n[1/2] consulting-agent 동기화" -ForegroundColor Cyan
if (Test-Path $ConsultingPath) {
    Set-Location $ConsultingPath
    if (-not $SkipPull) {
        if ($PSCmdlet.ShouldProcess("consulting-agent", "git pull")) {
            $pull1 = git pull --ff-only origin main 2>&1
            Write-Host $pull1
        }
    }
    $head1 = git rev-parse --short HEAD
    Write-Host "  HEAD: $head1 [$DeviceLabel]"
} else {
    Write-Host "  ❌ 경로 없음: $ConsultingPath" -ForegroundColor Red
}

# ── junggi-workspace 동기화 ──
Write-Host "`n[2/2] junggi-workspace 동기화" -ForegroundColor Cyan
if (Test-Path $WorkspacePath) {
    Set-Location $WorkspacePath
    if (-not $SkipPull) {
        if ($PSCmdlet.ShouldProcess("junggi-workspace", "git pull")) {
            $pull2 = git pull --ff-only origin main 2>&1
            Write-Host $pull2
        }
    }
    $head2 = git rev-parse --short HEAD
    Write-Host "  HEAD: $head2 [$DeviceLabel]"
} else {
    Write-Host "  ❌ 경로 없음: $WorkspacePath" -ForegroundColor Red
}

# ── UTF-8 BOM 검증 (.ps1) ──
Write-Host "`n[BOM 검증] .ps1 파일" -ForegroundColor Cyan
$ps1_files = Get-ChildItem -Path $ConsultingPath -Recurse -Filter "*.ps1" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "node_modules" }
$bom_fail = @()
foreach ($f in $ps1_files) {
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName) | Select-Object -First 3
    if (-not ($bytes.Count -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)) {
        $bom_fail += $f.FullName
    }
}
if ($bom_fail.Count -eq 0) {
    Write-Host "  ✅ 모든 .ps1 UTF-8 BOM 정상" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ BOM 누락 $($bom_fail.Count)건" -ForegroundColor Yellow
}

# ── ANTHROPIC_API_KEY 확인 ──
Write-Host "`n[환경변수]" -ForegroundColor Cyan
$key = [Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "User")
if ($key) {
    Write-Host "  ✅ ANTHROPIC_API_KEY 설정됨 ($($key.Substring(0,[Math]::Min(10,$key.Length)))...)"
} else {
    Write-Host "  ❌ ANTHROPIC_API_KEY 미설정" -ForegroundColor Red
}

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "  동기화 완료 [$DeviceLabel] $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

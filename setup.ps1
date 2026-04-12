# setup.ps1 — 컨설팅 에이전트 시스템 자동 설치 스크립트
# 실행: powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  중소기업 컨설팅 에이전트 시스템 v2 -- 자동 설치" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. API Key 확인·등록 ─────────────────────────────────────────────────
Write-Host "[1/4] ANTHROPIC_API_KEY 확인 중..." -ForegroundColor Yellow
$apiKey = [System.Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "User")

if (-not $apiKey) {
    Write-Host "  API Key가 등록되지 않았습니다." -ForegroundColor Red
    $apiKey = Read-Host "  ANTHROPIC_API_KEY를 입력하세요 (sk-ant-...)"
    if ($apiKey.StartsWith("sk-ant-")) {
        [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $apiKey, "User")
        $env:ANTHROPIC_API_KEY = $apiKey
        Write-Host "  API Key 등록 완료." -ForegroundColor Green
    } else {
        Write-Host "  [오류] 유효하지 않은 API Key 형식입니다." -ForegroundColor Red
        exit 1
    }
} else {
    $env:ANTHROPIC_API_KEY = $apiKey
    Write-Host "  API Key 확인됨 (prefix: $($apiKey.Substring(0, [Math]::Min(12, $apiKey.Length)))...)" -ForegroundColor Green
}

# ── 2. Python 확인 ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Python 환경 확인 중..." -ForegroundColor Yellow
try {
    $pyVer = python --version 2>&1
    Write-Host "  $pyVer" -ForegroundColor Green
} catch {
    Write-Host "  [오류] Python을 찾을 수 없습니다. python.org에서 설치하세요." -ForegroundColor Red
    exit 1
}

# ── 3. 패키지 설치 ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] 패키지 설치 중..." -ForegroundColor Yellow
$packages = @("anthropic")
foreach ($pkg in $packages) {
    Write-Host "  pip install $pkg ..." -NoNewline
    pip install $pkg --quiet 2>&1 | Out-Null
    Write-Host " 완료" -ForegroundColor Green
}

# ── 4. 파일 구조 검증 ────────────────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] 파일 구조 검증 중..." -ForegroundColor Yellow

$requiredFiles = @(
    "agents\base_agent.py",
    "agents\consulting_agents.py",
    "agents\verify_agent.py",
    "agents\legal_agent.py",
    "agents\patent_agent.py",
    "agents\labor_agent.py",
    "agents\industry_agent.py",
    "agents\web_research_agent.py",
    "agents\policy_funding_agent.py",
    "agents\cash_flow_agent.py",
    "agents\credit_rating_agent.py",
    "agents\real_estate_agent.py",
    "agents\insurance_agent.py",
    "agents\ma_valuation_agent.py",
    "agents\esg_risk_agent.py",
    "agents\verify_tax.py",
    "agents\__init__.py",
    "orchestrator.py",
    "run.py"
)

$missing = @()
foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $Root $file
    if (Test-Path $fullPath) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $file" -ForegroundColor Red
        $missing += $file
    }
}

# output 폴더 생성
$outputDir = Join-Path $Root "output"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
    Write-Host "  [생성] output\ 폴더" -ForegroundColor Yellow
}

Write-Host ""
if ($missing.Count -gt 0) {
    Write-Host "================================================================" -ForegroundColor Red
    Write-Host "  [오류] 누락 파일 $($missing.Count)개 발견. 재설치가 필요합니다." -ForegroundColor Red
    Write-Host "================================================================" -ForegroundColor Red
    exit 1
} else {
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "  설치 완료! 아래 명령으로 실행하세요:" -ForegroundColor Green
    Write-Host ""
    Write-Host "  cd $Root" -ForegroundColor Cyan
    Write-Host "  python run.py" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Green
}

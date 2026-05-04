#!/usr/bin/env bash
# sync_all_devices.sh — 3대 기기 동기화 스크립트 (macOS·Linux)
# 실행: bash sync_all_devices.sh

set -euo pipefail

CONSULTING_PATH="${HOME}/consulting-agent"
WORKSPACE_PATH="${HOME}/junggi-workspace"
MACHINE="$(hostname)"
USER_NAME="$(whoami)"

echo "============================================"
echo "  3대 기기 동기화 스크립트"
echo "  기기: ${MACHINE} / 사용자: ${USER_NAME}"
echo "============================================"

# 기기 레이블
case "${USER_NAME}" in
    "sik37")   DEVICE_LABEL="LAPTOP" ;;
    "Jy"|"jy") DEVICE_LABEL="OFFICE-B" ;;
    *)         DEVICE_LABEL="HOME-A" ;;
esac
echo "  레이블: ${DEVICE_LABEL}"

# ── consulting-agent 동기화 ──
echo ""
echo "[1/2] consulting-agent 동기화"
if [ -d "${CONSULTING_PATH}" ]; then
    cd "${CONSULTING_PATH}"
    git pull --ff-only origin main
    HEAD1=$(git rev-parse --short HEAD)
    echo "  HEAD: ${HEAD1} [${DEVICE_LABEL}]"
else
    echo "  ❌ 경로 없음: ${CONSULTING_PATH}"
fi

# ── junggi-workspace 동기화 ──
echo ""
echo "[2/2] junggi-workspace 동기화"
if [ -d "${WORKSPACE_PATH}" ]; then
    cd "${WORKSPACE_PATH}"
    git pull --ff-only origin main
    HEAD2=$(git rev-parse --short HEAD)
    echo "  HEAD: ${HEAD2} [${DEVICE_LABEL}]"
else
    echo "  ❌ 경로 없음: ${WORKSPACE_PATH}"
fi

# ── ANTHROPIC_API_KEY 확인 ──
echo ""
echo "[환경변수]"
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "  ✅ ANTHROPIC_API_KEY 설정됨 (${ANTHROPIC_API_KEY:0:10}...)"
else
    echo "  ❌ ANTHROPIC_API_KEY 미설정"
fi

echo ""
echo "============================================"
echo "  동기화 완료 [${DEVICE_LABEL}] $(date '+%Y-%m-%d %H:%M')"
echo "============================================"

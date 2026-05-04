# -*- coding: utf-8 -*-
"""
setup_vscode_integration.py
VS Code + Claude Code 통합 환경 자동 설정 스크립트.

실행: python setup_vscode_integration.py
"""
import os
import sys
import json
import pathlib
import subprocess
import shutil

ROOT = pathlib.Path(__file__).parent
VSCODE_DIR  = ROOT / ".vscode"
SKILLS_DIR  = ROOT / ".skills"
COMMANDS_DIR = ROOT / ".claude" / "commands"
OUTPUTS_DIR = ROOT / "outputs"


def check_python_packages():
    """필수 Python 패키지 설치 여부 확인."""
    required = ["openpyxl", "docx", "pptx", "anthropic"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg if pkg != "docx" else "docx")
        except ImportError:
            missing.append(pkg if pkg != "docx" else "python-docx")
    if missing:
        print(f"[설치 필요] pip install {' '.join(missing)}")
    else:
        print("[OK] 필수 패키지 모두 설치됨")
    return missing


def check_directories():
    """필수 디렉토리 존재 확인 및 생성."""
    dirs = [VSCODE_DIR, SKILLS_DIR, COMMANDS_DIR, OUTPUTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        status = "✅" if d.exists() else "❌"
        print(f"  {status} {d.relative_to(ROOT)}")


def verify_skills():
    """스킬 파일 존재 확인."""
    skill_files = list(SKILLS_DIR.rglob("SKILL.md"))
    print(f"[스킬] {len(skill_files)}개 SKILL.md 발견")
    for f in skill_files:
        print(f"  ✅ {f.relative_to(ROOT)}")
    return len(skill_files)


def verify_commands():
    """슬래시명령 파일 존재 확인."""
    cmd_files = list(COMMANDS_DIR.glob("*.md"))
    print(f"[슬래시명령] {len(cmd_files)}개 .md 발견")
    for f in sorted(cmd_files):
        print(f"  ✅ {f.name}")
    return len(cmd_files)


def verify_vscode():
    """VS Code 설정 파일 확인."""
    files = ["tasks.json", "launch.json", "settings.json", "extensions.json"]
    for fn in files:
        fp = VSCODE_DIR / fn
        status = "✅" if fp.exists() else "❌"
        print(f"  {status} .vscode/{fn}")


def check_api_key():
    """ANTHROPIC_API_KEY 환경변수 확인."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        print(f"[API Key] ✅ 설정됨 ({key[:10]}...)")
    else:
        print("[API Key] ❌ 미설정 — ANTHROPIC_API_KEY 환경변수 등록 필요")


def main():
    print("=" * 60)
    print("  중기이코노미 AI 컨설팅 하네스 VS Code 통합 검증")
    print("=" * 60)

    print("\n[1] 디렉토리 구조:")
    check_directories()

    print("\n[2] Python 패키지:")
    check_python_packages()

    print("\n[3] 스킬 파일:")
    skill_count = verify_skills()

    print("\n[4] 슬래시명령:")
    cmd_count = verify_commands()

    print("\n[5] VS Code 설정 파일:")
    verify_vscode()

    print("\n[6] API Key:")
    check_api_key()

    print("\n" + "=" * 60)
    print(f"  스킬 {skill_count}개 | 슬래시명령 {cmd_count}개 | 설정 완료")
    print("  VS Code에서 Ctrl+Shift+B → 'consulting-agent 실행' 선택")
    print("=" * 60)


if __name__ == "__main__":
    main()

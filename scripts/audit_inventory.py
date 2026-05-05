"""점검 범위 자동 수집 - 종합 인벤토리"""
from pathlib import Path
import os, json

home = Path(os.path.expanduser("~"))
ca_dir = home / "consulting-agent"

inventory = {
    "claude_md": [],
    "skills_md": [],
    "agents_py": [],
    "config_files": [],
}

# 1) 모든 CLAUDE.md
for path in home.rglob("CLAUDE.md"):
    s = str(path)
    if "node_modules" in s or ".git" in s: continue
    inventory["claude_md"].append(s)

# 2) 모든 SKILL.md
skills_dir = home / ".claude" / "skills"
if skills_dir.exists():
    for path in skills_dir.rglob("SKILL.md"):
        inventory["skills_md"].append(str(path))

# 3) consulting-agent 에이전트 .py
for path in (ca_dir / "agents").rglob("*.py"):
    if "__pycache__" in str(path): continue
    inventory["agents_py"].append(str(path))

# 4) 핵심 config
for f in ["router/command_router.json", ".env.example"]:
    p = ca_dir / f
    if p.exists(): inventory["config_files"].append(str(p))

out_dir = ca_dir / "outputs"
out_dir.mkdir(exist_ok=True)
out_file = out_dir / "INVENTORY_AUDIT_20260505.json"
out_file.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"=== 점검 범위 인벤토리 ===")
print(f"CLAUDE.md: {len(inventory['claude_md'])}개")
for p in sorted(inventory['claude_md']): print(f"  {p}")
print(f"\nSKILL.md: {len(inventory['skills_md'])}개")
print(f"agents/*.py: {len(inventory['agents_py'])}개")
print(f"config: {len(inventory['config_files'])}개")
print(f"\n저장: {out_file}")

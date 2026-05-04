"""schtasks 09:10 trigger entry point — JunggiExecutor
dry_run=True 강제 — destructive 자동 실행 절대 금지.
발견된 작업은 proposed_actions 목록으로만 출력.
실제 실행은 사용자 수동 승인 후 진행.
"""
import json
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.active.executor_agent import SystemEnhancementExecutorAgent


def main():
    discovery_dir = Path.home() / "consulting-agent" / "outputs" / "self_evolution"
    discovery_files = sorted(discovery_dir.glob("discovery_*.json")) if discovery_dir.exists() else []

    discovery_result = {}
    if discovery_files:
        discovery_result = json.loads(discovery_files[-1].read_text(encoding='utf-8'))

    agent = SystemEnhancementExecutorAgent()

    # dry_run=True 하드코딩 — 자동 실행 모드에서 실제 변경 절대 금지
    result = agent.analyze({
        'findings': discovery_result.get('findings', []),
        'trigger': 'schtasks_09:10',
        'dry_run': True,
        'auto_execute': False,
        'timestamp': datetime.now().isoformat(),
    })

    # proposed_actions: dry_run 시 executor_result 내 pending_approval 항목
    er = result.get('executor_result', {})
    proposed = [
        r for r in er.get('results', [])
        if r.get('status') == 'pending_approval'
    ]
    result['proposed_actions'] = proposed

    discovery_dir.mkdir(parents=True, exist_ok=True)
    out_file = discovery_dir / f"executor_{datetime.now():%Y%m%d_%H%M}.json"
    out_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding='utf-8'
    )

    actions   = result.get('actions_taken', [])
    print(f"OK Executor (actions={len(actions)}, proposed={len(proposed)}) -- {out_file}")
    print("   dry_run=True 강제 -- 실제 실행은 사용자 승인 후 수동 진행")
    return result


if __name__ == "__main__":
    main()

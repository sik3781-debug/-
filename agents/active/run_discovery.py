"""schtasks 09:05 trigger entry point — JunggiDiscovery"""
import json
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.active.discovery_agent import SystemEnhancementDiscoveryAgent


def main():
    verifier_dir = Path.home() / "consulting-agent" / "outputs" / "self_evolution"
    verifier_files = sorted(verifier_dir.glob("verifier_*.json")) if verifier_dir.exists() else []

    verifier_result = {}
    if verifier_files:
        verifier_result = json.loads(verifier_files[-1].read_text(encoding='utf-8'))

    agent = SystemEnhancementDiscoveryAgent()
    result = agent.analyze({
        'verifier_score': verifier_result.get('verification_score', 100),
        'trigger': 'schtasks_09:05',
        'dry_run': False,
        'timestamp': datetime.now().isoformat(),
    })

    verifier_dir.mkdir(parents=True, exist_ok=True)
    out_file = verifier_dir / f"discovery_{datetime.now():%Y%m%d_%H%M}.json"
    out_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding='utf-8'
    )

    findings = result.get('findings', [])
    print(f"OK Discovery (findings={len(findings)}) -- {out_file}")
    return result


if __name__ == "__main__":
    main()

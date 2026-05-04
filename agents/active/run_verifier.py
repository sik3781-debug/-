"""schtasks 09:00 trigger entry point — JunggiVerifier"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.active.verifier_agent import EnhancementVerifierAgent


def main():
    agent = EnhancementVerifierAgent()
    result = agent.analyze({
        'system_state': 'baseline',
        'trigger': 'schtasks_09:00',
        'dry_run': False,
        'timestamp': datetime.now().isoformat(),
    })

    out_dir = Path.home() / "consulting-agent" / "outputs" / "self_evolution"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"verifier_{datetime.now():%Y%m%d_%H%M}.json"
    out_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding='utf-8'
    )

    score = result.get('verification_score', 0)
    if score < 100:
        print(f"WARNING: Verifier score {score} < 100")
        sys.exit(1)

    print(f"OK Verifier (score={score}) -- {out_file}")
    return result


if __name__ == "__main__":
    main()

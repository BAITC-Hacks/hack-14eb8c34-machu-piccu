"""HackAlem weather dataset pipeline."""
import sys
from pathlib import Path

# Optional workspace-only installation. Normal installations use requirements.txt.
_deps = Path(__file__).resolve().parents[1] / ".deps"
if _deps.exists():
    sys.path.insert(0, str(_deps))

"""Print a validated per-shell Qt scale, independent of compositor/app scaling."""
import json
import math
import os
from pathlib import Path


def read_scale(home):
    try:
        value = json.loads((Path(home) / '.config/lickintosh/shell-config.json').read_text()).get('general', {}).get('shellScale', 1)
        if isinstance(value, bool):
            return 1.0
        value = float(value)
        return value if math.isfinite(value) and 0.75 <= value <= 2 else 1.0
    except (OSError, ValueError, TypeError, AttributeError):
        return 1.0


if __name__ == '__main__':
    print(format(read_scale(os.environ['HOME']), '.4g'))

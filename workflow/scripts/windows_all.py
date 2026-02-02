#!/usr/bin/env python3

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ["scope"] = "all"

from windows import main


if __name__ == "__main__":
    main()

"""Load Home Assistant before unrelated globally installed pytest plugins."""

import os
import sys
from pathlib import Path

os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import homeassistant  # noqa: E402,F401
import pytest  # noqa: E402

raise SystemExit(
    pytest.main(["-p", "pytest_asyncio.plugin", "-p", "pytest_socket", *sys.argv[1:]])
)

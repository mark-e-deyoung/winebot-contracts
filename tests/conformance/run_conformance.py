#!/usr/bin/env python3
"""Legacy conformance test runner — delegates to pytest-based suite.

Kept for backward compatibility. New work should use pytest directly:

    pip install -r tests/conformance/requirements.txt
    pytest tests/conformance/ -v --api-url http://localhost:8000 --api-token xxx
"""

import os
import sys
import subprocess


def main():
    api_url = os.environ.get("API_URL", "http://localhost:8000")
    api_token = os.environ.get("API_TOKEN", "")

    print(f"WineBot Contracts Conformance — {api_url}")
    print("Running pytest-based test suite...\n")

    cmd = [
        sys.executable, "-m", "pytest",
        os.path.join(os.path.dirname(__file__)),
        "-v", "--tb=short",
        "--api-url", api_url,
    ]
    if api_token:
        cmd += ["--api-token", api_token]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

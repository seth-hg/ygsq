#!/usr/bin/env python3

import os
import subprocess
import sys


def main():
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        f"{os.path.dirname(__file__)}/webui.py",
        "--server.headless=true",
        "--server.address=127.0.0.1",
        "--logger.level",
        "info",
    ]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

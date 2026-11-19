"""Create .venv and install everything needed for vSHACL work.

Mac:     python3.13 scripts/setup_dev.py
Windows: py -3.13 scripts\\setup_dev.py
"""
import subprocess
import sys
import venv
from pathlib import Path

if sys.version_info[:2] != (3, 13):
    sys.exit(f"Use Python 3.13, not {sys.version.split()[0]}.")

root = Path(__file__).resolve().parent.parent
env = root / ".venv"
python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
if not python.exists():
    venv.create(env, with_pip=True)


def run(*args):
    subprocess.run([str(python), *args], check=True, cwd=root)


run("-m", "pip", "install", "--upgrade", "pip")
run("-m", "pip", "install", "-e", ".[clip]", "pytest==9.2.0")
run("-m", "pytest", "-q", "-p", "no:cacheprovider", "test/test_mm_depicts.py")
print("vSHACL environment is ready.")

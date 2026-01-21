import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "app" / "api.py"

def run(cmd):
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))

if __name__ == "__main__":
    # Ensure pyinstaller is installed
    run([sys.executable, "-m", "pip", "install", "-U", "pyinstaller"])

    # Build sidecar exe
    run([
        sys.executable, "-m", "PyInstaller",
        "--name", "research-engine",
        "--onefile",
        "--console",
        "--paths", str(ROOT),
        "--hidden-import", "langchain_classic.retrievers",
        "--hidden-import", "langchain_postgres",
        "--hidden-import", "langchain_community.chat_models",
        str(API),
    ])

    print("\nBuilt: dist/research-engine.exe")

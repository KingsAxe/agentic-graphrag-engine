import os
import sys
import time
import signal
import subprocess
import requests
import webview

API_HOST = "127.0.0.1"
API_PORT = 8000
UI_HOST = "127.0.0.1"
UI_PORT = 8501

def exe_dir():
    # works in both dev + PyInstaller onefile
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def wait_http(url: str, timeout_s: int = 20) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(0.4)
    return False

def main():
    root = exe_dir()

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    # Start FastAPI
    api_cmd = [
        sys.executable, "-m", "uvicorn",
        "app.api:app",
        "--host", API_HOST,
        "--port", str(API_PORT),
    ]
    api_proc = subprocess.Popen(api_cmd, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Start Streamlit UI
    ui_cmd = [
        sys.executable, "-m", "streamlit", "run",
        os.path.join("ui", "streamlit_app.py"),
        "--server.address", UI_HOST,
        "--server.port", str(UI_PORT),
        "--server.headless", "true",
    ]
    ui_proc = subprocess.Popen(ui_cmd, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        # Wait for Streamlit
        ui_url = f"http://{UI_HOST}:{UI_PORT}"
        ok = wait_http(ui_url, timeout_s=30)
        if not ok:
            raise RuntimeError("Streamlit did not start in time. Check logs.")

        # Open desktop window
        window = webview.create_window(
            "Sovereign Research Engine",
            ui_url,
            width=1200,
            height=800,
        )
        webview.start()

    finally:
        # Ensure processes exit
        for p in (ui_proc, api_proc):
            if p and p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass

if __name__ == "__main__":
    main()

import os
import time
import requests
import streamlit as st

DEFAULT_API_BASE = os.getenv("SRE_API_BASE", "http://127.0.0.1:8000")

def api_base() -> str:
    return st.session_state.get("api_base", DEFAULT_API_BASE)

def set_api_base(url: str):
    st.session_state["api_base"] = url.rstrip("/")

def wait_for_backend(timeout_s: int = 12) -> bool:
    base = api_base()
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(f"{base}/health", timeout=2)
            if r.ok:
                return True
        except Exception:
            pass
        time.sleep(0.4)
    return False

def get_json(path: str):
    r = requests.get(f"{api_base()}{path}", timeout=30)
    r.raise_for_status()
    return r.json()

def post_json(path: str, payload: dict):
    # Streamlit calling REST APIs via requests is the standard approach. :contentReference[oaicite:1]{index=1}
    r = requests.post(f"{api_base()}{path}", json=payload, timeout=300)
    r.raise_for_status()
    return r.json()

def post_file(path: str, file_bytes: bytes, filename: str):
    files = {"file": (filename, file_bytes, "application/pdf")}
    r = requests.post(f"{api_base()}{path}", files=files, timeout=300)
    r.raise_for_status()
    return r.json()

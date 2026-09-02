"""
Modul untuk menyimpan perubahan basis pengetahuan langsung ke GitHub,
supaya perubahan yang dilakukan admin lewat versi PUBLIK (Streamlit Cloud)
tidak hilang saat aplikasi di-redeploy/restart.
"""

from __future__ import annotations
import base64
import os

GITHUB_REPO = "cahayatamila2005-pixel/rag-diskominfotik-ntb"
GITHUB_FILE_PATH = "data/knowledge_ai_ntb.txt"
GITHUB_API_BASE = "https://api.github.com"


def _get_token() -> str | None:
    try:
        import streamlit as st
        if "GITHUB_TOKEN" in st.secrets:
            return st.secrets["GITHUB_TOKEN"]
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN")


def sync_to_github(local_filepath: str) -> tuple[bool, str]:
    import requests

    token = _get_token()
    if not token:
        return False, "GITHUB_TOKEN belum diset di Secrets -- perubahan HANYA tersimpan sementara di server ini, belum permanen."

    if not os.path.isfile(local_filepath):
        return False, "File lokal tidak ditemukan, sinkronisasi dibatalkan."

    with open(local_filepath, "r", encoding="utf-8") as f:
        content = f.read()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"

    try:
        resp_get = requests.get(url, headers=headers, timeout=15)
        resp_get.raise_for_status()
        current_sha = resp_get.json()["sha"]

        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": "Update basis pengetahuan via panel admin (otomatis)",
            "content": encoded_content,
            "sha": current_sha,
        }
        resp_put = requests.put(url, headers=headers, json=payload, timeout=15)
        resp_put.raise_for_status()
        return True, "Perubahan berhasil disimpan permanen ke GitHub."
    except requests.exceptions.RequestException as e:
        return False, f"Gagal menyimpan ke GitHub (perubahan tetap ada sementara di server ini): {type(e).__name__}"

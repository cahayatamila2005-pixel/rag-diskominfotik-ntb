"""
Modul sederhana untuk mencatat setiap pertanyaan yang masuk dari warga,
supaya admin bisa melihat riwayat pertanyaan dan statistiknya di panel admin.

Disimpan sebagai CSV (bukan database) supaya tetap ringan dan mudah dibuka
manual kalau perlu (misal untuk lampiran laporan PKL).
"""

import os
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(BASE_DIR, "data", "question_log.csv")

FIELDNAMES = ["waktu", "pertanyaan", "terjawab", "skor", "sumber"]


def log_question(question: str, answered: bool, score: float, source: str = "") -> None:
    """Menambahkan satu baris log pertanyaan ke file CSV."""
    file_exists = os.path.isfile(LOG_PATH)
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pertanyaan": question,
            "terjawab": "Ya" if answered else "Tidak",
            "skor": round(score, 3),
            "sumber": source,
        })


def read_logs() -> list[dict]:
    """Membaca semua log pertanyaan, urutan terbaru di paling atas."""
    if not os.path.isfile(LOG_PATH):
        return []
    with open(LOG_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return list(reversed(rows))
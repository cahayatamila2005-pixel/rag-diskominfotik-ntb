"""
Modul sederhana untuk mencatat feedback (like/dislike) warga terhadap
jawaban chatbot. Berguna sebagai data evaluasi kuantitatif kualitas jawaban
untuk laporan (Bab IV), dan membantu admin tahu jawaban mana yang perlu
diperbaiki (banyak dislike).
"""

import os
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDBACK_PATH = os.path.join(BASE_DIR, "data", "feedback_log.csv")

FIELDNAMES = ["waktu", "pertanyaan", "jawaban_singkat", "feedback"]


def log_feedback(question: str, answer_snippet: str, feedback: str) -> None:
    file_exists = os.path.isfile(FEEDBACK_PATH)
    with open(FEEDBACK_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pertanyaan": question,
            "jawaban_singkat": answer_snippet[:200],
            "feedback": feedback,
        })


def read_feedback_logs() -> list[dict]:
    if not os.path.isfile(FEEDBACK_PATH):
        return []
    with open(FEEDBACK_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return list(reversed(rows))

"""
Loader pipeline RAG yang di-cache dengan @st.cache_resource.

Mendukung 2 jenis embedder yang bisa dipilih dari sidebar:
  - "tfidf"                 : cepat, 100% offline.
  - "sentence-transformers" : lebih akurat memahami makna kalimat, butuh
                               instalasi tambahan & internet saat pertama
                               kali dipakai (download model).

PENTING: threshold sentence-transformers (0.45) di bawah masih perkiraan
awal, BELUM diuji empiris seperti TF-IDF. Uji ulang sebelum dilaporkan
sebagai hasil final -- caranya sama seperti kalibrasi TF-IDF sebelumnya.
"""

import os
import streamlit as st
from rag import RAGPipeline
from embedder import TfidfEmbedder, STEmbedder

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH = os.path.join(BASE_DIR, "data", "knowledge_ai_ntb.txt")

THRESHOLD_BY_EMBEDDER = {
    "tfidf": 0.20,
    "sentence-transformers": 0.45,
}


@st.cache_resource
def load_pipeline(generation_mode: str = "extractive", embedder_type: str = "tfidf"):
    if embedder_type == "sentence-transformers":
        embedder = STEmbedder()
    else:
        embedder = TfidfEmbedder()

    threshold = THRESHOLD_BY_EMBEDDER.get(embedder_type, 0.20)

    pipeline = RAGPipeline(
        embedder=embedder,
        generation_mode=generation_mode,
        similarity_threshold=threshold,
    )
    pipeline.index_kb_file(KB_PATH)
    return pipeline

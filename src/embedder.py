"""
Modul embedding: mengubah teks jadi representasi vektor supaya bisa
dibandingkan kemiripannya secara matematis (cosine similarity).

Ada 2 backend:
1. TfidfEmbedder  -> jalan 100% offline, cocok untuk demo/latihan/
                     jika instansi tidak mengizinkan akses internet/API luar.
2. STEmbedder     -> pakai model sentence-transformers (butuh internet saat
                     pertama kali download model), hasilnya jauh lebih akurat
                     untuk memahami makna kalimat (bukan cuma kata yang sama persis).

Untuk laporan PKL: kamu bisa jelaskan kedua pendekatan ini di Bab III,
dan pilih salah satu (atau bandingkan keduanya) sebagai bagian evaluasi.
"""

from __future__ import annotations
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Stopword Bahasa Indonesia dasar. sklearn TfidfVectorizer hanya punya daftar
# stopword bawaan untuk Bahasa Inggris ('english'), jadi tanpa ini, kata-kata
# umum seperti "yang", "adalah", "bagaimana", "cara" ikut dihitung mirip di
# SETIAP pertanyaan, sehingga pertanyaan di luar topik pun tetap dapat skor
# kemiripan yang menyesatkan (positif palsu / false positive).
INDONESIAN_STOPWORDS = [
    "yang", "untuk", "pada", "ke", "para", "namun", "menurut", "antara", "dia",
    "dua", "ia", "seperti", "jika", "jika", "sehingga", "kembali", "dan", "tidak",
    "ini", "karena", "kepada", "oleh", "saat", "harus", "sementara", "setelah",
    "belum", "kami", "sekitar", "bagi", "serta", "di", "dari", "itu", "atau",
    "dengan", "adalah", "akan", "bisa", "dalam", "ada", "juga", "saya", "kita",
    "apa", "apakah", "bagaimana", "cara", "gimana", "gmn", "kapan", "dimana",
    "siapa", "mengapa", "kenapa", "sudah", "sedang", "yaitu", "merupakan",
    "secara", "berbagai", "beberapa", "hal", "mau", "ingin", "boleh", "bagaimanakah",
]


class TfidfEmbedder:
    """Embedding berbasis TF-IDF. Ringan, tanpa dependensi eksternal/internet."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words=INDONESIAN_STOPWORDS,
            ngram_range=(1, 1),
            sublinear_tf=True,  # redam pengaruh kata yang muncul berkali-kali di satu dokumen
            min_df=1,
        )
        self._fitted = False

    def fit(self, texts: list[str]):
        self.vectorizer.fit(texts)
        self._fitted = True
        return self

    def encode(self, texts: list[str]) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Panggil .fit() dulu dengan seluruh koleksi teks sebelum encode().")
        vectors = self.vectorizer.transform(texts)
        return vectors.toarray()


class STEmbedder:
    """
    Embedding berbasis sentence-transformers (butuh instalasi & internet
    saat pertama kali dipakai untuk mengunduh model).

    Cara pakai (di laptop yang ada internet):
        pip install sentence-transformers
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        from sentence_transformers import SentenceTransformer  # import lokal, opsional
        self.model = SentenceTransformer(model_name)

    def fit(self, texts: list[str]):
        # Tidak perlu fit terpisah, model sudah pre-trained
        return self

    def encode(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True)


def cosine_similarity_matrix(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
    """Menghitung cosine similarity antara satu query dan banyak dokumen."""
    query_norm = query_vec / (np.linalg.norm(query_vec, axis=-1, keepdims=True) + 1e-10)
    doc_norm = doc_vecs / (np.linalg.norm(doc_vecs, axis=-1, keepdims=True) + 1e-10)
    return np.dot(doc_norm, query_norm.T).flatten()
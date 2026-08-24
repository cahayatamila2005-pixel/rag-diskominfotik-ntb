"""
Vector store sederhana di memori, berbasis numpy.
Untuk skala kecil-menengah (ratusan-ribuan dokumen SOP), pendekatan ini
sudah cukup cepat dan tidak perlu instalasi FAISS/ChromaDB.

Kalau nanti dokumen sudah sangat banyak (puluhan ribu+), baru pertimbangkan
upgrade ke FAISS atau ChromaDB untuk pencarian yang lebih efisien.
"""

from __future__ import annotations
import numpy as np
from chunking import Chunk
from embedder import cosine_similarity_matrix


class SimpleVectorStore:
    def __init__(self):
        self.chunks: list[Chunk] = []
        self.vectors: np.ndarray | None = None

    def add(self, chunks: list[Chunk], vectors: np.ndarray):
        self.chunks = chunks
        self.vectors = vectors

    def search(self, query_vector: np.ndarray, top_k: int = 3) -> list[tuple[Chunk, float]]:
        """Mengembalikan top_k chunk paling mirip dengan query, beserta skornya."""
        if self.vectors is None:
            raise RuntimeError("Vector store masih kosong, panggil .add() dulu.")

        scores = cosine_similarity_matrix(query_vector, self.vectors)
        top_indices = np.argsort(scores)[::-1][:top_k]

        return [(self.chunks[i], float(scores[i])) for i in top_indices]
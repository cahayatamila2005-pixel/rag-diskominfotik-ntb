"""
Pipeline RAG (Retrieval-Augmented Generation) utama.

Alurnya:
  1. INDEXING  : dokumen -> chunk -> embedding -> simpan di vector store
  2. RETRIEVAL : pertanyaan user -> embedding -> cari chunk paling mirip
  3. GENERATION: chunk relevan + pertanyaan -> jawaban akhir

Ada 2 mode generation:
  - "extractive" : langsung tampilkan potongan dokumen paling relevan,
                   tanpa LLM sama sekali. 100% offline.
  - "llm"        : kirim chunk + pertanyaan ke LLM API supaya jawabannya
                   dirangkai jadi kalimat yang natural. Butuh API key & internet.
"""

from __future__ import annotations
import os
from chunking import chunk_document, Chunk
from kb_parser import parse_kb_file
from embedder import TfidfEmbedder
from vector_store import SimpleVectorStore


class RAGPipeline:
    def __init__(self, embedder=None, generation_mode: str = "extractive", similarity_threshold: float = 0.20):
        self.embedder = embedder or TfidfEmbedder()
        self.store = SimpleVectorStore()
        self.generation_mode = generation_mode
        self.similarity_threshold = similarity_threshold

    def index_documents(self, filepaths: list[str], max_chars: int = 500):
        all_chunks = []
        for fp in filepaths:
            all_chunks.extend(chunk_document(fp, max_chars=max_chars))
        self._build_index(all_chunks)
        print(f"[INDEXING] {len(all_chunks)} chunk berhasil diindeks dari {len(filepaths)} dokumen.")

    def index_kb_file(self, filepath: str):
        entries = parse_kb_file(filepath)
        chunks = [
            Chunk(id=i, text=entry.to_chunk_text(), source=f"{entry.id} - {entry.title}")
            for i, entry in enumerate(entries)
        ]
        self._build_index(chunks)
        print(f"[INDEXING] {len(chunks)} entry knowledge base berhasil diindeks dari {filepath}.")

    def _build_index(self, chunks: list[Chunk]):
        texts = [c.text for c in chunks]
        self.embedder.fit(texts)
        vectors = self.embedder.encode(texts)
        self.store.add(chunks, vectors)

    def retrieve(self, question: str, top_k: int = 3):
        query_vec = self.embedder.encode([question])
        results = self.store.search(query_vec, top_k=top_k)
        return results

    def generate_answer(self, question: str, top_k: int = 3) -> dict:
        results = self.retrieve(question, top_k=top_k)

        if self.generation_mode == "extractive":
            answer = self._generate_extractive(results)
        elif self.generation_mode == "llm":
            answer = self._generate_with_llm(question, results)
        else:
            raise ValueError(f"generation_mode tidak dikenal: {self.generation_mode}")

        return {
            "question": question,
            "answer": answer,
            "sources": [
                {"text": c.text, "source": c.source, "score": round(score, 3)}
                for c, score in results
            ],
        }

    def _generate_extractive(self, results) -> str:
        if not results or results[0][1] < self.similarity_threshold:
            return "Maaf, saya tidak menemukan informasi yang relevan di dokumen yang tersedia."

        best_chunk, score = results[0]
        return best_chunk.text

    def _generate_with_llm(self, question: str, results) -> str:
        import requests

        api_key = os.environ.get("LLM_API_KEY")
        api_base = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
        model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

        if not api_key:
            return "[ERROR] LLM_API_KEY belum diset. Set environment variable dulu untuk pakai mode ini."

        context = "\n\n".join([f"- {c.text}" for c, _ in results])
        prompt = f"""Kamu adalah asisten layanan publik Diskominfotik NTB.
Jawab pertanyaan warga HANYA berdasarkan konteks dokumen berikut. Jika informasi
tidak ada di konteks, katakan tidak tahu, jangan mengarang jawaban.

Konteks dokumen:
{context}

Pertanyaan warga: {question}

Jawaban (singkat, jelas, sopan):"""

        response = requests.post(
            f"{api_base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_path = os.path.join(base_dir, "data", "knowledge_ai_ntb.txt")

    pipeline = RAGPipeline(generation_mode="extractive")
    pipeline.index_kb_file(kb_path)

    pertanyaan_uji = [
        "Apa itu DDSS?",
        "Bagaimana cara lapor keluhan ke pemerintah?",
        "Saya mau daftar berobat ke rumah sakit gimana caranya?",
        "Aplikasi apa yang dipakai ASN buat absen?",
        "Bagaimana cara mengurus izin usaha UMKM?",
        "Wisata apa saja yang terkenal di NTB?",
    ]

    for q in pertanyaan_uji:
        result = pipeline.generate_answer(q, top_k=1)
        print(f"\nQ: {result['question']}")
        print(f"A: {result['answer'][:300]}...")
        print(f"   (sumber: {result['sources'][0]['source']}, skor: {result['sources'][0]['score']})")

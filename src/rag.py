
"""
Pipeline RAG (Retrieval-Augmented Generation) utama.
"""

from __future__ import annotations

import os

import requests

from chunking import chunk_document, Chunk
from kb_parser import parse_kb_file
from embedder import TfidfEmbedder
from vector_store import SimpleVectorStore


class RAGPipeline:
    def __init__(
        self,
        embedder=None,
        generation_mode: str = "extractive",
        similarity_threshold: float = 0.20,
    ):
        self.embedder = embedder or TfidfEmbedder()
        self.store = SimpleVectorStore()
        self.generation_mode = generation_mode
        self.similarity_threshold = similarity_threshold

    def index_documents(
        self,
        filepaths: list[str],
        max_chars: int = 500,
    ):
        all_chunks = []

        for fp in filepaths:
            all_chunks.extend(
                chunk_document(fp, max_chars=max_chars)
            )

        self._build_index(all_chunks)

        print(
            f"[INDEXING] {len(all_chunks)} chunk berhasil "
            f"diindeks dari {len(filepaths)} dokumen."
        )

    def index_kb_file(self, filepath: str):
        entries = parse_kb_file(filepath)

        chunks = [
            Chunk(
                id=i,
                text=entry.to_chunk_text(),
                source=f"{entry.id} - {entry.title}",
            )
            for i, entry in enumerate(entries)
        ]

        self._build_index(chunks)

        print(
            f"[INDEXING] {len(chunks)} entry knowledge base "
            f"berhasil diindeks dari {filepath}."
        )

    def _build_index(self, chunks: list[Chunk]):
        texts = [chunk.text for chunk in chunks]

        self.embedder.fit(texts)
        vectors = self.embedder.encode(texts)
        self.store.add(chunks, vectors)

    def retrieve(self, question: str, top_k: int = 3):
        query_vec = self.embedder.encode([question])
        return self.store.search(query_vec, top_k=top_k)

    def generate_answer(
        self,
        question: str,
        top_k: int = 3,
        llm_api_key: str | None = None,
        llm_api_base: str | None = None,
        llm_model: str | None = None,
    ) -> dict:
        results = self.retrieve(question, top_k=top_k)

        if self.generation_mode == "extractive":
            answer = self._generate_extractive(results)

        elif self.generation_mode == "llm":
            answer = self._generate_with_llm(
                question=question,
                results=results,
                llm_api_key=llm_api_key,
                llm_api_base=llm_api_base,
                llm_model=llm_model,
            )

        else:
            raise ValueError(
                f"generation_mode tidak dikenal: {self.generation_mode}"
            )

        return {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "text": chunk.text,
                    "source": chunk.source,
                    "score": round(float(score), 3),
                }
                for chunk, score in results
            ],
        }

    def _generate_extractive(self, results) -> str:
        if (
            not results
            or results[0][1] < self.similarity_threshold
        ):
            return (
                "Maaf, saya tidak menemukan informasi yang "
                "relevan di dokumen yang tersedia."
            )

        best_chunk, _ = results[0]
        return best_chunk.text

    def _generate_with_llm(
        self,
        question: str,
        results,
        llm_api_key: str | None = None,
        llm_api_base: str | None = None,
        llm_model: str | None = None,
    ) -> str:
        # Periksa relevansi sebelum menghubungi layanan LLM.
        if (
            not results
            or results[0][1] < self.similarity_threshold
        ):
            return self._generate_extractive(results)

        # Konfigurasi dapat diberikan oleh aplikasi atau environment.
        api_key = (
            llm_api_key
            or os.environ.get("LLM_API_KEY")
        )
        api_base = (
            llm_api_base
            or os.environ.get(
                "LLM_API_BASE",
                "https://api.openai.com/v1",
            )
        ).rstrip("/")
        model = (
            llm_model
            or os.environ.get(
                "LLM_MODEL",
                "gpt-4o-mini",
            )
        )

        # Jika API key belum tersedia, gunakan jawaban ekstraktif.
        if not api_key:
            return self._generate_extractive(results)

        context = "\n\n".join(
            f"- {chunk.text}"
            for chunk, _ in results
        )

        prompt = f"""Kamu adalah asisten layanan publik Diskominfotik NTB.

Jawab pertanyaan warga hanya berdasarkan konteks dokumen.
Jangan mengarang informasi, persyaratan, biaya, alamat, atau prosedur.
Jika informasi yang ditanyakan tidak tercantum dalam konteks,
jelaskan bahwa informasi tersebut belum tersedia.
Jawab dalam bahasa Indonesia yang singkat, jelas, dan sopan.

Konteks dokumen:
{context}

Pertanyaan warga:
{question}

Jawaban:"""

        try:
            response = requests.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "temperature": 0.2,
                },
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()
            answer = data["choices"][0]["message"]["content"]

            if not isinstance(answer, str) or not answer.strip():
                return self._generate_extractive(results)

            return answer.strip()

        except (
            requests.exceptions.RequestException,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
        ):
            # Jika layanan gagal, RAG tetap dapat menjawab
            # menggunakan dokumen paling relevan.
            return self._generate_extractive(results)


if __name__ == "__main__":
    base_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    kb_path = os.path.join(
        base_dir,
        "data",
        "knowledge_ai_ntb.txt",
    )

    pipeline = RAGPipeline(
        generation_mode="extractive"
    )
    pipeline.index_kb_file(kb_path)

    pertanyaan_uji = [
        "Apa itu DDSS?",
        "Bagaimana cara lapor keluhan ke pemerintah?",
    ]

    for question in pertanyaan_uji:
        result = pipeline.generate_answer(
            question,
            top_k=1,
        )

        print(f"\nQ: {result['question']}")
        print(f"A: {result['answer'][:300]}...")

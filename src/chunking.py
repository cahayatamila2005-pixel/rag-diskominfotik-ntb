"""
Modul untuk memecah dokumen panjang menjadi potongan (chunk) kecil.
Chunking penting supaya sistem retrieval bisa mencari bagian paling relevan,
bukan seluruh dokumen sekaligus.
"""

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    """Representasi satu potongan teks beserta metadatanya."""
    id: int
    text: str
    source: str  # nama file/dokumen asal


def load_text(filepath: str) -> str:
    """Membaca isi file teks."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def split_into_paragraphs(text: str) -> list[str]:
    """
    Memecah teks berdasarkan baris kosong (antar paragraf/topik).
    Cocok untuk dokumen SOP yang tiap topiknya dipisah paragraf.
    """
    parts = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in parts if p.strip()]


def chunk_document(filepath: str, max_chars: int = 500) -> list[Chunk]:
    """
    Memecah satu file dokumen menjadi beberapa Chunk.
    Jika satu paragraf masih lebih panjang dari max_chars, paragraf itu
    dipecah lagi per kalimat supaya potongannya tidak terlalu besar.
    """
    text = load_text(filepath)
    paragraphs = split_into_paragraphs(text)
    source_name = filepath.split("/")[-1]

    chunks: list[Chunk] = []
    chunk_id = 0

    for para in paragraphs:
        if len(para) <= max_chars:
            chunks.append(Chunk(id=chunk_id, text=para, source=source_name))
            chunk_id += 1
        else:
            # Pecah per kalimat lalu gabungkan sampai mendekati max_chars
            sentences = re.split(r"(?<=[.!?])\s+", para)
            buffer = ""
            for sent in sentences:
                if len(buffer) + len(sent) <= max_chars:
                    buffer += (" " if buffer else "") + sent
                else:
                    if buffer:
                        chunks.append(Chunk(id=chunk_id, text=buffer, source=source_name))
                        chunk_id += 1
                    buffer = sent
            if buffer:
                chunks.append(Chunk(id=chunk_id, text=buffer, source=source_name))
                chunk_id += 1

    return chunks


if __name__ == "__main__":
    # Uji cepat modul ini
    result = chunk_document("data/sop_contoh.txt")
    print(f"Total chunk dihasilkan: {len(result)}\n")
    for c in result[:3]:
        print(f"[Chunk {c.id}] ({c.source})\n{c.text[:150]}...\n")
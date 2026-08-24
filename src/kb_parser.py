"""
Parser khusus untuk file knowledge base berformat Botpress-style:

    ## KATEGORI X: NAMA KATEGORI

    ### KB-001: Judul Entry

    **Pertanyaan:**
    - Pertanyaan variasi 1
    - Pertanyaan variasi 2

    **Jawaban:**
    Isi jawaban lengkap...

    **Keywords:** kata1, kata2, kata3

Setiap entry KB-XXX diperlakukan sebagai SATU chunk utuh, bukan dipotong
per paragraf seperti chunking generik. Ini penting karena satu entry KB
memang dirancang sebagai satu unit informasi yang lengkap dan berdiri sendiri.

Pertanyaan-pertanyaan variasi (training phrases) ikut dimasukkan ke teks
chunk supaya sistem retrieval lebih mudah mencocokkan pertanyaan user yang
mirip dengan salah satu variasi tersebut (bukan cuma cocok dengan jawabannya).
"""

from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class KBEntry:
    id: str            # contoh: "KB-001"
    category: str       # contoh: "LAYANAN PUBLIK"
    title: str           # contoh: "Layanan yang Tersedia"
    questions: list[str]
    answer: str
    keywords: list[str]

    def to_chunk_text(self) -> str:
        """
        Gabungkan judul + pertanyaan variasi + jawaban jadi satu teks,
        supaya retrieval bisa cocok baik lewat pertanyaan maupun isi jawaban.
        """
        q_text = "\n".join(f"- {q}" for q in self.questions)
        return (
            f"Topik: {self.title}\n"
            f"Kategori: {self.category}\n"
            f"Variasi pertanyaan terkait:\n{q_text}\n\n"
            f"Jawaban: {self.answer}"
        )


def parse_kb_file(filepath: str) -> list[KBEntry]:
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    entries: list[KBEntry] = []
    current_category = "UMUM"

    # Pecah berdasarkan heading kategori dan entry KB, jaga urutan kemunculan.
    # Pola dibuat TOLERAN terhadap emoji apapun (atau tanpa emoji sama sekali)
    # di depan kata "KATEGORI" -- ini penting karena karakter emoji gampang
    # rusak/berubah kalau file sempat di-copy-paste manual lewat Notepad dsb.
    blocks = re.split(r"(?=^##\s.*KATEGORI|^### KB-\d+:)", text, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        cat_match = re.match(r"^##\s.*?KATEGORI\s*\d*:?\s*(.+)$", block, flags=re.MULTILINE)
        if cat_match:
            current_category = cat_match.group(1).strip()
            continue

        kb_match = re.match(r"^### (KB-\d+):\s*(.+)$", block, flags=re.MULTILINE)
        if not kb_match:
            continue

        kb_id = kb_match.group(1).strip()
        title = kb_match.group(2).strip()

        # Ambil pertanyaan-pertanyaan (baris berawalan "- " di bawah **Pertanyaan:**)
        q_section = re.search(r"\*\*Pertanyaan:\*\*\s*(.*?)\*\*Jawaban:\*\*", block, flags=re.DOTALL)
        questions = []
        if q_section:
            questions = [
                line.strip("- ").strip()
                for line in q_section.group(1).strip().splitlines()
                if line.strip().startswith("-")
            ]

        # Ambil jawaban (dari **Jawaban:** sampai **Keywords:** atau akhir blok)
        a_section = re.search(r"\*\*Jawaban:\*\*\s*(.*?)(\*\*Keywords:\*\*|$)", block, flags=re.DOTALL)
        answer = a_section.group(1).strip() if a_section else ""

        # Ambil keywords
        kw_section = re.search(r"\*\*Keywords:\*\*\s*(.+)", block)
        keywords = [k.strip() for k in kw_section.group(1).split(",")] if kw_section else []

        entries.append(KBEntry(
            id=kb_id,
            category=current_category,
            title=title,
            questions=questions,
            answer=answer,
            keywords=keywords,
        ))

    return entries


if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "data", "knowledge_ai_ntb.txt")

    entries = parse_kb_file(path)
    print(f"Total entry berhasil di-parse: {len(entries)}\n")
    for e in entries[:3]:
        print(f"[{e.id}] {e.title} ({e.category})")
        print(f"  Variasi pertanyaan: {len(e.questions)}")
        print(f"  Panjang jawaban: {len(e.answer)} karakter")
        print(f"  Keywords: {e.keywords}\n")
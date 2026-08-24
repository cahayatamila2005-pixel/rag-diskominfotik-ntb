# Chatbot Layanan Publik Berbasis RAG — Diskominfotik NTB

Prototipe chatbot yang menjawab pertanyaan warga berdasarkan dokumen SOP/peraturan resmi,
menggunakan pendekatan **Retrieval-Augmented Generation (RAG)** sederhana.

## Struktur Proyek

```
rag-diskominfotik/
├── data/
│   ├── knowledge_ai_ntb.txt   # knowledge base ASLI Portal NTB (48 entry, format KB-XXX)
│   └── sop_contoh.txt         # contoh dokumen SOP bebas (opsional, format berbeda)
├── src/
│   ├── chunking.py         # memecah dokumen teks bebas jadi potongan kecil
│   ├── kb_parser.py        # parser khusus format knowledge base KB-XXX
│   ├── embedder.py         # mengubah teks jadi vektor (TF-IDF atau sentence-transformers)
│   ├── vector_store.py     # penyimpanan & pencarian vektor sederhana
│   ├── rag.py              # pipeline utama: indexing, retrieval, generation
│   └── app.py              # antarmuka web (Streamlit)
├── requirements.txt
└── README.md
```

## Cara Menjalankan

1. **Install dependensi** (butuh Python 3.10+ dan koneksi internet):
   ```bash
   pip install -r requirements.txt
   ```

2. **Coba pipeline lewat terminal dulu** (cepat, tanpa antarmuka web):
   ```bash
   cd src
   python rag.py
   ```
   Ini akan menjalankan 3 contoh pertanyaan uji dan menampilkan jawabannya.

3. **Jalankan antarmuka web**:
   ```bash
   streamlit run src/app.py
   ```
   Buka browser ke alamat yang muncul di terminal (biasanya `http://localhost:8501`).

## Mengganti / Menambah Data Knowledge Base

Data utama sudah pakai knowledge base asli Portal NTB (`data/knowledge_ai_ntb.txt`,
48 entry). Kalau ada update atau tambahan entry baru, cukup ikuti format yang sama:

```
### KB-XXX: Judul Topik

**Pertanyaan:**
- Variasi pertanyaan 1
- Variasi pertanyaan 2

**Jawaban:**
Isi jawaban lengkap...

**Keywords:** kata1, kata2, kata3
```

Lalu jalankan ulang `pipeline.index_kb_file(...)` — sistem otomatis mem-parsing ulang.

Kalau kamu punya dokumen SOP tambahan yang formatnya bebas (bukan format KB-XXX),
gunakan `pipeline.index_documents([...])` seperti pada `data/sop_contoh.txt`.

## Dua Mode yang Tersedia

| Aspek | Mode Extractive | Mode LLM |
|---|---|---|
| Kebutuhan internet/API | Tidak perlu | Perlu (API key LLM) |
| Kualitas jawaban | Menampilkan potongan dokumen apa adanya | Jawaban dirangkai natural |
| Cocok untuk | Demo cepat, instansi dengan pembatasan akses API eksternal | Hasil akhir yang lebih matang untuk laporan |

Untuk mengaktifkan mode LLM, set environment variable sebelum menjalankan:
```bash
export LLM_API_KEY="isi_dengan_api_key_kamu"
export LLM_API_BASE="https://api.groq.com/openai/v1"   # atau endpoint kompatibel OpenAI lainnya
export LLM_MODEL="llama-3.1-8b-instant"                  # sesuaikan dengan model yang tersedia
```
Lalu pilih mode "llm" di sidebar aplikasi Streamlit, atau ubah
`generation_mode="llm"` langsung di kode.

## Upgrade Embedding (Opsional)

Secara default proyek ini pakai **TF-IDF** (`TfidfEmbedder`) supaya bisa langsung
jalan tanpa instalasi tambahan. Untuk hasil pencarian yang lebih akurat secara makna
(bukan cuma kata yang sama persis), install dan pakai `STEmbedder`:

```bash
pip install sentence-transformers
```
```python
from embedder import STEmbedder
pipeline = RAGPipeline(embedder=STEmbedder(), generation_mode="extractive")
```

Perbandingan hasil TF-IDF vs sentence-transformers ini bisa jadi bagian menarik
di Bab IV (Pengujian & Evaluasi) laporan akhir kamu.

## Untuk Laporan PKL

Setiap modul di `src/` dipetakan langsung ke bagian metodologi yang sudah
dibahas di kerangka laporan:
- `chunking.py` → tahap persiapan data
- `embedder.py` & `vector_store.py` → tahap embedding & retrieval
- `rag.py` → integrasi retrieval + generation (inti dari RAG)
- `app.py` → implementasi antarmuka

Jangan lupa ambil screenshot hasil percobaan dan catat skor kemiripan (similarity
score) untuk beberapa pertanyaan sebagai bukti evaluasi di Bab IV.

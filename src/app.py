"""
Antarmuka web untuk chatbot RAG, menggunakan Streamlit.

Cara menjalankan (di laptop dengan Python & internet, dari folder root proyek):
    pip install -r requirements.txt
    streamlit run src/app.py
"""

import os
import streamlit as st
from styles import CUSTOM_CSS, skor_ke_kelas
from pipeline_loader import load_pipeline, KB_PATH
from logger import log_question
from feedback_logger import log_feedback
from kb_parser import parse_kb_file

st.set_page_config(page_title="Tanya NTB — Layanan Publik", page_icon="🏛️", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="ntb-banner">
        <div class="eyebrow">Portal Layanan Publik · Provinsi NTB</div>
        <h1>Tanya NTB</h1>
        <div class="subtitle">Asisten informasi layanan publik berbasis pencarian dokumen resmi (RAG)</div>
    </div>
    <div class="ntb-weave"></div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("#### Pengaturan")
    mode = st.radio(
        "Mode jawaban",
        options=["extractive (offline)", "llm (butuh API key)"],
        help="Extractive: tampilkan potongan dokumen langsung. LLM: jawaban dirangkai natural oleh AI.",
    )
    generation_mode = "extractive" if mode.startswith("extractive") else "llm"

    embedder_choice = st.radio(
        "Metode pencarian (embedding)",
        options=["TF-IDF (offline, cepat)", "Sentence-Transformers (lebih akurat, butuh internet)"],
        help="TF-IDF cocokkan kata persis. Sentence-Transformers memahami makna kalimat, lebih baik untuk pertanyaan dengan kata berbeda dari dokumen.",
    )
    embedder_type = "tfidf" if embedder_choice.startswith("TF-IDF") else "sentence-transformers"

    if generation_mode == "llm":
        api_key_input = st.text_input("LLM_API_KEY", type="password")
        if api_key_input:
            os.environ["LLM_API_KEY"] = api_key_input

    top_k = st.slider("Jumlah dokumen sumber yang dicari", 1, 5, 3)

    st.divider()
    st.caption("Basis pengetahuan: layanan Portal NTB")
    st.caption("🔐 Panel admin ada di menu halaman (sidebar atas)")


pipeline = load_pipeline(generation_mode, embedder_type)

if "messages" not in st.session_state:
    st.session_state.messages = []

try:
    kb_entries = parse_kb_file(KB_PATH)
except FileNotFoundError:
    kb_entries = []


def render_answer(answer: str, sources: list[dict]):
    if "tidak menemukan" in answer.lower():
        st.markdown(
            f"""
            <div class="kartu-kosong">
                <span class="label">Tidak ditemukan</span>
                {answer}
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.write(answer)

    with st.expander("📄 Lihat sumber dokumen yang digunakan"):
        for src in sources:
            kelas_skor = skor_ke_kelas(src["score"])
            st.markdown(
                f"""
                <div class="kartu-sumber">
                    <span class="sumber-label">{src['source']}</span>
                    <span class="skor-badge {kelas_skor}">skor {src['score']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.text(src["text"])


def render_feedback_widget(idx: int):
    msg = st.session_state.messages[idx]

    if "tidak menemukan" in msg["content"].lower():
        return

    if msg.get("feedback"):
        emoji = "👍" if msg["feedback"] == "like" else "👎"
        st.caption(f"Anda menilai jawaban ini {emoji} — terima kasih atas masukannya!")
        return

    col1, col2, _ = st.columns([1, 1, 8])
    pertanyaan_terkait = st.session_state.messages[idx - 1]["content"] if idx > 0 else ""

    with col1:
        if st.button("👍", key=f"like_{idx}"):
            msg["feedback"] = "like"
            log_feedback(pertanyaan_terkait, msg["content"], "like")
            st.rerun()
    with col2:
        if st.button("👎", key=f"dislike_{idx}"):
            msg["feedback"] = "dislike"
            log_feedback(pertanyaan_terkait, msg["content"], "dislike")
            st.rerun()


def ajukan_pertanyaan(pertanyaan: str):
    st.session_state.messages.append({"role": "user", "content": pertanyaan})
    result = pipeline.generate_answer(pertanyaan, top_k=top_k)

    terjawab = "tidak menemukan" not in result["answer"].lower()
    skor_teratas = result["sources"][0]["score"] if result["sources"] else 0.0
    sumber_teratas = result["sources"][0]["source"] if (terjawab and result["sources"]) else ""
    log_question(pertanyaan, terjawab, skor_teratas, sumber_teratas)

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "feedback": None,
    })


with st.expander("📚 Jelajahi berdasarkan kategori"):
    if not kb_entries:
        st.caption("Basis pengetahuan belum tersedia.")
    else:
        kategori_list = sorted(set(e.category for e in kb_entries))
        kategori_dipilih = st.selectbox(
            "Pilih kategori layanan",
            options=["-- Pilih kategori --"] + kategori_list,
            key="jelajah_kategori",
        )

        if kategori_dipilih != "-- Pilih kategori --":
            topik_kategori = [e for e in kb_entries if e.category == kategori_dipilih]
            st.caption(f"{len(topik_kategori)} topik dalam kategori ini — klik untuk langsung bertanya:")

            cols = st.columns(2)
            for i, entry in enumerate(topik_kategori):
                pertanyaan_wakil = entry.questions[0] if entry.questions else entry.title
                with cols[i % 2]:
                    if st.button(entry.title, key=f"topik_{entry.id}", use_container_width=True):
                        st.session_state.pending_question = pertanyaan_wakil
                        st.rerun()

if not st.session_state.messages and kb_entries:
    st.markdown("**💡 Pertanyaan populer:**")
    suggested = []
    seen_categories = set()
    for e in kb_entries:
        if e.category not in seen_categories and e.questions:
            suggested.append(e.questions[0])
            seen_categories.add(e.category)
        if len(suggested) >= 4:
            break

    cols_sugg = st.columns(2)
    for i, q in enumerate(suggested):
        with cols_sugg[i % 2]:
            if st.button(q, key=f"suggest_{i}", use_container_width=True):
                st.session_state.pending_question = q
                st.rerun()

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            render_answer(msg["content"], msg.get("sources", []))
            render_feedback_widget(i)
        else:
            st.write(msg["content"])

pertanyaan_ketik = st.chat_input("Tanyakan sesuatu, misal: 'Apa itu DDSS?'")
pertanyaan_dari_klik = st.session_state.pop("pending_question", None)
pertanyaan_final = pertanyaan_dari_klik or pertanyaan_ketik

if pertanyaan_final:
    with st.chat_message("user"):
        st.write(pertanyaan_final)

    with st.chat_message("assistant"):
        with st.spinner("Mencari jawaban..."):
            ajukan_pertanyaan(pertanyaan_final)
            idx_terbaru = len(st.session_state.messages) - 1
            last_result = st.session_state.messages[idx_terbaru]
            render_answer(last_result["content"], last_result.get("sources", []))
            render_feedback_widget(idx_terbaru)

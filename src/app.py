"""
Tanya NTB
Chatbot RAG Layanan Publik Provinsi NTB
"""

import streamlit as st

from styles import CUSTOM_CSS, skor_ke_kelas
from pipeline_loader import load_pipeline
from logger import log_question


# ============================================================
# KONFIGURASI
# ============================================================

st.set_page_config(
    page_title="Tanya NTB — Layanan Publik",
    page_icon="🏛️",
    layout="centered"
)


# ============================================================
# CSS PROJECT
# ============================================================

st.markdown(
    CUSTOM_CSS,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
"""<style>
.ntb-banner-final {
    background-color: #073b36;
    padding: 30px 30px 28px 30px;
    margin: 0;
    border-radius: 0;
}

.ntb-eyebrow-final {
    color: #f0b84b !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    margin-bottom: 10px !important;
    text-transform: uppercase !important;
}

.ntb-title-final {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 44px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    margin: 0 !important;
    padding: 0 !important;
}

.ntb-subtitle-final {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    line-height: 1.5 !important;
    margin-top: 10px !important;
}

.ntb-weave-final {
    height: 8px;
    margin: 0;
    background: repeating-linear-gradient(
        -45deg,
        #d9a441 0px,
        #d9a441 10px,
        transparent 10px,
        transparent 20px
    );
}

.category-title-final {
    color: #073b36 !important;
    font-size: 19px !important;
    font-weight: 700 !important;
    margin-top: 22px !important;
    margin-bottom: 10px !important;
}

.quick-title-final {
    color: #073b36 !important;
    font-size: 17px !important;
    font-weight: 700 !important;
    margin-top: 18px !important;
    margin-bottom: 8px !important;
}
</style>""",
    unsafe_allow_html=True
)


st.markdown(
"""<div class="ntb-banner-final"><div class="ntb-eyebrow-final">PORTAL LAYANAN PUBLIK · PROVINSI NTB</div><div class="ntb-title-final">Tanya NTB</div><div class="ntb-subtitle-final">Asisten informasi layanan publik berbasis pencarian dokumen resmi (RAG)</div></div><div class="ntb-weave-final"></div>""",
    unsafe_allow_html=True
)


# ============================================================
# PENGATURAN INTERNAL
# ============================================================

GENERATION_MODE = "extractive"
TOP_K = 3


# ============================================================
# LOAD PIPELINE
# ============================================================

pipeline = load_pipeline(GENERATION_MODE)


# ============================================================
# DATA KATEGORI
# ============================================================

kategori_pertanyaan = {
    "Semua Kategori": [
        "Apa saja layanan publik yang tersedia di Portal NTB?",
        "Bagaimana cara mendapatkan informasi layanan pemerintah?"
    ],

    "Layanan Publik": [
        "Apa saja layanan publik yang tersedia di Portal NTB?",
        "Bagaimana cara mengakses layanan publik NTB?"
    ],

    "PPID & Informasi Publik": [
        "Apa itu PPID?",
        "Bagaimana cara meminta informasi publik?"
    ],

    "Pengaduan Masyarakat": [
        "Bagaimana cara menyampaikan pengaduan?",
        "Kalau ingin melaporkan masalah pelayanan pemerintah, ke mana?"
    ],

    "SPBE & Teknologi Informasi": [
        "Apa itu SPBE?",
        "Apa yang dimaksud dengan layanan SPBE?"
    ],

    "Data & NTB Satu Data": [
        "Apa itu NTB Satu Data?",
        "Di mana saya bisa melihat data Provinsi NTB?"
    ],

    "Layanan Digital": [
        "Apa itu DDSS?",
        "Apa saja layanan digital pemerintah yang tersedia?"
    ],

    "Kontak & Informasi Kantor": [
        "Di mana lokasi kantor Diskominfotik NTB?",
        "Berapa nomor kontak Diskominfotik NTB?"
    ],

    "Layanan Kesehatan": [
        "Apa saja layanan kesehatan yang tersedia?",
        "Bagaimana cara mendapatkan informasi layanan kesehatan?"
    ],

    "Layanan Pendidikan": [
        "Apa saja layanan pendidikan yang tersedia?",
        "Bagaimana cara mendapatkan informasi penerimaan pendidikan?"
    ]
}


# ============================================================
# PILIH KATEGORI
# ============================================================

st.markdown(
"""<div class="category-title-final">🔎 Pilih Kategori Layanan</div>""",
    unsafe_allow_html=True
)

selected_category = st.selectbox(
    "Kategori layanan",
    list(kategori_pertanyaan.keys()),
    label_visibility="collapsed"
)


# ============================================================
# PERTANYAAN CEPAT
# ============================================================

st.markdown(
"""<div class="quick-title-final">💡 Pertanyaan Cepat</div>""",
    unsafe_allow_html=True
)

questions = kategori_pertanyaan[selected_category]

col1, col2 = st.columns(2)

with col1:
    if st.button(
        questions[0],
        use_container_width=True,
        key="question_1"
    ):
        st.session_state["pending_question"] = questions[0]

with col2:
    if st.button(
        questions[1],
        use_container_width=True,
        key="question_2"
    ):
        st.session_state["pending_question"] = questions[1]


# ============================================================
# FUNGSI MENAMPILKAN JAWABAN
# ============================================================

def render_answer(answer: str, sources: list[dict]):

    if "tidak menemukan" in answer.lower():

        st.markdown(
            f"""<div class="kartu-kosong"><span class="label">Tidak ditemukan</span><div>{answer}</div></div>""",
            unsafe_allow_html=True
        )

        return

    st.write(answer)

    if sources:

        with st.expander("📄 Lihat sumber dokumen yang digunakan"):

            for src in sources:

                score = src.get("score", 0.0)

                source_name = src.get(
                    "source",
                    "Dokumen tidak diketahui"
                )

                source_text = src.get(
                    "text",
                    ""
                )

                kelas_skor = skor_ke_kelas(score)

                st.markdown(
                    f"""<div class="kartu-sumber"><span class="sumber-label">{source_name}</span><span class="skor-badge {kelas_skor}">skor {score}</span></div>""",
                    unsafe_allow_html=True
                )

                st.text(source_text)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ============================================================
# RIWAYAT CHAT
# ============================================================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        if msg["role"] == "assistant":

            render_answer(
                msg["content"],
                msg.get("sources", [])
            )

        else:

            st.write(msg["content"])


# ============================================================
# INPUT CHAT
# ============================================================

chat_question = st.chat_input(
    "Tanyakan sesuatu, misal: 'Apa itu DDSS?'"
)


# ============================================================
# TENTUKAN PERTANYAAN
# ============================================================

question = None

if st.session_state.get("pending_question"):

    question = st.session_state["pending_question"]

    st.session_state["pending_question"] = None

elif chat_question:

    question = chat_question


# ============================================================
# PROSES PERTANYAAN
# ============================================================

if question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):

        with st.spinner("Mencari jawaban..."):

            try:

                result = pipeline.generate_answer(
                    question,
                    top_k=TOP_K
                )

                answer = result.get(
                    "answer",
                    "Maaf, sistem tidak menemukan jawaban."
                )

                sources = result.get(
                    "sources",
                    []
                )

                render_answer(
                    answer,
                    sources
                )

                terjawab = (
                    "tidak menemukan"
                    not in answer.lower()
                )

                if sources:

                    skor_teratas = sources[0].get(
                        "score",
                        0.0
                    )

                else:

                    skor_teratas = 0.0

                if terjawab and sources:

                    sumber_teratas = sources[0].get(
                        "source",
                        ""
                    )

                else:

                    sumber_teratas = ""

                log_question(
                    question,
                    terjawab,
                    skor_teratas,
                    sumber_teratas
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    }
                )

            except Exception as e:

                st.error(
                    "Maaf, terjadi kesalahan saat memproses pertanyaan."
                )

                with st.expander("Detail error"):

                    st.code(str(e))

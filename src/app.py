"""
Tanya NTB
Chatbot RAG Layanan Publik Provinsi NTB

Kategori dan pertanyaan dibaca otomatis dari:
data/knowledge_ai_ntb.txt
"""

import re
from pathlib import Path

import streamlit as st

from styles import CUSTOM_CSS, skor_ke_kelas
from pipeline_loader import load_pipeline
from logger import log_question


# ============================================================
# KONFIGURASI HALAMAN
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
# CSS TAMBAHAN
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

.category-info {
    color: #666666 !important;
    font-size: 13px !important;
    margin-top: 5px !important;
    margin-bottom: 10px !important;
}

</style>""",
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

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
# LOKASI KNOWLEDGE BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

KB_FILE = BASE_DIR / "data" / "knowledge_ai_ntb.txt"


# ============================================================
# FUNGSI MEMBACA KNOWLEDGE BASE
# ============================================================

@st.cache_data
def load_knowledge_base():

    if not KB_FILE.exists():

        return {}, 0


    try:

        text = KB_FILE.read_text(
            encoding="utf-8",
            errors="replace"
        )

    except Exception:

        text = KB_FILE.read_text(
            errors="replace"
        )


    # --------------------------------------------------------
    # Cari semua kategori
    # --------------------------------------------------------

    category_pattern = re.compile(
        r"^##\s*KATEGORI\s+\d+\s*:\s*(.+?)\s*$",
        re.MULTILINE
    )

    category_matches = list(
        category_pattern.finditer(text)
    )


    categories = {}


    # --------------------------------------------------------
    # Proses setiap kategori
    # --------------------------------------------------------

    for i, category_match in enumerate(category_matches):

        category_name = category_match.group(1).strip()


        start = category_match.end()


        if i + 1 < len(category_matches):

            end = category_matches[i + 1].start()

        else:

            end = len(text)


        category_text = text[
            start:end
        ]


        questions = []


        # ----------------------------------------------------
        # Cari setiap KB dalam kategori
        # ----------------------------------------------------

        kb_pattern = re.compile(
            r"^###\s*KB-\d+\s*:\s*(.+?)\s*$",
            re.MULTILINE
        )

        kb_matches = list(
            kb_pattern.finditer(category_text)
        )


        for j, kb_match in enumerate(kb_matches):

            kb_title = kb_match.group(1).strip()


            kb_start = kb_match.end()


            if j + 1 < len(kb_matches):

                kb_end = kb_matches[j + 1].start()

            else:

                kb_end = len(category_text)


            kb_text = category_text[
                kb_start:kb_end
            ]


            # ------------------------------------------------
            # Cari bagian Pertanyaan
            # ------------------------------------------------

            question_match = re.search(
                r"\*\*Pertanyaan:\*\*(.*?)(?=\n\s*\*\*Jawaban:|\Z)",
                kb_text,
                re.DOTALL | re.IGNORECASE
            )


            if question_match:

                question_text = question_match.group(1)


                found_questions = re.findall(
                    r"^\s*-\s*(.+?)\s*$",
                    question_text,
                    re.MULTILINE
                )


                for q in found_questions:

                    q = q.strip()

                    if q and q not in questions:

                        questions.append(q)


            # ------------------------------------------------
            # Kalau tidak ada pertanyaan, gunakan judul KB
            # ------------------------------------------------

            if not questions and kb_title:

                questions.append(
                    kb_title
                )


        categories[category_name] = questions


    return categories, len(category_matches)


# ============================================================
# LOAD KATEGORI
# ============================================================

kategori_data, jumlah_kategori = load_knowledge_base()


# ============================================================
# LOAD PIPELINE RAG
# ============================================================

pipeline = load_pipeline(
    GENERATION_MODE
)


# ============================================================
# CEK KNOWLEDGE BASE
# ============================================================

if not kategori_data:

    st.warning(
        "Kategori Knowledge Base tidak ditemukan. "
        "Pastikan file data/knowledge_ai_ntb.txt tersedia."
    )

    kategori_data = {
        "Semua Kategori": [
            "Apa saja layanan publik yang tersedia di NTB?"
        ]
    }


# ============================================================
# TAMBAHKAN SEMUA KATEGORI
# ============================================================

category_names = list(
    kategori_data.keys()
)


# ============================================================
# PILIH KATEGORI
# ============================================================

st.markdown(
"""<div class="category-title-final">🔎 Pilih Kategori Layanan</div>""",
    unsafe_allow_html=True
)


st.markdown(
f"""<div class="category-info">Tersedia {jumlah_kategori} kategori layanan dari Knowledge Base.</div>""",
    unsafe_allow_html=True
)


selected_category = st.selectbox(
    "Kategori layanan",
    category_names,
    label_visibility="collapsed"
)


# ============================================================
# PERTANYAAN DARI KATEGORI
# ============================================================

selected_questions = kategori_data.get(
    selected_category,
    []
)


# ============================================================
# PERTANYAAN CEPAT
# ============================================================

if selected_questions:

    st.markdown(
"""<div class="quick-title-final">💡 Pertanyaan Cepat</div>""",
        unsafe_allow_html=True
    )


    # Ambil maksimal 4 pertanyaan
    quick_questions = selected_questions[:4]


    # --------------------------------------------------------
    # Jika hanya 1 pertanyaan
    # --------------------------------------------------------

    if len(quick_questions) == 1:

        if st.button(
            quick_questions[0],
            use_container_width=True,
            key="quick_0"
        ):

            st.session_state[
                "pending_question"
            ] = quick_questions[0]


    # --------------------------------------------------------
    # Jika 2 pertanyaan
    # --------------------------------------------------------

    elif len(quick_questions) == 2:

        col1, col2 = st.columns(2)


        with col1:

            if st.button(
                quick_questions[0],
                use_container_width=True,
                key="quick_0"
            ):

                st.session_state[
                    "pending_question"
                ] = quick_questions[0]


        with col2:

            if st.button(
                quick_questions[1],
                use_container_width=True,
                key="quick_1"
            ):

                st.session_state[
                    "pending_question"
                ] = quick_questions[1]


    # --------------------------------------------------------
    # Jika 3 atau 4 pertanyaan
    # --------------------------------------------------------

    else:

        col1, col2 = st.columns(2)


        with col1:

            if st.button(
                quick_questions[0],
                use_container_width=True,
                key="quick_0"
            ):

                st.session_state[
                    "pending_question"
                ] = quick_questions[0]


        with col2:

            if st.button(
                quick_questions[1],
                use_container_width=True,
                key="quick_1"
            ):

                st.session_state[
                    "pending_question"
                ] = quick_questions[1]


        if len(quick_questions) > 2:

            col3, col4 = st.columns(2)


            with col3:

                if st.button(
                    quick_questions[2],
                    use_container_width=True,
                    key="quick_2"
                ):

                    st.session_state[
                        "pending_question"
                    ] = quick_questions[2]


            with col4:

                if len(quick_questions) > 3:

                    if st.button(
                        quick_questions[3],
                        use_container_width=True,
                        key="quick_3"
                    ):

                        st.session_state[
                            "pending_question"
                        ] = quick_questions[3]


# ============================================================
# FUNGSI MENAMPILKAN JAWABAN
# ============================================================

def render_answer(
    answer: str,
    sources: list[dict]
):

    if "tidak menemukan" in answer.lower():

        st.markdown(
            f"""<div class="kartu-kosong"><span class="label">Tidak ditemukan</span><div>{answer}</div></div>""",
            unsafe_allow_html=True
        )

        return


    st.write(answer)


    if sources:

        with st.expander(
            "📄 Lihat sumber dokumen yang digunakan"
        ):

            for src in sources:

                score = src.get(
                    "score",
                    0.0
                )

                source_name = src.get(
                    "source",
                    "Dokumen tidak diketahui"
                )

                source_text = src.get(
                    "text",
                    ""
                )

                kelas_skor = skor_ke_kelas(
                    score
                )


                st.markdown(
                    f"""<div class="kartu-sumber"><span class="sumber-label">{source_name}</span><span class="skor-badge {kelas_skor}">skor {score}</span></div>""",
                    unsafe_allow_html=True
                )


                st.text(
                    source_text
                )


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


if "pending_question" not in st.session_state:

    st.session_state.pending_question = None


# ============================================================
# TAMPILKAN RIWAYAT CHAT
# ============================================================

for msg in st.session_state.messages:

    with st.chat_message(
        msg["role"]
    ):

        if msg["role"] == "assistant":

            render_answer(
                msg["content"],
                msg.get(
                    "sources",
                    []
                )
            )

        else:

            st.write(
                msg["content"]
            )


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


if st.session_state.get(
    "pending_question"
):

    question = st.session_state[
        "pending_question"
    ]

    st.session_state[
        "pending_question"
    ] = None


elif chat_question:

    question = chat_question


# ============================================================
# PROSES PERTANYAAN
# ============================================================

if question:

    # --------------------------------------------------------
    # Simpan pertanyaan user
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )


    # --------------------------------------------------------
    # Tampilkan pertanyaan
    # --------------------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.write(
            question
        )


    # --------------------------------------------------------
    # Proses RAG
    # --------------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Mencari jawaban..."
        ):

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


                # ------------------------------------------------
                # Logging
                # ------------------------------------------------

                terjawab = (
                    "tidak menemukan"
                    not in answer.lower()
                )


                if sources:

                    skor_teratas = sources[
                        0
                    ].get(
                        "score",
                        0.0
                    )

                else:

                    skor_teratas = 0.0


                if terjawab and sources:

                    sumber_teratas = sources[
                        0
                    ].get(
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


                # ------------------------------------------------
                # Simpan jawaban
                # ------------------------------------------------

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


                with st.expander(
                    "Detail error"
                ):

                    st.code(
                        str(e)
                    )

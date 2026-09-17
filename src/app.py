"""
Tanya NTB
Chatbot informasi layanan publik berbasis Retrieval-Augmented Generation (RAG).

Cara menjalankan:
    streamlit run src/app.py
"""

import re
from pathlib import Path

import streamlit as st

from styles import CUSTOM_CSS, skor_ke_kelas
from pipeline_loader import load_pipeline
from logger import log_question


# =========================================================
# KONFIGURASI HALAMAN
# =========================================================

st.set_page_config(
    page_title="Tanya NTB — Layanan Publik",
    page_icon="🏛️",
    layout="centered"
)


# =========================================================
# CSS TAMBAHAN
# =========================================================

st.markdown(
    """
<style>

/* =====================================================
   SIDEBAR
   ===================================================== */

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #073b3a 0%,
        #0a4643 55%,
        #063331 100%
    );
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem;
}


/* =====================================================
   BRAND SIDEBAR
   ===================================================== */

.sidebar-brand {
    padding: 10px 8px 18px 8px;
}

.sidebar-logo {
    font-size: 32px;
    margin-bottom: 5px;
}

.sidebar-title {
    color: white;
    font-size: 24px;
    font-weight: 800;
    margin-bottom: 4px;
}

.sidebar-subtitle {
    color: #d4e7e4;
    font-size: 12px;
    line-height: 1.6;
}


/* =====================================================
   GARIS
   ===================================================== */

.sidebar-line {
    height: 1px;
    background: rgba(255,255,255,0.18);
    margin: 4px 8px 18px 8px;
}


/* =====================================================
   KARTU BANTUAN
   ===================================================== */

.sidebar-help {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 13px;
    padding: 14px;
    margin: 12px 4px;
}

.sidebar-help-title {
    color: white;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 7px;
}

.sidebar-help-text {
    color: #dcebea;
    font-size: 12px;
    line-height: 1.6;
}


/* =====================================================
   KARTU INFORMASI
   ===================================================== */

.sidebar-info {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 13px;
    padding: 13px;
    margin: 12px 4px;
}

.sidebar-info-title {
    color: white;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 9px;
}

.sidebar-info-item {
    color: #d8e9e7;
    font-size: 12px;
    margin: 7px 0;
    line-height: 1.4;
}


/* =====================================================
   FOOTER
   ===================================================== */

.sidebar-footer {
    color: rgba(255,255,255,0.55);
    font-size: 10px;
    text-align: center;
    line-height: 1.5;
    padding: 18px 5px 8px 5px;
}


/* =====================================================
   HEADER
   ===================================================== */

.ntb-banner-custom {
    background: #073b3a;
    padding: 28px 30px 25px 30px;
    border-radius: 0 0 16px 16px;
}

.ntb-eyebrow-custom {
    color: #e0ae43;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 9px;
}

.ntb-title-custom {
    color: white;
    font-size: 38px;
    font-weight: 800;
    margin: 0;
    line-height: 1.1;
}

.ntb-subtitle-custom {
    color: #d6e8e5;
    font-size: 14px;
    line-height: 1.6;
    margin-top: 9px;
    max-width: 700px;
}

.ntb-weave-custom {
    height: 10px;
    margin-bottom: 25px;
    background: repeating-linear-gradient(
        135deg,
        #d8a847 0px,
        #d8a847 7px,
        transparent 7px,
        transparent 15px
    );
}


/* =====================================================
   KATEGORI
   ===================================================== */

.category-intro {
    background: #f7f8f5;
    border: 1px solid #e4e8e4;
    border-radius: 12px;
    padding: 13px 15px;
    margin: 10px 0 12px 0;
}

.category-title {
    font-size: 15px;
    font-weight: 700;
    color: #254442;
    margin-bottom: 3px;
}

.category-description {
    font-size: 12px;
    color: #697775;
    line-height: 1.5;
}


/* =====================================================
   CONTOH PERTANYAAN
   ===================================================== */

.question-example {
    background: #f8faf8;
    border: 1px solid #e2e8e5;
    border-radius: 9px;
    padding: 9px 12px;
    margin: 6px 0;
    color: #294846;
    font-size: 12px;
    line-height: 1.5;
}


/* =====================================================
   KETERANGAN KOSONG
   ===================================================== */

.question-empty {
    background: #f8faf8;
    border: 1px solid #e2e8e5;
    border-radius: 9px;
    padding: 11px 13px;
    color: #697775;
    font-size: 12px;
    line-height: 1.5;
}


/* =====================================================
   RESPONSIVE
   ===================================================== */

@media (max-width: 700px) {

    .ntb-title-custom {
        font-size: 30px;
    }

    .ntb-banner-custom {
        padding: 22px 20px;
    }

}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# CSS PROJECT
# =========================================================

st.markdown(
    CUSTOM_CSS,
    unsafe_allow_html=True
)


# =========================================================
# PATH PROJECT
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# FILE KNOWLEDGE BASE
# =========================================================

KB_FILE = BASE_DIR / "data" / "knowledge_ai_ntb.txt"


# =========================================================
# FUNGSI MEMBERSIHKAN TEKS
# =========================================================

def bersihkan_teks(teks):
    """
    Membersihkan teks dari Markdown dan karakter
    yang tidak diperlukan.
    """

    if not teks:
        return ""

    teks = str(teks).strip()

    # Hapus bold Markdown
    teks = re.sub(r"\*+", "", teks)

    # Hapus backtick
    teks = teks.replace("`", "")

    # Hapus bullet
    teks = re.sub(
        r"^\s*[-•]\s*",
        "",
        teks
    )

    # Hapus spasi berlebihan
    teks = re.sub(
        r"\s+",
        " ",
        teks
    )

    return teks.strip()


# =========================================================
# VALIDASI PERTANYAAN
# =========================================================

def pertanyaan_valid(teks):
    """
    Memastikan teks merupakan pertanyaan yang valid.
    """

    if not teks:
        return False

    teks = bersihkan_teks(teks)

    if not teks:
        return False

    if len(teks) < 4:
        return False

    # Jangan tampilkan hanya karakter Markdown
    if teks in [
        "*",
        "**",
        "***"
    ]:
        return False

    # Harus memiliki minimal satu huruf/angka
    if not any(
        karakter.isalnum()
        for karakter in teks
    ):
        return False

    return True


# =========================================================
# BACA KNOWLEDGE BASE
# =========================================================

def baca_kategori_kb():
    """
    Membaca kategori dan contoh pertanyaan
    dari knowledge_ai_ntb.txt.

    Format KB:

    ## KATEGORI 1: APLIKASI & SISTEM

    ### KB-004: DDSS

    **Pertanyaan:**
    - Apa itu DDSS?
    - DDSS untuk apa?
    - Bagaimana cara menggunakan DDSS?

    **Jawaban:**
    ...
    """

    kategori_data = {}

    # -----------------------------------------------------
    # CEK FILE
    # -----------------------------------------------------

    if not KB_FILE.exists():
        return kategori_data


    # -----------------------------------------------------
    # BACA FILE
    # -----------------------------------------------------

    try:

        text = KB_FILE.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    except Exception:

        return kategori_data


    # -----------------------------------------------------
    # VARIABEL
    # -----------------------------------------------------

    current_category = None
    sedang_baca_pertanyaan = False


    # =====================================================
    # BACA SETIAP BARIS
    # =====================================================

    for line in text.splitlines():

        line = line.strip()


        # -------------------------------------------------
        # LEWATI BARIS KOSONG
        # -------------------------------------------------

        if not line:
            continue


        # =================================================
        # DETEKSI KATEGORI
        #
        # ## KATEGORI 1: APLIKASI & SISTEM
        # =================================================

        match_kategori = re.match(
            r"^##\s*KATEGORI\s+\d+\s*:\s*(.+?)\s*$",
            line,
            re.IGNORECASE
        )


        if match_kategori:

            current_category = bersihkan_teks(
                match_kategori.group(1)
            )

            sedang_baca_pertanyaan = False


            if current_category:

                if current_category not in kategori_data:

                    kategori_data[
                        current_category
                    ] = []


            continue


        # -------------------------------------------------
        # JIKA BELUM ADA KATEGORI
        # -------------------------------------------------

        if not current_category:
            continue


        # =================================================
        # DETEKSI HEADER PERTANYAAN
        #
        # **Pertanyaan:**
        # =================================================

        if re.match(
            r"^\*{0,2}\s*Pertanyaan\s*:\s*\*{0,2}\s*$",
            line,
            re.IGNORECASE
        ):

            sedang_baca_pertanyaan = True

            continue


        # =================================================
        # DETEKSI HEADER JAWABAN
        #
        # **Jawaban:**
        # =================================================

        if re.match(
            r"^\*{0,2}\s*Jawaban\s*:\s*\*{0,2}\s*$",
            line,
            re.IGNORECASE
        ):

            sedang_baca_pertanyaan = False

            continue


        # =================================================
        # DETEKSI KEYWORDS
        #
        # **Keywords:** ...
        # =================================================

        if re.match(
            r"^\*{0,2}\s*Keywords\s*:",
            line,
            re.IGNORECASE
        ):

            sedang_baca_pertanyaan = False

            continue


        # =================================================
        # AMBIL PERTANYAAN
        #
        # - Apa itu DDSS?
        # - DDSS untuk apa?
        # =================================================

        if sedang_baca_pertanyaan:

            # Hanya membaca bullet
            if re.match(
                r"^\s*[-•]\s+",
                line
            ):

                pertanyaan = bersihkan_teks(
                    line
                )


                if pertanyaan_valid(
                    pertanyaan
                ):

                    if pertanyaan not in kategori_data[
                        current_category
                    ]:

                        kategori_data[
                            current_category
                        ].append(
                            pertanyaan
                        )


    return kategori_data


# =========================================================
# LOAD KATEGORI
# =========================================================

kategori_data = baca_kategori_kb()

jumlah_kategori = len(
    kategori_data
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    # -----------------------------------------------------
    # BRAND
    # -----------------------------------------------------

    st.markdown(
        '<div class="sidebar-brand">'
        '<div class="sidebar-logo">🏛️</div>'
        '<div class="sidebar-title">Tanya NTB</div>'
        '<div class="sidebar-subtitle">'
        'Teman cari informasi<br>'
        'seputar NTB'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # GARIS
    # -----------------------------------------------------

    st.markdown(
        '<div class="sidebar-line"></div>',
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # BANTUAN
    # -----------------------------------------------------

    st.markdown(
        '<div class="sidebar-help">'
        '<div class="sidebar-help-title">'
        '💬 Butuh info?'
        '</div>'
        '<div class="sidebar-help-text">'
        'Tanya aja di kolom chat 😊<br>'
        'Saya bantu menemukan informasi '
        'dari dokumen resmi.'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # INFORMASI
    # -----------------------------------------------------

    st.markdown(
        f'<div class="sidebar-info">'
        f'<div class="sidebar-info-title">'
        f'📚 Informasi'
        f'</div>'
        f'<div class="sidebar-info-item">'
        f'• 🏛️ Layanan Pemerintah'
        f'</div>'
        f'<div class="sidebar-info-item">'
        f'• 📊 Data & Informasi NTB'
        f'</div>'
        f'<div class="sidebar-info-item">'
        f'• 📢 Bantuan & Pengaduan'
        f'</div>'
        f'<div class="sidebar-info-item">'
        f'• 📑 Dokumen & Peraturan'
        f'</div>'
        f'<div class="sidebar-info-item">'
        f'• ✨ {jumlah_kategori} kategori tersedia'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # CARA MENGGUNAKAN
    # -----------------------------------------------------

    st.markdown(
        '<div class="sidebar-help">'
        '<div class="sidebar-help-title">'
        '💡 Cara menggunakan'
        '</div>'
        '<div class="sidebar-help-text">'
        '1. Ketik pertanyaan kamu<br>'
        '2. Tekan Enter<br>'
        '3. Tanya NTB mencari informasi<br>'
        '4. Lihat jawaban dan sumbernya'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    st.markdown(
        '<div class="sidebar-footer">'
        'Tanya NTB · Layanan Informasi Publik<br>'
        'Provinsi Nusa Tenggara Barat'
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# HEADER UTAMA
# =========================================================

st.markdown(
    '<div class="ntb-banner-custom">'
    '<div class="ntb-eyebrow-custom">'
    'PORTAL LAYANAN PUBLIK · PROVINSI NTB'
    '</div>'
    '<div class="ntb-title-custom">'
    'Tanya NTB'
    '</div>'
    '<div class="ntb-subtitle-custom">'
    'Temukan informasi layanan publik NTB dengan mudah '
    'melalui chatbot berbasis RAG.'
    '</div>'
    '</div>'
    '<div class="ntb-weave-custom"></div>',
    unsafe_allow_html=True
)


# =========================================================
# KATEGORI
# =========================================================

if kategori_data:

    st.markdown(
        '<div class="category-intro">'
        '<div class="category-title">'
        '📚 Mau cari berdasarkan kategori?'
        '</div>'
        '<div class="category-description">'
        f'Tersedia {jumlah_kategori} kategori informasi '
        'dari Knowledge Base.'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # DAFTAR KATEGORI
    # -----------------------------------------------------

    daftar_kategori = list(
        kategori_data.keys()
    )


    # -----------------------------------------------------
    # DROPDOWN
    # -----------------------------------------------------

    kategori_pilihan = st.selectbox(
        "Pilih kategori",
        daftar_kategori,
        label_visibility="collapsed"
    )


    # -----------------------------------------------------
    # AMBIL PERTANYAAN
    # -----------------------------------------------------

    pertanyaan_kategori = kategori_data.get(
        kategori_pilihan,
        []
    )


    # -----------------------------------------------------
    # TAMPILKAN CONTOH PERTANYAAN
    # -----------------------------------------------------

    if pertanyaan_kategori:

        st.markdown(
            f"**💬 Contoh pertanyaan tentang "
            f"{kategori_pilihan}:**"
        )


        # Maksimal 4 pertanyaan
        for pertanyaan in pertanyaan_kategori[:4]:

            st.markdown(
                f'<div class="question-example">'
                f'💬 {pertanyaan}'
                f'</div>',
                unsafe_allow_html=True
            )


    # -----------------------------------------------------
    # JIKA KOSONG
    # -----------------------------------------------------

    else:

        st.markdown(
            f'<div class="question-empty">'
            f'💡 Silakan langsung tanyakan '
            f'informasi seputar {kategori_pilihan} '
            f'melalui kolom chat di bawah.'
            f'</div>',
            unsafe_allow_html=True
        )


    st.markdown("---")


# =========================================================
# KONFIGURASI RAG
# =========================================================

# Pengaturan RAG tidak ditampilkan kepada pengguna.

GENERATION_MODE = "extractive"

TOP_K = 3


# =========================================================
# LOAD PIPELINE
# =========================================================

pipeline = load_pipeline(
    GENERATION_MODE
)


# =========================================================
# FUNGSI MENAMPILKAN JAWABAN
# =========================================================

def render_answer(
    answer: str,
    sources: list[dict]
):

    # -----------------------------------------------------
    # TIDAK DITEMUKAN
    # -----------------------------------------------------

    if "tidak menemukan" in answer.lower():

        st.markdown(
            f'<div class="kartu-kosong">'
            f'<span class="label">'
            f'Tidak ditemukan'
            f'</span>'
            f'<div>{answer}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        return


    # -----------------------------------------------------
    # JAWABAN
    # -----------------------------------------------------

    st.write(
        answer
    )


    # -----------------------------------------------------
    # SUMBER
    # -----------------------------------------------------

    if sources:

        with st.expander(
            "📄 Lihat sumber dokumen yang digunakan"
        ):

            for src in sources:

                score = src.get(
                    "score",
                    0.0
                )


                kelas_skor = skor_ke_kelas(
                    score
                )


                source_name = src.get(
                    "source",
                    "Dokumen tidak diketahui"
                )


                source_text = src.get(
                    "text",
                    ""
                )


                st.markdown(
                    f'<div class="kartu-sumber">'
                    f'<span class="sumber-label">'
                    f'{source_name}'
                    f'</span>'
                    f'<span class="skor-badge '
                    f'{kelas_skor}">'
                    f'skor {score}'
                    f'</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )


                st.text(
                    source_text
                )


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# =========================================================
# TAMPILKAN RIWAYAT CHAT
# =========================================================

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


# =========================================================
# INPUT PERTANYAAN
# =========================================================

question = st.chat_input(
    "Tanyakan sesuatu, misal: Apa itu DDSS?"
)


# =========================================================
# PROSES PERTANYAAN
# =========================================================

if question:

    # -----------------------------------------------------
    # SIMPAN PERTANYAAN
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )


    # -----------------------------------------------------
    # TAMPILKAN PERTANYAAN
    # -----------------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.write(
            question
        )


    # -----------------------------------------------------
    # JAWABAN
    # -----------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "🔎 Sedang mencari informasi..."
        ):

            try:

                # -----------------------------------------
                # PROSES RAG
                # -----------------------------------------

                result = pipeline.generate_answer(
                    question,
                    top_k=TOP_K
                )


                # -----------------------------------------
                # AMBIL JAWABAN
                # -----------------------------------------

                answer = result.get(
                    "answer",
                    "Maaf, sistem tidak menemukan jawaban."
                )


                # -----------------------------------------
                # AMBIL SUMBER
                # -----------------------------------------

                sources = result.get(
                    "sources",
                    []
                )


                # -----------------------------------------
                # TAMPILKAN
                # -----------------------------------------

                render_answer(
                    answer,
                    sources
                )


                # -----------------------------------------
                # STATUS
                # -----------------------------------------

                terjawab = (
                    "tidak menemukan"
                    not in answer.lower()
                )


                # -----------------------------------------
                # SKOR
                # -----------------------------------------

                if sources:

                    skor_teratas = sources[
                        0
                    ].get(
                        "score",
                        0.0
                    )

                else:

                    skor_teratas = 0.0


                # -----------------------------------------
                # SUMBER UTAMA
                # -----------------------------------------

                if (
                    terjawab
                    and sources
                ):

                    sumber_teratas = sources[
                        0
                    ].get(
                        "source",
                        ""
                    )

                else:

                    sumber_teratas = ""


                # -----------------------------------------
                # LOGGING
                # -----------------------------------------

                log_question(
                    question,
                    terjawab,
                    skor_teratas,
                    sumber_teratas
                )


                # -----------------------------------------
                # SIMPAN JAWABAN
                # -----------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    }
                )


            except Exception as e:

                st.error(
                    "Maaf, terjadi kesalahan saat "
                    "memproses pertanyaan."
                )


                with st.expander(
                    "Detail error"
                ):

                    st.code(
                        str(e)
                    )
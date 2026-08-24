"""
Panel Admin — kelola knowledge base tanpa perlu edit kode.

Fitur:
  - Login sederhana pakai password
  - Lihat semua entry KB
  - Tambah entry baru
  - Edit / hapus entry yang sudah ada
  - Re-index otomatis setelah perubahan disimpan

Ganti password default di bagian ADMIN_PASSWORD sebelum dipakai sungguhan,
atau set environment variable ADMIN_PASSWORD supaya tidak tertulis di kode.
"""

import os
import sys

# Supaya bisa import modul dari src/ meski halaman ini ada di src/pages/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from style import CUSTOM_CSS
from kb_parser import parse_kb_file, KBEntry
from kb_writer import save_kb_file, next_kb_id
from pipeline_loader import load_pipeline, KB_PATH

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

st.set_page_config(page_title="Panel Admin — Tanya NTB", page_icon="🔐", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="ntb-banner">
        <div class="eyebrow">Portal Layanan Publik · Provinsi NTB</div>
        <h1>Panel Admin</h1>
        <div class="subtitle">Kelola basis pengetahuan chatbot Tanya NTB</div>
    </div>
    <div class="ntb-weave"></div>
    """,
    unsafe_allow_html=True,
)

# --- Gerbang login ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    with st.form("login_form"):
        password = st.text_input("Password admin", type="password")
        submitted = st.form_submit_button("Masuk")
        if submitted:
            if password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Password salah.")
    st.stop()

# --- Konten setelah login ---
col_a, col_b = st.columns([4, 1])
with col_a:
    st.success("Login berhasil sebagai admin.")
with col_b:
    if st.button("Keluar"):
        st.session_state.admin_logged_in = False
        st.rerun()

entries = parse_kb_file(KB_PATH)
st.caption(f"Total entry saat ini: {len(entries)}")

tab_lihat, tab_tambah, tab_edit = st.tabs(["📋 Lihat Semua", "➕ Tambah Entry", "✏️ Edit / Hapus"])

# =========================================================
# TAB: LIHAT SEMUA
# =========================================================
with tab_lihat:
    kategori_list = sorted(set(e.category for e in entries))
    filter_kategori = st.selectbox("Filter kategori", options=["Semua"] + kategori_list)

    tampil = entries if filter_kategori == "Semua" else [e for e in entries if e.category == filter_kategori]

    for e in tampil:
        with st.expander(f"{e.id} — {e.title}"):
            st.markdown(f"**Kategori:** {e.category}")
            st.markdown("**Variasi pertanyaan:**")
            for q in e.questions:
                st.markdown(f"- {q}")
            st.markdown(f"**Jawaban:** {e.answer}")
            st.markdown(f"**Keywords:** {', '.join(e.keywords)}")

# =========================================================
# TAB: TAMBAH ENTRY
# =========================================================
with tab_tambah:
    st.markdown("#### Tambah Entry Baru")

    kategori_existing = sorted(set(e.category for e in entries))
    pilih_kategori = st.selectbox(
        "Kategori", options=kategori_existing + ["+ Kategori baru..."], key="tambah_kategori_pilih"
    )
    if pilih_kategori == "+ Kategori baru...":
        kategori_final = st.text_input("Nama kategori baru", key="tambah_kategori_baru")
    else:
        kategori_final = pilih_kategori

    judul = st.text_input("Judul topik", key="tambah_judul")
    pertanyaan_raw = st.text_area(
        "Variasi pertanyaan (satu per baris)",
        key="tambah_pertanyaan",
        placeholder="Bagaimana cara membuat KTP?\nSyarat bikin KTP apa saja?",
        height=100,
    )
    jawaban = st.text_area("Jawaban lengkap", key="tambah_jawaban", height=150)
    keywords_raw = st.text_input(
        "Keywords (pisahkan dengan koma)", key="tambah_keywords", placeholder="ktp, identitas, kependudukan"
    )

    if st.button("💾 Simpan Entry Baru", type="primary"):
        if not (kategori_final and judul and pertanyaan_raw and jawaban):
            st.error("Kategori, judul, pertanyaan, dan jawaban wajib diisi.")
        else:
            new_entry = KBEntry(
                id=next_kb_id(entries),
                category=kategori_final.strip().upper(),
                title=judul.strip(),
                questions=[q.strip() for q in pertanyaan_raw.splitlines() if q.strip()],
                answer=jawaban.strip(),
                keywords=[k.strip() for k in keywords_raw.split(",") if k.strip()],
            )
            entries.append(new_entry)
            save_kb_file(KB_PATH, entries)
            load_pipeline.clear()  # paksa re-index saat halaman utama dibuka lagi
            st.success(f"Entry {new_entry.id} berhasil disimpan dan basis pengetahuan sudah di-reindex.")
            st.rerun()

# =========================================================
# TAB: EDIT / HAPUS
# =========================================================
with tab_edit:
    st.markdown("#### Edit atau Hapus Entry")

    if not entries:
        st.info("Belum ada entry.")
    else:
        opsi = [f"{e.id} — {e.title}" for e in entries]
        pilihan = st.selectbox("Pilih entry", options=opsi, key="edit_pilih")
        idx = opsi.index(pilihan)
        target = entries[idx]

        kategori_edit = st.text_input("Kategori", value=target.category, key="edit_kategori")
        judul_edit = st.text_input("Judul", value=target.title, key="edit_judul")
        pertanyaan_edit = st.text_area(
            "Variasi pertanyaan (satu per baris)",
            value="\n".join(target.questions),
            key="edit_pertanyaan",
            height=100,
        )
        jawaban_edit = st.text_area("Jawaban", value=target.answer, key="edit_jawaban", height=150)
        keywords_edit = st.text_input(
            "Keywords (pisahkan dengan koma)", value=", ".join(target.keywords), key="edit_keywords"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Simpan Perubahan", type="primary"):
                entries[idx] = KBEntry(
                    id=target.id,
                    category=kategori_edit.strip().upper(),
                    title=judul_edit.strip(),
                    questions=[q.strip() for q in pertanyaan_edit.splitlines() if q.strip()],
                    answer=jawaban_edit.strip(),
                    keywords=[k.strip() for k in keywords_edit.split(",") if k.strip()],
                )
                save_kb_file(KB_PATH, entries)
                load_pipeline.clear()
                st.success(f"Entry {target.id} berhasil diperbarui dan basis pengetahuan sudah di-reindex.")
                st.rerun()

        with col2:
            if st.button("🗑️ Hapus Entry", type="secondary"):
                entries.pop(idx)
                save_kb_file(KB_PATH, entries)
                load_pipeline.clear()
                st.success(f"Entry {target.id} berhasil dihapus dan basis pengetahuan sudah di-reindex.")
                st.rerun()
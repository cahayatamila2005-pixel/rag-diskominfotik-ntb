"""
Panel Admin — kelola knowledge base tanpa perlu edit kode.

Fitur:
  - Login sederhana pakai password
  - Lihat semua entry KB
  - Tambah entry baru
  - Edit / hapus entry yang sudah ada
  - Re-index otomatis setelah perubahan disimpan
  - Riwayat & statistik pertanyaan warga (termasuk feedback like/dislike)
  - Grafik & Statistik (tab terpisah)
  - Backup & restore otomatis

Ganti password default di bagian ADMIN_PASSWORD sebelum dipakai sungguhan,
atau set environment variable ADMIN_PASSWORD supaya tidak tertulis di kode.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from collections import Counter
from styles import CUSTOM_CSS
from kb_parser import parse_kb_file, KBEntry
from kb_writer import save_kb_file, next_kb_id, list_backups, restore_backup
from pipeline_loader import load_pipeline, KB_PATH
from logger import read_logs
from feedback_logger import read_feedback_logs

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

col_a, col_b = st.columns([4, 1])
with col_a:
    st.success("Login berhasil sebagai admin.")
with col_b:
    if st.button("Keluar"):
        st.session_state.admin_logged_in = False
        st.rerun()

entries = parse_kb_file(KB_PATH)
st.caption(f"Total entry saat ini: {len(entries)}")

tab_lihat, tab_tambah, tab_edit, tab_log, tab_grafik, tab_backup = st.tabs(
    ["📋 Lihat Semua", "➕ Tambah Entry", "✏️ Edit / Hapus", "📊 Riwayat Pertanyaan", "📈 Grafik & Statistik", "🗂️ Backup & Restore"]
)

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
            load_pipeline.clear()
            st.success(f"Entry {new_entry.id} berhasil disimpan dan basis pengetahuan sudah di-reindex.")
            st.rerun()

with tab_edit:
    st.markdown("#### Edit atau Hapus Entry")

    if not entries:
        st.info("Belum ada entry.")
    else:
        opsi = [f"{e.id} — {e.title}" for e in entries]
        pilihan = st.selectbox("Pilih entry", options=opsi, key="edit_pilih")
        idx = opsi.index(pilihan)
        target = entries[idx]

        st.markdown(
            f"""
            <div class="kartu-sumber">
                <span class="sumber-label">{target.id} · {target.category}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(f"**{target.title}**")
        for q in target.questions:
            st.markdown(f"- {q}")
        st.write(target.answer)
        st.caption(f"Keywords: {', '.join(target.keywords)}")

        col1, col2 = st.columns(2)
        with col1:
            konfirmasi_hapus = st.checkbox(f"Ya, hapus {target.id} ini", key="edit_konfirmasi_hapus")
        with col2:
            if st.button("🗑️ Hapus Entry", type="secondary", disabled=not konfirmasi_hapus):
                entries.pop(idx)
                save_kb_file(KB_PATH, entries)
                load_pipeline.clear()
                st.success(f"Entry {target.id} berhasil dihapus dan basis pengetahuan sudah di-reindex.")
                st.rerun()

        st.divider()

        edit_mode = st.checkbox("✏️ Edit entry ini", key="edit_mode_toggle")
        if edit_mode:
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

with tab_log:
    st.markdown("#### Riwayat Pertanyaan Warga")

    logs = read_logs()

    if not logs:
        st.info("Belum ada pertanyaan yang masuk dari warga.")
    else:
        total = len(logs)
        terjawab = sum(1 for r in logs if r["terjawab"] == "Ya")
        persen = round(terjawab / total * 100, 1) if total else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pertanyaan", total)
        col2.metric("Terjawab", f"{terjawab} ({persen}%)")
        col3.metric("Tidak Terjawab", total - terjawab)

        filter_status = st.selectbox(
            "Filter", options=["Semua", "Terjawab", "Tidak Terjawab"], key="log_filter"
        )
        if filter_status == "Terjawab":
            tampil = [r for r in logs if r["terjawab"] == "Ya"]
        elif filter_status == "Tidak Terjawab":
            tampil = [r for r in logs if r["terjawab"] == "Tidak"]
        else:
            tampil = logs

        st.caption(f"Menampilkan {len(tampil)} dari {total} pertanyaan (terbaru di atas)")
        st.dataframe(tampil, use_container_width=True, hide_index=True)

        tidak_terjawab_unik = sorted(set(
            r["pertanyaan"] for r in logs if r["terjawab"] == "Tidak"
        ))
        if tidak_terjawab_unik:
            with st.expander(f"❓ {len(tidak_terjawab_unik)} pertanyaan unik yang belum terjawab"):
                for q in tidak_terjawab_unik:
                    st.markdown(f"- {q}")

    st.divider()
    st.markdown("#### 👍👎 Feedback Warga terhadap Jawaban")

    feedback_logs = read_feedback_logs()
    if not feedback_logs:
        st.info("Belum ada feedback yang masuk dari warga.")
    else:
        total_fb = len(feedback_logs)
        suka = sum(1 for r in feedback_logs if r["feedback"] == "like")
        tidak_suka = total_fb - suka
        persen_suka = round(suka / total_fb * 100, 1) if total_fb else 0

        colf1, colf2, colf3 = st.columns(3)
        colf1.metric("Total Feedback", total_fb)
        colf2.metric("👍 Suka", f"{suka} ({persen_suka}%)")
        colf3.metric("👎 Tidak Suka", tidak_suka)

        with st.expander(f"Lihat semua {total_fb} feedback"):
            st.dataframe(feedback_logs, use_container_width=True, hide_index=True)

        dislike_list = [r for r in feedback_logs if r["feedback"] == "dislike"]
        if dislike_list:
            with st.expander(f"👎 {len(dislike_list)} jawaban yang mendapat dislike (perlu ditinjau)"):
                for r in dislike_list:
                    st.markdown(f"**Q:** {r['pertanyaan']}")
                    st.caption(f"A: {r['jawaban_singkat']}")
                    st.divider()

with tab_grafik:
    st.markdown("#### Grafik & Statistik")

    logs = read_logs()

    if not logs:
        st.info("Belum ada data pertanyaan untuk ditampilkan sebagai grafik.")
    else:
        tanggal_counter = Counter(r["waktu"][:10] for r in logs)
        tanggal_sorted = dict(sorted(tanggal_counter.items()))
        df_tanggal = pd.DataFrame(
            {"Jumlah Pertanyaan": list(tanggal_sorted.values())},
            index=list(tanggal_sorted.keys()),
        )
        st.markdown("##### 📅 Jumlah Pertanyaan per Hari")
        st.line_chart(df_tanggal)

        id_to_category = {e.id: e.category for e in entries}
        kategori_counter = Counter()
        for r in logs:
            sumber = r.get("sumber", "")
            if sumber:
                kb_id = sumber.split(" - ")[0].strip()
                kategori = id_to_category.get(kb_id, "Lainnya")
            else:
                kategori = "Tidak Terjawab"
            kategori_counter[kategori] += 1

        df_kategori = pd.DataFrame(
            {"Jumlah": list(kategori_counter.values())},
            index=list(kategori_counter.keys()),
        )
        st.markdown("##### 🏷️ Kategori Paling Sering Ditanya")
        st.bar_chart(df_kategori)

        total_logs = len(logs)
        terjawab_logs = sum(1 for r in logs if r["terjawab"] == "Ya")
        tidak_terjawab_logs = total_logs - terjawab_logs

        df_status = pd.DataFrame(
            {"Jumlah": [terjawab_logs, tidak_terjawab_logs]},
            index=["Terjawab", "Tidak Terjawab"],
        )
        st.markdown("##### ✅❌ Rasio Pertanyaan Terjawab vs Tidak")
        st.bar_chart(df_status)

    feedback_logs = read_feedback_logs()
    if feedback_logs:
        st.divider()
        suka = sum(1 for r in feedback_logs if r["feedback"] == "like")
        tidak_suka = len(feedback_logs) - suka
        df_feedback = pd.DataFrame(
            {"Jumlah": [suka, tidak_suka]},
            index=["👍 Suka", "👎 Tidak Suka"],
        )
        st.markdown("##### 👍👎 Distribusi Feedback Warga")
        st.bar_chart(df_feedback)

with tab_backup:
    st.markdown("#### Backup & Restore Data")
    st.caption("Setiap kali data disimpan/diubah, sistem otomatis membuat backup. Maksimal 20 backup terakhir disimpan.")

    backups = list_backups(KB_PATH)

    if not backups:
        st.info("Belum ada backup tersedia.")
    else:
        st.caption(f"Total backup tersedia: {len(backups)}")
        opsi_backup = [f"{b['waktu']}" for b in backups]
        pilihan_backup = st.selectbox("Pilih titik waktu untuk dipulihkan", options=opsi_backup, key="restore_pilih")
        idx_backup = opsi_backup.index(pilihan_backup)
        target_backup = backups[idx_backup]

        st.caption(f"File backup: {target_backup['filename']}")

        konfirmasi_restore = st.checkbox(
            f"Ya, pulihkan data ke kondisi {target_backup['waktu']} (kondisi SAAT INI juga akan otomatis di-backup dulu)",
            key="restore_konfirmasi",
        )
        if st.button("♻️ Pulihkan dari Backup Ini", type="primary", disabled=not konfirmasi_restore):
            restore_backup(KB_PATH, target_backup["path"])
            load_pipeline.clear()
            st.success(f"Berhasil dipulihkan ke kondisi {target_backup['waktu']}. Data sudah di-reindex.")
            st.rerun()

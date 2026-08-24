"""
Styling kustom untuk antarmuka chatbot, terinspirasi identitas visual NTB:
teal seperti laut Lombok, aksen emas seperti benang songket, dan motif garis
tipis mengambil dari pinggiran kain tenun sebagai elemen ciri khas halaman.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');

:root {
    --ink: #172422;
    --paper: #F6F2E7;
    --paper-card: #FCFAF3;
    --teal: #0E3D3B;
    --teal-deep: #0A2E2C;
    --gold: #C89B3C;
    --clay: #B8563C;
    --mist: #DCD5C3;
}

/* --- Latar & tipografi dasar --- */
.stApp {
    background-color: var(--paper);
}
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: var(--ink);
}

/* --- Sembunyikan header bawaan Streamlit yang polos --- */
header[data-testid="stHeader"] {
    background-color: transparent;
}

/* --- Banner judul kustom --- */
.ntb-banner {
    background: var(--teal-deep);
    margin: -1rem -1rem 1.75rem -1rem;
    padding: 1.6rem 2rem 1.1rem 2rem;
}
.ntb-banner .eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 0.35rem;
}
.ntb-banner h1 {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 2rem;
    color: var(--paper);
    margin: 0;
    line-height: 1.15;
}
.ntb-banner .subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 0.88rem;
    color: #C9D6D2;
    margin-top: 0.3rem;
}
/* motif garis tipis ala pinggiran tenun */
.ntb-weave {
    height: 6px;
    margin: 0 -1rem 1.5rem -1rem;
    background: repeating-linear-gradient(
        135deg,
        var(--gold) 0px, var(--gold) 8px,
        var(--paper) 8px, var(--paper) 16px
    );
    opacity: 0.85;
}

/* --- Sidebar --- */
section[data-testid="stSidebar"] {
    background-color: var(--teal-deep);
}
section[data-testid="stSidebar"] * {
    color: var(--paper) !important;
}
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stSlider label {
    font-size: 0.9rem;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(246,242,231,0.2);
}

/* --- Bubble chat --- */
div[data-testid="stChatMessage"] {
    background: transparent;
    padding: 0.15rem 0;
}
div[data-testid="stChatMessageContent"] {
    background: var(--paper-card);
    border: 1px solid var(--mist);
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
}

/* --- Input chat --- */
div[data-testid="stChatInput"] textarea {
    background: var(--paper-card);
    border: 1.5px solid var(--mist);
}

/* --- Kartu sumber (dalam expander) --- */
.kartu-sumber {
    background: var(--paper-card);
    border: 1px solid var(--mist);
    border-left: 3px solid var(--gold);
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.6rem;
}
.kartu-sumber .sumber-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--teal);
    font-weight: 500;
}
.skor-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    padding: 0.1rem 0.5rem;
    border-radius: 999px;
    margin-left: 0.4rem;
}
.skor-tinggi { background: #DCEEE8; color: #0E3D3B; }
.skor-sedang { background: #F3E9CE; color: #8A6A1E; }
.skor-rendah { background: #F1E2DB; color: var(--clay); }

/* --- Kartu status "tidak ditemukan" --- */
.kartu-kosong {
    background: #FBF1EC;
    border: 1px solid #E8C4B4;
    border-left: 3px solid var(--clay);
    border-radius: 8px;
    padding: 0.85rem 1.05rem;
    font-size: 0.92rem;
}
.kartu-kosong .label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--clay);
    display: block;
    margin-bottom: 0.25rem;
}
</style>
"""


def skor_ke_kelas(score: float) -> str:
    """Menentukan kelas CSS badge skor berdasarkan tingkat kemiripan."""
    if score >= 0.35:
        return "skor-tinggi"
    if score >= 0.20:
        return "skor-sedang"
    return "skor-rendah"
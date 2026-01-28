import streamlit as st

# ==========================================
# 0. PAGE CONFIG (WAJIB PALING ATAS)
# ==========================================
st.set_page_config(
    page_title="KUA Tangerang",
    layout="wide",
    page_icon="🏛️"
)
st.markdown("""
    <style>
        /* Paksa Sidebar jadi Gelap */
        [data-testid="stSidebar"] {
            background-color: #001a1a !important;
        }
        [data-testid="stSidebar"] * {
            color: #00FF00 !important;
        }
        
        /* Paksa Header atas jadi Gelap */
        [data-testid="stHeader"] {
            background-color: #001a1a !important;
            color: white !important;
        }
        
        /* Bikin tombol di sidebar jadi ijo neon */
        section[data-testid="stSidebar"] .stButton button {
            background-color: #003333 !important;
            color: #00FF00 !important;
            border: 1px solid #00FF00 !important;
        }
        
        /* Menghilangkan blok putih di judul atas */
        .stApp {
            background-color: #001a1a;
        }
    </style>
""", unsafe_allow_html=True)
# ==========================================
# 1. IMPORT LAIN (SETELAH PAGE CONFIG)
# ==========================================
import os
import base64
import time
from utils.database import load_data, save_data, load_config
from modules import (
    dashboard, surat_masuk, surat_keluar,
    bp4, wakaf, buku_tamu,
    akta_nikah, settings,
    duplikat_nikah, rumah_ibadah,
    stok_opname
)
from utils.ui import hide_sidebar

# ==========================================
# 2. SIDEBAR DIMATIKAN SEKALI SAJA
# ==========================================
hide_sidebar()

# ==========================================
# 3. INITIALIZE SESSION STATE
# ==========================================
if "logged_in" not in st.session_state:
    if "session_token" in st.query_params:
        st.session_state.logged_in = True
        st.session_state.user_role = st.query_params.get("role", "pegawai")
    else:
        st.session_state.logged_in = False

if "menu_selected" not in st.session_state:
    st.session_state.menu_selected = "🏠 Dashboard"

if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()

# ==========================================
# 4. LOAD CONFIG
# ==========================================
cfg = load_config()
favicon_path = "logo_kantor.png"

# ==========================================
# 5. SESSION TIMEOUT (30 MENIT)
# ==========================================
TIMEOUT_SECONDS = 30 * 60

if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > TIMEOUT_SECONDS:
        st.session_state.logged_in = False
        st.query_params.clear()
        st.rerun()
    else:
        st.session_state.last_activity = time.time()
# ==========================================
# 3. CSS GLOBAL (BEAST MODE DESIGN)
# ==========================================
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top left, #004d40, #00251a, #000000); background-attachment: fixed; }
    h1, h2, h3, p, span, label, div { color: white !important; font-family: 'Inter', sans-serif; }
    .glow-text { color: #00ff96 !important; text-shadow: 0 0 10px #00ff96, 0 0 20px #00ff96; font-weight: 900; text-align: center; }
    .login-box { background: rgba(255, 255, 255, 0.03); padding: 40px; border-radius: 20px; border: 1px solid rgba(0, 255, 150, 0.3); max-width: 450px; margin: auto; }
    
    /* SIDEBAR BUTTONS GLASS MORPHISM */
    div[data-testid="stSidebar"] .stButton button {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(0, 255, 150, 0.2) !important;
        color: white !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 10px 20px !important;
        border-radius: 12px !important;
        margin-bottom: 5px !important;
    }

    /* ACTIVE BUTTON NEON */
    div[data-testid="stSidebar"] .stButton button[kind="primary"] {
        background: #00ff96 !important;
        color: #000000 !important;
        font-weight: 900 !important;
        box-shadow: 0 0 20px rgba(0, 255, 150, 0.4);
        border: none !important;
    }
    /* TAMBAHKAN INI DI app.py (di dalam tag <style>) */
    .card-nav {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: 0.3s;
    }

    /* Variasi Warna Border Kiri agar beda tiap menu */
    .border-biru { border-left: 5px solid #00d4ff !important; }
    .border-merah { border-left: 5px solid #ff4b4b !important; }
    .border-hijau { border-left: 5px solid #00ff96 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}    
    </style>
    """, unsafe_allow_html=True)

def get_logo_html():
    if os.path.exists(favicon_path):
        with open(favicon_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        return f"<div style='text-align:center; border: 1px solid rgba(0, 255, 150, 0.3); border-radius: 15px; padding: 15px; margin-bottom: 20px; background: rgba(0,0,0,0.2);'><img src='data:image/png;base64,{img_b64}' style='width:80px;'></div>"
    return "<div style='text-align:center; font-size:50px; margin-bottom:20px; border: 1px solid rgba(0, 255, 150, 0.3); border-radius: 15px; padding: 15px;'>🏛️</div>"

# ==========================================
# 4. HALAMAN LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.container():
        st.markdown(f"<div class='login-box'>{get_logo_html()}<h2 class='glow-text'>EXECUTIVE LOGIN</h2><p style='text-align:center; opacity:0.6; margin-bottom:30px;'>{cfg['nama_kantor']}</p></div>", unsafe_allow_html=True)
        tab_pegawai, tab_admin = st.tabs(["👥 LOGIN PEGAWAI", "🔒 LOGIN ADMIN"])
        
        with tab_pegawai:
            u_peg = st.text_input("Username / NIP", key="u_peg")
            p_peg = st.text_input("Kode Akses", type="password", key="p_peg")
            if st.button("🚀 MASUK SEBAGAI PEGAWAI"):
                if p_peg == "kua-tangerang" and u_peg.strip() != "": 
                    st.session_state.logged_in = True
                    st.session_state.user_role = "pegawai"
                    st.query_params["session_token"] = "active"
                    st.query_params["role"] = "pegawai"
                    st.rerun()
                else: st.error("Gagal Login!")

        with tab_admin:
            u_adm = st.text_input("Admin ID", key="u_adm", value=cfg['admin_user'])
            p_adm = st.text_input("Admin Password", type="password", key="p_adm")
            if st.button("🔓 MASUK SEBAGAI ADMIN"):
                if u_adm == cfg['admin_user'] and p_adm == cfg['admin_pass']:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "admin"
                    st.query_params["session_token"] = "active"
                    st.query_params["role"] = "admin"
                    st.rerun()
                else: st.error("Admin Salah!")

# ==========================================
# 5. HALAMAN UTAMA (LOGGED IN) - VERSI CLEAN
# ==========================================
else:
    # Sidebar hanya untuk Branding & Logout
    with st.sidebar:
        if os.path.exists(favicon_path):
            st.image(favicon_path, width=80)
        st.markdown("<h3 class='glow-text' style='font-size: 1.2rem;'>Aplikasi Layanan KUA Tangerang</h3>", unsafe_allow_html=True)
        st.markdown("<br><hr style='opacity:0.2;'>", unsafe_allow_html=True)
        
        # Tombol Kembali ke Dashboard (Jika sedang di dalam modul)
        if st.session_state.menu_selected != "🏠 Dashboard":
            if st.button("🏠 Kembali ke Dashboard", use_container_width=True):
                st.session_state.menu_selected = "🏠 Dashboard"
                st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.query_params.clear() 
            st.rerun()

    # --- RENDER LOGIC ---
    menu = st.session_state.menu_selected
    
    # Map modul tetap sama seperti sebelumnya
    if menu == "🏠 Dashboard": 
        dashboard.render()
    elif menu == "📥 Surat Masuk": 
        surat_masuk.render()
    elif menu == "📤 Surat Keluar": 
        surat_keluar.render()
    elif menu == "👨‍👩‍👧‍👦 BP4": 
        bp4.render()
    elif menu == "🌱 Wakaf": 
        wakaf.render()
    elif menu == "🕌 Rumah Ibadah": 
        rumah_ibadah.render()
    elif menu == "📒 Buku Tamu": 
        buku_tamu.render()
    elif menu == "📜 Arsip Akta Nikah": 
        akta_nikah.render()
    elif menu == "📖 Duplikat Nikah": 
        duplikat_nikah.render()
    elif menu == "📦 Stok Opname": 
        stok_opname.render()
    elif menu == "⚙️ Control Settings": 

        settings.render()



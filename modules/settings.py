import streamlit as st
from utils.database import load_config, save_config

def render():
    st.markdown("<h1 style='font-weight: 800;'>⚙️ Control Settings</h1>", unsafe_allow_html=True)
    
    cfg = load_config()
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    
    st.subheader("🏢 Profil Kantor")
    nama_k = st.text_input("Nama Satker / KUA", value=cfg['nama_kantor'])
    
    st.markdown("---")
    st.subheader("🔐 Keamanan Akses")
    c1, c2 = st.columns(2)
    new_user = c1.text_input("Admin Username", value=cfg['admin_user'])
    new_pass = c2.text_input("Admin Password", value=cfg['admin_pass'], type="password")
    
    st.markdown("---")
    st.subheader("☁️ Sinkronisasi")
    g_url = st.text_input("Google Apps Script URL", value=cfg['google_url'])
    
    if st.button("💾 SIMPAN PERUBAHAN", use_container_width=True):
        new_data = {
            "nama_kantor": nama_k,
            "admin_user": new_user,
            "admin_pass": new_pass,
            "google_url": g_url
        }
        save_config(new_data)
        st.success("✅ Pengaturan Berhasil Disimpan! Silakan Refresh halaman.")
        st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)
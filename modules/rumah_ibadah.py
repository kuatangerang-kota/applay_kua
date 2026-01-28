import streamlit as st
import pandas as pd
import sqlite3

# 1. Koneksi Database
def get_connection():
    conn = sqlite3.connect("database_kua.db")
    return conn

# 2. Setup Tabel
def create_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rumah_ibadah 
                 (nama TEXT, jenis TEXT, jalan TEXT, rt TEXT, rw TEXT, 
                  kelurahan TEXT, kecamatan TEXT, kota TEXT, provinsi TEXT, 
                  pengurus TEXT, hp TEXT)''')
    conn.commit()
    conn.close()

def render():
    create_table()
    st.markdown("<h1 class='glow-text'>🕌 DATA RUMAH IBADAH</h1>", unsafe_allow_html=True)
    
    # --- FORM INPUT ---
    with st.form("form_rumah_ibadah"):
        col_nama, col_jenis = st.columns(2)
        with col_nama:
            nama = st.text_input("Nama Rumah Ibadah")
        with col_jenis:
            jenis = st.selectbox("Jenis", ["Masjid", "Musholla", "Gereja", "Vihara", "Pura", "Klenteng"])
        
        st.markdown("### 📍 Detail Lokasi")
        jalan = st.text_input("Nama Jalan / No. Rumah")
        
        c_rt, c_rw, c_kel = st.columns([1, 1, 2])
        with c_rt: rt = st.text_input("RT")
        with c_rw: rw = st.text_input("RW")
        with c_kel:
            kelurahan = st.selectbox("Kelurahan", ["Babakan", "Buaran Indah", "Cikokol", "Kelapa Indah", "Sukasari", "Sukajadi", "Sukarasa", "Tanah Tinggi"])
            
        # --- INI YANG GUA BALIKIN LAGI, BRO ---
        c_kec, c_kot, c_prov = st.columns(3)
        with c_kec:
            kecamatan = st.text_input("Kecamatan", value="Tangerang", disabled=True)
        with c_kot:
            kota = st.text_input("Kota", value="Kota Tangerang", disabled=True)
        with c_prov:
            provinsi = st.text_input("Provinsi", value="Banten", disabled=True)
            
        st.write("---")
        st.markdown("### 👤 Kontak Pengurus")
        col_pengurus, col_hp = st.columns([2, 1])
        with col_pengurus:
            pengelola = st.text_input("Nama Ketua DKM / Pengurus")
        with col_hp:
            no_hp = st.text_input("No. HP / WhatsApp")

        submit = st.form_submit_button("💾 SIMPAN DATA SEKARANG")
        
        if submit:
            if nama and jalan and no_hp:
                conn = get_connection()
                c = conn.cursor()
                # Simpan semua data termasuk kota & prov
                c.execute("INSERT INTO rumah_ibadah VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                          (nama, jenis, jalan, rt, rw, kelurahan, kecamatan, kota, provinsi, pengelola, no_hp))
                conn.commit()
                conn.close()
                st.success(f"✅ Berhasil Simpan: {nama}")
                st.rerun()
            else:
                st.error("❌ Nama, Jalan, dan No HP jangan dikosongin, Bro!")

    # --- TABEL DATA ASLI ---
    st.write("##")
    st.markdown("### 📋 Daftar Rumah Ibadah Tercatat")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM rumah_ibadah", conn)
    conn.close()
    
    if not df.empty:
        # Menampilkan tabel data yang beneran lu input
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Tombol Download Data Asli
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Excel (CSV)", data=csv, file_name='data_ibadah_tng.csv', mime='text/csv')
    else:
        st.info("Database masih kosong. Silakan input data di atas.")
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader

# 1. Konfigurasi Cloudinary
if "cloudinary" in st.secrets:
    cloudinary.config(
        cloud_name = st.secrets["cloudinary"]["cloud_name"],
        api_key = st.secrets["cloudinary"]["api_key"],
        api_secret = st.secrets["cloudinary"]["api_secret"],
        secure = True
    )

def load_data(jenis):
    # Paksa mapping nama agar sesuai dengan yang lu mau di Sheets
    mapping = {
        "surat_masuk": "masuk",
        "surat_keluar": "keluar",
        "buku_tamu": "tamu",
        "stok_opname": "stok"
    }
    
    # Kalau nama 'jenis' ada di mapping, ganti jadi nama barunya
    nama_tab = mapping.get(jenis, jenis)
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=nama_tab, ttl=0)
        return df.fillna("")
    except Exception as e:
        st.error(f"Error baca tab {nama_tab}: {e}")
        return pd.DataFrame()

def save_data(jenis, df):
    """Simpan data ke Google Sheets"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet=jenis, data=df)
        st.toast(f"✅ Data {jenis} Berhasil di-Backup!")
    except Exception as e:
        st.error(f"Gagal Sinkronisasi: {e}")

def delete_data(jenis, index):
    """Hapus data dari Google Sheets"""
    try:
        df = load_data(jenis)
        if not df.empty:
            df = df.drop(df.index[index])
            save_data(jenis, df)
    except Exception as e:
        st.error(f"Gagal hapus: {e}")

def save_uploaded_file(uploaded_file, category="umum"):
    """Upload file ke Cloudinary"""
    if uploaded_file:
        try:
            res = cloudinary.uploader.upload(uploaded_file, folder=f"applay_kua/{category}")
            return res['secure_url']
        except:
            return ""
    return ""

# --- FUNGSI TAMBAHAN AGAR TIDAK ERROR (DUMMY) ---

def load_config():
    """Mengambil konfigurasi lengkap agar main.py tidak error lagi"""
    return {
        "admin_user": "admin", # Tambahkan ini agar baris 146 aman
        "admin_password": "admin", 
        "app_name": "Applay KUA Tangerang",
        "nama_kantor": "KANTOR URUSAN AGAMA KECAMATAN TANGERANG"
    }

def save_config(config):
    """Agar modul settings tidak error"""
    return True

def simpan_ke_google_sheets(df, jenis):
    """Alias untuk save_data"""
    return save_data(jenis, df)





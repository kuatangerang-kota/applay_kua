import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader

# --- 1. CONFIG CLOUDINARY (Buat Upload File) ---
if "cloudinary" in st.secrets:
    cloudinary.config(
        cloud_name = st.secrets["cloudinary"]["cloud_name"],
        api_key = st.secrets["cloudinary"]["api_key"],
        api_secret = st.secrets["cloudinary"]["api_secret"],
        secure = True
    )

# --- 2. FUNGSI DATABASE ---
def load_data(jenis):
    # Mapping agar Python tau tab mana yang harus dibuka (sesuai gambar lu)
    mapping = {
        "surat_masuk": "data_masuk",
        "surat_keluar": "data_keluar",
        "buku_tamu": "data_tamu",
        "stok_opname": "data_stok",
        "akta_nikah": "data_akta_nik_baru",
        "duplikat_nikah": "data_duplikat_nikah",
        "wakaf": "data_wakaf",
        "bp4": "data_bp4",
        "rumah_ibadah": "data_rumah_ibadah"
    }
    nama_tab = mapping.get(jenis, jenis)
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=nama_tab, ttl=0)
        return df.fillna("")
    except:
        return pd.DataFrame()

def save_data(jenis, df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet=jenis, data=df)
        st.toast(f"✅ Data {jenis} Berhasil di-Update!")
    except:
        pass

def delete_data(jenis, index):
    try:
        df = load_data(jenis)
        if not df.empty:
            df = df.drop(df.index[index])
            save_data(jenis, df)
    except:
        pass

def save_uploaded_file(uploaded_file, category="umum"):
    """Fungsi ini yang dicari sama wakaf.py biar gak ImportError"""
    if uploaded_file:
        try:
            res = cloudinary.uploader.upload(uploaded_file, folder=f"applay_kua/{category}")
            return res['secure_url']
        except:
            return ""
    return ""

# --- 3. FUNGSI PENDUKUNG ---
def load_config():
    return {
        "admin_user": "admin",
        "admin_password": "admin", 
        "app_name": "Applay KUA Tangerang",
        "nama_kantor": "KUA KECAMATAN TANGERANG"
    }

def save_config(config): return True
def simpan_ke_google_sheets(df, jenis): return save_data(jenis, df)

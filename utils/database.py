import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader

# --- 1. CONFIG CLOUDINARY ---
if "cloudinary" in st.secrets:
    cloudinary.config(
        cloud_name = st.secrets["cloudinary"]["cloud_name"],
        api_key = st.secrets["cloudinary"]["api_key"],
        api_secret = st.secrets["cloudinary"]["api_secret"],
        secure = True
    )

# --- 2. FUNGSI UTAMA DATABASE ---
def load_data(jenis):
    mapping = {
        "surat_masuk": "masuk", "surat_keluar": "keluar", "buku_tamu": "tamu",
        "stok_opname": "stok", "akta_nikah": "akta_nik_baru"
    }
    nama_tab = mapping.get(jenis, jenis)
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=nama_tab, ttl=0)
        return df.fillna("")
    except Exception as e:
        st.error(f"❌ Gagal baca tab: '{nama_tab}'")
        return pd.DataFrame()

def save_data(jenis, df):
    mapping = {
        "surat_masuk": "masuk", "surat_keluar": "keluar", "buku_tamu": "tamu",
        "stok_opname": "stok", "akta_nikah": "akta_nik_baru"
    }
    nama_tab = mapping.get(jenis, jenis)
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet=nama_tab, data=df)
        st.toast(f"✅ Data {nama_tab} Berhasil di-Update!")
    except Exception as e:
        st.error(f"❌ Gagal simpan ke Sheets: {e}")

def delete_data(jenis, index):
    """Fungsi ini WAJIB ada buat bp4.py"""
    try:
        df = load_data(jenis)
        if not df.empty:
            df = df.drop(df.index[index])
            save_data(jenis, df)
    except Exception as e:
        st.error(f"❌ Gagal hapus: {e}")

def save_uploaded_file(uploaded_file, category="umum"):
    if uploaded_file:
        try:
            res = cloudinary.uploader.upload(uploaded_file, folder=f"applay_kua/{category}")
            return res['secure_url']
        except:
            return ""
    return ""

# --- 3. FUNGSI PENDUKUNG (AGAR TIDAK ERROR) ---
def load_config():
    return {
        "admin_user": "admin",
        "admin_password": "admin", 
        "app_name": "Applay KUA Tangerang",
        "nama_kantor": "KANTOR URUSAN AGAMA KECAMATAN TANGERANG"
    }

def save_config(config): return True
def simpan_ke_google_sheets(df, jenis): return save_data(jenis, df)

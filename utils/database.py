import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader

# Konek ke Cloudinary pake data dari Secrets
cloudinary.config(
    cloud_name = st.secrets["cloudinary"]["cloud_name"],
    api_key = st.secrets["cloudinary"]["api_key"],
    api_secret = st.secrets["cloudinary"]["api_secret"],
    secure = True
)

def load_data(jenis):
    """Ambil data dari Google Sheets"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=jenis, ttl="0")
        return df.fillna("")
    except:
        return pd.DataFrame()

def save_data(jenis, df):
    """Simpan data ke Google Sheets"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet=jenis, data=df)

def save_uploaded_file(uploaded_file, category="umum"):
    """Upload file ke Cloudinary & dapet link URL otomatis"""
    if uploaded_file:
        try:
            # File langsung terbang ke awan Cloudinary
            res = cloudinary.uploader.upload(uploaded_file, folder=f"applay_kua/{category}")
            # Link inilah yang bakal masuk ke tabel Google Sheets lu
            return res['secure_url']
        except Exception as e:
            st.error(f"Gagal upload ke Cloudinary: {e}")
            return ""
    return ""
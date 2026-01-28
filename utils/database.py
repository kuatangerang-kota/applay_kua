import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def load_data(jenis):
    # Mapping ini adalah 'penerjemah' antara kodingan dan nama tab di Sheets lu
    mapping = {
        "surat_masuk": "masuk",
        "surat_keluar": "keluar",
        "buku_tamu": "tamu",
        "stok_opname": "stok",
        "akta_nikah": "akta_nik_baru",
        "duplikat_nikah": "duplikat_nikah",
        "rumah_ibadah": "rumah_ibadah",
        "wakaf": "wakaf",
        "bp4": "bp4"
    }
    
    # Ambil nama tab dari mapping, kalau tidak ada pakai nama aslinya
    nama_tab = mapping.get(jenis, jenis)
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # WAJIB: Pakai nama_tab dan ttl=0 supaya data selalu terbaru
        df = conn.read(worksheet=nama_tab, ttl=0)
        return df.fillna("")
    except Exception as e:
        # Jika error, munculkan pesan di aplikasi biar kita tahu tab mana yang salah nama
        st.error(f"❌ Python gagal nemu tab: '{nama_tab}'. Pastikan di Sheets namanya '{nama_tab}' (huruf kecil semua)")
        return pd.DataFrame()

# Jangan lupa fungsi dummy ini tetap harus ada di bawahnya
def load_config():
    return {
        "admin_user": "admin",
        "admin_password": "admin", 
        "app_name": "Applay KUA Tangerang",
        "nama_kantor": "KANTOR URUSAN AGAMA KECAMATAN TANGERANG"
    }

def save_data(jenis, df):
    try:
        nama_tab = {
            "surat_masuk": "masuk", "surat_keluar": "keluar", "buku_tamu": "tamu",
            "stok_opname": "stok", "akta_nikah": "akta_nik_baru"
        }.get(jenis, jenis)
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet=nama_tab, data=df)
        st.toast(f"✅ Data {nama_tab} Berhasil di-Update!")
    except Exception as e:
        st.error(f"Gagal simpan: {e}")

def save_config(config): return True
def simpan_ke_google_sheets(df, jenis): return save_data(jenis, df)

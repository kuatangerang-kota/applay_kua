import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def load_data(jenis):
    # Mapping otomatis biar sinkron sama nama tab di gambar lu (image_8b9d3a.png)
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
        # Sekarang dia nyari tab 'data_wakaf', 'data_bp4', dll sesuai gambar lu
        df = conn.read(worksheet=nama_tab, ttl=0)
        return df.fillna("")
    except Exception as e:
        # Balikin kosong biar gak ngerusak dashboard kalau tab belum dibuat
        return pd.DataFrame()

# Fungsi pendukung lainnya biar modul gak error
def save_data(jenis, df): return None
def delete_data(jenis, index): return None
def load_config():
    return {"admin_user": "admin", "admin_pass": "kua123", "nama_kantor": "KUA KECAMATAN TANGERANG"}

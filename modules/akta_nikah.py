import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from PIL import Image
from utils.database import load_data, save_data
import base64

# Folder utama aplikasi
UPLOAD_DIR = "data_lokal/attachments/"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def render():
    st.markdown("<h1 class='glow-text' style='text-align: center;'>📜 DATABASE AKTA NIKAH</h1>", unsafe_allow_html=True)

    # 1. LOAD DATA
    df = load_data("akta_nik_baru")

    # 2. TRICK BIAR FORM KOSONG SETELAH SUKSES
    # Kita pakai 'form_tick' sebagai key. Kalau nilainya berubah, form otomatis reset.
    if "form_tick" not in st.session_state:
        st.session_state.form_tick = 0

    with st.expander("➕ INPUT DATA AKTA BARU", expanded=False):
        # Tambahkan key unik yang diambil dari session_state
        with st.form(f"form_akta_{st.session_state.form_tick}", clear_on_submit=False):
            c1, c2 = st.columns(2)
            no_in = c1.text_input("Nomor Akta")
            s_in = c1.text_input("Nama Suami").upper()
            i_in = c2.text_input("Nama Istri").upper()
            up_f = c2.file_uploader("Upload Scan (Wajib)", type=['jpg', 'jpeg', 'png', 'pdf'])
            
            submit_btn = st.form_submit_button("🚀 SIMPAN DATA")
            
            if submit_btn:
                # --- VALIDASI GAGAL (ISIAN TETAP ADA) ---
                if not no_in:
                    st.error("⚠️ Nomor Akta tidak boleh kosong!")
                elif not s_in:
                    st.error("⚠️ Nama Suami tidak boleh kosong!")
                elif not up_f:
                    st.error("❌ DOKUMEN WAJIB DIUPLOAD!")
                else:
                    # --- PROSES SIMPAN ---
                    if not df.empty and "no_akta" in df.columns and no_in in df['no_akta'].values:
                        st.error(f"❌ Nomor Akta {no_in} sudah ada!")
                    else:
                        # ... (Logika simpan file Anda tetap sama) ...
                        import re
                        match_tahun = re.search(r'(19|20)\d{2}', no_in)
                        tahun_arsip = match_tahun.group(0) if match_tahun else "Manual_Check"
                        PATH_TAHUN = os.path.join(UPLOAD_DIR, tahun_arsip)
                        if not os.path.exists(PATH_TAHUN): os.makedirs(PATH_TAHUN)
                        
                        no_aman = no_in.replace("/", "-").replace("\\", "-")
                        ext = up_f.name.split('.')[-1].lower()
                        fn = f"Akta_{no_aman}_{int(time.time())}.{ext}"
                        ps = os.path.join(PATH_TAHUN, fn)
                        
                        with open(ps, "wb") as f: f.write(up_f.getbuffer())
                        
                        # Update DB
                        new_row = {"no_akta": no_in, "suami": s_in, "istri": i_in, "file_scan": ps, "waktu_input": datetime.now().strftime("%Y-%m-%d %H:%M")}
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data("akta_nik_baru", df)
                        
                        # --- VALIDASI BERHASIL (WAJIB KOSONG) ---
                        st.success("🌟 DATA BERHASIL DISIMPAN!")
                        st.balloons()
                        
                        # Ubah nilai form_tick agar Streamlit menganggap form ini "baru"
                        st.session_state.form_tick += 1
                        time.sleep(1)
                        st.rerun()

    st.markdown("---")

    # --- 3. LOGIKA PENCARIAN (FUZZY MATCH: VERSI ACHMAD & AHMAD) ---
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    if "temp_query" not in st.session_state:
        st.session_state.temp_query = ""

    # KODE KERAMAT: Logika kemiripan nama yang diperluas
    def fuzzy_match(val, q):
        if not q: return False
        import re
        
        # 1. Normalisasi teks: Huruf besar, buang spasi, dan standarisasi bunyi
        v = str(val).strip().upper().replace("P", "F").replace("SY", "S").replace("DJ", "J").replace("I", "Y")
        qs = str(q).strip().upper().replace("P", "F").replace("SY", "S").replace("DJ", "J").replace("I", "Y")
        
        # 2. TAMBAHAN KHUSUS: Menangani ACHMAD vs AHMAD vs AKHMAD
        # Kita anggap CH dan KH itu sama dengan H agar pencarian lebih luas
        v = v.replace("CH", "H").replace("KH", "H")
        qs = qs.replace("CH", "H").replace("KH", "H")
        
        # 3. Normalisasi dobel huruf (MUHAMMAD -> MUHAMAD)
        v_clean = re.sub(r'(.)\1+', r'\1', v)
        qs_clean = re.sub(r'(.)\1+', r'\1', qs)
        
        return qs_clean in v_clean or qs in v

    def handle_search():
        st.session_state.search_query = st.session_state.temp_query

    def reset_pencarian():
        st.session_state.search_query = ""
        st.session_state.temp_query = ""

    col_search, col_btn_search, col_btn_reset = st.columns([3, 1, 1])
    
    with col_search:
        query_input = st.text_input(
            "🔍 Cari Nama atau No Akta", 
            placeholder="Contoh: Ahmad atau Achmad...",
            key="temp_query",
            on_change=handle_search
        )
    
    with col_btn_search:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 CARI", use_container_width=True, type="primary"):
            st.session_state.search_query = st.session_state.temp_query
            st.rerun()

    with col_btn_reset:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        if st.button("🧹 RESET", use_container_width=True, on_click=reset_pencarian):
            st.rerun()

    # --- 4. EKSEKUSI FILTER ---
    current_q = st.session_state.search_query
    
    if current_q:
        if not df.empty:
            # Jalankan logika fuzzy match pada setiap baris
            mask = df.apply(lambda row: any(fuzzy_match(v, current_q) for v in row), axis=1)
            df_view = df[mask]

            if not df_view.empty:
                st.success(f"✅ Ditemukan **{len(df_view)}** data untuk '{current_q}'")
                st.data_editor(df_view, use_container_width=True, hide_index=False, key="editor_akta")
                
                # --- 5. PREVIEW SCAN (LOGIKA JEMBATAN ARSIP LAMA & BARU) ---
                st.markdown("---")
                pilihan_label = ["--- Pilih Data untuk Preview ---"] + \
                                [f"{r.get('no_akta','?')} - {r.get('suami', 'Tanpa Nama')}" for _, r in df_view.iterrows()]
                
                terpilih = st.selectbox("Pilih berkas:", pilihan_label, key="pilih_preview")

                if terpilih != "--- Pilih Data untuk Preview ---":
                    idx_pilih = pilihan_label.index(terpilih) - 1
                    row_pilih = df_view.iloc[idx_pilih]
                    
                    path_database = str(row_pilih.get('file_scan', ''))
                    
                    path_lengkap = path_database
                    if not os.path.exists(path_lengkap):
                        nama_file_saja = os.path.basename(path_database)
                        path_lama = os.path.join(UPLOAD_DIR, nama_file_saja)
                        if os.path.exists(path_lama):
                            path_lengkap = path_lama

                    # Render File
                    if os.path.exists(path_lengkap):
                        if path_lengkap.lower().endswith('.pdf'):
                            with open(path_lengkap, "rb") as f:
                                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                            st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800"></iframe>', unsafe_allow_html=True)
                        else:
                            st.image(path_lengkap, use_container_width=True)
                    else:
                        st.error(f"⚠️ Berkas tidak ditemukan di folder lama maupun baru.")
            else:
                # --- NOTIFIKASI DATA TIDAK DITEMUKAN ---
                st.warning(f"🕵️‍♂️ Data dengan kata kunci '{current_q}' tidak ditemukan.")
                st.info("Saran: Coba gunakan potongan nama saja atau cek kembali nomor akta yang dicari.")
        else:
            st.error("⚠️ Database masih kosong. Input data dulu Bro!")
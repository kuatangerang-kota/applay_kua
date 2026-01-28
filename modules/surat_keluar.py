import streamlit as st
import pandas as pd
import os
import time
import base64
from datetime import datetime
from utils.database import load_data, save_data, delete_data, save_uploaded_file

def render():
    st.markdown("<h1 style='font-weight: 800;'>📤 Manajemen Surat Keluar</h1>", unsafe_allow_html=True)
    
    # 1. LOAD DATA
    df_raw = load_data("keluar")
    
    # Normalisasi & Filter Tahun
    if not df_raw.empty:
        df_raw.columns = [str(c).strip().lower().replace(" ", "_") for c in df_raw.columns]
        df_raw['dt_object'] = pd.to_datetime(df_raw['tanggal_kirim'], errors='coerce')
        df_raw['tahun_arsip'] = df_raw['dt_object'].dt.year.fillna(0).astype(int)
    else:
        df_raw = pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["📝 Registrasi Keluar", "📁 Arsip & Kelola", "📊 Preview & Cetak"])

    # --- TAB 1: INPUT ---
    with tab1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.form("fm_keluar_beast", clear_on_submit=True):
            c1, c2 = st.columns(2)
            no_s = c1.text_input("Nomor Surat Keluar")
            tgl_k = c2.date_input("Tanggal Dikirim", datetime.now())
            tujuan = c1.text_input("Instansi Tujuan")
            perihal = c2.text_input("Perihal")
            up_f = st.file_uploader("Upload Scan (PDF/JPG)", type=['pdf', 'jpg', 'jpeg', 'png'])
            
            if st.form_submit_button("🚀 SIMPAN SURAT KELUAR"):
                if no_s and tujuan:
                    fn = save_uploaded_file(up_f, category="surat_keluar")
                    new_row = {
                        "no_surat": no_s, "tanggal_kirim": str(tgl_k),
                        "tujuan": tujuan, "perihal": perihal,
                        "nama_file": fn, "waktu_input": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    df_new = pd.concat([df_raw, pd.DataFrame([new_row])], ignore_index=True)
                    # Bersihkan kolom pembantu sebelum save
                    cols_to_drop = [c for c in ['dt_object', 'tahun_arsip'] if c in df_new.columns]
                    save_data("keluar", df_new.drop(columns=cols_to_drop))
                    st.success("Surat Keluar Berhasil Diarsipkan!")
                    st.rerun()

    # --- TAB 2: MANAJEMEN ---
    with tab2:
        if not df_raw.empty:
            list_tahun = sorted(df_raw['tahun_arsip'].unique(), reverse=True)
            thn_sel = st.selectbox("📂 Pilih Tahun Arsip:", list_tahun, key="thn_kel_arsip")
            
            # --- BAGIAN INI YANG MEMPERBAIKI NOMOR URUT ---
            # Filter berdasarkan tahun
            df_filtered = df_raw[df_raw['tahun_arsip'] == thn_sel].copy()
            
            # Simpan index asli database ke kolom tersembunyi agar tidak hilang saat diedit
            df_filtered['original_index'] = df_filtered.index 
            
            # Reset index agar tampilan mulai dari 1, 2, 3...
            df_display = df_filtered.drop(columns=['dt_object', 'tahun_arsip', 'original_index']).reset_index(drop=True)
            df_display.index += 1 
            
            st.markdown(f"**Menampilkan Arsip Tahun: {thn_sel}**")
            edited_display = st.data_editor(
                df_display, 
                use_container_width=True, 
                hide_index=False, 
                disabled=["nama_file", "waktu_input"], 
                key=f"editor_kel_{thn_sel}"
            )
            
            c_up, c_del = st.columns([3, 1])
            
            if c_up.button("💾 SIMPAN PERUBAHAN TABEL", use_container_width=True):
                # Kembalikan data yang diedit ke posisi index aslinya
                for i, row in edited_display.iterrows():
                    orig_idx = df_filtered.iloc[i-1]['original_index']
                    for col in edited_display.columns:
                        df_raw.at[orig_idx, col] = row[col]
                
                # Simpan
                final_save = df_raw.drop(columns=['dt_object', 'tahun_arsip', 'original_index'], errors='ignore')
                save_data("keluar", final_save)
                st.success("Perubahan Berhasil Disimpan!")
                st.rerun()

            with c_del:
                target_no_urut = st.selectbox("Hapus No Urut:", df_display.index, key="del_idx_kel")
                if st.button("🗑️ HAPUS", type="primary", use_container_width=True):
                    # Cari index asli dari nomor urut yang dipilih
                    real_idx_to_delete = df_filtered.iloc[target_no_urut-1]['original_index']
                    
                    # Hapus file fisik
                    f_name = df_raw.at[real_idx_to_delete, 'nama_file']
                    f_path = os.path.join("data_lokal/attachments/", str(f_name))
                    if f_name and os.path.exists(f_path):
                        try: os.remove(f_path)
                        except: pass
                        
                    # Hapus dari dataframe dan save
                    df_final = df_raw.drop(real_idx_to_delete)
                    final_save = df_final.drop(columns=['dt_object', 'tahun_arsip', 'original_index'], errors='ignore')
                    save_data("keluar", final_save)
                    st.rerun()
        else:
            st.info("Belum ada data surat keluar.")

    # --- TAB 3: PREVIEW & REKAP ---
    with tab3:
        if not df_raw.empty:
            st.subheader("🔍 Preview Dokumen")
            c_p1, c_p2 = st.columns(2)
            
            # Mapping bulan untuk keperluan filter
            BULAN_INDONESIA = {
                1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
            }

            list_thn_prev = sorted(df_raw['tahun_arsip'].unique(), reverse=True)
            thn_p = c_p1.selectbox("Filter Tahun:", list_thn_prev, key="prev_thn_kel")
            
            df_prev = df_raw[df_raw['tahun_arsip'] == thn_p]
            sel_preview = c_p2.selectbox("Pilih Nomor Surat:", ["-"] + df_prev["no_surat"].tolist(), key="prev_cet_kel")
            
            # BAGIAN 1: PREVIEW FILE SCAN
            if sel_preview != "-":
                data_row = df_prev[df_prev["no_surat"] == sel_preview].iloc[0]
                col_view, col_info = st.columns([2, 1])
                
                with col_info:
                    st.markdown(f"""
                    <div style='background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; border: 1px solid #00ff96;'>
                        <h4 style='color: #00ff96; margin-top:0;'>Detail Surat</h4>
                        <p><b>No Surat:</b> {data_row['no_surat']}</p>
                        <p><b>Tujuan:</b> {data_row['tujuan']}</p>
                        <p><b>Perihal:</b> {data_row['perihal']}</p>
                    </div>""", unsafe_allow_html=True)

                with col_view:
                    fn_p = data_row.get('nama_file', '')
                    path_p = os.path.join("data_lokal", "attachments", "surat_keluar", str(fn_p))
                    if fn_p and os.path.exists(path_p):
                        if str(fn_p).lower().endswith('.pdf'):
                            with open(path_p, "rb") as f:
                                b64 = base64.b64encode(f.read()).decode('utf-8')
                            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" style="border-radius:10px;"></iframe>', unsafe_allow_html=True)
                        else:
                            st.image(path_p, use_container_width=True)
                    else:
                        st.warning("⚠️ File scan tidak ditemukan.")

            # BAGIAN 2: RINGKASAN BULANAN (Selalu tampil di bawah)
            st.markdown("---")
            st.subheader("📊 Ringkasan Bulanan Surat Keluar")
            
            col_bln, col_thn = st.columns(2)
            bulan_pilih = col_bln.selectbox("Bulan Rekap", list(BULAN_INDONESIA.values()), 
                                            index=datetime.now().month-1, key="bln_keluar")
            tahun_pilih = col_thn.selectbox("Tahun Rekap", [2024, 2025, 2026], 
                                            index=1, key="thn_keluar")
            
            df_rk = df_raw.copy()
            if not df_rk.empty:
                # Pastikan kolom tanggal kirim sudah jadi datetime untuk filter
                df_rk['dt_temp'] = pd.to_datetime(df_rk['tanggal_kirim'], errors='coerce')
                angka_bln = [k for k, v in BULAN_INDONESIA.items() if v == bulan_pilih][0]
                
                df_filtered_k = df_rk[(df_rk['dt_temp'].dt.month == angka_bln) & 
                                      (df_rk['dt_temp'].dt.year == tahun_pilih)]
                
                if not df_filtered_k.empty:
                    # Tampilkan Tabel
                    st.dataframe(df_filtered_k.drop(columns=['dt_temp', 'dt_object', 'tahun_arsip'], errors='ignore'), 
                                 use_container_width=True, hide_index=True)
                    
                    # Tombol Cetak Rekap Bulanan
                    from utils.pdf_gen import create_rekap_surat_pdf
                    pdf_rek_keluar = create_rekap_surat_pdf(df_filtered_k, "keluar", bulan_pilih, tahun_pilih)
                    st.download_button(
                        label=f"📂 DOWNLOAD REKAP SURAT KELUAR {bulan_pilih.upper()}",
                        data=pdf_rek_keluar,
                        file_name=f"Rekap_Surat_Keluar_{bulan_pilih}_{tahun_pilih}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.info(f"ℹ️ Tidak ada data surat keluar pada bulan {bulan_pilih} {tahun_pilih}.")
        else:
            st.info("📂 Belum ada data surat keluar untuk ditampilkan.")
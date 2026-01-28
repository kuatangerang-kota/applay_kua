import streamlit as st
from utils.database import load_data, save_data, delete_data, save_uploaded_file
from utils.pdf_gen import create_disposisi_pdf
import pandas as pd
from datetime import datetime
import os
import base64
import time

# Mapping Bulan Indonesia
BULAN_INDONESIA = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def render():
    st.markdown("<h1 style='font-weight: 800;'>📥 Manajemen Surat Masuk</h1>", unsafe_allow_html=True)
    
    df = load_data("masuk")
    
    if not df.empty:
        df['dt_object'] = pd.to_datetime(df['Tanggal Terima'], errors='coerce')
        df['tahun_arsip'] = df['dt_object'].dt.year.fillna(0).astype(int)
    
    tab1, tab2, tab3 = st.tabs(["📝 Registrasi Baru", "📂 Arsip & Manajemen", "📊 Preview & Cetak"])

    with tab1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.form("fm_masuk_beast", clear_on_submit=True):
            c1, c2 = st.columns(2)
            no_surat = c1.text_input("Nomor Surat Resmi")
            tgl_terima = c2.date_input("Tanggal Diterima", datetime.now())
            pengirim = c1.text_input("Instansi Pengirim")
            perihal = c2.text_input("Perihal")
            up_file = st.file_uploader("Upload Scan Surat", type=['pdf', 'jpg', 'png'])
            disposisi = st.text_area("Instruksi / Disposisi Awal")

            if st.form_submit_button("🚀 ARSIPKAN SURAT"):
                if no_surat and pengirim:
                    fn = save_uploaded_file(up_file, category="surat_masuk")
                    wkt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_entry = {
                        "No Surat": no_surat, "Tanggal Terima": str(tgl_terima),
                        "Pengirim": pengirim, "Perihal": perihal,
                        "Disposisi": disposisi if disposisi else "-",
                        "Nama File": fn, "Waktu Input": wkt
                    }
                    df_new = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                    if 'dt_object' in df_new.columns: df_new = df_new.drop(columns=['dt_object', 'tahun_arsip'])
                    save_data("masuk", df_new)
                    st.success("Berhasil disimpan!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        if not df.empty:
            list_tahun = sorted(df['tahun_arsip'].unique(), reverse=True)
            filter_thn = st.selectbox("📂 Pilih Tahun Arsip:", list_tahun, key="filter_thn_masuk")
            
            # --- FIX NOMOR URUT (RESET INDEX BIAR START 1) ---
            df_filtered_view = df[df['tahun_arsip'] == filter_thn].drop(columns=['dt_object', 'tahun_arsip'])
            df_filtered_view = df_filtered_view.reset_index(drop=True)
            df_filtered_view.index += 1 
            
            st.markdown(f"**Menampilkan Data Tahun: {filter_thn}**")
            edited_df = st.data_editor(df_filtered_view,
                                     use_container_width=True, hide_index=False,
                                     disabled=["Waktu Input", "Nama File"], key=f"editor_masuk_{filter_thn}")
            
            c_save, c_del = st.columns([3, 1])
            if c_save.button("💾 SIMPAN PERUBAHAN TABEL", use_container_width=True):
                # Kembalikan index ke 0-based sebelum save agar sinkron dengan database
                df_to_save_final = edited_df.copy()
                df_to_save_final.index -= 1
                
                # Update ke dataframe asli
                df.update(df_to_save_final)
                df_db = df.drop(columns=['dt_object', 'tahun_arsip'])
                save_data("masuk", df_db)
                st.success("Data Diperbarui!")
                st.rerun()

            with c_del:
                target_idx_view = st.selectbox("Hapus No Urut:", df_filtered_view.index, key="del_idx_masuk")
                target_idx_real = df[df['tahun_arsip'] == filter_thn].index[target_idx_view - 1]
                
                if st.button("🗑️ HAPUS DATA", type="primary", use_container_width=True):
                    f_name = df.at[target_idx_real, 'Nama File']
                    f_path = os.path.join("data_lokal", "attachments", "surat_masuk", str(f_name))
                    
                    if f_name and os.path.exists(f_path):
                        try: os.remove(f_path)
                        except: pass
                    
                    df_final = df.drop(target_idx_real).drop(columns=['dt_object', 'tahun_arsip'])
                    save_data("masuk", df_final)
                    st.success("Data Berhasil Dihapus!")
                    st.rerun()
        else:
            st.info("Belum ada data surat masuk.")

    with tab3:
        if not df.empty:
            st.subheader("🔍 Preview & Cetak Lembar Disposisi")
            c_f1, c_f2 = st.columns(2)
            list_tahun_prev = sorted(df['tahun_arsip'].unique(), reverse=True)
            thn_p = c_f1.selectbox("Filter Tahun:", list_tahun_prev, key="prev_thn_masuk")
            df_prev = df[df['tahun_arsip'] == thn_p]
            sel_preview = c_f2.selectbox("Pilih Nomor Surat:", ["-"] + df_prev["No Surat"].tolist(), key="prev_cetak_masuk")
            
            if sel_preview != "-":
                row_data = df_prev[df_prev["No Surat"] == sel_preview].iloc[0]
                col_view, col_info = st.columns([2, 1])
                with col_info:
                    st.markdown(f"""
                    <div style='background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; border: 1px solid #00ff96;'>
                        <h4 style='color: #00ff96; margin-top:0;'>Detail Surat Masuk</h4>
                        <p><b>Dari:</b><br>{row_data['Pengirim']}</p>
                        <p><b>No Surat:</b><br>{row_data['No Surat']}</p>
                        <p><b>Perihal:</b><br>{row_data['Perihal']}</p>
                        <p><b>Disposisi:</b><br>{row_data['Disposisi']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    pdf_dis = create_disposisi_pdf(row_data)
                    st.download_button(label="🖨️ DOWNLOAD LEMBAR DISPOSISI", data=pdf_dis, file_name=f"Disposisi_{sel_preview}.pdf", mime="application/pdf", use_container_width=True)

                with col_view:
                    nama_file_saja = row_data.get('Nama File', '')
                    path_lengkap = os.path.join("data_lokal", "attachments", "surat_masuk", str(nama_file_saja))
                    if nama_file_saja and os.path.exists(path_lengkap):
                        ext = str(nama_file_saja).lower()
                        if ext.endswith('.pdf'):
                            with open(path_lengkap, "rb") as f:
                                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" style="border-radius:10px;"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                        else: st.image(path_lengkap, use_container_width=True, caption=f"Scan: {nama_file_saja}")
                    else: st.warning("⚠️ File scan tidak ditemukan.")
            
            st.markdown("---")
            st.subheader("📊 Ringkasan Bulanan")
            col_bln, col_thn = st.columns(2)
            bulan_pilih = col_bln.selectbox("Bulan", list(BULAN_INDONESIA.values()), index=datetime.now().month-1)
            tahun_pilih = col_thn.selectbox("Tahun", [2025, 2026], index=1)
            df_r = df.copy()
            if not df_r.empty:
                df_r['dt_temp'] = pd.to_datetime(df_r['Tanggal Terima'], errors='coerce')
                angka_bln = [k for k, v in BULAN_INDONESIA.items() if v == bulan_pilih][0]
                df_filtered = df_r[(df_r['dt_temp'].dt.month == angka_bln) & (df_r['dt_temp'].dt.year == tahun_pilih)]
                if not df_filtered.empty:
                    st.dataframe(df_filtered.drop(columns=['dt_temp', 'dt_object', 'tahun_arsip']), use_container_width=True, hide_index=True)
                    from utils.pdf_gen import create_rekap_surat_pdf
                    pdf_rek_masuk = create_rekap_surat_pdf(df_filtered, "masuk", bulan_pilih, tahun_pilih)
                    st.download_button(
                        label=f"📂 DOWNLOAD REKAP SURAT MASUK {bulan_pilih.upper()}",
                        data=pdf_rek_masuk,
                        file_name=f"Rekap_Surat_Masuk_{bulan_pilih}_{tahun_pilih}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else: st.info("Tidak ada data pada periode ini.")
        else: st.info("Belum ada data untuk direkap.")
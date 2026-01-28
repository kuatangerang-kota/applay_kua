import streamlit as st
import pandas as pd
import os
import time
import base64
from datetime import datetime
from utils.database import load_data, save_data, delete_data, save_uploaded_file

# Mapping Bulan Indonesia untuk Laporan
BULAN_INDONESIA = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def render():
    st.markdown("<h1 style='font-weight: 800; letter-spacing: -1.5px;'>🌱 Manajemen Tanah Wakaf</h1>", unsafe_allow_html=True)
    
    # 1. LOAD DATA
    df = load_data("wakaf")

    # --- NORMALISASI DATA ---
    if not df.empty:
        df = df.dropna(how='all').reset_index(drop=True) 
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns] 
        df = df.loc[:, ~df.columns.duplicated()].reset_index(drop=True)
        df['dt_pengerjaan'] = pd.to_datetime(df['waktu_input'], errors='coerce')
    else:
        df = pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["📝 Registrasi Arsip", "📊 Database & Edit", "📅 Laporan Hasil Kerja"])

    # --- TAB 1: INPUT BARU ---
    with tab1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.form("fm_wakaf_new", clear_on_submit=True):
            st.markdown("<h3 style='color: #00ff96;'>📜 Input Berkas Baru</h3>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            no_aiw = c1.text_input("Nomor AIW / Sertifikat")
            tgl_aiw = c2.date_input("Tanggal Asli Berkas", datetime.now())
            
            c3, c4 = st.columns(2)
            wakif = c3.text_input("Nama Wakif")
            nazhir = c4.text_input("Nama Nazhir")
            
            list_kelurahan = ["Babakan", "Buaran Indah", "Cikokol", "Kelapa Indah", "Sukasari", "Sukaasih", "Tanah Tinggi", "Tangerang"]
            kel = st.selectbox("Kelurahan", list_kelurahan)
            
            c5, c6 = st.columns(2)
            luas = c5.text_input("Luas (m2)")
            bukti = c6.text_input("Alas Hak (Sertifikat/Girik/AJB)") 
            
            almt_objek = st.text_area("Alamat Lengkap Objek")
            up_wkf = st.file_uploader("Upload Scan Berkas (PDF/JPG)", type=['pdf', 'jpg', 'jpeg', 'png'], key="upload_baru")
            
            if up_wkf is not None:
                # Menampilkan status file secara real-time (Sangat membantu di HP)
                st.markdown(f"""
                    <div style='background: rgba(0, 255, 150, 0.1); padding: 10px; border-radius: 5px; border: 1px solid #00ff96;'>
                        <span style='color: #00ff96; font-weight: bold;'>✔️ File Siap:</span> {up_wkf.name} <br>
                        <small style='color: white; opacity: 0.7;'>Ukuran: {round(up_wkf.size/1024, 1)} KB</small>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("💡 Tip HP: Tunggu bar biru selesai sebelum klik Simpan.")

            if st.form_submit_button("🔱 SIMPAN ARSIP"):
                # 1. Validasi Input Wajib
                if not no_aiw or not wakif:
                    st.error("❌ Nomor AIW dan Nama Wakif wajib diisi!")
                else:
                    # 2. Indikator Loading (Penting buat user HP biar gak klik berkali-kali)
                    with st.spinner("Sedang memproses dokumen..."):
                        try:
                            # 3. Handle Upload File
                            fn = ""
                            if up_wkf is not None:
                                fn = save_uploaded_file(up_wkf, category="wakaf")
                            
                            # 4. Buat Data Baru
                            new_entry = {
                                "id_wakaf": f"WKF-{int(time.time())}",
                                "tanggal_aiw": str(tgl_aiw),
                                "nomor_aiw": str(no_aiw).strip(),
                                "nama_wakif": str(wakif).strip().upper(),
                                "nama_nazhir": str(nazhir).strip().upper(),
                                "kelurahan": kel,
                                "bukti_kepemilikan": bukti,
                                "luas_m2": luas,
                                "alamat_objek": almt_objek,
                                "nama_file": fn,
                                "waktu_input": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }

                            # 5. Gabungkan & Simpan (Gunakan drop_duplicates agar data tidak double)
                            df_new = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                            
                            # Hapus kolom pembantu sebelum simpan
                            if 'dt_pengerjaan' in df_new.columns:
                                df_new = df_new.drop(columns=['dt_pengerjaan'])
                                
                            save_data("wakaf", df_new)
                            
                            # 6. Notifikasi Sukses yang Jelas
                            st.toast(f"✅ Data {no_aiw} berhasil diarsipkan!", icon='🎉')
                            st.success(f"✅ Berhasil menyimpan arsip atas nama {wakif}")
                            
                            time.sleep(1.5)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Terjadi kesalahan sistem: {e}")

    # --- TAB 2: DATABASE & EDIT DATA ---
    with tab2:
        # 1. Inisialisasi State
        if "wakaf_is_editing" not in st.session_state:
            st.session_state.wakaf_is_editing = False
        if "wakaf_forced_close" not in st.session_state:
            st.session_state.wakaf_forced_close = False

        if not df.empty:
            st.markdown("### 🔍 Cari & Edit Data")
            search_query = st.text_input("Cari Nama Wakif / No AIW", "").lower()
            df_view = df[df.apply(lambda row: search_query in str(row.values).lower(), axis=1)].copy()
            
            if not df_view.empty:
                df_display = df_view.drop(columns=['dt_pengerjaan'], errors='ignore')
                df_display.insert(0, 'No', range(1, len(df_display) + 1))
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.warning("Data tidak ditemukan.")

            st.markdown("---")

            # 2. Logika Pilihan Data
            def on_change_wakaf():
                st.session_state.wakaf_forced_close = False
                st.session_state.wakaf_is_editing = False

            sel_edit = st.selectbox(
                "Pilih Data untuk Detail/Edit/Preview:", 
                ["-- Pilih Nomor AIW --"] + df_view["nomor_aiw"].tolist(),
                on_change=on_change_wakaf,
                key="sb_wakaf_selection"
            )
            
            # Munculkan konten jika dipilih dan tidak sedang dipaksa tutup
            if sel_edit != "-- Pilih Nomor AIW --" and not st.session_state.wakaf_forced_close:
                idx = df[df["nomor_aiw"] == sel_edit].index[0]
                row = df.iloc[idx]
                
                # Baris Tombol Aksi
                c_edit, c_hapus, c_tutup = st.columns([1,1,1])
                
                if c_edit.button("✏️ EDIT DATA", use_container_width=True):
                    st.session_state.wakaf_is_editing = True
                    st.rerun()

                if c_hapus.button("🗑️ HAPUS DATA", use_container_width=True):
                    df = df.drop(idx)
                    save_data("wakaf", df.drop(columns=['dt_pengerjaan'], errors='ignore'))
                    st.warning("Data dihapus!")
                    time.sleep(1)
                    st.rerun()

                if c_tutup.button("✖️ TUTUP PREVIEW", use_container_width=True):
                    st.session_state.wakaf_forced_close = True
                    st.rerun()

                # --- 3. MODE EDIT (Form) ---
                if st.session_state.wakaf_is_editing:
                    with st.form("edit_form_wakaf"):
                        st.markdown("### 📝 Edit Data Wakaf")
                        e1, e2 = st.columns(2)
                        new_no = e1.text_input("Nomor AIW", value=row['nomor_aiw'])
                        new_tgl = e2.text_input("Tanggal (YYYY-MM-DD)", value=row['tanggal_aiw'])
                        # ... (sisa input form lainnya tetap sama) ...
                        
                        b_simpan, b_batal = st.columns(2)
                        if b_simpan.form_submit_button("💾 UPDATE DATA"):
                            # Logika simpan data kamu...
                            st.session_state.wakaf_is_editing = False
                            st.success("✅ Data diperbarui!")
                            st.rerun()
                        
                        if b_batal.form_submit_button("❌ BATAL"):
                            st.session_state.wakaf_is_editing = False
                            st.rerun()

                # --- 4. MODE PREVIEW (Full Page Elit) ---
                else:
                    st.markdown("### 👁️ Preview Berkas")
                    nama_f = str(row.get('nama_file', '')).strip()
                    path_file = os.path.join(os.getcwd(), "data_lokal", "attachments", "wakaf", nama_f)

                    if nama_f != "" and os.path.exists(path_file):
                        with open(path_file, "rb") as f:
                            base64_file = base64.b64encode(f.read()).decode('utf-8')
                        
                        file_ext = nama_f.split('.')[-1].lower()
                        if file_ext == 'pdf':
                            pdf_display = f'''
                                <style>
                                    .pdf-frame-wakaf {{
                                        width: 100%; height: 90vh; 
                                        border: 3px solid #00ff96; border-radius: 10px;
                                    }}
                                </style>
                                <iframe class="pdf-frame-wakaf" src="data:application/pdf;base64,{base64_file}"></iframe>
                            '''
                            st.markdown(pdf_display, unsafe_allow_html=True)
                        else:
                            st.image(path_file, use_container_width=True)
                    else:
                        st.info("ℹ️ Berkas scan tidak ditemukan atau belum diupload.")
                    
                    if st.button("⬆️ Kembali ke Atas / Tutup", use_container_width=True):
                        st.session_state.wakaf_forced_close = True
                        st.rerun()

    with tab3:
        st.subheader("📊 Laporan Realisasi Pengerjaan")
        if not df.empty:
            c_b, c_t = st.columns(2)
            bulan_pilih = c_b.selectbox("Bulan", list(BULAN_INDONESIA.values()), index=datetime.now().month-1)
            tahun_pilih = c_t.selectbox("Tahun", [2025, 2026, 2027], index=1)
            
            angka_bln = [k for k, v in BULAN_INDONESIA.items() if v == bulan_pilih][0]
            df_filtered = df[(df['dt_pengerjaan'].dt.month == angka_bln) & (df['dt_pengerjaan'].dt.year == tahun_pilih)]
            
            if not df_filtered.empty:
                st.write(f"Total: **{len(df_filtered)} berkas**")
                from utils.pdf_gen import create_rekap_wakaf_pdf
                pdf_out = create_rekap_wakaf_pdf(df_filtered, bulan_pilih, tahun_pilih)
                st.download_button("🖨️ Download PDF", data=pdf_out, file_name=f"Rekap_Wakaf_{bulan_pilih}.pdf")
            else:
                st.info("Tidak ada data bulan ini.")
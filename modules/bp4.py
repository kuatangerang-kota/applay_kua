import streamlit as st
from utils.database import load_data, save_data, delete_data
from utils.pdf_gen import create_panggilan_bp4_pdf, create_rekap_bp4_pdf
import pandas as pd
from datetime import datetime

# Mapping Bulan Indonesia
BULAN_INDONESIA = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def render():
    st.markdown("<h1 style='font-weight: 800;'>👨‍👩‍👧‍👦 Manajemen Konseling & Mediasi BP4</h1>", unsafe_allow_html=True)
    
    df_raw = load_data("bp4")
    current_year = datetime.now().year
    
    if not df_raw.empty:
        df_raw['dt_object'] = pd.to_datetime(df_raw['Tanggal Konseling'], errors='coerce')
        df_raw['tahun_arsip'] = df_raw['dt_object'].dt.year.fillna(0).astype(int)
    
    tab1, tab2, tab3 = st.tabs(["📝 Registrasi Pengaduan", "📂 Database Perkara", "📊 Rekap Bulanan"])

    # --- TAB 1: INPUT PENGADUAN BARU ---
    with tab1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        
        # 1. Pilih Pengadu DI LUAR FORM supaya label di bawahnya langsung berubah (Reaktif)
        st.markdown("### ⚖️ Penentuan Pihak")
        pengadu_role = st.selectbox("Pihak Pengadu (Yang Datang Melapor):", ["Suami", "Istri"], key="p_role_main")
        
        # Logika penentuan lawan
        teradu_role = "Istri" if pengadu_role == "Suami" else "Suami"
        
        st.divider()

        # 2. Baru masuk ke Form untuk pengisian detail
        with st.form("fm_bp4_beast_updated", clear_on_submit=True):
            st.markdown(f"### 📝 Detail Identitas ({pengadu_role} vs {teradu_role})")
            
            c_p, c_t = st.columns(2)
            nama_pengadu = c_p.text_input(f"Nama Pengadu ({pengadu_role})")
            nama_teradu = c_t.text_input(f"Nama Teradu ({teradu_role})")
            
            st.markdown("---")
            st.markdown("### 👤 Identitas Tambahan")
            c1, c2, c3 = st.columns(3)
            tgl_nikah = c1.date_input("Tanggal Nikah", datetime.now())
            kua_nikah = c2.text_input("KUA Tempat Nikah")
            jml_anak = c3.number_input("Jumlah Anak", min_value=0, step=1)
            
            # Label alamat otomatis mengikuti Teradu
            alamat_teradu = st.text_area(f"Alamat Lengkap {teradu_role} (Untuk Pengiriman Surat Panggilan)")

            st.markdown("---")
            st.subheader("📝 Detail Masalah")
            tgl_k = st.date_input("Tanggal Pengaduan", datetime.now())
            permasalahan = st.text_area("Masalah Utama / Uraian Pengaduan")
            konselor = st.text_input("Petugas Penerima", value="Admin")

            if st.form_submit_button("🚀 DAFTARKAN PENGADUAN"):
                if nama_pengadu and nama_teradu:
                    new_id = f"BP4-{len(df_raw)+1:04d}"
                    
                    # Mapping tetap agar database konsisten (Suami & Istri)
                    s_nama = nama_pengadu if pengadu_role == "Suami" else nama_teradu
                    i_nama = nama_pengadu if pengadu_role == "Istri" else nama_teradu
                    
                    new_case = {
                        "ID Kasus": new_id, 
                        "Tanggal Konseling": str(tgl_k), 
                        "Nama Suami": s_nama, 
                        "Nama Istri": i_nama,
                        "Pengadu": nama_pengadu,
                        "Teradu": nama_teradu,
                        "Role Teradu": teradu_role,
                        "Tanggal Nikah": str(tgl_nikah), 
                        "KUA Tempat Nikah": kua_nikah,
                        "Alamat Sekarang": alamat_teradu, 
                        "Jumlah Anak": str(jml_anak), 
                        "Permasalahan": permasalahan, 
                        "Solusi": f"[Laporan Awal]: {permasalahan}", 
                        "Status": "Baru", 
                        "Konselor": konselor, 
                        "Status Panggilan": "Menunggu Panggilan 1", 
                        "Waktu Input": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    df_new = pd.concat([df_raw, pd.DataFrame([new_case])], ignore_index=True)
                    save_data("bp4", df_new.drop(columns=['dt_object', 'tahun_arsip'], errors='ignore'))
                    st.success(f"✅ Berhasil! Surat panggilan akan ditujukan kepada {nama_teradu} ({teradu_role}).")
                    st.rerun()
                else:
                    st.error("Nama Pengadu dan Teradu wajib diisi!")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 2: DATABASE & UPDATE MEDIASI ---
    # --- TAB 2: DATABASE & UPDATE MEDIASI ---
    with tab2:
        if not df_raw.empty:
            list_tahun = sorted(df_raw['tahun_arsip'].unique(), reverse=True)
            thn_sel = st.selectbox("📂 Pilih Tahun:", list_tahun)
            
            df_filtered = df_raw[df_raw['tahun_arsip'] == thn_sel].copy()

            # --- TAMBAHKAN LOGIKA PROTEKSI INI (ANTI ERROR) ---
            # Cek kolom baru satu per satu, kalau gak ada buatkan kolom default
            for col in ["Pengadu", "Teradu", "Status Panggilan", "Role Teradu"]:
                if col not in df_filtered.columns:
                    df_filtered[col] = "-"
            # --------------------------------------------------

            df_filtered['original_index'] = df_filtered.index
            
            # Tampilkan kolom yang relevan saja untuk kemudahan baca
            cols_show = ["ID Kasus", "Pengadu", "Teradu", "Tanggal Konseling", "Status", "Status Panggilan"]
            
            # Sekarang baris ini aman dari KeyError
            df_display = df_filtered[cols_show].reset_index(drop=True)
            df_display.index += 1
            
            st.dataframe(df_display, use_container_width=True)
            
            st.markdown("### 🛠️ Manajemen Perkara & Panggilan")
            sel_no = st.selectbox("Pilih No Urut Perkara:", ["-"] + df_display.index.tolist())
            
            if sel_no != "-":
                idx_target = df_filtered.iloc[sel_no-1]['original_index']
                # Mengambil data baris yang dipilih
                row_data = df_raw.loc[idx_target].to_dict()

                # Pastikan row_data juga punya key yang lengkap agar form di bawahnya tidak error
                for k in ["Pengadu", "Teradu", "Status Panggilan", "Role Teradu", "Solusi"]:
                    if k not in row_data:
                        row_data[k] = "-" if k != "Solusi" else ""
                
                c_up1, c_up2 = st.columns([2, 1])
                
                with c_up1:
                    st.markdown(f"<div style='background: rgba(0, 255, 150, 0.05); padding: 15px; border-radius: 10px; border-left: 5px solid #00ff96;'>", unsafe_allow_html=True)
                    st.markdown(f"**Pihak Teradu (Akan Dipanggil):** {row_data['Teradu']} ({row_data['Role Teradu']})")
                    st.markdown(f"**Alamat Panggilan:** {row_data['Alamat Sekarang']}")
                    
                    catatan_baru = st.text_area("Update Hasil Mediasi / Pertemuan:", placeholder="Ketik hasil mediasi terbaru di sini...")
                    c_s1, c_s2 = st.columns(2)
                    status_baru = c_s1.selectbox("Status Perkara:", ["Baru", "Proses", "Selesai", "Rujuk", "Cerai"], index=["Baru", "Proses", "Selesai", "Rujuk", "Cerai"].index(row_data['Status']))
                    panggil_baru = c_s2.selectbox("Status Panggilan:", ["Menunggu Panggilan 1", "Panggilan 1 Terkirim", "Menunggu Panggilan 2", "Panggilan 2 Terkirim", "Hadir"], index=0)
                    
                    if st.button("💾 UPDATE PERKARA", use_container_width=True):
                        if catatan_baru:
                            waktu_skr = datetime.now().strftime("%d/%m/%Y")
                            riwayat_update = f"{row_data['Solusi']}\n[{waktu_skr}]: {catatan_baru}"
                            df_raw.at[idx_target, 'Solusi'] = riwayat_update
                            df_raw.at[idx_target, 'Status'] = status_baru
                            df_raw.at[idx_target, 'Status Panggilan'] = panggil_baru
                            save_data("bp4", df_raw.drop(columns=['dt_object', 'tahun_arsip'], errors='ignore'))
                            st.success("✅ Riwayat mediasi diperbarui!")
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                with c_up2:
                    st.markdown("### 🖨️ Cetak Surat")
                    # Logika Nama untuk PDF: Teradu yang diundang
                    pdf_panggilan = create_panggilan_bp4_pdf(row_data)
                    st.download_button(
                        label=f"📄 CETAK PANGGILAN {row_data['Role Teradu'].upper()}",
                        data=pdf_panggilan,
                        file_name=f"Surat_Panggilan_{row_data['Teradu']}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.info("Surat ini akan ditujukan kepada Teradu untuk hadir ke KUA melakukan mediasi.")
        else:
            st.info("Belum ada data pengaduan.")

    # --- TAB 3: REKAP BULANAN ---
    with tab3:
        # (Tetap sama seperti kode sebelumnya, menggunakan df_raw)
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        thn_range = list(range(current_year - 2, current_year + 2))
        bln_p = c1.selectbox("Bulan Rekap", list(BULAN_INDONESIA.values()), index=datetime.now().month-1)
        thn_p = c2.selectbox("Tahun Rekap", thn_range, index=thn_range.index(current_year))

        if not df_raw.empty:
            bln_idx = [k for k, v in BULAN_INDONESIA.items() if v == bln_p][0]
            df_rekap = df_raw[(df_raw['dt_object'].dt.month == bln_idx) & (df_raw['dt_object'].dt.year == thn_p)]
            
            if not df_rekap.empty:
                st.write(f"Ditemukan **{len(df_rekap)}** data perkara.")
                st.dataframe(df_rekap.drop(columns=['dt_object', 'tahun_arsip'], errors='ignore'), use_container_width=True)
                pdf_rekap = create_rekap_bp4_pdf(df_rekap, bln_p, thn_p)
                st.download_button(
                    label=f"📂 DOWNLOAD LAPORAN {bln_p.upper()} {thn_p}",
                    data=pdf_rekap,
                    file_name=f"Laporan_BP4_{bln_p}_{thn_p}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("Tidak ada data perkara pada periode ini.")
        st.markdown('</div>', unsafe_allow_html=True)
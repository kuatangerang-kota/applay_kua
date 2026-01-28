import streamlit as st
import pandas as pd
import os
import base64
import io
from datetime import datetime
from utils.database import load_data, save_data, save_uploaded_file

BULAN_INDONESIA = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def render():
    st.markdown(
        "<h1 style='font-weight:800;'>📖 Ekspedisi Duplikat Buku Nikah (NA)</h1>",
        unsafe_allow_html=True
    )

    # ================= LOAD DATA =================
    df = load_data("duplikat_nikah")
    if df.empty:
        df = pd.DataFrame(columns=[
            "no_duplikat", "tgl_proses", "nama_suami", "nama_istri",
            "no_akta_asal", "tgl_akad", "alasan",
            "nama_file", "waktu_input"
        ])

    df["dt_object"] = pd.to_datetime(df["tgl_proses"], errors="coerce")

    tab1, tab2, tab3 = st.tabs([
        "📝 Registrasi Permohonan",
        "📂 Database Duplikat",
        "📊 Rekap & Laporan"
    ])

    # ================= TAB 1 : INPUT =================
    with tab1:
        st.subheader("📝 Registrasi Permohonan Duplikat")

        with st.form("form_input"):
            c1, c2 = st.columns(2)
            tgl_proses_input = c1.date_input("Tanggal Proses", value=datetime.now())
            no_dup = c2.text_input("Nomor Duplikat Baru")
            
            st.markdown("---")
            
            c3, c4 = st.columns(2)
            nama_suami = c3.text_input("Nama Suami")
            nama_istri = c4.text_input("Nama Istri")
            no_akta = c3.text_input("No Akta Nikah Lama")
            tgl_akad = c4.date_input("Tanggal Akad", value=datetime(2000, 1, 1))

            alasan = st.selectbox("Alasan", ["Rusak", "Hilang", "Perubahan Data / Isbat"])
            berkas = st.file_uploader("Upload Scan", type=["pdf", "jpg", "jpeg", "png"])

            if st.form_submit_button("🚀 SIMPAN DATA"):
                fn = save_uploaded_file(berkas, category="duplikat") if berkas else ""

                entry = {
                    "no_duplikat": no_dup,
                    "tgl_proses": tgl_proses_input.strftime("%Y-%m-%d"), # <-- PAKAI INPUTAN MANUAL
                    "nama_suami": nama_suami,
                    "nama_istri": nama_istri,
                    "no_akta_asal": no_akta,
                    "tgl_akad": str(tgl_akad),
                    "alasan": alasan,
                    "nama_file": fn,
                    "waktu_input": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
                save_data("duplikat_nikah", df.drop(columns=["dt_object"], errors="ignore"))
                st.success("✅ Data berhasil disimpan")
                st.rerun()

    with tab2:
        st.subheader("📂 Database Duplikat")

        # 1. Inisialisasi State agar stabil
        if "is_editing" not in st.session_state:
            st.session_state.is_editing = False
        if "target_idx" not in st.session_state:
            st.session_state.target_idx = None
        if "forced_close" not in st.session_state:
            st.session_state.forced_close = False

        if df.empty:
            st.info("Belum ada data.")
        else:
            # Tampilkan Tabel
            df_view = df.drop(columns=["dt_object"], errors="ignore").copy()
            df_view.index = range(1, len(df_view) + 1)
            st.dataframe(df_view, use_container_width=True)

            st.markdown("---")

            # 2. PILIH DATA
            # Kita pantau apakah user mengubah pilihan di selectbox
            def on_change_selection():
                st.session_state.forced_close = False # Reset tutup jika user pilih data lain
                st.session_state.is_editing = False

            sel_dup = st.selectbox(
                "🔍 Pilih Data untuk Detail/Edit/Preview",
                ["-"] + df["no_duplikat"].tolist(),
                key="sb_database_nikah",
                on_change=on_change_selection
            )

            # Logika: Munculkan konten HANYA jika dipilih DAN tidak sedang dipaksa tutup
            if sel_dup != "-" and not st.session_state.forced_close:
                idx = df[df["no_duplikat"] == sel_dup].index[0]
                row = df.loc[idx]

                # Tombol Aksi (Edit & Hapus)
                c_edit, c_hapus, c_tutup_atas = st.columns([1, 1, 1])
                
                if c_edit.button("✏️ EDIT DATA", use_container_width=True):
                    st.session_state.is_editing = True
                    st.session_state.target_idx = idx
                    st.rerun()
                
                if c_hapus.button("🗑️ HAPUS", use_container_width=True):
                    df_new = df.drop(idx)
                    save_data("duplikat_nikah", df_new.drop(columns=["dt_object"], errors="ignore"))
                    st.rerun()

                if c_tutup_atas.button("✖️ TUTUP PREVIEW", use_container_width=True):
                    st.session_state.forced_close = True
                    st.rerun()

                # --- 3. FORM EDITOR ---
                if st.session_state.is_editing and st.session_state.target_idx == idx:
                    # ... (Bagian Form Editor kamu tetap sama seperti sebelumnya) ...
                    # (Pastikan di dalam tombol BATAL form editor, tambahkan st.session_state.is_editing = False)
                    pass 

                # --- 4. PREVIEW FULL PAGE ---
                elif not st.session_state.is_editing:
                    st.markdown("### 👁️ Preview Dokumen")
                    fn = row.get("nama_file", "")
                    path = os.path.join("data_lokal", "attachments", "duplikat", str(fn))

                    if fn and os.path.exists(path):
                        if fn.lower().endswith(".pdf"):
                            with open(path, "rb") as f:
                                b64 = base64.b64encode(f.read()).decode()
                            
                            pdf_display = f'''
                                <style>
                                    .pdf-frame {{
                                        width: 100%; height: 90vh; 
                                        border: 3px solid #2E7D32; border-radius: 10px;
                                    }}
                                </style>
                                <iframe class="pdf-frame" src="data:application/pdf;base64,{b64}"></iframe>
                            '''
                            st.markdown(pdf_display, unsafe_allow_html=True)
                        else:
                            st.image(path, use_container_width=True)
                    else:
                        st.warning("⚠️ File scan tidak ditemukan.")
                    
                    if st.button("⬆️ Tutup Preview & Kembali ke Tabel", use_container_width=True):
                        st.session_state.forced_close = True
                        st.rerun()



    # ================= TAB 3 : REKAP =================
    with tab3:
        st.subheader("📊 Rekap & Laporan Duplikat Nikah")

        if df.empty:
            st.info("Tidak ada data.")
        else:
            # === FILTER ===
            c1, c2 = st.columns(2)

            bln = c1.selectbox(
                "Bulan",
                list(BULAN_INDONESIA.values()),
                index=datetime.now().month - 1
            )

            thn = c2.selectbox(
                "Tahun",
                sorted(df["dt_object"].dt.year.dropna().unique(), reverse=True)
            )

            bln_idx = [k for k, v in BULAN_INDONESIA.items() if v == bln][0]

            df_f = df[
                (df["dt_object"].dt.month == bln_idx) &
                (df["dt_object"].dt.year == thn)
            ].copy()

            st.metric("📁 Total Permohonan", len(df_f))

            df_view = df_f.drop(columns=["dt_object"], errors="ignore")
            df_view.index = range(1, len(df_view) + 1)

            st.dataframe(df_view, use_container_width=True)

            # === DOWNLOAD EXCEL SIAP CETAK (VERSI BERKELAS) ===
            st.markdown("### ⬇️ Download Laporan Resmi (Excel)")

            df_print = df_f[[
                "no_duplikat",
                "tgl_proses",
                "nama_suami",
                "nama_istri",
                "no_akta_asal",
                "tgl_akad",
                "alasan"
            ]].copy()

            def tgl_id(val):
                try:
                    d = pd.to_datetime(val)
                    return f"{d.day} {BULAN_INDONESIA[d.month]} {d.year}"
                except:
                    return val

            df_print["tgl_proses"] = df_print["tgl_proses"].apply(tgl_id)
            df_print["tgl_akad"]   = df_print["tgl_akad"].apply(tgl_id)

            df_print.index = range(1, len(df_print) + 1)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                workbook  = writer.book
                worksheet = workbook.add_worksheet("Laporan")
                writer.sheets["Laporan"] = worksheet

                title_fmt = workbook.add_format({
                    "bold": True, "font_size": 14, "align": "center"
                })
                subtitle_fmt = workbook.add_format({
                    "italic": True, "align": "center"
                })
                header_fmt = workbook.add_format({
                    "bold": True,
                    "bg_color": "#2E7D32",
                    "color": "white",
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter"
                })
                cell_fmt = workbook.add_format({
                    "border": 1,
                    "valign": "vcenter"
                })

                worksheet.merge_range(
                    "A1:G1",
                    "LAPORAN REKAPITULASI DUPLIKAT BUKU NIKAH",
                    title_fmt
                )
                worksheet.merge_range(
                    "A2:G2",
                    f"Periode {bln} {thn}",
                    subtitle_fmt
                )

                # === HEADER TABEL ===
                start_row = 4
                for col, name in enumerate([
                    "No Duplikat", "Tanggal Proses", "Nama Suami",
                    "Nama Istri", "No Akta Nikah", "Tanggal Akad", "Alasan"
                ]):
                    worksheet.write(start_row, col, name, header_fmt)

                # === ISI TABEL ===
                for r, row in enumerate(df_print.values):
                    for c, val in enumerate(row):
                        worksheet.write(start_row + r + 1, c, val, cell_fmt)

                # AUTO WIDTH
                widths = [18, 18, 22, 22, 20, 18, 18]
                for i, w in enumerate(widths):
                    worksheet.set_column(i, i, w)

                # === TTD ===
                ttd_row = start_row + len(df_print) + 4
                tgl_cetak = tgl_id(datetime.now())

                worksheet.merge_range(
                    f"E{ttd_row}:G{ttd_row}",
                    f"Tangerang, {tgl_cetak}"
                )
                worksheet.merge_range(
                    f"E{ttd_row+1}:G{ttd_row+1}",
                    "Kepala KUA"
                )
                worksheet.merge_range(
                    f"E{ttd_row+5}:G{ttd_row+5}",
                    "( __________________________ )"
                )

                worksheet.set_paper(9)          # A4
                worksheet.set_margins(left=0.5, right=0.5, top=0.75, bottom=0.75)
                worksheet.center_horizontally()
                worksheet.center_vertically()

            st.download_button(
                "⬇️ Download Excel",
                output.getvalue(),
                file_name=f"Laporan_Duplikat_{bln}_{thn}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )




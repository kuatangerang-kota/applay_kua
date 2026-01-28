import streamlit as st
import pandas as pd
from datetime import datetime
import re
import time
import io
from utils.database import load_data, save_data

# ======================================================
# UTIL
# ======================================================
def hit_jml_perf(aw, ak):
    try:
        n_aw = int(re.sub(r'\D', '', str(aw)))
        n_ak = int(re.sub(r'\D', '', str(ak)))
        return (n_ak - n_aw) + 1 if n_ak >= n_aw else 0
    except:
        return 0

# ======================================================
# STYLING WIBA
# ======================================================
def wibawa_table(df):
    if df.empty:
        return df

    jumlah_cols = ['Jml NA', 'Jml NB', 'Jml N', 'Jml DN']

    def highlight_total(row):
        if "TOTAL" in str(row['No. Dokumen']).upper() or "SISA" in str(row['No. Dokumen']).upper():
            return [
                'background-color: #374151; color: #f9fafb; font-weight:bold; border-top:2px solid #9ca3af;'
            ] * len(row)
        return [''] * len(row)

    styler = (
        df.style
        .set_properties(**{
            'color': '#f9fafb',
            'text-align': 'center',
            'font-size': '14px'
        })
        .set_table_styles([
            {'selector': 'th',
             'props': [
                 ('background-color', '#020617'),
                 ('color', '#ffffff'),
                 ('font-weight', 'bold'),
                 ('text-align', 'center'),
                 ('border', '1px solid #334155')
             ]},
            {'selector': 'tbody tr:nth-child(odd)',
             'props': [('background-color', '#020617')]},
            {'selector': 'tbody tr:nth-child(even)',
             'props': [('background-color', '#020617cc')]},
            {'selector': 'td',
             'props': [('border', '1px solid #334155')]}
        ])
        .set_properties(
            subset=jumlah_cols,
            **{'color': '#ffffff', 'font-weight': 'bold'}
        )
        .apply(highlight_total, axis=1)
    )

    return styler

# ======================================================
# PREVIEW LAPORAN
# ======================================================
def render_preview_native(df):
    st.markdown(f"#### **LAPORAN STOK - {datetime.now().strftime('%B %Y').upper()}**")

    df = df.copy()
    df['Keterangan'] = df['Keterangan'].fillna("-").astype(str).str.upper()
    df['Tanggal_dt'] = pd.to_datetime(df['Tanggal'])
    df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0).astype(int)

    cols = [
        'No. Dokumen', 'Tgl', 'Seri',
        'No. Perforasi (NA)', 'Jml NA',
        'Jml NB', 'Jml N',
        'No. Perforasi (DN)', 'Jml DN'
    ]

    def gather(df_f):
        if df_f.empty:
            return pd.DataFrame(columns=cols)

        res = []
        for (tgl, ket), g in df_f.groupby(['Tanggal', 'Keterangan'], sort=False):
            r = {c: "" for c in cols}
            r['No. Dokumen'] = ket
            r['Tgl'] = pd.to_datetime(tgl).strftime('%d-%m-%Y')
            r['Jml NA'] = r['Jml NB'] = r['Jml N'] = r['Jml DN'] = 0

            for _, x in g.iterrows():
                m = x['Model']
                if m == "Model NA":
                    r['Seri'] = "BA"
                    r['No. Perforasi (NA)'] = f"{x['Perf_Awal']} - {x['Perf_Akhir']}"
                    r['Jml NA'] += x['Jumlah']
                elif m == "Model NB":
                    r['Jml NB'] += x['Jumlah']
                elif m == "Model N":
                    r['Jml N'] += x['Jumlah']
                elif m == "Model DN":
                    r['No. Perforasi (DN)'] = f"{x['Perf_Awal']} - {x['Perf_Akhir']}"
                    r['Jml DN'] += x['Jumlah']
            res.append(r)

        df_out = pd.DataFrame(res, columns=cols)

        if not df_out.empty:
            total = {c: "" for c in cols}
            total['No. Dokumen'] = "**TOTAL**"
            total['Jml NA'] = df_out['Jml NA'].sum()
            total['Jml NB'] = df_out['Jml NB'].sum()
            total['Jml N']  = df_out['Jml N'].sum()
            total['Jml DN'] = df_out['Jml DN'].sum()
            df_out = pd.concat([df_out, pd.DataFrame([total])], ignore_index=True)

        df_out.index = range(1, len(df_out) + 1)
        return df_out

    st.markdown("##### **📥 A. PENERIMAAN (+)**")
    df_masuk = gather(df[df['Jenis'] == 'Masuk'])
    st.dataframe(wibawa_table(df_masuk), use_container_width=True, hide_index=True)

    st.markdown("##### **📤 B. PENGELUARAN (-)**")
    df_keluar = df[df['Jenis'] == 'Keluar'].copy()
    df_keluar['Tanggal_dt'] = pd.to_datetime(df_keluar['Tanggal'], errors='coerce')
    df_keluar = df_keluar.sort_values(by='Tanggal_dt', ascending=True)
    st.dataframe(wibawa_table(gather(df_keluar)), use_container_width=True, hide_index=True)

    st.markdown("##### **⚖️ C. REKAP SISA AKHIR**")
    sisa = {c: "" for c in cols}
    sisa['No. Dokumen'] = "SISA STOK SAAT INI"
    sisa['Tgl'] = datetime.now().strftime('%d-%m-%Y')

    stok_murni = {}
    for m in ["Model NA", "Model NB", "Model N", "Model DN"]:
        m_in = df[(df['Model'] == m) & (df['Jenis'] == 'Masuk')]['Jumlah'].sum()
        m_out = df[(df['Model'] == m) & (df['Jenis'] == 'Keluar')]['Jumlah'].sum()
        stok_murni[m] = m_in - m_out

    total_fisik_na = int(stok_murni['Model NA'])
    sisa['Jml NA'] = total_fisik_na
    sisa['Jml NB'] = int(stok_murni['Model NB'])
    sisa['Jml N']  = int(stok_murni['Model N'])
    sisa['Jml DN'] = total_fisik_na
    sisa['Seri']   = "BA"

    # Perhitungan Perforasi Sisa
    df_na_masuk = df[(df['Model']=='Model NA') & (df['Jenis']=='Masuk')]
    df_pengurang_na = df[((df['Model'] == 'Model NA') | (df['Model'] == 'Model DN')) & (df['Jenis'] == 'Keluar')]

    perf_ranges = []
    for _, row in df_na_masuk.iterrows():
        try:
            aw, ak = int(row['Perf_Awal']), int(row['Perf_Akhir'])
            perf_ranges.append((aw, ak))
        except: continue

    for _, row in df_pengurang_na.iterrows():
        try:
            out_aw, out_ak = int(row['Perf_Awal']), int(row['Perf_Akhir'])
            new_ranges = []
            for aw, ak in perf_ranges:
                if out_ak < aw or out_aw > ak:
                    new_ranges.append((aw, ak))
                else:
                    if aw < out_aw: new_ranges.append((aw, out_aw - 1))
                    if ak > out_ak: new_ranges.append((out_ak + 1, ak))
            perf_ranges = new_ranges
        except: continue

    if perf_ranges:
        perf_ranges.sort()
        perf_sisa_str = ", ".join(f"{aw}-{ak}" for aw, ak in perf_ranges)
    else:
        perf_sisa_str = "-"
    sisa['No. Perforasi (NA)'] = perf_sisa_str

    df_sisa = pd.DataFrame([sisa], columns=cols)
    st.dataframe(wibawa_table(df_sisa), use_container_width=True, hide_index=True)

    # ======================================================
    # DOWNLOAD EXCEL
    # ======================================================
    st.divider()
    st.markdown("### ⬇️ Download Laporan Resmi (Excel)")
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_masuk_raw = df[df['Jenis'] == 'Masuk'].sort_values('Tanggal')
        df_keluar_raw = df[df['Jenis'] == 'Keluar'].sort_values('Tanggal')
        
        df_m_xls = gather(df_masuk_raw)
        df_k_xls = gather(df_keluar_raw)
        df_s_xls = pd.DataFrame([sisa], columns=cols)

        sheet_name = "Laporan_Stok"
        workbook  = writer.book
        fmt_judul = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        fmt_header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        fmt_border = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        fmt_sub = workbook.add_format({'bold': True, 'font_size': 11})

        def apply_style(df_f, start_row, worksheet):
            for col_num, value in enumerate(df_f.columns.values):
                worksheet.write(start_row, col_num, value, fmt_header)
            for r in range(len(df_f)):
                for c in range(len(df_f.columns)):
                    worksheet.write(start_row + 1 + r, c, df_f.iloc[r, c], fmt_border)

        df_m_xls.to_excel(writer, sheet_name=sheet_name, startrow=4, index=False)
        worksheet = writer.sheets[sheet_name]
        apply_style(df_m_xls, 4, worksheet)
        
        row_b = 4 + len(df_m_xls) + 4
        df_k_xls.to_excel(writer, sheet_name=sheet_name, startrow=row_b, index=False)
        apply_style(df_k_xls, row_b, worksheet)
        
        row_c = row_b + len(df_k_xls) + 4
        df_s_xls.to_excel(writer, sheet_name=sheet_name, startrow=row_c, index=False)
        apply_style(df_s_xls, row_c, worksheet)

        worksheet.merge_range('A1:I1', f"LAPORAN STOK OPNAME - {datetime.now().strftime('%B %Y').upper()}", fmt_judul)
        worksheet.write(3, 0, "A. PENERIMAAN (+)", fmt_sub)
        worksheet.write(row_b - 1, 0, "B. PENGELUARAN (-)", fmt_sub)
        worksheet.write(row_c - 1, 0, "C. REKAP SISA AKHIR", fmt_sub)

        rt = row_c + 4
        worksheet.write(rt, 7, f"Tangerang, {datetime.now().strftime('%d %B %Y')}", workbook.add_format({'align': 'center'}))
        worksheet.write(rt + 1, 7, "Kepala KUA Tangerang", workbook.add_format({'align': 'center', 'bold': True}))
        worksheet.write(rt + 5, 7, "( ________________________ )", workbook.add_format({'align': 'center'}))

        worksheet.set_column('A:A', 25); worksheet.set_column('B:I', 15)
        worksheet.set_paper(9); worksheet.set_landscape()

    st.download_button(label="📥 DOWNLOAD EXCEL SIAP CETAK", data=output.getvalue(), 
                       file_name=f"Laporan_Stok_KUA.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ======================================================
# MAIN RENDER
# ======================================================
def render():
    st.title("APPLAY: STOK OPNAME KUA")
    df = load_data("stok")

    if "mn" not in st.session_state: st.session_state.mn = "IN"
    if "ed" not in st.session_state: st.session_state.ed = None
    if "tr" not in st.session_state: st.session_state.tr = str(time.time())

    # Navigasi Utama
    c1, c2, c3 = st.columns(3)
    if c1.button("➕ INPUT", use_container_width=True): 
        st.session_state.mn = "IN"; st.session_state.ed = None; st.rerun()
    if c2.button("📊 LAPORAN", use_container_width=True): 
        st.session_state.mn = "OUT"; st.rerun()
    if c3.button("📜 RIWAYAT", use_container_width=True): 
        st.session_state.mn = "HIST"; st.rerun()

    st.divider()

    # --- MENU INPUT ---
    if st.session_state.mn == "IN":
        k = st.session_state.tr
        if st.session_state.ed is not None:
            r = df.iloc[st.session_state.ed]
            val_m, val_t, val_j, val_aw, val_ak, val_jml, val_k = r['Model'], datetime.strptime(r['Tanggal'], '%Y-%m-%d'), r['Jenis'], r['Perf_Awal'], r['Perf_Akhir'], r['Jumlah'], r['Keterangan']
        else:
            # DEFAULT JENIS SEKARANG: KELUAR
            val_m, val_t, val_j, val_aw, val_ak, val_jml, val_k = "Model NA", datetime.now(), "Keluar", "", "", 1, ""

        ms = st.selectbox("Model", ["Model NA", "Model NB", "Model N", "Model DN"], index=["Model NA", "Model NB", "Model N", "Model DN"].index(val_m), key=f"m_{k}")
        tgl = st.date_input("Tanggal", value=val_t, key=f"t_{k}")
        
        # Radio Button Jenis dengan default Keluar (index 1)
        list_jenis = ["Masuk", "Keluar"]
        jenis = st.radio("Jenis", list_jenis, index=list_jenis.index(val_j), horizontal=True, key=f"j_{k}")

        auto_n = 0
        if ms in ["Model NA", "Model DN"]:
            c1, c2 = st.columns(2)
            aw = c1.text_input("Awal", value=val_aw, key=f"a_{k}"); ak = c2.text_input("Akhir", value=val_ak, key=f"b_{k}")
            jml = hit_jml_perf(aw, ak)
            st.info(f"Jumlah Terhitung: {jml}")
            if ms == "Model NA": auto_n = jml // 2
        else:
            jml = st.number_input("Jumlah", min_value=1, value=int(val_jml), key=f"n_{k}")
            aw = ak = "-"

        ket = st.text_input("BA / Dokumen", value=val_k, key=f"d_{k}")

        if st.button("SIMPAN DATA", type="primary", use_container_width=True):
            if not ket:
                st.error("Isi dulu Nomor Dokumennya!")
            else:
                new_data = {
                    "Tanggal": str(tgl), "Jenis": jenis, "Model": ms, 
                    "Perf_Awal": aw, "Perf_Akhir": ak, "Jumlah": int(jml), "Keterangan": ket
                }

                if st.session_state.ed is not None:
                    # PROSES EDIT
                    df.iloc[st.session_state.ed] = new_data
                    save_data("stok", df)
                    
                    # --- NOTIFIKASI DISINI ---
                    st.success(f"✅ Data '{ket}' Berhasil Diperbarui!")
                    st.toast("Data tersimpan!", icon="💾")
                    
                    # Tunggu sebentar biar user liat pesannya
                    time.sleep(1.2)
                    
                    st.session_state.ed = None # Reset mode edit
                else:
                    # PROSES INPUT BARU
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    if ms == "Model NA" and auto_n > 0:
                        extra = {"Tanggal": str(tgl), "Jenis": jenis, "Model": "Model N", "Perf_Awal": "-", "Perf_Akhir": "-", "Jumlah": auto_n, "Keterangan": ket}
                        df = pd.concat([df, pd.DataFrame([extra])], ignore_index=True)
                    
                    save_data("stok", df)
                    st.success("🚀 Data Baru Berhasil Disimpan!")
                    st.toast("Tersimpan!", icon="🚀")
                    time.sleep(1.2)

                # Reset dan pindah menu biar user liat hasilnya
                st.session_state.tr = str(time.time())
                st.session_state.mn = "HIST" # Pindah ke riwayat
                st.rerun()

    # --- MENU LAPORAN ---
    elif st.session_state.mn == "OUT":
        if not df.empty: render_preview_native(df)

    # --- MENU RIWAYAT (MODE TABEL - BALANCED WITH LAPORAN) ---
    elif st.session_state.mn == "HIST":
        st.subheader("📜 RIWAYAT TRANSAKSI (TAMPILAN JELAS)")
        
        # 1. LOGIKA DATA & FILTER
        df_h = df.copy()
        df_h['Tanggal_dt'] = pd.to_datetime(df_h['Tanggal'])
        df_h['MY'] = df_h['Tanggal_dt'].dt.strftime('%B %Y')

        # Menu Pilihan Bulan (Agar estafet laporan rapi)
        list_bulan = ["SEMUA BULAN"] + sorted(df_h['MY'].unique().tolist(), 
                                              key=lambda x: datetime.strptime(x, '%B %Y'), 
                                              reverse=True)
        pilihan_bulan = st.selectbox("📅 Pilih Periode Laporan", list_bulan)
        
        if pilihan_bulan != "SEMUA BULAN":
            df_h = df_h[df_h['MY'] == pilihan_bulan]

        if not df_h.empty:
            # Urutkan dari yang terbaru
            df_h = df_h.sort_values(by='Tanggal_dt', ascending=False)
            hari_map = {'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu', 
                        'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'}
            
            # 2. HEADER TABEL RAKSASA (Senada dengan Tab Laporan)
            st.markdown("""
                <div style='display: flex; background-color: #020617; padding: 15px 5px; border-radius: 8px; border: 2px solid #334155; text-align: center; align-items: center; margin-bottom: 15px;'>
                    <div style='flex: 1.5; color: white; font-weight: bold; font-size: 18px;'>TANGGAL</div>
                    <div style='flex: 2.5; color: white; font-weight: bold; font-size: 18px;'>BA / DOKUMEN</div>
                    <div style='flex: 1; color: white; font-weight: bold; font-size: 18px;'>NA</div>
                    <div style='flex: 1; color: white; font-weight: bold; font-size: 18px;'>N</div>
                    <div style='flex: 1; color: white; font-weight: bold; font-size: 18px;'>NB</div>
                    <div style='flex: 1; color: white; font-weight: bold; font-size: 18px;'>DN</div>
                    <div style='flex: 2.5; color: white; font-weight: bold; font-size: 18px;'>AKSI PEGAWAI</div>
                </div>
            """, unsafe_allow_html=True)

            # 3. LOOPING BARIS DATA (Grouping per Tanggal & BA)
            for (tgl, ket), g in df_h.groupby(['Tanggal', 'Keterangan'], sort=False):
                dt_obj = pd.to_datetime(tgl)
                hari_id = hari_map.get(dt_obj.strftime('%A'), dt_obj.strftime('%A'))
                
                with st.container():
                    c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 2.5, 1, 1, 1, 1, 2.5])
                    
                    # Kolom 1: Tanggal (Tahun Lengkap)
                    c1.markdown(f"<div style='text-align:center;'><p style='margin:0; font-size:14px; color:#9ca3af;'>{hari_id}</p><b style='font-size:18px;'>{dt_obj.strftime('%d/%m/%Y')}</b></div>", unsafe_allow_html=True)

                    # Kolom 2: Nama BA / Dokumen
                    jenis = g['Jenis'].iloc[0]
                    clr = "#22c55e" if jenis == "Masuk" else "#f97316"
                    c2.markdown(f"<div style='text-align:center;'><b style='font-size:20px;'>{ket}</b><br><span style='color:{clr}; font-size:14px; font-weight:bold;'>{jenis.upper()}</span></div>", unsafe_allow_html=True)

                    # Kolom 3-6: Angka QTY Raksasa (24px)
                    for m_name, col_q in zip(["Model NA", "Model N", "Model NB", "Model DN"], [c3, c4, c5, c6]):
                        row_m = g[g['Model'] == m_name]
                        qty = row_m['Jumlah'].sum() if not row_m.empty else "-"
                        col_q.markdown(f"<div style='text-align:center; font-size:24px; font-weight:bold; color:#38bdf8; margin-top:5px;'>{qty}</div>", unsafe_allow_html=True)

                    # Kolom 7: Tombol Aksi (Teks Jelas)
                    idx_first = g.index[0]
                    with c7:
                        ce, cd = st.columns(2)
                        
                        # Tombol EDIT
                        if ce.button(f"📝 EDIT", key=f"e_{idx_first}", use_container_width=True):
                            st.session_state.ed, st.session_state.mn = idx_first, "IN"
                            st.rerun()
                        
                        # Tombol HAPUS dengan Feedback
                        if cd.button(f"🗑️ HAPUS", key=f"d_{idx_first}", use_container_width=True, type="secondary"):
                            # Hapus data berdasarkan index group
                            df_updated = df.drop(g.index)
                            save_data("stok", df_updated)
                            
                            # Kasih tanda sukses hapus
                            st.toast(f"🗑️ Data {ket} telah dihapus!", icon='🚮')
                            
                            # Jeda dikit biar toast kelihatan sebelum rerun
                            time.sleep(0.8) 
                            st.rerun()
                    
                    st.markdown("<hr style='margin:10px 0; border:1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
from fpdf import FPDF
from datetime import datetime
import os
import io

# KONFIGURASI LOGO BERBEDA
LOGO_KANTOR = "logo_kantor.png"
LOGO_BP4 = "logo_bp4.png"

def format_tgl_indo(tgl_str):
    try:
        dt = datetime.strptime(str(tgl_str), '%Y-%m-%d')
        return dt.strftime('%d-%m-%Y')
    except:
        return tgl_str

# ==========================================
# 1. FUNGSI DISPOSISI (SURAT MASUK) - REVISI
# ==========================================
def create_disposisi_pdf(data_row):
    pdf = FPDF(format='A5') 
    pdf.add_page()
    
    # 1. LOGO (Posisi sudah sesuai instruksi lu)
    if os.path.exists(LOGO_KANTOR):
        try: pdf.image(LOGO_KANTOR, 10, 10, 18) 
        except: pass
    
    # 2. HEADER KOP SURAT (Geser kanan 1 tab / ~25mm agar tidak nabrak logo)
    pdf.set_x(30) # Geser posisi awal teks ke kanan
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 5, "KEMENTERIAN AGAMA REPUBLIK INDONESIA", 0, 1, "C")
    
    pdf.set_x(30)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "KANTOR URUSAN AGAMA KECAMATAN TANGERANG", 0, 1, "C")
    
    pdf.set_x(30)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 5, "Jl. Jenderal Sudirman No. 8 Kota Tangerang", 0, 1, "C")
    
    pdf.ln(1); pdf.line(10, 30, 138, 30); pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "LEMBAR DISPOSISI", 0, 1, "C")
    pdf.ln(2)
    
    # 3. DETAIL SURAT (Dibuat rapet/satu paragraf, jarak antar baris 5mm)
    pdf.set_font("Arial", "", 10)
    y_start = pdf.get_y()
    
    # Label (Jarak y cuma selisih 5)
    pdf.text(10, y_start, "Surat Dari")
    pdf.text(10, y_start + 5, "No Surat")
    pdf.text(10, y_start + 10, "Perihal")

    # Titik Dua (Sejajar di 35)
    pdf.text(35, y_start, ":")
    pdf.text(35, y_start + 5, ":")
    pdf.text(35, y_start + 10, ":")

    # Isi (Sejajar di 38)
    pdf.text(38, y_start, f"{data_row.get('Pengirim', '-')}")
    pdf.text(38, y_start + 5, f"{data_row.get('No Surat', '-')}")
    pdf.text(38, y_start + 10, f"{data_row.get('Perihal', '-')}")

    tgl_terima_indo = format_tgl_indo(data_row.get('Tanggal Terima', '-'))
    pdf.text(95, y_start, f"Diterima: {tgl_terima_indo}")
    
    pdf.ln(22)
    
    # 4. KOTAK INSTRUKSI
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, pdf.get_y(), 128, 40, 'F')
    pdf.set_font("Arial", "B", 9)
    pdf.text(15, pdf.get_y() + 7, "INSTRUKSI / DISPOSISI KEPALA:")
    
    pdf.set_y(pdf.get_y() + 8)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 8, f"\"{data_row.get('Disposisi', '-')}\"", align='C')
    
    # 5. TANDA TANGAN (Posisi Kanan A5)
    pdf.ln(25) 
    
    pdf.set_font('Arial', '', 10)
    tgl_now = datetime.now().strftime('%d-%m-%Y')
    
    pdf.set_x(85)
    pdf.cell(53, 5, f"Tangerang, {tgl_now}", 0, 1, "C")
    pdf.set_x(85)
    pdf.cell(53, 5, "Mengetahui,", 0, 1, "C")
    pdf.ln(15) 
    
    # Baris Nama & NIP
    pdf.set_x(85)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(53, 3, "H. ANSHARI, S.Ag", 0, 1, "C")
    pdf.set_font('Arial', '', 8)
    pdf.set_x(85)
    pdf.cell(53, 5, "NIP. 197107041998031003", 0, 1, "C")
    
    # 6. FIX FOOTER (MATIKAN AUTO BREAK)
    pdf.set_auto_page_break(False) # <--- INI KUNCINYA
    pdf.set_y(-12) # Posisi mepet bawah
    pdf.set_font("Arial", "I", 7)
    pdf.cell(0, 10, f"Dicetak otomatis via Executive Apps pada {datetime.now().strftime('%H:%M:%S')}", 0, 0, "C")
    
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 2. FUNGSI PANGGILAN BP4 (INDIVIDUAL)
# ==========================================
def create_panggilan_bp4_pdf(data_row):
    pdf = FPDF()
    pdf.set_margins(10, 10, 10)
    pdf.add_page()
    
    # Header logo tetap sama
    if os.path.exists(LOGO_BP4): 
        try: pdf.image(LOGO_BP4, 20, 10, 30)
        except: pass
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 7, "BADAN PENASIHATAN PEMBINAAN", 0, 1, "C")
    pdf.cell(0, 7, "DAN PELESTARIAN PERKAWINAN (BP4)", 0, 1, "C")
    pdf.cell(0, 7, "KECAMATAN TANGERANG", 0, 1, "C")
    pdf.ln(2); pdf.set_line_width(0.6); pdf.line(10, 42, 200, 42); pdf.ln(10)
    
    # Ambil status panggilan untuk Judul (Contoh: "Menunggu Panggilan 1" -> "KE-1")
    status_p = data_row.get('Status Panggilan', '1')
    no_panggil = "KE-1" if "1" in status_p else "KE-2" if "2" in status_p else "PANGGILAN"
    
    pdf.set_left_margin(25); pdf.set_right_margin(25)
    
    # Judul Surat Dinamis
    pdf.set_font("Arial", "BU", 12)
    pdf.cell(0, 10, f"SURAT PANGGILAN {no_panggil}", 0, 1, "C")
    pdf.ln(5)
    
    # Identitas Surat
    pdf.set_font("Arial", "", 11)
    pdf.cell(30, 7, "Nomor", 0, 0); pdf.cell(0, 7, f": {data_row.get('ID Kasus','-')}/BP4/{datetime.now().year}", 0, 1)
    pdf.cell(30, 7, "Perihal", 0, 0); pdf.set_font("Arial", "B", 11); pdf.cell(0, 7, f": Panggilan Mediasi", 0, 1)
    
    pdf.ln(5); pdf.set_font("Arial", "", 11); pdf.cell(0, 7, "Yth,", 0, 1)
    
    # HANYA MEMANGGIL PIHAK TERADU
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, f"Sdr/i. {data_row.get('Teradu', 'Nama Teradu')}", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7, f"Alamat: {data_row.get('Alamat Sekarang','-')}")
    
    pdf.ln(8); pdf.cell(0, 7, "Assalamualaikum Wr. Wb", 0, 1)
    
    # Isi surat disesuaikan: memanggil teradu karena adanya laporan dari pengadu
    p_role = "Suami" if data_row.get('Role Teradu') == "Istri" else "Istri"
    pdf.multi_cell(0, 7, f"Sehubungan dengan adanya pengaduan dari {p_role} Saudara/i (Sdr/i. {data_row.get('Pengadu')}) ke kantor BP4 Kecamatan Tangerang perihal permasalahan rumah tangga, maka untuk proses mediasi/klarifikasi, kami mengharap kehadiran Saudara/i pada:")
    
    # Detail Waktu (Sama seperti sebelumnya)
    tgl_konsel_indo = format_tgl_indo(data_row.get('Tanggal Konseling', '-'))
    pdf.ln(5); pdf.set_x(35)
    pdf.cell(35, 8, "Hari / Tanggal", 0, 0); pdf.cell(0, 8, f": {tgl_konsel_indo}", 0, 1)
    pdf.set_x(35); pdf.cell(35, 8, "Waktu", 0, 0); pdf.cell(0, 8, ": Pukul 09:00 WIB", 0, 1)
    pdf.set_x(35); pdf.cell(35, 8, "Tempat", 0, 0); pdf.cell(0, 8, ": Kantor KUA/BP4 Kec. Tangerang", 0, 1)
    
    pdf.ln(8); pdf.multi_cell(0, 7, "Mengingat pentingnya hal tersebut, kehadiran Saudara/i sangat diharapkan. Demikian, atas perhatiannya kami ucapkan terima kasih.")
    pdf.ln(5); pdf.cell(0, 7, "Wassalamualaikum Wr. Wb", 0, 1)
    
    # Tanda Tangan
    pdf.ln(10); pdf.set_x(120)
    pdf.cell(0, 7, f"Tangerang, {datetime.now().strftime('%d-%m-%Y')}", 0, 1, "C")
    pdf.set_x(120); pdf.cell(0, 7, "Ketua BP4 Kec. Tangerang,", 0, 1, "C")
    pdf.ln(18); pdf.set_x(120); pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, f"( {data_row.get('Konselor','Admin')} )", 0, 1, "C")
    
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 3. REKAP BP4
# ==========================================
def create_rekap_bp4_pdf(df_rekap, bulan, tahun):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"LAPORAN KONSELING BP4", ln=True, align='C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Kecamatan Tangerang - Periode: {bulan} {tahun}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font('Arial', 'B', 10); pdf.set_text_color(255, 255, 255); pdf.set_fill_color(34, 139, 34)   
    w = [15, 45, 60, 60, 45, 55] 
    cols = ['No', 'Tgl Konseling', 'Nama Suami', 'Nama Istri', 'Status', 'Konselor']
    for i in range(len(cols)): pdf.cell(w[i], 12, cols[i], 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 10)
    for i, (_, r) in enumerate(df_rekap.iterrows(), 1):
        tgl_f = format_tgl_indo(str(r.get('Tanggal Konseling','-')))
        pdf.cell(w[0], 10, str(i), 1, 0, 'C')
        pdf.cell(w[1], 10, tgl_f, 1, 0, 'C')
        pdf.cell(w[2], 10, str(r.get('Nama Suami', '-'))[:35], 1, 0, 'L')
        pdf.cell(w[3], 10, str(r.get('Nama Istri', '-'))[:35], 1, 0, 'L')
        pdf.cell(w[4], 10, str(r.get('Status', '-')), 1, 0, 'C')
        pdf.cell(w[5], 10, str(r.get('Konselor', '-')), 1, 1, 'C')

    # TTD KUA RAPAT
    pdf.ln(10)
    if pdf.get_y() > 160: pdf.add_page()
    tgl_now = datetime.now().strftime('%d-%m-%Y')
    pdf.set_x(200); pdf.set_font('Arial', '', 11)
    pdf.cell(80, 5, f"Tangerang, {tgl_now}", 0, 1, "C")
    pdf.set_x(200); pdf.cell(80, 5, "Mengetahui,", 0, 1, "C")
    pdf.set_x(200); pdf.cell(80, 5, "Kepala KUA Kec. Tangerang", 0, 1, "C")
    pdf.ln(15); pdf.set_x(200); pdf.set_font('Arial', 'BU', 11)
    pdf.cell(80, 5, "H. ANSHARI, S.Ag", 0, 1, "C") 
    pdf.set_font('Arial', '', 8); pdf.set_x(200)
    pdf.cell(80, 5, "NIP. 197107041998031003", 0, 1, "C")
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 4. REKAP SURAT (MASUK/KELUAR)
# ==========================================
def create_rekap_surat_pdf(df_rekap, tipe, bulan, tahun):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"LAPORAN BULANAN SURAT {tipe.upper()}", ln=True, align='C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Kecamatan Tangerang - Periode: {bulan} {tahun}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font('Arial', 'B', 10); pdf.set_text_color(255, 255, 255); pdf.set_fill_color(34, 139, 34)   
    if tipe.lower() == "masuk":
        w = [15, 40, 45, 60, 60, 60]; cols = ['No', 'Tgl Terima', 'No Surat', 'Pengirim', 'Perihal', 'Disposisi']
    else:
        w = [15, 40, 50, 85, 90]; cols = ['No', 'Tgl Kirim', 'No Surat', 'Tujuan', 'Perihal']
        
    for i in range(len(cols)): pdf.cell(w[i], 12, cols[i], 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
    for i, (_, r) in enumerate(df_rekap.iterrows(), 1):
        if tipe.lower() == "masuk":
            tgl = format_tgl_indo(str(r.get('Tanggal Terima','-')))
            pdf.cell(w[0], 10, str(i), 1, 0, 'C')
            pdf.cell(w[1], 10, tgl, 1, 0, 'C')
            pdf.cell(w[2], 10, str(r.get('No Surat', '-'))[:25], 1, 0, 'L')
            pdf.cell(w[3], 10, str(r.get('Pengirim', '-'))[:35], 1, 0, 'L')
            pdf.cell(w[4], 10, str(r.get('Perihal', '-'))[:35], 1, 0, 'L')
            pdf.cell(w[5], 10, str(r.get('Disposisi', '-'))[:35], 1, 1, 'L')
        else:
            tgl = format_tgl_indo(str(r.get('tanggal_kirim','-')))
            pdf.cell(w[0], 10, str(i), 1, 0, 'C')
            pdf.cell(w[1], 10, tgl, 1, 0, 'C')
            pdf.cell(w[2], 10, str(r.get('no_surat', '-'))[:30], 1, 0, 'L')
            pdf.cell(w[3], 10, str(r.get('tujuan', '-'))[:45], 1, 0, 'L')
            pdf.cell(w[4], 10, str(r.get('perihal', '-'))[:50], 1, 1, 'L')

    # TTD KUA RAPAT
    pdf.ln(10)
    if pdf.get_y() > 160: pdf.add_page()
    tgl_now = datetime.now().strftime('%d-%m-%Y')
    pdf.set_x(200); pdf.set_font('Arial', '', 11)
    pdf.cell(80, 5, f"Tangerang, {tgl_now}", 0, 1, "C")
    pdf.set_x(200); pdf.cell(80, 5, "Mengetahui,", 0, 1, "C")
    pdf.set_x(200); pdf.cell(80, 5, "Kepala KUA Kec. Tangerang", 0, 1, "C")
    pdf.ln(15); pdf.set_x(200); pdf.set_font('Arial', 'BU', 11)
    pdf.cell(80, 5, "H. ANSHARI, S.Ag", 0, 1, "C") 
    pdf.set_font('Arial', '', 8); pdf.set_x(200)
    pdf.cell(80, 5, "NIP. 197107041998031003", 0, 1, "C")
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 5. REKAP WAKAF
# ==========================================
def create_rekap_wakaf_pdf(df_rekap, bulan, tahun):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"LAPORAN PENGERJAAN DIGITALISASI WAKAF", ln=True, align='C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Kecamatan Tangerang - Periode Kerja: {bulan} {tahun}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font('Arial', 'B', 9); pdf.set_text_color(255, 255, 255); pdf.set_fill_color(34, 139, 34)   
    w = [10, 30, 45, 45, 45, 30, 25, 50]
    cols = ['No', 'Tgl Berkas', 'No AIW/Sertifikat', 'Wakif', 'Nazhir', 'Kelurahan', 'Luas', 'Saksi-Saksi']
    for i in range(len(cols)): pdf.cell(w[i], 12, cols[i], 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 8)
    for i, (_, r) in enumerate(df_rekap.iterrows(), 1):
        tgl = format_tgl_indo(str(r.get('tanggal_aiw','-')))
        saksi_text = f"{r.get('saksi_1','-')} / {r.get('saksi_2','-')}"
        pdf.cell(w[0], 10, str(i), 1, 0, 'C')
        pdf.cell(w[1], 10, tgl, 1, 0, 'C')
        pdf.cell(w[2], 10, str(r.get('nomor_aiw', '-'))[:25], 1, 0, 'L')
        pdf.cell(w[3], 10, str(r.get('nama_wakif', '-'))[:25], 1, 0, 'L')
        pdf.cell(w[4], 10, str(r.get('nama_nazhir', '-'))[:25], 1, 0, 'L')
        pdf.cell(w[5], 10, str(r.get('kelurahan', '-')), 1, 0, 'C')
        pdf.cell(w[6], 10, f"{r.get('luas_m2', 0)} m2", 1, 0, 'C')
        pdf.cell(w[7], 10, saksi_text[:35], 1, 1, 'L')

    # TTD KUA RAPAT
    pdf.ln(10)
    if pdf.get_y() > 160: pdf.add_page()
    tgl_now = datetime.now().strftime('%d-%m-%Y')
    pdf.set_x(200); pdf.set_font('Arial', '', 11)
    pdf.cell(80, 5, f"Tangerang, {tgl_now}", 0, 1, "C")
    pdf.set_x(200); pdf.cell(80, 5, "Mengetahui,", 0, 1, "C")
    pdf.set_x(200); pdf.cell(80, 5, "Kepala KUA Kec. Tangerang", 0, 1, "C")
    pdf.ln(15); pdf.set_x(200); pdf.set_font('Arial', 'BU', 11)
    pdf.cell(80, 5, "H. ANSHARI, S.Ag", 0, 1, "C") 
    pdf.set_font('Arial', '', 8); pdf.set_x(200)
    pdf.cell(80, 5, "NIP. 197107041998031003", 0, 1, "C")
    
    return pdf.output(dest='S').encode('latin-1')
# ==========================================
# 6. REKAP DUPLIKAT BUKU NIKAH (NA)
# ==========================================
def create_rekap_duplikat_pdf(df_rekap, bulan, tahun):
    # Setup Page Landscape A4
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # Judul
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"LAPORAN PENERBITAN DUPLIKAT BUKU NIKAH (NA)", ln=True, align='C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Kecamatan Tangerang - Periode: {bulan} {tahun}", ln=True, align='C')
    pdf.ln(10)
    
    # Header Tabel (Warna Hijau sesuai gaya asli lu)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(34, 139, 34)   
    
    # Definisi Lebar Kolom (Total 277mm untuk Landscape A4)
    w = [10, 35, 30, 45, 45, 35, 30, 47] 
    cols = ['No', 'No Duplikat', 'Tgl Proses', 'Nama Suami', 'Nama Istri', 'No Akta Asal', 'Tgl Akad', 'Alasan']
    
    for i in range(len(cols)):
        pdf.cell(w[i], 12, cols[i], 1, 0, 'C', True)
    pdf.ln()
    
    # Isi Data Tabel
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 8)
    
    for i, (_, r) in enumerate(df_rekap.iterrows(), 1):
        # Format tanggal pengerjaan dan tanggal akad
        tgl_p = format_tgl_indo(str(r.get('tgl_proses','-')))
        tgl_a = format_tgl_indo(str(r.get('tgl_akad','-')))
        
        pdf.cell(w[0], 10, str(i), 1, 0, 'C')
        pdf.cell(w[1], 10, str(r.get('no_duplikat', '-')), 1, 0, 'C')
        pdf.cell(w[2], 10, tgl_p, 1, 0, 'C')
        pdf.cell(w[3], 10, str(r.get('nama_suami', '-'))[:25], 1, 0, 'L')
        pdf.cell(w[4], 10, str(r.get('nama_istri', '-'))[:25], 1, 0, 'L')
        pdf.cell(w[5], 10, str(r.get('no_akta_asal', '-')), 1, 0, 'C')
        pdf.cell(w[6], 10, tgl_a, 1, 0, 'C')
        pdf.cell(w[7], 10, str(r.get('alasan', '-')), 1, 1, 'C')

    # Tanda Tangan (Sesuai format asli lu: H. ANSHARI, S.Ag)
    pdf.ln(10)
    if pdf.get_y() > 160: pdf.add_page()
    tgl_now = datetime.now().strftime('%d-%m-%Y')
    
    pdf.set_x(200)
    pdf.set_font('Arial', '', 11)
    pdf.cell(80, 5, f"Tangerang, {tgl_now}", 0, 1, "C")
    pdf.set_x(200)
    pdf.cell(80, 5, "Mengetahui,", 0, 1, "C")
    pdf.set_x(200)
    pdf.cell(80, 5, "Kepala KUA Kec. Tangerang", 0, 1, "C")
    pdf.ln(15)
    pdf.set_x(200)
    pdf.set_font('Arial', 'BU', 11)
    pdf.cell(80, 5, "H. ANSHARI, S.Ag", 0, 1, "C") 
    pdf.set_font('Arial', '', 8)
    pdf.set_x(200)
    pdf.cell(80, 5, "NIP. 197107041998031003", 0, 1, "C")
    
    return pdf.output(dest='S').encode('latin-1')
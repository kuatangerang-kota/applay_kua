import streamlit as st
import pandas as pd
import os, base64
from utils.database import load_data, load_config


def render():
    pd.set_option("display.max_colwidth", None)

    # ================= DATA =================
    df_m  = load_data("masuk")
    df_k  = load_data("keluar")
    df_n  = load_data("akta_nik_baru")
    df_b  = load_data("bp4")
    df_dn = load_data("duplikat_nikah")
    df_t  = load_data("tamu")
    df_w  = load_data("wakaf")
    df_ri = load_data("rumah_ibadah")
    df_s  = load_data("stok")

    # ================= CSS =================
    st.markdown("""
    <style>
    .card-wrap{
        position: relative;
        width: 100%;
    }

    .dashboard-card{
        backdrop-filter: blur(16px);
        border-radius: 16px;
        padding: 18px 10px;
        min-height: 165px;
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
        text-align:center;
        animation: neonPulse 5s ease-in-out infinite;
        transition: transform .25s ease;
    }

    .dashboard-card:hover{
        transform: translateY(-4px) scale(1.02);
    }

    @keyframes neonPulse{
        0%{ box-shadow:0 0 6px rgba(0,255,150,.25);}
        50%{ box-shadow:0 0 16px rgba(0,255,150,.55);}
        100%{ box-shadow:0 0 6px rgba(0,255,150,.25);}
    }

    .hud-title{
        text-align:center;
        font-size:.75rem;
        letter-spacing:3px;
        opacity:.6;
        margin-bottom:25px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ================= HEADER + LOGO =================
    logo_html = ""
    logo_path = os.path.join(os.path.dirname(__file__), "..", "logo_kantor.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{b64}' style='width:90px;margin-bottom:10px;'>"

    st.markdown(f"""
    <div style="text-align:center;margin-bottom:25px;">
        {logo_html}
        <div style="font-size:.85rem;letter-spacing:4px;opacity:.65;">APLIKASI LAYANAN</div>
        <div class="glow-text" style="font-size:2.6rem;font-weight:900;">KUA TANGERANG</div>
        <div class="hud-title">REALTIME SERVICE COMMAND CENTER</div>
    </div>
    """, unsafe_allow_html=True)

    # ================= CARD =================
    def card(emoji, title, value, target, color="#00ff96", small=False):
        size = "1.1rem" if small else "1.8rem"

        st.markdown(f"""
        <div class="dashboard-card" style="border:2px solid {color}44;">
            <div style="font-size:2.2rem;filter:drop-shadow(0 0 8px {color});">{emoji}</div>
            <div style="font-size:.7rem;font-weight:800;opacity:.7">{title.upper()}</div>
            <div style="font-size:{size};font-weight:900;color:{color};text-shadow:0 0 6px {color}88">
                {value}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Buka {title}", key=f"btn_{target}", use_container_width=True):
            st.session_state.menu_selected = target
            st.rerun()


    # ================= GRID =================
    r = [st.columns(3) for _ in range(3)]

    with r[0][0]: card("📥","Surat Masuk",len(df_m),"📥 Surat Masuk")
    with r[0][1]: card("📤","Surat Keluar",len(df_k),"📤 Surat Keluar","#00d4ff")
    with r[0][2]: card("📜","Arsip Akta Nikah",len(df_n),"📜 Arsip Akta Nikah")

    with r[1][0]: card("👨‍👩‍👧","BP4",len(df_b),"👨‍👩‍👧‍👦 BP4","#bf00ff")
    with r[1][1]: card("📖","Duplikat NA",len(df_dn),"📖 Duplikat Nikah","#bf00ff")
    with r[1][2]: card("📒","Buku Tamu",len(df_t),"📒 Buku Tamu","#00d4ff")

    with r[2][0]: card("🌱","Arsip Wakaf",len(df_w),"🌱 Wakaf","#ffaa00")
    with r[2][1]: card("🕌","Rumah Ibadah",len(df_ri),"🕌 Rumah Ibadah","#ffaa00")

    # ================= STOK =================
    val_na = val_n = val_nb = 0
    if not df_s.empty:
        df_s.columns = df_s.columns.str.strip()
        if "Jumlah" in df_s.columns:
            df_s["Jumlah"] = pd.to_numeric(df_s["Jumlah"], errors="coerce").fillna(0)

        def sisa(model):
            m = df_s[(df_s["Model"]==model)&(df_s["Jenis"]=="Masuk")]["Jumlah"].sum()
            k = df_s[(df_s["Model"]==model)&(df_s["Jenis"]=="Keluar")]["Jumlah"].sum()
            return int(m-k)

        val_na,val_n,val_nb = sisa("Model NA"),sisa("Model N"),sisa("Model NB")

    with r[2][2]:
        card("📦","Stok",f"NA:{val_na} N:{val_n} NB:{val_nb}","📦 Stok Opname","#ffffff",small=True)

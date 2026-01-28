import streamlit as st
import json
import os

USER_FILE = "user_config.json"

def get_user_credentials():
    default_user = {"username": "admin", "password": "admin123"}
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r") as f: return json.load(f)
        except: return default_user
    return default_user

def login_page():
    # --- UI PREMIUM (CSS) ---
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #004d40 0%, #00251a 100%);
        }
        div[data-testid="stForm"] {
            background-color: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            border: none;
        }
        h1, h2, p {
            color: white !important;
            text-align: center;
        }
        .stButton button {
            background-color: #004d40 !important;
            color: white !important;
            border-radius: 10px;
            height: 3em;
            width: 100%;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- KONTEN LOGIN ---
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1>🏛️</h1>", unsafe_allow_html=True)
        st.markdown("<h2>SISTEM LAYANAN KUA</h2>", unsafe_allow_html=True)
        st.markdown("<p>Kecamatan Tangerang - Kota Tangerang</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.text_input("Username", placeholder="Masukkan Username")
            p = st.text_input("Password", type="password", placeholder="Masukkan Password")
            
            submit = st.form_submit_button("MASUK APLIKASI")
            
            if submit:
                creds = get_user_credentials()
                if u == creds["username"] and p == creds["password"]:
                    st.session_state.logged_in = True
                    st.success("Akses diterima! Membuka Dashboard...")
                    st.rerun()
                elif u == "pegawai" and p == "pegawai123":
                    st.session_state.logged_in = True
                    st.session_state.role = "pegawai"
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
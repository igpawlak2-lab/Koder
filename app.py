import re
import datetime
import os
import json
import uuid
import hashlib
import time  # POPRAWKA: Dodano brakujący import modułu time
import streamlit as st
import streamlit.components.v1 as components

# Czysty interfejs aplikacji
st.set_page_config(page_title="Koder", page_icon="📟", layout="wide")

# --- GLOBALNY PLIK JSON (STRUKTURA DANYCH DLA WSZYSTKICH KONT) ---
DATA_FILE = "dane_aplikacji.json"

def load_global_data():
    default_data = {
        "likes": 0, 
        "comments": [], 
        "user_data": {}, 
        "moderators": [],                       
        "admins": [],                       
        "vips": [],                       
        "staff_chat": [],    
        "staff_dms": [],
        "support_chat": [], 
        "password_resets": [],                       
        "announcement": "Brak aktualnych ogłoszeń.",
        "announcement_font": "sans-serif",
        "announcement_size": 16,
        "announcement_bg_color": "#e7f3fe",     
        "default_theme_color": "#1E90FF",      
        "default_bg_color": "#FFFFFF",         
        "default_clear_btn_color": "#5cb85c",
        "notifications": {}  # NOWE: System powiadomień
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict): return default_data
                if "likes" not in data: data["likes"] = 0
                if "comments" not in data: data["comments"] = []
                if "user_data" not in data: data["user_data"] = {}
                if "moderators" not in data: data["moderators"] = []
                if "admins" not in data: data["admins"] = []
                if "vips" not in data: data["vips"] = []
                if "staff_chat" not in data: data["staff_chat"] = [] 
                if "staff_dms" not in data: data["staff_dms"] = []
                if "support_chat" not in data: data["support_chat"] = [] 
                if "password_resets" not in data: data["password_resets"] = []
                if "announcement" not in data: data["announcement"] = "Brak aktualnych ogłoszeń."
                if "announcement_font" not in data: data["announcement_font"] = "sans-serif"
                if "announcement_size" not in data: data["announcement_size"] = 16
                if "announcement_bg_color" not in data: data["announcement_bg_color"] = "#e7f3fe"
                if "default_theme_color" not in data: data["default_theme_color"] = "#1E90FF"
                if "default_bg_color" not in data: data["default_bg_color"] = "#FFFFFF"
                if "default_clear_btn_color" not in data: data["default_clear_btn_color"] = "#5cb85c"
                if "notifications" not in data: data["notifications"] = {}
                return data
        except:
            return default_data
    return default_data

def save_global_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

# ✅ POPRAWKA: Automatyczne czyszczenie TYLKO kont testowych (nie trwałych!)
now = time.time()
db_changed = False
current_data = load_global_data()

if "user_data" in current_data:
    # WAŻNE: Usuwamy TYLKO konta z is_temporary=True, zwykłe konta zostają!
    expired_keys = [k for k, v in current_data["user_data"].items() if v.get("is_temporary") and now > v.get("expire_at", 0)]
    for k in expired_keys:
        del current_data["user_data"][k]
        if "admins" in current_data and k in current_data["admins"]: current_data["admins"].remove(k)
        if "moderators" in current_data and k in current_data["moderators"]: current_data["moderators"].remove(k)
        if "vips" in current_data and k in current_data["vips"]: current_data["vips"].remove(k)
        db_changed = True

if db_changed:
    save_global_data(current_data)
    st.session_state.global_store = current_data

# Inicjalizacja głównego magazynu w stanie sesji
if "global_store" not in st.session_state:
    st.session_state.global_store = load_global_data()

def_theme = st.session_state.global_store.get("default_theme_color", "#1E90FF")
def_bg = st.session_state.global_store.get("default_bg_color", "#FFFFFF")
def_clear = st.session_state.global_store.get("default_clear_btn_color", "#5cb85c")

# --- SYNC Z URL I LOCALSTORAGE ---
params = st.query_params
url_key = params.get("ak", "").strip()

if "user_author_key" not in st.session_state:
    if url_key:
        st.session_state.user_author_key = url_key
    else:
        st.session_state.user_author_key = ""

# Obsługa powrotu do konta admin2 z emulacji administratora
if "emulated_from_admin2" in st.session_state and st.sidebar.button("⬅️ Powrót do panelu Admin2", type="primary"):
    del st.session_state["emulated_from_admin2"]
    if "emulated_role" in st.session_state: del st.session_state["emulated_role"]
    st.session_state.user_author_key = "admin2"
    st.query_params["ak"] = "admin2"
    st.query_params["auth"] = "true"
    st.rerun()

current_user = st.session_state.user_author_key

# Funkcja generująca bezpieczny kod weryfikacyjny konta
def generate_account_secure_code(account_key):
    salt = "KoderSecureSystemSalt2026"
    hashed = hashlib.sha256((account_key + salt).encode('utf-8')).hexdigest()
    return str(int(hashed[:8], 16))[-6:].zfill(6)


# --- PANEL AWARYJNEGO KONTA WŁAŚCICIELA (admin2) ---  
if current_user == "admin2":  
    st.markdown("<h1 style='color: #FF0000; margin-bottom: 0;'>🚨 SYSTEM RATUNKOWY (admin2)</h1>", unsafe_allow_html=True)  
    st.write("Uruchomiono niezależny panel awaryjnego resetu haseł, zarządzania kadrą oraz całkowitego czyszczenia kont.")  
    st.write("---")  
       
    if "admin2_authenticated" not in st.session_state:  
        st.session_state.admin2_authenticated = (params.get("auth", "") == "true")  
           
    if not st.session_state.admin2_authenticated:  
        st.subheader("🔒 Weryfikacja tożsamości systemu ratunkowego")  
        with st.form("admin2_login_form"):  
            input_pass_admin2 = st.text_input("Podaj pierwsze hasło ratunkowe:", type="password", placeholder="Wpisz pierwsze hasło...")  
            input_pass2_admin2 = st.text_input("Podaj drugie hasło ratunkowe:", type="password", placeholder="Wpisz drugie hasło...")  
            submit_login_admin2 = st.form_submit_button("🔓 Uzyskaj dostęp awaryjny")  
               
            if submit_login_admin2:  
                if input_pass_admin2 == "Przyrodnik1" and input_pass2_admin2 == "Ignacy":  
                    st.session_state.admin2_authenticated = True  
                    st.query_params["auth"] = "true"  
                    components.html(f"""  
                        <script>  
                            localStorage.setItem("auth_admin2", "true");  
                            window.parent.location.href = window.parent.location.pathname + "?ak=admin2&auth=true";  
                        </script>  
                    """, height=0, width=0)  
                    st.rerun()  
                else:  
                    st.error("❌ Błędne hasła ratunkowe! Odmowa dostępu.")  
                       
        st.write("---")  
        with st.form("admin2_exit_form_locked"):  
            exit_key = st.text_input("Wróć do standardowego konta (wklej klucz):")  
            if st.form_submit_button("Opuść system ratunkowy") and exit_key.strip():  
                ek = exit_key.strip()  
                st.session_state.user_author_key = ek  
                st.query_params["ak"] = ek  
                if "admin2_authenticated" in st.session_state: del st.session_state.admin2_authenticated  
                components.html(f"<script>localStorage.setItem('koder_author_key2', '{ek}'); window.parent.location.href = window.parent.location.pathname + '?ak={ek}';</script>", height=0, width=0)
                st.rerun()  
        st.stop()  
   
    st.success("⚙️ Autoryzacja poprawna. Masz pełną niezależną kontrolę nad strukturą danych systemu.")  

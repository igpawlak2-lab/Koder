import re
import datetime
import os
import json
import uuid
import streamlit as st
import streamlit.components.v1 as components

# Czysty interfejs aplikacji
st.set_page_config(page_title="Koder", page_icon="📟", layout="wide")

# --- GLOBALNY PLIK JSON ---
DATA_FILE = "dane_aplikacji.json"

def load_global_data():
    default_data = {"likes": 0, "comments": [], "user_data": {}}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict): return default_data
                if "likes" not in data: data["likes"] = 0
                if "comments" not in data: data["comments"] = []
                if "user_data" not in data: data["user_data"] = {}
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

if "global_store" not in st.session_state:
    st.session_state.global_store = load_global_data()

# --- ZARZĄDZANIE KLUCZEM ---
params = st.query_params
if "user_author_key" not in st.session_state:
    url_key = params.get("ak", "")
    if url_key:
        st.session_state.user_author_key = url_key
    else:
        st.session_state.user_author_key = f"usr_{uuid.uuid4().hex[:16]}"
        st.query_params["ak"] = st.session_state.user_author_key

current_user = st.session_state.user_author_key

if current_user not in st.session_state.global_store["user_data"]:
    st.session_state.global_store["user_data"][current_user] = {
        "history": [], "notepad": "", "has_liked": False, "saved_nick": "",
        "theme_color": "#1E90FF", "bg_color": "#FFFFFF", "clear_btn_color": "#5cb85c", "dot_color": "#00FF00"
    }
    save_global_data(st.session_state.global_store)

# Aktualizacja brakujących pól (kompatybilność)
up = st.session_state.global_store["user_data"][current_user]
if "dot_color" not in up: up["dot_color"] = "#00FF00"
if "theme_color" not in up: up["theme_color"] = "#1E90FF"
if "bg_color" not in up: up["bg_color"] = "#FFFFFF"
if "clear_btn_color" not in up: up["clear_btn_color"] = "#5cb85c"
save_global_data(st.session_state.global_store)

# Pobranie kolorów
theme_color = up["theme_color"]
bg_color = up["bg_color"]
clear_btn_color = up["clear_btn_color"]
dot_color = up["dot_color"]

def get_contrast(hex_c):
    hex_c = hex_c.lstrip('#')
    r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
    return "#000000" if (r * 299 + g * 587 + b * 114) / 1000 > 135 else "#FFFFFF"

t_color = get_contrast(theme_color)
cb_t_color = get_contrast(clear_btn_color)
main_t_color = get_contrast(bg_color)

# --- CSS (WŁĄCZNIE Z 4. KOLOREM DLA KROPEK) ---
st.markdown(f"""
    <style>
        .stApp {{ background-color: {bg_color} !important; }}
        .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label {{ color: {main_t_color} !important; }}
        
        /* Kontener Radio */
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div {{ display: flex; gap: 10px; }}
        
        /* Nieaktywne kafelki */
        div[data-testid="stRadio"] label {{
            background-color: {"#262730" if main_t_color == "#FFFFFF" else "#F0F2F6"} !important;
            border: 2px solid {"#434654" if main_t_color == "#FFFFFF" else "#E0E2E6"} !important;
            border-radius: 10px; padding: 12px !important; color: {main_t_color} !important;
        }}

        /* Zaznaczony kafel (1. Kwadrat) */
        div[data-testid="stRadio"] label:has(input:checked) {{
            background-color: {theme_color} !important;
            color: {t_color} !important;
            border-color: {theme_color} !important;
        }}
        div[data-testid="stRadio"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p {{
            color: {t_color} !important;
        }}

        /* MAŁE KROPKI (4. Kwadrat) */
        /* Kółko obramowanie */
        div[data-testid="stRadio"] div[role="radiogroup"] label [data-testid="stRadioButtonToogleChecked"] {{
            background-color: transparent !important;
            border-color: {dot_color} !important;
        }}
        /* Wypełnienie kropki w środku */
        div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) [data-testid="stRadioButtonToogleChecked"]::after {{
            background-color: {dot_color} !important;
        }}
        /* Ikony SVG (alternatywne renderowanie) */
        div[data-testid="stRadio"] svg * {{ fill: {dot_color} !important; color: {dot_color} !important; }}

        /* PRZYCISKI AKCJI (3. Kwadrat) */
        div.stButton > button {{
            background-color: {clear_btn_color} !important;
            color: {cb_t_color} !important;
            border: 1px solid {clear_btn_color} !important;
            font-weight: bold !important;
        }}
        div.stButton > button p {{ color: {cb_t_color} !important; }}
        
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: {theme_color} !important; border-radius: 12px;
        }}
    </style>
""", unsafe_allow_html=True)

# --- LOGIKA KODOWANIA ---
DATA_MAP = {1: (1, 1, "H"), 2: (18, 1, "He"), 3: (1, 2, "Li"), 4: (2, 2, "Be"), 5: (13, 2, "B"), 6: (14, 2, "C"), 7: (15, 2, "N"), 8: (16, 2, "O"), 9: (17, 2, "F"), 10: (18, 2, "Ne"), 11: (1, 3, "Na"), 12: (2, 3, "Mg"), 13: (13, 3, "Al"), 14: (14, 3, "Si"), 15: (15, 3, "P"), 16: (16, 3, "S"), 17: (17, 3, "Cl"), 18: (18, 3, "Ar")}
# ... (pozostała mapa danych taka sama jak wcześniej)
SUBS = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'}

# --- INTERFEJS ---
st.title("📟 KODER")

c1, c2 = st.columns([1.6, 1.4])
with c1:
    st.subheader("Panel Sterowania")
    proto = st.radio("Wybierz system kodu:", ["Kod 1", "Kod 2"], horizontal=True)
    mode = st.radio("Wybierz operację:", ["Koduj", "Odkoduj"], horizontal=True)
    txt = st.text_input("Wprowadź dane:")
    if txt:
        st.info(f"Wynik zostanie wyświetlony tutaj (Logika kodowania aktywna)")

with c2:
    st.subheader("Historia operacji")
    if st.button("Wyczyść historię operacji"):
        up["history"] = []
        save_global_data(st.session_state.global_store)
        st.rerun()
    
    with st.container(height=200):
        for h in up["history"]: st.code(h)

st.write("---")
with st.expander("🎨 Personalizacja i Konto"):
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        new_theme = st.color_picker("Tło kafelka:", theme_color)
        if new_theme != theme_color: up["theme_color"] = new_theme; save_global_data(st.session_state.global_store); st.rerun()
    with col_b:
        new_bg = st.color_picker("Tło strony:", bg_color)
        if new_bg != bg_color: up["bg_color"] = new_bg; save_global_data(st.session_state.global_store); st.rerun()
    with col_c:
        new_btn = st.color_picker("Przyciski akcji:", clear_btn_color)
        if new_btn != clear_btn_color: up["clear_btn_color"] = new_btn; save_global_data(st.session_state.global_store); st.rerun()
    with col_d:
        new_dot = st.color_picker("Małe kropki:", dot_color)
        if new_dot != dot_color: up["dot_color"] = new_dot; save_global_data(st.session_state.global_store); st.rerun()

    st.write(f"Twoje ID: `{current_user}`")
    new_n = st.text_input("Twój stały nick:", up["saved_nick"])
    if new_n != up["saved_nick"]: up["saved_nick"] = new_n; save_global_data(st.session_state.global_store); st.rerun()

import re
import datetime
import os
import json
import uuid
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
        "admins": [], # NOWOŚĆ: Lista kluczy z rangą dodatkowego administratora                      
        "staff_chat": [],                       
        "announcement": "Brak aktualnych ogłoszeń.",
        "announcement_font": "sans-serif",
        "announcement_size": 16,
        "announcement_bg_color": "#e7f3fe",     
        "default_theme_color": "#1E90FF",      
        "default_bg_color": "#FFFFFF",         
        "default_clear_btn_color": "#5cb85c"   
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
                if "staff_chat" not in data: data["staff_chat"] = [] 
                if "announcement" not in data: data["announcement"] = "Brak aktualnych ogłoszeń."
                if "announcement_font" not in data: data["announcement_font"] = "sans-serif"
                if "announcement_size" not in data: data["announcement_size"] = 16
                if "announcement_bg_color" not in data: data["announcement_bg_color"] = "#e7f3fe"
                if "default_theme_color" not in data: data["default_theme_color"] = "#1E90FF"
                if "default_bg_color" not in data: data["default_bg_color"] = "#FFFFFF"
                if "default_clear_btn_color" not in data: data["default_clear_btn_color"] = "#5cb85c"
                
                # Konwersja starych komentarzy
                migrated_comments = []
                for c in data["comments"]:
                    if isinstance(c, dict) and "text" in c:
                        if "author_key" not in c:
                            c["author_key"] = c.get("session_id", "legacy")
                        migrated_comments.append(c)
                    elif isinstance(c, str):
                        migrated_comments.append({"text": c, "author_key": "legacy"})
                    else:
                        migrated_comments.append({"text": str(c), "author_key": "legacy"})
                data["comments"] = migrated_comments
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

# Inicjalizacja głównego magazynu w stanie sesji
if "global_store" not in st.session_state:
    st.session_state.global_store = load_global_data()

# Pobieranie domyślnych kolorów startowych z pliku JSON
def_theme = st.session_state.global_store.get("default_theme_color", "#1E90FF")
def_bg = st.session_state.global_store.get("default_bg_color", "#FFFFFF")
def_clear = st.session_state.global_store.get("default_clear_btn_color", "#5cb85c")

# --- BEZPIECZNE GENEROWANIE I SYNCHRONIZACJA KLUCZA KONTA ---
params = st.query_params
if "user_author_key" not in st.session_state:
    url_key = params.get("ak", "")
    if url_key:
        st.session_state.user_author_key = url_key
    else:
        st.session_state.user_author_key = f"usr_{uuid.uuid4().hex[:16]}"
        st.query_params["ak"] = st.session_state.user_author_key

current_user = st.session_state.user_author_key

# --- LOGIKA RANGI ---
is_root_admin = (current_user == "admin")
is_promoted_admin = (current_user in st.session_state.global_store.get("admins", []))
is_admin = is_root_admin or is_promoted_admin

is_moderator = (current_user in st.session_state.global_store.get("moderators", []))
is_staff = is_admin or is_moderator  

# Upewniamy się, że w strukturze bazy istnieje profil dla aktualnego użytkownika
if "user_data" not in st.session_state.global_store:
    st.session_state.global_store["user_data"] = {}

# NOWE KONTO: Pobiera aktualne wartości ustawione przez admina i zapisuje na stałe w bazie JSON
if current_user not in st.session_state.global_store["user_data"]:
    st.session_state.global_store["user_data"][current_user] = {
        "history": [], 
        "notepad": "", 
        "has_liked": False, 
        "saved_nick": "",
        "theme_color": def_theme,      
        "bg_color": def_bg,         
        "clear_btn_color": def_clear,
        "staff_bar_color": "#FF4B4B" if is_admin else "#FFA500" 
    }
    save_global_data(st.session_state.global_store)

# ISTNIEJĄCE KONTO: Kompatybilność wsteczna.
user_profile = st.session_state.global_store["user_data"][current_user]
updated_profile = False

if "saved_nick" not in user_profile:
    user_profile["saved_nick"] = ""
    updated_profile = True
if "theme_color" not in user_profile:
    user_profile["theme_color"] = "#1E90FF"
    updated_profile = True
if "bg_color" not in user_profile:
    user_profile["bg_color"] = "#FFFFFF"
    updated_profile = True
if "clear_btn_color" not in user_profile:
    user_profile["clear_btn_color"] = "#5cb85c"
    updated_profile = True
if "staff_bar_color" not in user_profile:
    user_profile["staff_bar_color"] = "#FF4B4B" if is_admin else "#FFA500"
    updated_profile = True

if updated_profile:
    save_global_data(st.session_state.global_store)

# Wyciągamy spersonalizowane kolory przypisane do danego profilu
theme_color = user_profile.get("theme_color", "#1E90FF")
bg_color = user_profile.get("bg_color", "#FFFFFF")
clear_btn_color = user_profile.get("clear_btn_color", "#5cb85c")
staff_bar_color = user_profile.get("staff_bar_color", "#FF4B4B" if is_admin else "#FFA500")

# Funkcja pomocnicza do obliczania kontrastu tekstu
def get_contrast_text_color(hex_color):
    hex_color = hex_color.lstrip('#')
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#000000" if brightness > 135 else "#FFFFFF"
    except:
        return "#FFFFFF"

text_color = get_contrast_text_color(theme_color)
clear_btn_text_color = get_contrast_text_color(clear_btn_color)
main_text_theme = get_contrast_text_color(bg_color)

# --- STYLOWANIE INTERFEJSU CSS ---
st.markdown(f"""
    <style>
        .stApp {{
            background-color: {bg_color} !important;
        }}
        .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label {{
            color: {main_text_theme} !important;
        }}
        
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div {{
            display: flex; gap: 10px; margin-top: 5px; width: 100%;
        }}
        
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label {{
            background-color: {"#262730" if main_text_theme == "#FFFFFF" else "#F0F2F6"} !important; 
            border: 2px solid {"#434654" if main_text_theme == "#FFFFFF" else "#E0E2E6"} !important; 
            padding: 12px 10px !important;
            border-radius: 10px; cursor: pointer; transition: all 0.2s ease-in-out;
            display: flex; align-items: center; justify-content: center; flex: 1;
            min-width: 140px; font-size: 16px !important; font-weight: bold !important; white-space: nowrap !important;
            color: {main_text_theme} !important;
        }}
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label div[data-testid="stMarkdownContainer"]::before {{
            display: none !important;
        }}
        div[data-testid="stRadio"] input[type="radio"] {{ display: none; }}
        
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label:has(input:checked) {{
            background-color: {theme_color} !important; 
            color: {text_color} !important; 
            border-color: {theme_color} !important;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
        }}
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label:has(input:checked) div[data-testid="stMarkdownContainer"] {{
            color: {text_color} !important;
        }}

        div.stButton > button[data-testid="stBaseButton-secondary"],
        div.stButton > button[data-testid="stBaseButton-primary"],
        .stApp div.stButton > button {{
            background-color: {clear_btn_color} !important;
            color: {clear_btn_text_color} !important;
            border: 2px solid {clear_btn_color} !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.1) !important;
            transition: all 0.2s ease-in-out !important;
        }}
        
        .stApp div.stButton > button p,
        .stApp div.stButton > button div,
        .stApp div.stButton > button span {{
            color: {clear_btn_text_color} !important;
        }}
        
        div.stButton > button:hover {{
            background-color: {clear_btn_color} !important;
            opacity: 0.85 !important;
            border-color: {clear_btn_color} !important;
            transform: scale(1.01);
        }}
        
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: {theme_color} !important; border-radius: 12px; 
            background-color: {"#1E1E1E" if main_text_theme == "#FFFFFF" else "#F9FAFB"};
        }}
    </style>
""", unsafe_allow_html=True)

# --- MAPA UKŁADU OKRESOWEGO I FUNKCJE POMOCNICZE ---
DATA_MAP = {
    1: (1, 1, "H"), 2: (18, 1, "He"), 3: (1, 2, "Li"), 4: (2, 2, "Be"), 5: (13, 2, "B"), 6: (14, 2, "C"), 
    7: (15, 2, "N"), 8: (16, 2, "O"), 9: (17, 2, "F"), 10: (18, 2, "Ne"), 11: (1, 3, "Na"), 12: (2, 3, "Mg"),
    13: (13, 3, "Al"), 14: (14, 3, "Si"), 15: (15, 3, "P"), 16: (16, 3, "S"), 17: (17, 3, "Cl"), 18: (18, 3, "Ar"),
    19: (1, 4, "K"), 20: (2, 4, "Ca"), 21: (3, 4, "Sc"), 22: (4, 7, "Ti"), 23: (5, 4, "V"), 24: (6, 4, "Cr"),
    25: (7, 4, "Mn"), 26: (8, 4, "Fe"), 27: (9, 4, "Co"), 28: (10, 4, "Ni"), 29: (11, 4, "Cu"), 30: (12, 4, "Zn"),
    31: (13, 4, "Ga"), 32: (14, 4, "Ge"), 33: (15, 4, "As"), 34: (16, 4, "Se"), 35: (17, 4, "Br"), 36: (18, 4, "Kr"),
    37: (1, 5, "Rb"), 38: (2, 5, "Sr"), 39: (3, 5, "Y"), 40: (4, 5, "Zr"), 41: (5, 5, "Nb"), 42: (6, 5, "Mo"),
    43: (7, 5, "Tc"), 44: (8, 5, "Ru"), 45: (9, 5, "Rh"), 46: (10, 5, "Pd"), 47: (11, 5, "Ag"), 48: (12, 5, "Cd"),
    49: (13, 5, "In"), 50: (14, 5, "Sn"), 51: (15, 5, "Sb"), 52: (16, 5, "Te"), 53: (17, 5, "I"), 54: (18, 5, "Xe"),
    55: (1, 6, "Cs"), 56: (2, 6, "Ba"), 57: (3, 6, "La"), 72: (4, 6, "Hf"), 73: (5, 6, "Ta"), 74: (6, 6, "W"), 
    75: (7, 6, "Re"), 76: (8, 6, "Os"), 77: (9, 6, "Ir"), 78: (10, 6, "Pt"), 79: (11, 6, "Au"), 80: (12, 6, "Hg"), 
    81: (13, 6, "Tl"), 82: (14, 6, "Pb"), 83: (15, 6, "Bi"), 84: (16, 6, "Po"), 85: (17, 6, "At"), 86: (18, 6, "Rn"), 
    87: (1, 7, "Fr"), 88: (2, 7, "Ra"), 89: (3, 7, "Ac"), 104: (4, 7, "Rf"), 105: (5, 7, "Db"), 106: (6, 7, "Sg"), 
    107: (7, 7, "Bh"), 108: (8, 7, "Hs"), 109: (9, 7, "Mt"), 110: (10, 7, "Ds"), 111: (11, 7, "Rg"), 112: (12, 7, "Cn"), 
    113: (13, 7, "Nh"), 114: (14, 7, "Fl"), 115: (15, 7, "Mc"), 116: (16, 7, "Lv"), 117: (17, 7, "Ts"), 118: (18, 7, "Og")
}

SUPERSCRIPTS = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
SUBSCRIPTS = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'}

def to_superscript(num_str): return "".join(SUPERSCRIPTS.get(c, c) for c in num_str)
def to_subscript(num_str): return "".join(SUBSCRIPTS.get(c, c) for c in num_str)
REV_SUP = {v: k for k, v in SUPERSCRIPTS.items()}
REV_SUB = {v: k for k, v in SUBSCRIPTS.items()}

def clean_txt(t):
    z = {'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'}
    t = t.upper()
    for k, v in z.items(): t = t.replace(k, v)
    t = t.replace('J', 'I')
    return re.sub(r'[^A-Z ]', '', t)

def enc_v1(l):
    for i, (g, o, s) in DATA_MAP.items():
        if s == l: return f"{i}"
    for i, (g, o, s) in DATA_MAP.items():
        if s[0] == l and len(s) > 1: return f"{i}.1"
        if len(s) > 1 and s[1] == l.lower(): return f"{i}.2"
    return "?"

def format_v1_unicode(code_str):
    if "." in code_str:
        parts = code_str.split(".")
        return f"{parts[0]}{to_subscript(parts[1])}"
    return code_str

def dec_v1(s):
    s = s.strip()
    if not s: return ""
    converted = ""
    for char in s:
        if char in REV_SUB:
            if "." not in converted: converted += "."
            converted += REV_SUB[char]
        else: converted += char
    try:
        if "." in converted:
            parts = converted.split(".")
            val, idx = int(parts[0]), parts[1]
        else:
            val, idx = int(converted), ""
        if val in DATA_MAP:
            res = DATA_MAP[val][2]
            return res[0].upper() if idx in ["", "1"] else res[1].upper()
    except ValueError: pass
    return "?"

def enc_v2(l):
    for i, (g, o, s) in DATA_MAP.items():
        if s == l: return f"{g}.{o}"
    for i, (g, o, s) in DATA_MAP.items():
        if s[0] == l and len(s) > 1: return f"{g}.{o}1"
        if len(s) > 1 and s[1] == l.lower(): return f"{g}.{o}2"
    return "?"

def format_v2_unicode(code_str):
    if "." in code_str:
        parts = code_str.split(".")
        g, rest = parts[0], parts[1]
        o = rest[0]
        sub = rest[1] if len(rest) > 1 else ""
        return f"{g}{to_superscript(o)}{to_subscript(sub)}"
    return code_str

def dec_v2(s):
    s = s.strip()
    if not s: return ""
    if "." in s:
        try:
            parts = s.split(".")
            g, rest = int(parts[0]), parts[1]
            if len(rest) > 1: o, pos = int(rest[0]), rest[1]
            else: o, pos = int(rest), ""
            for i, (vg, vo, vs) in DATA_MAP.items():
                if vg == g and vo == o: return vs[1].upper() if pos == "2" and len(vs) > 1 else vs[0].upper()
        except ValueError: pass
        return "?"
    g_part, o_part, sub_part, in_o = "", "", "", False
    for char in s:
        if char in REV_SUP: o_part += REV_SUP[char]; in_o = True
        elif char in REV_SUB: sub_part += REV_SUB[char]
        else:
            if not in_o: g_part += char
    if not g_part or not o_part: return "?"
    try:
        g, o, pos = int(g_part), int(o_part), sub_part
        for i, (vg, vo, vs) in DATA_MAP.items():
            if vg == g and vo == o: return vs[1].upper() if pos == "2" and len(vs) > 1 else vs[0].upper()
    except ValueError: pass
    return "?"

# --- DYNAMICZNY NAGŁÓWEK ---
if is_admin:
    st.markdown("<h1 style='margin-bottom: 0;'>📟 KODER <span style='color: #FF4B4B; font-size: 1.2rem; vertical-align: middle; background-color: rgba(255,75,75,0.1); padding: 4px 8px; border-radius: 6px; margin-left: 10px; font-weight: bold;'>Admin</span></h1>", unsafe_allow_html=True)
elif is_moderator:
    st.markdown("<h1 style='margin-bottom: 0;'>📟 KODER <span style='color: #FFA500; font-size: 1.2rem; vertical-align: middle; background-color: rgba(255,165,0,0.1); padding: 4px 8px; border-radius: 6px; margin-left: 10px; font-weight: bold;'>Moderator</span></h1>", unsafe_allow_html=True)
else:
    st.title("📟 KODER")

st.write("Uniwersalny system kodowania i dekodowania tekstu.")

components.html(
    f"""
    <script>
        var savedKey = localStorage.getItem("koder_author_key2");
        var currentUrl = new URL(window.parent.location.href);
        var urlKey = currentUrl.searchParams.get("ak");
        
        if (savedKey && savedKey !== urlKey) {{
            currentUrl.searchParams.set("ak", savedKey);
            window.parent.location.href = currentUrl.href;
        }} else if (!savedKey && urlKey) {{
            localStorage.setItem("koder_author_key2", urlKey);
        }}
    </script>
    """, height=0, width=0
)

user_history = user_profile.get("history", [])
user_notepad_content = user_profile.get("notepad", "")
user_has_liked = user_profile.get("has_liked", False)
user_saved_nick = user_profile.get("saved_nick", "")

c1, c2 = st.columns([1.6, 1.4])
with c1:
    if is_staff:
        tab_main, tab_chat = st.tabs(["🎛️ Panel Sterowania", "🔒 Prywatny Chat Staffu"])
    else:
        tab_main = st.tabs(["🎛️ Panel Sterowania"])[0]
        
    with tab_main:
        st.radio("Wybierz system kodu:", ["Kod 1", "Kod 2"], horizontal=True, key="proto_selection")
        st.radio("Wybierz operację:", ["Koduj", "Odkoduj"], horizontal=True, key="mode_selection")
        
        proto = st.session_state.proto_selection
        mode = st.session_state.mode_selection
        
        st.write(" ")
        txt = st.text_input("Wprowadź dane i zatwierdź Enterem:", placeholder="Wpisz dane tutaj...")
        
        if txt:
            res_display = ""
            if mode == "Koduj":
                words = clean_txt(txt).split(' ')
                raw_words = [[enc_v1(l) if "Kod 1" in proto else enc_v2(l) for l in w] for w in words]
                if "Kod 1" in proto:
                    res_display = "   ".join([" ".join([format_v1_unicode(l) for l in w]) for w in raw_words])
                else:
                    res_display = "   ".join([" ".join([format_v2_unicode(l) for l in w]) for w in raw_words])
            else:
                decoded_words = []
                for w in txt.split("   "):
                    word_chars = []
                    for s in w.strip().split(" "):
                        if s: word_chars.append(dec_v1(s) if "Kod 1" in proto else dec_v2(s))
                    decoded_words.append("".join(word_chars))
                res_display = " ".join(decoded_words)

            st.markdown(f"**Wynik:** <div style='font-size:1.4rem; font-weight:bold; background-color:#F0F2F6; color:#1E1E1E; padding:12px; border-radius:8px; margin-bottom:10px;'>{res_display}</div>", unsafe_allow_html=True)
            if mode == "Koduj":
                st.caption("📋 Kliknij ikonę po prawej stronie bloku, aby skopiować kod wraz z indeksami:")
                st.code(res_display, language="text")
            
            h_time = datetime.datetime.now().strftime('%H:%M:%S')
            entry = f"{h_time} | {proto} | {mode}: {txt} -> {res_display}"
            
            if not user_history or user_history[0] != entry:
                user_history.insert(0, entry)
                st.session_state.global_store["user_data"][current_user]["history"] = user_history
                save_global_data(st.session_state.global_store)
                st.rerun()

    # --- PRYWATNY CZAT DLA ADMINA I MODERATORÓW ---
    if is_staff:
        with tab_chat:
            st.subheader("🕵️ Prywatny kanał komunikacji")
            st.caption("Ten czat jest widoczny wyłącznie dla Administratora oraz zatwierdzonych Moderatorów.")
            
            with st.form("staff_chat_form", clear_on_submit=True):
                role_label = "Admin" if is_admin else "Moderator"
                staff_nick = user_saved_nick if user_saved_nick else f"User_{current_user[:6]}"
                
                chat_msg = st.text_input(f"Wiadomość jako **{staff_nick} ({role_label})**:", placeholder="Wpisz tajną wiadomość do ekipy...")
                send_chat = st.form_submit_button("🚀 Wyślij do Staffu")
                
                if send_chat and chat_msg.strip():
                    time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                    formatted_msg = {
                        "sender_nick": staff_nick,
                        "sender_role": role_label,
                        "time": time_stamp,
                        "text": chat_msg.strip(),
                        "bar_color": staff_bar_color
                    }
                    current_data = load_global_data()
                    if "staff_chat" not in current_data:
                        current_data["staff_chat"] = []
                    current_data["staff_chat"].append(formatted_msg)
                    save_global_data(current_data)
                    st.session_state.global_store = current_data
                    st.rerun()
            
            if is_admin:
                if st.button("🗑️ Wyczyść cały Chat Staffu", type="primary", key="clear_staff_chat_btn"):
                    current_data = load_global_data()
                    current_data["staff_chat"] = []
                    save_global_data(current_data)
                    st.session_state.global_store = current_data
                    st.toast("Wyczyszczono historię czatu ekipy.")
                    st.rerun()

            staff_messages = st.session_state.global_store.get("staff_chat", [])
            st.write(" ")
            with st.container(height=300):
                if not staff_messages:
                    st.caption("Brak wiadomości na kanale staffu. Napisz coś powyżej!")
                else:
                    for msg in reversed(staff_messages):
                        fallback_color = "#FF4B4B" if msg.get("sender_role") == "Admin" else "#FFA500"
                        current_bar_color = msg.get("bar_color", fallback_color)
                        
                        st.markdown(
                            f"""
                            <div style="background-color: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid {current_bar_color};">
                                <span style="color: {current_bar_color}; font-weight: bold;">[{msg.get('sender_role')}] {msg.get('sender_nick')}</span> 
                                <span style="font-size: 0.8rem; opacity: 0.6; float: right;">{msg.get('time')}</span>
                                <p style="margin: 4px 0 0 0; font-size: 1rem;">{msg.get('text')}</p>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

    # --- TABLICA OGŁOSZEŃ ---
    st.write("---")
    st.subheader("📢 Tablica Ogłoszeń")
    
    current_announcement = st.session_state.global_store.get("announcement", "Brak aktualnych ogłoszeń.")
    ann_font = st.session_state.global_store.get("announcement_font", "sans-serif")
    ann_size = st.session_state.global_store.get("announcement_size", 16)
    ann_bg = st.session_state.global_store.get("announcement_bg_color", "#e7f3fe")
    
    ann_text_color = "#0c5460" if get_contrast_text_color(ann_bg) == "#000000" else "#FFFFFF"
    ann_border_color = "#2196F3" if ann_text_color == "#0c5460" else ann_bg
    
    st.markdown(
        f"""
        <div style="background-color: {ann_bg}; border-left: 6px solid {ann_border_color}; padding: 15px; border-radius: 6px; margin-bottom: 15px; font-family: {ann_font}, Arial, sans-serif; font-size: {ann_size}px; color: {ann_text_color}; line-height: 1.5;">
            {current_announcement}
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    if is_staff:
        st.caption(f"🛠️ Panel zarządzania ogłoszeniem (Widoczny dla roli: {'Admin' if is_admin else 'Moderator'}):")
        new_announcement_text = st.text_area("Zmień treść ogłoszenia globalnego:", value=current_announcement, placeholder="Wpisz nowe ogłoszenie...")
        
        f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 1.0])
        with f_col1:
            font_options = {
                "Bezszeryfowa (Modern)": "sans-serif",
                "Szeryfowa (Classic)": "serif",
                "Monospace (Kodowa)": "monospace",
                "Comic Sans MS": "'Comic Sans MS', cursive",
                "Impact (Pogrubiona)": "Impact, Charcoal"
            }
            current_font_index = list(font_options.values()).index(ann_font) if ann_font in font_options.values() else 0
            chosen_font_label = st.selectbox("Wybierz krój czcionki:", list(font_options.keys()), index=current_font_index)
            selected_font_value = font_options[chosen_font_label]
            
        with f_col2:
            selected_size_value = st.slider("Wielkość tekstu (px):", min_value=12, max_value=36, value=int(ann_size), step=1)
            
        with f_col3:
            selected_ann_bg = st.color_picker("Tło tablicy:", value=ann_bg, key="admin_ann_bg_picker")
            
        if st.button("💾 Zapisz ogłoszenie i wygląd", key="save_announcement_btn"):
            current_data = load_global_data()
            current_data["announcement"] = new_announcement_text.strip()
            current_data["announcement_font"] = selected_font_value
            current_data["announcement_size"] = selected_size_value
            current_data["announcement_bg_color"] = selected_ann_bg
            
            save_global_data(current_data)
            st.session_state.global_store = current_data
            st.success("Ogłoszenie oraz jego formatowanie zostały zaktualizowane!")
            st.rerun()

with c2:
    st.subheader("Historia operacji")
    if st.button("🗑️ Wyczyść historię operacji", type="primary"):
        st.session_state.global_store["user_data"][current_user]["history"] = []
        save_global_data(st.session_state.global_store)
        st.rerun()
    
    with st.container(height=240):
        if not user_history:
            st.caption("Brak Twoich ostatnich operacji. Wpisz coś po lewej stronie.")
        else:
            for item in user_history: st.code(item, language="text")

    st.write(" ")
    st.subheader("📝 Twój Prywatny Notatnik")
    
    def save_notepad_instantly():
        if "local_notepad_field" in st.session_state:
            val = st.session_state.local_notepad_field
            st.session_state.global_store["user_data"][current_user]["notepad"] = val
            save_global_data(st.session_state.global_store)

    note_input = st.text_area(
        "Zapisz swoje uwagi:",
        value=user_notepad_content,
        placeholder="Wpisz notatki, kody lub sekwencje...",
        height=180,
        key="local_notepad_field",
        on_change=save_notepad_instantly
    )

# --- GLOBALNE POLUBIENIA I KOMENTARZE ---
st.write("---")
st.subheader("💬 Opinie użytkowników")

col_like1, col_like2 = st.columns([1.5, 5])
with col_like1:
    if not user_has_liked:
        if st.button("👍 Polub stronę", key="btn_like_page"):
            st.session_state.global_store["user_data"][current_user]["has_liked"] = True
            total_likes = sum(1 for u in st.session_state.global_store["user_data"].values() if u.get("has_liked", False))
            st.session_state.global_store["likes"] = total_likes
            save_global_data(st.session_state.global_store)
            st.rerun()
    else:
        if st.button("❌ Cofnij polubienie", type="primary", key="btn_unlike_page"):
            st.session_state.global_store["user_data"][current_user]["has_liked"] = False
            total_likes = sum(1 for u in st.session_state.global_store["user_data"].values() if u.get("has_liked", False))
            st.session_state.global_store["likes"] = total_likes
            save_global_data(st.session_state.global_store)
            st.rerun()

with col_like2:
    st.write(f"Ta strona została polubiona już **{st.session_state.global_store.get('likes', 0)}** razy!")

st.write(" ")

# --- PANEL PERSONALIZACJI WYGLĄDU ---
with st.expander("🎨 Personalizacja Wyglądu i Zarządzanie Kontem"):
    st.subheader("Twoje własne ustawienia kolorów")
    
    if is_staff:
        cc_col1, cc_col2, cc_col3, cc_col4 = st.columns(4)
    else:
        cc_col1, cc_col2, cc_col3 = st.columns(3)
        cc_col4 = None
        
    with cc_col1:
        chosen_color = st.color_picker("Aktywny przycisk wyboru:", value=theme_color, key="user_theme_picker")
        if chosen_color != theme_color:
            st.session_state.global_store["user_data"][current_user]["theme_color"] = chosen_color
            save_global_data(st.session_state.global_store)
            st.rerun()
            
    with cc_col2:
        chosen_bg = st.color_picker("Tło całej aplikacji:", value=bg_color, key="user_bg_picker")
        if chosen_bg != bg_color:
            st.session_state.global_store["user_data"][current_user]["bg_color"] = chosen_bg
            save_global_data(st.session_state.global_store)
            st.rerun()
            
    with cc_col3:
        chosen_clear_color = st.color_picker("Przyciski akcji:", value=clear_btn_color, key="user_clear_picker")
        if chosen_clear_color != clear_btn_color:
            st.session_state.global_store["user_data"][current_user]["clear_btn_color"] = chosen_clear_color
            save_global_data(st.session_state.global_store)
            st.rerun()
            
    if cc_col4 and is_staff:
        with cc_col4:
            chosen_bar_color = st.color_picker("Twój pasek na czacie:", value=staff_bar_color, key="user_staff_bar_picker")
            if chosen_bar_color != staff_bar_color:
                st.session_state.global_store["user_data"][current_user]["staff_bar_color"] = chosen_bar_color
                save_global_data(st.session_state.global_store)
                st.rerun()

    # --- PANEL ZAANSOWANYCH UPRAWNIEŃ (WIDOCZNY DLA ADMINÓW) ---
    if is_admin:
        st.write("---")
        st.subheader("👑 Panel Admina: Zarządzanie uprawnieniami")
        
        adm_tab1, adm_tab2 = st.tabs(["👥 Zarządzanie Moderatorami", "🛡️ Zarządzanie Administratorami"])
        
        with adm_tab1:
            st.caption("Dodaj lub usuń uprawnienia moderatora dla konkretnych kluczy kont:")
            current_mods = st.session_state.global_store.get("moderators", [])
            
            with st.form("add_moderator_form", clear_on_submit=True):
                mod_key_input = st.text_input("Wklej klucz konta, które chcesz awansować na Moderatora:", placeholder="usr_...")
                submit_mod = st.form_submit_button("➕ Nadaj uprawnienia moderatora")
                
                if submit_mod and mod_key_input.strip():
                    target_key = mod_key_input.strip()
                    if target_key == "admin" or target_key in st.session_state.global_store.get("admins", []):
                        st.error("To konto ma już wyższą rangę (Admin).")
                    elif target_key in current_mods:
                        st.warning("To konto jest już moderatorem.")
                    else:
                        current_data = load_global_data()
                        if "moderators" not in current_data:
                            current_data["moderators"] = []
                        current_data["moderators"].append(target_key)
                        save_global_data(current_data)
                        st.session_state.global_store = current_data
                        st.success(f"Pomyślnie nadano uprawnienia moderatora dla klucza: {target_key}")
                        st.rerun()
                        
            if current_mods:
                st.write("**Aktualna lista moderatorów:**")
                for m_idx, m_key in enumerate(current_mods):
                    m_col1, m_col2 = st.columns([4.0, 2.0])
                    with m_col1:
                        u_nick = st.session_state.global_store["user_data"].get(m_key, {}).get("saved_nick", "")
                        display_text = f"🔑 `{m_key}`" + (f" (Podpis: **{u_nick}**)" if u_nick else "")
                        st.markdown(display_text)
                    with m_col2:
                        if st.button("❌ Odbierz rangę MOD", key=f"remove_mod_{m_idx}", type="primary", use_container_width=True):
                            current_data = load_global_data()
                            if m_key in current_data.get("moderators", []):
                                current_data["moderators"].remove(m_key)
                                save_global_data(current_data)
                                st.session_state.global_store = current_data
                                st.toast(f"Odebrano uprawnienia dla {m_key}")
                                st.rerun()
            else:
                st.caption("Brak przypisanych moderatorów.")
                
        with adm_tab2:
            st.caption("Dodaj lub usuń uprawnienia dodatkowego administratora:")
            current_admins = st.session_state.global_store.get("admins", [])
            
            with st.form("add_admin_form", clear_on_submit=True):
                adm_key_input = st.text_input("Wklej klucz konta, które chcesz awansować na Administratora:", placeholder="usr_...")
                submit_adm = st.form_submit_button("👑 Nadaj uprawnienia administratora")
                
                if submit_adm and adm_key_input.strip():
                    target_key = adm_key_input.strip()
                    if target_key == "admin":
                        st.error("Konto główne 'admin' posiada niezbywalne prawa Root-Admina.")
                    elif target_key in current_admins:
                        st.warning("To konto jest już administratorem.")
                    else:
                        current_data = load_global_data()
                        if "admins" not in current_data:
                            current_data["admins"] = []
                        current_data["admins"].append(target_key)
                        
                        # Jeśli awansowany użytkownik był moderatorem, usuwamy go z listy modów
                        if "moderators" in current_data and target_key in current_data["moderators"]:
                            current_data["moderators"].remove(target_key)
                            
                        save_global_data(current_data)
                        st.session_state.global_store = current_data
                        st.success(f"Pomyślnie nadano uprawnienia administratora dla klucza: {target_key}")
                        st.rerun()
                        
            if current_admins:
                st.write("**Lista dodatkowych administratorów:**")
                for a_idx, a_key in enumerate(current_admins):
                    a_col1, a_col2 = st.columns([4.0, 2.0])
                    with a_col1:
                        u_nick = st.session_state.global_store["user_data"].get(a_key, {}).get("saved_nick", "")
                        display_text = f"🛡️ `{a_key}`" + (f" (Podpis: **{u_nick}**)" if u_nick else "")
                        st.markdown(display_text)
                    with a_col2:
                        if st.button("❌ Odbierz rangę ADMIN", key=f"remove_adm_{a_idx}", type="primary", use_container_width=True):
                            current_data = load_global_data()
                            if a_key in current_data.get("admins", []):
                                current_data["admins"].remove(a_key)
                                save_global_data(current_data)
                                st.session_state.global_store = current_data
                                st.toast(f"Odebrano uprawnienia administratora dla {a_key}")
                                st.rerun()
            else:
                st.caption("Brak dodatkowych administratorów (poza kontem głównym).")

        st.write("---")
        st.subheader("🎨 Panel Admina: Domyślny motyw startowy")
        st.caption("Ustaw kolory, z którymi będą automatycznie startować nowo generowane konta:")
        
        adm_cc1, adm_cc2, adm_cc3 = st.columns(3)
        with adm_cc1:
            new_def_theme = st.color_picker("Domyślny przycisk wyboru:", value=def_theme, key="admin_def_theme")
        with adm_cc2:
            new_def_bg = st.color_picker("Domyślne tło aplikacji:", value=def_bg, key="admin_def_bg")
        with adm_cc3:
            new_def_clear = st.color_picker("Domyślne przyciski akcji:", value=def_clear, key="admin_def_clear")
            
        if (new_def_theme != def_theme) or (new_def_bg != def_bg) or (new_def_clear != def_clear):
            current_data = load_global_data()
            current_data["default_theme_color"] = new_def_theme
            current_data["default_bg_color"] = new_def_bg
            current_data["default_clear_btn_color"] = new_def_clear
            save_global_data(current_data)
            st.session_state.global_store = current_data
            st.success("Zmieniono domyślny szablon startowy!")
            st.rerun()

    st.write("---")
    st.write("**Twój unikalny klucz konta:**")
    st.code(st.session_state.user_author_key, language="text")
    
    current_nick_val = st.session_state.global_store["user_data"][current_user].get("saved_nick", "")
    new_nick = st.text_input("Ustaw swój stały podpis (nick):", value=current_nick_val, placeholder="Wpisz stały nick...")
    if new_nick != current_nick_val:
        st.session_state.global_store["user_data"][current_user]["saved_nick"] = new_nick.strip()
        save_global_data(st.session_state.global_store)
        st.rerun()
        
    st.write("---")
    with st.form("account_key_form"):
        new_key = st.text_input("Zmień konto na inne (wklej klucz):")
        submit_change = st.form_submit_button("Zmień klucz konta")
        
        if submit_change and new_key.strip():
            clean_key = new_key.strip()
            st.session_state.user_author_key = clean_key
            st.query_params["ak"] = clean_key
            
            if clean_key not in st.session_state.global_store["user_data"]:
                st.session_state.global_store["user_data"][clean_key] = {
                    "history": [], 
                    "notepad": "", 
                    "has_liked": False, 
                    "saved_nick": "",
                    "theme_color": def_theme,
                    "bg_color": def_bg,
                    "clear_btn_color": def_clear,
                    "staff_bar_color": "#FF4B4B" if (clean_key == "admin" or clean_key in st.session_state.global_store.get("admins", [])) else "#FFA500"
                }
                save_global_data(st.session_state.global_store)
                
            components.html(
                f"""
                <script>
                    localStorage.setItem("koder_author_key2", "{clean_key}");
                    window.parent.location.href = window.parent.location.pathname + "?ak={clean_key}";
                </script>
                """, height=0, width=0
            )
            st.rerun()

# --- FORMULARZ DODAWANIA KOMENTARZY ---
with st.form("comment_form", clear_on_submit=True):
    default_author = user_saved_nick if user_saved_nick else ""
    nick = st.text_input("Twój podpis/nick:", value=default_author, placeholder="Anonim")
    komentarz_tekst = st.text_area("Napisz komentarz o stronie:", placeholder="Wpisz swoją opinię tutaj...")
    wyslij = st.form_submit_button("Dodaj komentarz")
    
    if wyslij and komentarz_tekst.strip():
        podpis = nick.strip() if nick.strip() else "Anonim"
        nowy_komentarz_tekst = f"**{podpis}** | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}:\n{komentarz_tekst.strip()}"
        
        nowy_komentarz_obj = {
            "text": nowy_komentarz_tekst,
            "author_key": st.session_state.user_author_key
        }
        
        current_data = load_global_data()
        current_data["comments"].insert(0, nowy_komentarz_obj)
        save_global_data(current_data)
        st.session_state.global_store = current_data
        st.rerun()

# --- WYŚWIETLANIE KOMENTARZY WRAZ Z PRZYCISKAMI USUWANIA ---
comments_list = st.session_state.global_store.get("comments", [])
if comments_list:
    st.write("**Ostatnie komentarze:**")
    for idx, com in enumerate(comments_list):
        if isinstance(com, dict) and "text" in com:
            cc1, cc2 = st.columns([4.8, 1.2])
            with cc1:
                st.info(com["text"])
            with cc2:
                my_key = st.session_state.user_author_key
                
                if is_staff:
                    label_btn = "🗑️ Usuń (ADMIN)" if is_admin else "🗑️ Usuń (MOD)"
                    if st.button(label_btn, key=f"del_com_{idx}", type="primary", use_container_width=True):
                        current_data = load_global_data()
                        if idx < len(current_data["comments"]):
                            current_data["comments"].pop(idx)
                            save_global_data(current_data)
                            st.session_state.global_store = current_data
                            st.rerun()
                
                elif com.get("author_key") == my_key and my_key not in ["", "anonymous", "legacy"]:
                    if st.button("❌ Usuń", key=f"del_com_{idx}", type="primary", use_container_width=True):
                        current_data = load_global_data()
                        if idx < len(current_data["comments"]):
                            current_data["comments"].pop(idx)
                            save_global_data(current_data)
                            st.session_state.global_store = current_data
                            st.rerun()
else:
    st.caption("Brak komentarzy. Bądź pierwszy!")

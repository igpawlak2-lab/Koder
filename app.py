import re
import datetime
import os
import json
import streamlit as st

# Czysty interfejs bez elementów chemicznych
st.set_page_config(page_title="Koder", page_icon="📟", layout="wide")

# --- TRWAŁE ZAPISYWANIE DANYCH DO PLIKU (Żeby opinie i lajki nie znikały) ---
DATA_FILE = "dane_aplikacji.json"

def load_global_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"likes": 0, "comments": []}

def save_global_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

# Ładowanie danych na starcie do pamięci podręcznej sesji
if "global_store" not in st.session_state:
    st.session_state.global_store = load_global_data()

# --- MODYFIKACJA INTERFEJSU (CSS) ---
st.markdown("""
    <style>
        /* Zamiana st.radio w duże, prostokątne przyciski */
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div {
            display: flex;
            gap: 10px;
            margin-top: 5px;
            width: 100%;
        }
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label {
            background-color: #F0F2F6;
            border: 2px solid #E0E2E6;
            padding: 12px 10px !important;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 1;
            min-width: 140px;
            font-size: 16px !important;
            font-weight: bold !important;
            white-space: nowrap !important;
        }
        /* Ukrycie domyślnych małych kółek radio */
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label div[data-testid="stMarkdownContainer"]::before {
            display: none !important;
        }
        div[data-testid="stRadio"] input[type="radio"] {
            display: none;
        }
        /* Efekt podświetlenia wybranego kafelka (akcent niebieski) */
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label:has(input:checked) {
            background-color: #1E90FF !important;
            color: white !important;
            border-color: #1E90FF !important;
            box-shadow: 0px 4px 10px rgba(30, 144, 255, 0.3);
        }
        /* Nagłówki nad kafelkami */
        div[data-testid="stRadio"] label div[data-testid="stWidgetLabel"] p {
            font-size: 16px !important;
            font-weight: bold;
            color: #31333E;
        }
        
        /* Wymuszenie koloru niebieskiego dla natywnej ramki Streamlit */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #1E90FF !important;
            border-radius: 12px;
            background-color: #F9FAFB;
        }
    </style>
""", unsafe_allow_html=True)

# Ukryta mapa danych
DATA_MAP = {
    1: (1, 1, "H"), 2: (18, 1, "He"), 3: (1, 2, "Li"), 4: (2, 2, "Be"), 5: (13, 2, "B"), 6: (14, 2, "C"), 
    7: (15, 2, "N"), 8: (16, 2, "O"), 9: (17, 2, "F"), 10: (18, 2, "Ne"), 11: (1, 3, "Na"), 12: (2, 3, "Mg"),
    13: (13, 3, "Al"), 14: (14, 3, "Si"), 15: (15, 3, "P"), 16: (16, 3, "S"), 17: (17, 3, "Cl"), 18: (18, 3, "Ar"),
    19: (1, 4, "K"), 20: (2, 4, "Ca"), 21: (3, 4, "Sc"), 22: (4, 4, "Ti"), 23: (5, 4, "V"), 24: (6, 4, "Cr"),
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

def clean_txt(t):
    z = {'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'}
    t = t.upper()
    for k, v in z.items(): t = t.replace(k, v)
    return re.sub(r'[^A-Z ]', '', t)

# --- POPRAWIONY KOD 1 ---
def enc_v1(l):
    for i, (g, o, s) in DATA_MAP.items():
        if s == l: return f"{i}"
    for i, (g, o, s) in DATA_MAP.items():
        if s[0] == l and len(s) > 1: return f"{i}.1"
        if len(s) > 1 and s[1] == l.lower(): return f"{i}.2"
    return "?"

def dec_v1(s):
    s = s.strip()
    if not s: return ""
    try:
        if "." in s:
            parts = s.split(".")
            val = int(parts[0])
            idx = parts[1]
        else:
            val = int(s)
            idx = ""
        if val in DATA_MAP:
            res = DATA_MAP[val][2]
            return res[0].upper() if idx in ["", "1"] else res[1].upper()
    except ValueError: pass
    return "?"

# --- POPRAWIONY KOD 2 ---
def enc_v2(l):
    for i, (g, o, s) in DATA_MAP.items():
        if s == l: return f"{g}.{o}"
    for i, (g, o, s) in DATA_MAP.items():
        if s[0] == l and len(s) > 1: return f"{g}.{o}1"
        if len(s) > 1 and s[1] == l.lower(): return f"{g}.{o}2"
    return "?"

def dec_v2(s):
    s = s.strip()
    if not s: return ""
    if "." not in s: return "?"
    try:
        parts = s.split(".")
        g = int(parts[0])
        rest = parts[1]
        if len(rest) > 1:
            o = int(rest[0])
            pos = rest[1]
        else:
            o = int(rest)
            pos = ""
        for i, (vg, vo, vs) in DATA_MAP.items():
            if vg == g and vo == o:
                return vs[1].upper() if pos == "2" and len(vs) > 1 else vs[0].upper()
    except ValueError: pass
    return "?"

# Lokalna historia sesji danej przeglądarki
if "history" not in st.session_state: 
    st.session_state.history = []
if "has_liked" not in st.session_state:
    st.session_state.has_liked = False
if "notepad_content" not in st.session_state:
    st.session_state.notepad_content = ""

st.title("📟 KODER")
st.write("Uniwersalny system kodowania i dekodowania tekstu.")

c1, c2 = st.columns([1.6, 1.4])
with c1:
    st.subheader("Panel Sterowania")
    proto = st.radio("Wybierz system kodu:", ["Kod 1", "Kod 2"], horizontal=True)
    mode = st.radio("Wybierz operację:", ["Koduj", "Odkoduj"], horizontal=True)
    
    st.write(" ")
    txt = st.text_input("Wprowadź dane i zatwierdź Enterem:", placeholder="Wpisz dane tutaj...")
    
    if txt:
        res = ""
        if mode == "Koduj":
            words = clean_txt(txt).split(' ')
            res = "   ".join([" ".join([enc_v1(l) if "Kod 1" in proto else enc_v2(l) for l in w]) for w in words])
        else:
            res = " ".join(["".join([dec_v1(s) if "Kod 1" in proto else dec_v2(s) for s in w.strip().split(" ") if s]) for w in txt.split("   ")])
        st.info(f"**Wynik:**\n`{res}`")
        entry = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {proto} ({mode}): {txt} -> {res}"
        if not st.session_state.history or st.session_state.history[0] != entry: st.session_state.history.insert(0, entry)

with c2:
    st.subheader("Historia operacji")
    
    with st.container(border=True):
        if st.button("Wyczyść historię", type="primary", key="btn_clear_history"): 
            st.session_state.history = []
            st.rerun()
            
        st.write(" ")
        
        if not st.session_state.history:
            st.caption("Brak zarejestrowanych operacji w tej sesji.")
        else:
            for item in st.session_state.history: 
                st.text(item)
                st.write("---")
                
    # --- BEZPIECZNY NOTATNIK ---
    st.write(" ")
    st.subheader("📝 Twój Notatnik")
    
    note_input = st.text_area(
        "Zapisz swoje uwagi (tekst zapamiętuje się podczas pracy z kodami):",
        value=st.session_state.notepad_content,
        placeholder="Tutaj możesz swobodnie pisać...",
        height=180,
        key="local_notepad"
    )
    st.session_state.notepad_content = note_input

# --- SEKCJA GLOBALNYCH POLUBIEŃ I KOMENTARZY ---
st.write("---")
st.subheader("💬 Opinie użytkowników")

col_like1, col_like2 = st.columns([1.5, 5])
with col_like1:
    if not st.session_state.has_liked:
        if st.button("👍 Polub stronę", key="btn_like_page"):
            st.session_state.global_store["likes"] += 1
            save_global_data(st.session_state.global_store)
            st.session_state.has_liked = True
            st.rerun()
    else:
        if st.button("❌ Cofnij polubienie", type="primary", key="btn_unlike_page"):
            st.session_state.global_store["likes"] = max(0, st.session_state.global_store["likes"] - 1)
            save_global_data(st.session_state.global_store)
            st.session_state.has_liked = False
            st.rerun()

with col_like2:
    st.write(f"Ta strona została polubiona już **{st.session_state.global_store['likes']}** razy!")

st.write(" ")

with st.form("comment_form", clear_on_submit=True):
    nick = st.text_input("Twój podpis/nick:", placeholder="Anonim")
    komentarz_tekst = st.text_area("Napisz komentarz o stronie:", placeholder="Wpisz swoją opinię tutaj...")
    wyslij = st.form_submit_button("Dodaj komentarz")
    
    if wyslij and komentarz_tekst.strip():
        podpis = nick.strip() if nick.strip() else "Anonim"
        nowy_komentarz = f"**{podpis}** ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}):\n{komentarz_tekst.strip()}"
        st.session_state.global_store["comments"].insert(0, nowy_komentarz)
        save_global_data(st.session_state.global_store)
        st.rerun()

if st.session_state.global_store["comments"]:
    st.write("**Ostatnie komentarze (widoczne dla wszystkich):**")
    for com in st.session_state.global_store["comments"]:
        st.info(com)
else:
    st.caption("Brak komentarzy. Bądź pierwszy!")

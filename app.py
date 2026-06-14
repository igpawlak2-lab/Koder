import re
import datetime
import streamlit as st

# Całkowita anonimizacja interfejsu
st.set_page_config(page_title="Koder", page_icon="📟", layout="wide")

# Ukryta baza danych (mapowanie techniczne)
DATA_MAP = {
    1: (1, 1, "H"), 2: (18, 1, "He"), 3: (1, 2, "Li"), 4: (2, 2, "Be"), 5: (13, 2, "B"), 6: (14, 2, "C"), 
    7: (15, 2, "N"), 8: (16, 2, "O"), 9: (17, 2, "F"), 10: (18, 2, "Ne"), 11: (1, 3, "Na"), 12: (2, 3, "Mg"),
    13: (13, 3, "Al"), 14: (14, 3, "Si"), 15: (15, 3, "P"), 16: (16, 3, "S"), 17: (17, 3, "Cl"), 18: (18, 3, "Ar"),
    19: (1, 4, "K"), 20: (2, 4, "Ca"), 21: (3, 4, "Sc"), 22: (4, 4, "Ti"), 23: (5, 4, "V"), 24: (6, 4, "Cr"),
    25: (7, 4, "Mn"), 26: (8, 4, "Fe"), 27: (9, 4, "Co"), 28: (10, 4, "Ni"), 29: (11, 4, "Cu"), 30: (12, 4, "Zn")
    # ... baza może być kontynuowana w ten sam sposób
}

SUB = {"0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉"}
SUP = {"1": "⁽¹⁾", "2": "⁽²⁾"}

def clean_txt(t):
    z = {'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'}
    t = t.upper()
    for k, v in z.items(): t = t.replace(k, v)
    return re.sub(r'[^A-Z ]', '', t)

def enc_v1(l):
    for i, (g, o, s) in DATA_MAP.items():
        if s == l: return f"{i}"
        if s[0] == l and len(s) > 1: return f"{i}₁"
        if len(s) > 1 and s[1] == l.lower(): return f"{i}₂"
    return "?"

def dec_v1(s):
    s = s.strip().replace("₁", "1").replace("₂", "2")
    idx = s[-1] if len(s) > 1 and s[-1] in ["1", "2"] else ""
    val = int(s[:-1]) if idx else int(s)
    if val in DATA_MAP:
        res = DATA_MAP[val][2]
        return res[0].upper() if idx in ["", "1"] else res[1].upper()
    return "?"

def enc_v2(l):
    for i, (g, o, s) in DATA_MAP.items():
        sub_o = "".join(SUB[c] for c in str(o))
        if s == l: return f"{g}{sub_o}"
        if s[0] == l and len(s) > 1: return f"{g}{sub_o}{SUP['1']}"
        if len(s) > 1 and s[1] == l.lower(): return f"{g}{sub_o}{SUP['2']}"
    return "?"

def dec_v2(s):
    s = s.strip()
    for k, v in SUB.items(): s = s.replace(v, k)
    s = s.replace("⁽¹⁾", "¹").replace("⁽²⁾", "²")
    pos = "1" if s.endswith("¹") else ("2" if s.endswith("²") else "")
    if pos: s = s[:-1]
    if len(s) < 2: return "?"
    o, g = int(s[-1]), int(s[:-1])
    for i, (vg, vo, vs) in DATA_MAP.items():
        if vg == g and vo == o:
            return vs[1].upper() if pos == "2" and len(vs) > 1 else vs[0].upper()
    return "?"

if "history" not in st.session_state: st.session_state.history = []

st.title("📟 KODER: SYSTEM OBFUSKACJI")
st.write("Bezpieczny protokół mapowania danych Alpha/Beta.")

c1, c2 = st.columns([2, 1])
with c1:
    proto = st.radio("Protokół:", ["Alpha (Numerical)", "Beta (Grid)"], horizontal=True)
    mode = st.radio("Operacja:", ["Koduj", "Odkoduj"], horizontal=True)
    txt = st.text_input("Wprowadź sekwencję:")
    
    if txt:
        res = ""
        if mode == "Koduj":
            words = clean_txt(txt).split(' ')
            res = "   ".join([" ".join([enc_v1(l) if "Alpha" in proto else enc_v2(l) for l in w]) for w in words])
        else:
            res = " ".join(["".join([dec_v1(s) if "Alpha" in proto else dec_v2(s) for s in w.strip().split(" ") if s]) for w in txt.split("   ")])
        st.code(res, language=None)
        entry = f"[{datetime.datetime.now().strftime('%H:%M')}] {proto}: {txt} -> {res}"
        if not st.session_state.history or st.session_state.history[0] != entry: st.session_state.history.insert(0, entry)

with c2:
    st.subheader("Logi systemowe")
    if st.button("Wyczyść logi"): st.session_state.history = []; st.rerun()
    for item in st.session_state.history: st.caption(item)
        

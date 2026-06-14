import re
import datetime
import streamlit as st

# Konfiguracja strony internetowej
st.set_page_config(page_title="Super Koder Chemii", page_icon="🧪", layout="wide")

# Pełna baza pierwiastków
ELEMENTS_DATA = {
    1: (1, 1, "H"), 2: (18, 1, "He"),
    3: (1, 2, "Li"), 4: (2, 2, "Be"), 5: (13, 2, "B"), 6: (14, 2, "C"), 7: (15, 2, "N"), 8: (16, 2, "O"), 9: (17, 2, "F"), 10: (18, 2, "Ne"),
    11: (1, 3, "Na"), 12: (2, 3, "Mg"), 13: (13, 3, "Al"), 14: (14, 3, "Si"), 15: (15, 3, "P"), 16: (16, 3, "S"), 17: (17, 3, "Cl"), 18: (18, 3, "Ar"),
    19: (1, 4, "K"), 20: (2, 4, "Ca"), 21: (3, 4, "Sc"), 22: (4, 4, "Ti"), 23: (5, 4, "V"), 24: (6, 4, "Cr"), 25: (7, 4, "Mn"), 26: (8, 4, "Fe"),
    27: (9, 4, "Co"), 28: (10, 4, "Ni"), 29: (11, 4, "Cu"), 30: (12, 4, "Zn"), 31: (13, 4, "Ga"), 32: (14, 4, "Ge"), 33: (15, 4, "As"), 34: (16, 4, "Se"),
    35: (17, 4, "Br"), 36: (18, 4, "Kr"),
    37: (1, 5, "Rb"), 38: (2, 5, "Sr"), 39: (3, 5, "Y"), 40: (4, 5, "Zr"), 41: (5, 5, "Nb"), 42: (6, 5, "Mo"), 43: (7, 5, "Tc"), 44: (8, 5, "Ru"),
    45: (9, 5, "Rh"), 46: (10, 5, "Pd"), 47: (11, 5, "Ag"), 48: (12, 5, "Cd"), 49: (13, 5, "In"), 50: (14, 5, "Sn"), 51: (15, 5, "Sb"), 52: (16, 5, "Te"),
    53: (17, 5, "I"), 54: (18, 5, "Xe"),
    55: (1, 6, "Cs"), 56: (2, 6, "Ba"), 57: (3, 6, "La"), 58: (3, 6, "Ce"), 59: (3, 6, "Pr"), 60: (3, 6, "Nd"), 61: (3, 6, "Pm"), 62: (3, 6, "Sm"),
    63: (3, 6, "Eu"), 64: (3, 6, "Gd"), 65: (3, 6, "Tb"), 66: (3, 6, "Dy"), 67: (3, 6, "Ho"), 68: (3, 6, "Er"), 69: (3, 6, "Tm"), 70: (3, 6, "Yb"),
    71: (3, 6, "Lu"), 72: (4, 6, "Hf"), 73: (5, 6, "Ta"), 74: (6, 6, "W"), 75: (7, 6, "Re"), 76: (8, 6, "Os"), 77: (9, 6, "Ir"), 78: (10, 6, "Pt"),
    79: (11, 6, "Au"), 80: (12, 6, "Hg"), 81: (13, 6, "Tl"), 82: (14, 6, "Pb"), 83: (15, 6, "Bi"), 84: (16, 6, "Po"), 85: (17, 6, "At"), 86: (18, 6, "Rn"),
    87: (1, 7, "Fr"), 88: (2, 7, "Ra"), 89: (3, 7, "Ac"), 90: (3, 7, "Th"), 91: (3, 7, "Pa"), 92: (3, 7, "U"), 93: (3, 7, "Np"), 94: (3, 7, "Pu"),
    95: (3, 7, "Am"), 96: (3, 7, "Cm"), 97: (3, 7, "Bk"), 98: (3, 7, "Cf"), 99: (3, 7, "Es"), 100: (3, 7, "Fm"), 101: (3, 7, "Md"), 102: (3, 7, "No"),
    103: (3, 7, "Lr"), 104: (4, 7, "Rf"), 105: (5, 7, "Db"), 106: (6, 7, "Sg"), 107: (7, 7, "Bh"), 108: (8, 7, "Hs"), 109: (9, 7, "Mt"), 110: (10, 7, "Ds"),
    111: (11, 7, "Rg"), 112: (12, 7, "Cn"), 113: (13, 7, "Nh"), 114: (14, 7, "Fl"), 115: (15, 7, "Mc"), 116: (16, 7, "Lv"), 117: (17, 7, "Ts"), 118: (18, 7, "Og")
}

SUB_DIGITS = {"0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉"}
SUP_DIGITS = {"1": "⁽¹⁾", "2": "⁽²⁾"}

def do_subscript(number_str):
    return "".join(SUB_DIGITS.get(char, char) for char in str(number_str))

def przygotuj_tekst(tekst):
    zamiany = {'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'}
    tekst = tekst.upper()
    for polski, zwykly in zamiany.items():
        tekst = tekst.replace(polski, zwykly)
    return re.sub(r'[^A-Z ]', '', tekst)

# --- LOGIKA DEKODOWANIA/KODOWANIA ---
def koduj_litere_v1(litera):
    for atom, (g, o, symbol) in ELEMENTS_DATA.items():
        if symbol == litera: return f"{atom}"
    for atom, (g, o, symbol) in ELEMENTS_DATA.items():
        if symbol[0] == litera and len(symbol) > 1: return f"{atom}₁"
    for atom, (g, o, symbol) in ELEMENTS_DATA.items():
        if len(symbol) > 1 and symbol[1] == litera.lower(): return f"{atom}₂"
    return None

def odkoduj_symbol_v1(symbol):
    symbol = symbol.strip().replace("₁", "1").replace("₂", "2")
    if not symbol: return ""
    indeks = symbol[-1] if len(symbol) > 1 and symbol[-1] in ["1", "2"] else ""
    atom_str = symbol[:-1] if indeks else symbol
    try:
        atom = int(atom_str)
        if atom in ELEMENTS_DATA:
            sym = ELEMENTS_DATA[atom][2]
            return sym[0].upper() if indeks in ["", "1"] else sym[1].upper()
    except ValueError: pass
    return "?"

def koduj_litere_v2(litera):
    for atom, (grupa, okres, symbol) in ELEMENTS_DATA.items():
        if symbol == litera: return f"{grupa}.{do_subscript(okres)}"
    for atom, (grupa, okres, symbol) in ELEMENTS_DATA.items():
        if symbol[0] == litera and len(symbol) > 1: return f"{grupa}.{do_subscript(okres)}{SUP_DIGITS['1']}"
    for atom, (grupa, okres, symbol) in ELEMENTS_DATA.items():
        if len(symbol) > 1 and symbol[1] == litera.lower(): return f"{grupa}.{do_subscript(okres)}{SUP_DIGITS['2']}"
    return None

def odkoduj_symbol_v2(symbol):
    symbol = symbol.strip()
    if not symbol: return ""
    for sub, reg in SUB_DIGITS.items(): symbol = symbol.replace(reg, sub)
    symbol = symbol.replace("⁽¹⁾", "1").replace("⁽²⁾", "2")
    
    if "." in symbol:
        czesci = symbol.split(".")
        try:
            grupa = int(czesci[0])
            reszta = czesci[1]
            if len(reszta) == 2 and reszta[1] in ["1", "2"]:
                okres = int(reszta[0])
                pozycja = reszta[1]
            else:
                okres = int(reszta)
                pozycja = ""
        except (ValueError, IndexError): return "?"
    else: return "?"

    for atom, (g, o, sym) in ELEMENTS_DATA.items():
        if g == grupa and o == okres:
            if pozycja == "2" and len(sym) > 1: return sym[1].upper()
            return sym[0].upper()
    return "?"

# --- OBSŁUGA HISTORII W PAMIĘCI SESJI ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- BUDOWANIE STRONY WWW ---
st.title("🧪 CHRONO-KODER CHEMICZNY")
st.write("Zamieniaj tekst na kody pierwiastków chemicznych i odwrotnie bezpośrednio w przeglądarce!")

# Układ dwóch kolumn na stronie internetowej
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Panel Sterowania")
    
    # Opcje wyboru (ładne kafelki)
    system = st.radio("Wybierz system kodu:", ["Kod 1 (Liczby atomowe)", "Kod 2a (Grupa.Okres)"], horizontal=True)
    tryb = st.radio("Wybierz operację:", ["Koduj", "Odkoduj"], horizontal=True)
    
    # Podpowiedź formatu
    placeholder = "Wpisz tekst do zakodowania..." if tryb == "Koduj" else ("Wpisz kody (np. 211 401)" if "Kod 1" in system else "Wpisz kody (np. 1.32 16.2)")
    
    # Pole wpisywania tekstu
    wejscie_tekst = st.text_input("Wpisz dane i zatwierdź Enterem:", placeholder=placeholder)
    
    if wejscie_tekst:
        wersja = "1" if "Kod 1" in system else "2"
        system_etykieta = "Kod 1" if wersja == "1" else "Kod 2a"
        
        # Przetwarzanie
        if tryb == "Koduj":
            czysty = przygotuj_tekst(wejscie_tekst)
            wynik = []
            for slowo in czysty.split(' '):
                if not slowo: continue
                kody = [koduj_litere_v1(l) if wersja == "1" else koduj_litere_v2(l) for l in slowo]
                wynik.append(" ".join([k if k else "?" for k in kody]))
            odpowiedz = "   ".join(wynik)
        else:
            wyrazy = wejscie_tekst.split("   ")
            wynik = []
            for w in wyrazy:
                odkodowane = [odkoduj_symbol_v1(s) if wersja == "1" else odkoduj_symbol_v2(s) for s in w.strip().split(" ") if s]
                wynik.append("".join(odkodowane))
            odpowiedz = " ".join(wynik)
            
        # Wyświetlenie wyniku w ramce
        st.info(f"**Wynik:**\n`{odpowiedz}`")
        
        # Zapis do historii (tylko jeśli nie jest to duplikat ostatniego wpisu)
        czas = datetime.datetime.now().strftime("%H:%M:%S")
        nowy_wpis = f"[{czas}] {system_etykieta} ({tryb}):\nIN: {wejscie_tekst} -> OUT: {odpowiedz}"
        if not st.session_state.history or st.session_state.history[0] != nowy_wpis:
            st.session_state.history.insert(0, nowy_wpis)

with col2:
    st.subheader("Historia operacji")
    if st.button("Wyczyść historię", type="primary"):
        st.session_state.history = []
        st.rerun()
        
    if st.session_state.history:
        for item in st.session_state.history:
            st.text(item)
            st.write("---")
    else:
        st.caption("Brak operacji w tej sesji.")
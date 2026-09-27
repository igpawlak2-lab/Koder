import datetime
import hashlib
import json
import os
import re
import time
import uuid

import streamlit as st
import streamlit.components.v1 as components

# Czysty interfejs aplikacji
st.set_page_config(page_title="Koder", page_icon="📟", layout="wide")

# --- STAŁE CZASOWE (W SEKUNDACH) ---
CZAS_KONTA_TESTOWEGO = 20 * 60  # 20 minut = 1200 sekund
BEZPIECZNY_CZAS_ZWYKLEGO = 2_000_000_000  # 2 miliardy sekund (~63,4 roku)

# --- GLOBALNY PLIK JSON (STRUKTURA DANYCH DLA WSZYSTKICH KONT) ---
DATA_FILE = "dane_aplikacji.json"


def normalize_user_profile(account_key, user_profile):
    """Ujednolica profil konta: zwykłe konto ma być trwałe, testowe tylko tymczasowe."""
    if not isinstance(user_profile, dict):
        return {}

    if "is_temporary" not in user_profile or user_profile["is_temporary"] is None:
        user_profile["is_temporary"] = False
    else:
        user_profile["is_temporary"] = bool(user_profile["is_temporary"])

    if "expire_at" not in user_profile or user_profile["expire_at"] is None:
        user_profile["expire_at"] = None

    if "created_at" not in user_profile:
        user_profile["created_at"] = time.time()

    if "sec_code" not in user_profile:
        user_profile["sec_code"] = generate_account_secure_code(account_key)

    return user_profile


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
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return default_data
                if "likes" not in data:
                    data["likes"] = 0
                if "comments" not in data:
                    data["comments"] = []
                if "user_data" not in data:
                    data["user_data"] = {}
                if "moderators" not in data:
                    data["moderators"] = []
                if "admins" not in data:
                    data["admins"] = []
                if "vips" not in data:
                    data["vips"] = []
                if "staff_chat" not in data:
                    data["staff_chat"] = []
                if "staff_dms" not in data:
                    data["staff_dms"] = []
                if "support_chat" not in data:
                    data["support_chat"] = []
                if "password_resets" not in data:
                    data["password_resets"] = []
                if "announcement" not in data:
                    data["announcement"] = "Brak aktualnych ogłoszeń."
                if "announcement_font" not in data:
                    data["announcement_font"] = "sans-serif"
                if "announcement_size" not in data:
                    data["announcement_size"] = 16
                if "announcement_bg_color" not in data:
                    data["announcement_bg_color"] = "#e7f3fe"
                if "default_theme_color" not in data:
                    data["default_theme_color"] = "#1E90FF"
                if "default_bg_color" not in data:
                    data["default_bg_color"] = "#FFFFFF"
                if "default_clear_btn_color" not in data:
                    data["default_clear_btn_color"] = "#5cb85c"

                # Normalizacja kont: zwykłe konta są trwałe, tylko testowe mają limit czasu.
                for user_key, user_profile in list(data.get("user_data", {}).items()):
                    if not isinstance(user_profile, dict):
                        continue
                    data["user_data"][user_key] = normalize_user_profile(user_key, user_profile)

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


# Funkcja generująca bezpieczny kod weryfikacyjny konta
def generate_account_secure_code(account_key):
    salt = "KoderSecureSystemSalt2026"
    hashed = hashlib.sha256((account_key + salt).encode("utf-8")).hexdigest()
    return str(int(hashed[:8], 16))[-6:].zfill(6)


# --- FUNKCJA POMOCNICZA: TWORZENIE NOWEGO KONTA ---
def create_user_account(account_key, password=None, is_temporary=False):
    """Tworzy lub aktualizuje konto użytkownika z zachowaniem hasła i licznika wygaśnięcia."""
    teraz_ts = time.time()
    current_data = st.session_state.global_store

    if "user_data" not in current_data:
        current_data["user_data"] = {}

    existing_user = current_data["user_data"].get(account_key, {})

    if is_temporary:
        expire_at = teraz_ts + CZAS_KONTA_TESTOWEGO
    else:
        expire_at = None

    user_info = {
        "created_at": existing_user.get("created_at", teraz_ts),
        "is_temporary": bool(is_temporary),
        "expire_at": expire_at,
        "sec_code": existing_user.get("sec_code") or generate_account_secure_code(account_key),
    }

    if password is not None:
        user_info["password"] = password
    elif "password" in existing_user:
        user_info["password"] = existing_user["password"]

    current_data["user_data"][account_key] = normalize_user_profile(account_key, user_info)

    save_global_data(current_data)
    st.session_state.global_store = current_data


# --- 1. INICJALIZACJA STANOWISKA SESJI (NAJPIERW) ---
if "global_store" not in st.session_state:
    st.session_state.global_store = load_global_data()

# --- 2. AUTOMATYCZNE CZYSZCZENIE KONT (TYLKO KONTY TYMCZASOWE) ---
teraz = time.time()
db_changed = False
current_data = st.session_state.global_store

if "user_data" in current_data:
    expired_keys = []

    for k, v in list(current_data["user_data"].items()):
        if not isinstance(v, dict):
            continue
        if v.get("is_temporary") is True:
            expire_time = v.get("expire_at")
            if expire_time is not None and teraz > expire_time:
                expired_keys.append(k)

    if expired_keys:
        for k in expired_keys:
            if k in current_data["user_data"]:
                del current_data["user_data"][k]
                db_changed = True

            if "admins" in current_data and k in current_data["admins"]:
                current_data["admins"].remove(k)
                db_changed = True

            if "moderators" in current_data and k in current_data["moderators"]:
                current_data["moderators"].remove(k)
                db_changed = True

            if "vips" in current_data and k in current_data["vips"]:
                current_data["vips"].remove(k)
                db_changed = True

    if db_changed:
        save_global_data(current_data)
        st.session_state.global_store = current_data


# --- 3. PRZYPISANIE ZMIENNYCH Z AKTUALNEGO STANU ---
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

# ... reszta pliku bez zmian ...

# Dodatkowa korekta rejestracji standardowych kont: ustawienie trwałego statusu
# (umieszczona w sekcji rejestracji, gdy użytkownik zakłada konto)
# Warto dodać do obiektu nowo tworzonego profilu:
# "is_temporary": False,
# "expire_at": None,
# w miejscach tworzenia user_data.

# Normalizacja wszystkich istniejących profili podczas ładowania jest już w `load_global_data()`.

# Sekcja rejestracji zwykłych kont: upewniamy się, że nowy profil jest trwały.
# --- NOWY EKRAN LOGOWANIA I REJESTRACJI ---
if not current_user:
    st.title("📟 Witamy w aplikacji Koder")
    st.write("Aby korzystać z systemu kodowania oraz paneli społecznościowych, musisz posiadać konto.")

    components.html("""
        <script>
            var savedKey = localStorage.getItem("koder_author_key2");
            if (savedKey) {
                var currentUrl = new URL(window.parent.location.href);
                currentUrl.searchParams.set("ak", savedKey);
                window.parent.location.href = currentUrl.href;
            }
        </script>
    """, height=0, width=0)

    tab_login, tab_register = st.tabs(["🔑 Zaloguj się", "📝 Załóż nowe konto"])

    with tab_register:
        st.subheader("Utwórz unikalny profil")
        with st.form("register_form_global_fixed"):
            reg_key = st.text_input("Wybierz swój Klucz Konta (Login):", placeholder="np. mojekonto123").strip()
            reg_nick = st.text_input("Twój podpis/nick (opcjonalnie):", placeholder="np. Janek")
            reg_pass = st.text_input("Ustaw hasło (zostaw puste, jeśli nie chcesz hasła):", type="password", placeholder="Opcjonalne...")
            submit_reg = st.form_submit_button("🚀 Zarejestruj konto")

            if submit_reg:
                if not reg_key:
                    st.error("❌ Klucz konta nie może być pusty!")
                elif reg_key == "admin2":
                    st.error("❌ Klucz 'admin2' jest rezerwowany przez system ratunkowy.")
                elif reg_key in st.session_state.global_store["user_data"]:
                    st.error("❌ Podany klucz konta jest już zajęty! Wybierz inny.")
                else:
                    st.session_state.global_store["user_data"][reg_key] = normalize_user_profile(reg_key, {
                        "history": [], "notepad": "", "has_liked": False,
                        "saved_nick": reg_nick.strip() if reg_nick.strip() else reg_key,
                        "password": reg_pass.strip(),
                        "theme_color": def_theme, "bg_color": def_bg, "clear_btn_color": def_clear,
                        "staff_bar_color": "#FF4B4B",
                        "can_reset_passwords": False,
                        "is_temporary": False,
                        "expire_at": None,
                    })
                    save_global_data(st.session_state.global_store)

                    st.session_state.user_author_key = reg_key
                    st.query_params["ak"] = reg_key
                    if reg_pass.strip():
                        st.session_state.account_authenticated = True
                        st.query_params["auth"] = "true"
                        components.html(f'<script>localStorage.setItem("auth_{reg_key}", "true"); window.parent.parent.location.href = window.parent.parent.location.pathname + "?ak={reg_key}&auth=true";</script>', height=0, width=0)
                    else:
                        st.session_state.account_authenticated = False
                        components.html(f"<script>localStorage.setItem('koder_author_key2', '{reg_key}'); window.parent.parent.location.href = window.parent.parent.location.pathname + '?ak={reg_key}';</script>", height=0, width=0)

                    st.success("🎉 Konto zostało pomyślnie utworzone!")
                    st.rerun()

# Poniżej istnieje reszta pliku; nie zmieniamy jej logicznie, tylko upewniamy się, że
# każda nowo tworzona ścieżka profilu ma poprawne pola stałe i trwałe.

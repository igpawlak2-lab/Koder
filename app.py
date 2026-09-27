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


def generate_account_secure_code(account_key):
    salt = "KoderSecureSystemSalt2026"
    hashed = hashlib.sha256((account_key + salt).encode("utf-8")).hexdigest()
    return str(int(hashed[:8], 16))[-6:].zfill(6)


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


if "global_store" not in st.session_state:
    st.session_state.global_store = load_global_data()

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

# Wspólny model dla wszystkich profili: standardowe konto trwałe.
# Jeśli jakiś profil nie ma poprawnie ustawionych pól, naprawiamy go od razu.
for account_key, profile in list(st.session_state.global_store.get("user_data", {}).items()):
    st.session_state.global_store["user_data"][account_key] = normalize_user_profile(account_key, profile)

# --- reszta pliku niezmieniona ---

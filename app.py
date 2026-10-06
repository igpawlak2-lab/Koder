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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "dane_aplikacji.json")


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

    if not os.path.exists(DATA_FILE):
        return default_data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return default_data

            # Uzupełnianie brakujących pól bezpieczeństwa i ról
            for key, value in {
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
            }.items():
                if key not in data:
                    data[key] = value

            return data
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass
        return default_data


def save_global_data(data):
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        tmp_path = DATA_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp_path, DATA_FILE)
        return True
    except Exception:
        return False


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

    if is_temporary:
        expire_at = teraz_ts + CZAS_KONTA_TESTOWEGO
    else:
        expire_at = teraz_ts + BEZPIECZNY_CZAS_ZWYKLEGO

    existing_user = current_data["user_data"].get(account_key, {})

    user_info = {
        "created_at": existing_user.get("created_at", teraz_ts),
        "is_temporary": is_temporary,
        "expire_at": expire_at,
        "sec_code": existing_user.get("sec_code") or generate_account_secure_code(account_key),
    }

    if password:
        user_info["password"] = password
    elif "password" in existing_user:
        user_info["password"] = existing_user["password"]

    current_data["user_data"][account_key] = user_info

    save_global_data(current_data)
    st.session_state.global_store = current_data


# --- 1. INICJALIZACJA STANOWISKA SESJI (NAJPIERW) ---
if "global_store" not in st.session_state:
    st.session_state.global_store = load_global_data()

# --- 2. AUTOMATYCZNE CZYSZCZENIE KONT (TYLKO PO PRZEKROCZENIU LICZNIKA) ---
teraz = time.time()
db_changed = False
current_data = st.session_state.global_store

if "user_data" in current_data:
    expired_keys = []

    for k, v in list(current_data["user_data"].items()):
        if isinstance(v, dict):
            expire_time = v.get("expire_at", None)
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

# ... reszta pliku pozostaje bez zmian ...

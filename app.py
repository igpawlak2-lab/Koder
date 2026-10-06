import json
import os
import time
import hashlib

import streamlit as st

st.set_page_config(page_title="Koder", page_icon="📟", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = os.path.join(BASE_DIR, "styles.css")
if os.path.exists(CSS_PATH):
    try:
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

CZA_S_KONTA_TESTOWEGO = 20 * 60
DATA_FILE = os.path.join(BASE_DIR, "dane_aplikacji.json")


def default_store():
    return {
        "likes": 0,
        "comments": [],
        "user_data": {},
        "moderators": [],
        "admins": [],
        "vips": [],
        "announcement": "Brak aktualnych ogłoszeń.",
        "default_theme_color": "#1E90FF",
        "default_bg_color": "#FFFFFF",
        "default_clear_btn_color": "#5cb85c",
    }


def generate_account_secure_code(account_key):
    salt = "KoderSecureSystemSalt2026"
    digest = hashlib.sha256((account_key + salt).encode("utf-8")).hexdigest()
    return str(int(digest[:8], 16))[-6:].zfill(6)


def normalize_user_profile(account_key, profile):
    if not isinstance(profile, dict):
        return {}

    profile.setdefault("saved_nick", account_key)
    profile.setdefault("password", "")
    profile.setdefault("history", [])
    profile.setdefault("notepad", "")
    profile.setdefault("has_liked", False)
    profile.setdefault("theme_color", "#1E90FF")
    profile.setdefault("bg_color", "#FFFFFF")
    profile.setdefault("clear_btn_color", "#5cb85c")
    profile.setdefault("staff_bar_color", "#FF4B4B")
    profile.setdefault("can_reset_passwords", False)
    profile.setdefault("created_at", time.time())
    profile.setdefault("is_temporary", False)
    profile["is_temporary"] = bool(profile.get("is_temporary", False))
    profile.setdefault("expire_at", None)
    if profile["is_temporary"] and profile["expire_at"] is None:
        profile["expire_at"] = time.time() + CZA_S_KONTA_TESTOWEGO
    if not profile["is_temporary"]:
        profile["expire_at"] = None
    profile.setdefault("sec_code", generate_account_secure_code(account_key))
    return profile


def ensure_user_profile(storage, account_key):
    if not isinstance(storage, dict):
        storage = {}
    storage.setdefault("user_data", {})
    if account_key not in storage["user_data"] or not isinstance(storage["user_data"][account_key], dict):
        storage["user_data"][account_key] = {}
    storage["user_data"][account_key] = normalize_user_profile(account_key, storage["user_data"][account_key])
    return storage


def load_global_data():
    defaults = default_store()
    if not os.path.exists(DATA_FILE):
        return defaults

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return defaults

    if not isinstance(data, dict):
        return defaults

    for key, value in defaults.items():
        if key not in data:
            data[key] = value

    if not isinstance(data.get("user_data"), dict):
        data["user_data"] = {}
    if not isinstance(data.get("moderators"), list):
        data["moderators"] = []
    if not isinstance(data.get("admins"), list):
        data["admins"] = []
    if not isinstance(data.get("vips"), list):
        data["vips"] = []

    for user_key, profile in list(data["user_data"].items()):
        if isinstance(profile, dict):
            data["user_data"][user_key] = normalize_user_profile(user_key, profile)

    return data


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


def persist_store(data=None):
    if data is None:
        data = st.session_state.global_store
    if not isinstance(data, dict):
        data = {}
    data.setdefault("user_data", {})
    for key, profile in list(data["user_data"].items()):
        if isinstance(profile, dict):
            data["user_data"][key] = normalize_user_profile(key, profile)
    save_global_data(data)
    st.session_state.global_store = data
    return data


def purge_expired_accounts(data):
    if not isinstance(data, dict):
        return default_store()
    now = time.time()
    expired = []
    user_data = data.get("user_data", {})
    for key, profile in list(user_data.items()):
        if isinstance(profile, dict) and profile.get("is_temporary"):
            expire_at = profile.get("expire_at")
            if expire_at is not None and now > float(expire_at):
                expired.append(key)

    for key in expired:
        user_data.pop(key, None)
        for role in ("admins", "moderators", "vips"):
            if role in data and key in data[role]:
                data[role] = [x for x in data[role] if x != key]

    if expired:
        save_global_data(data)
    return data


if "global_store" not in st.session_state:
    st.session_state.global_store = load_global_data()

st.session_state.global_store = purge_expired_accounts(st.session_state.global_store)


def set_role(target_key, new_role):
    data = load_global_data()
    data = ensure_user_profile(data, target_key)
    for role in ("admins", "moderators", "vips"):
        data.setdefault(role, [])
        if target_key in data[role]:
            data[role] = [x for x in data[role] if x != target_key]

    if new_role == "admin":
        data["admins"].append(target_key)
    elif new_role == "moderator":
        data["moderators"].append(target_key)
    elif new_role == "vip":
        data["vips"].append(target_key)

    persist_store(data)
    return data


def get_current_user():
    return st.session_state.get("user_author_key", "")


# --- login/register ---
if "user_author_key" not in st.session_state:
    st.session_state.user_author_key = ""

if not st.session_state.user_author_key:
    st.title("Koder")
    st.write("Zaloguj się lub utwórz konto.")

    login_tab, register_tab = st.tabs(["Zaloguj", "Rejestracja"])

    with login_tab:
        with st.form("login_form"):
            key = st.text_input("Klucz konta")
            password = st.text_input("Hasło", type="password")
            submitted = st.form_submit_button("Zaloguj")
            if submitted:
                data = load_global_data()
                if key not in data.get("user_data", {}):
                    st.error("Konto nie istnieje.")
                else:
                    profile = data["user_data"][key]
                    profile = normalize_user_profile(key, profile)
                    if profile.get("password", "") != password:
                        st.error("Błędne hasło.")
                    else:
                        st.session_state.user_author_key = key
                        st.success("Zalogowano.")
                        st.rerun()

    with register_tab:
        with st.form("register_form"):
            key = st.text_input("Nowy klucz konta")
            nick = st.text_input("Nick")
            password = st.text_input("Hasło", type="password")
            temporary = st.checkbox("Konto testowe (20 min)")
            submitted = st.form_submit_button("Utwórz konto")
            if submitted:
                if not key:
                    st.error("Klucz nie może być pusty.")
                else:
                    data = load_global_data()
                    data = ensure_user_profile(data, key)
                    data["user_data"][key].update({
                        "saved_nick": nick or key,
                        "password": password,
                        "is_temporary": temporary,
                        "expire_at": time.time() + CZA_S_KONTA_TESTOWEGO if temporary else None,
                    })
                    persist_store(data)
                    st.session_state.user_author_key = key
                    st.success("Konto utworzone.")
                    st.rerun()

    st.stop()

current_user = get_current_user()
store = load_global_data()
store = ensure_user_profile(store, current_user)
profile = store["user_data"][current_user]

if profile.get("is_temporary") and profile.get("expire_at") is not None:
    left = int(float(profile["expire_at"]) - time.time())
    if left <= 0:
        store["user_data"].pop(current_user, None)
        for role in ("admins", "moderators", "vips"):
            if role in store and current_user in store[role]:
                store[role] = [x for x in store[role] if x != current_user]
        persist_store(store)
        st.session_state.user_author_key = ""
        st.rerun()

st.title(f"Witaj, {profile.get('saved_nick', current_user)}")

roles = []
if current_user in store.get("admins", []):
    roles.append("admin")
if current_user in store.get("moderators", []):
    roles.append("moderator")
if current_user in store.get("vips", []):
    roles.append("vip")
if not roles:
    roles.append("user")

st.write("Rangi:", ", ".join(roles))

if profile.get("is_temporary"):
    st.caption("To konto testowe. Wygasa automatycznie po 20 minutach.")
else:
    st.caption("To konto jest trwałe.")

# --- admin panel ---
if current_user in store.get("admins", []) or current_user == "admin":
    st.subheader("Panel administracyjny")
    with st.form("admin_role_form"):
        target_key = st.selectbox("Użytkownik", options=sorted(store.get("user_data", {}).keys()))
        role = st.selectbox("Ranga", ["user", "vip", "moderator", "admin"])
        submitted = st.form_submit_button("Zapisz rangę")
        if submitted:
            if target_key == "admin":
                st.warning("Nie można zmienić rangi głównego administratora.")
            else:
                set_role(target_key, role)
                st.success("Ranga zapisana.")
                st.rerun()

# --- profile settings ---
with st.expander("Ustawienia profilu"):
    user_saved_nick = st.text_input("Nick", value=profile.get("saved_nick", current_user))
    if user_saved_nick != profile.get("saved_nick", current_user):
        store["user_data"][current_user]["saved_nick"] = user_saved_nick.strip() or current_user
        persist_store(store)
        st.rerun()

    new_password = st.text_input("Nowe hasło", type="password")
    if new_password:
        if st.button("Zapisz hasło"):
            store["user_data"][current_user]["password"] = new_password
            persist_store(store)
            st.success("Hasło zapisane.")
            st.rerun()

    if st.button("Usuń hasło"):
        store["user_data"][current_user]["password"] = ""
        persist_store(store)
        st.success("Hasło usunięte.")
        st.rerun()

    st.write("Kod bezpieczeństwa:", generate_account_secure_code(current_user))

# --- Koder tool ---
st.subheader("Narzędzie Koder")
text = st.text_input("Wpisz tekst")
if text:
    mode = st.radio("Tryb", ["Koduj", "Dekoduj"], horizontal=True)
    if mode == "Koduj":
        result = " ".join([f"{ch}:{ord(ch)}" for ch in text])
    else:
        try:
            parts = text.split()
            result = "".join(chr(int(p.split(":")[-1])) for p in parts if ":" in p)
        except Exception:
            result = "Błąd dekodowania"
    st.code(result)

st.write("---")
if st.button("Wyloguj"):
    st.session_state.user_author_key = ""
    st.rerun()

# --- user list for admins ---
with st.expander("Lista użytkowników"):
    for key, profile_data in sorted(store.get("user_data", {}).items()):
        status = "testowe" if profile_data.get("is_temporary") else "trwałe"
        st.write(f"- {key} | {profile_data.get('saved_nick')} | {status} | hasło={'tak' if profile_data.get('password') else 'nie'}")

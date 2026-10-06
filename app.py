import hashlib
import json
import os
import time

import streamlit as st

# --- Stałe aplikacji ---
TEMP_ACCOUNT_LIFETIME = 20 * 60
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "dane_aplikacji.json")


def default_store():
    return {
        "likes": 0,
        "comments": [],
        "user_data": {},
        "moderators": [],
        "admins": [],
        "vips": [],
        "announcement": "Brak ogłoszeń.",
        "default_theme_color": "#1E90FF",
        "default_bg_color": "#FFFFFF",
        "default_clear_btn_color": "#5cb85c",
    }


def generate_account_secure_code(account_key):
    salt = "KoderSecureSystemSalt2026"
    hashed = hashlib.sha256((account_key + salt).encode("utf-8")).hexdigest()
    return str(int(hashed[:8], 16))[-6:].zfill(6)


def normalize_user_profile(account_key, user_profile):
    if not isinstance(user_profile, dict):
        return {}

    user_profile.setdefault("saved_nick", account_key)
    user_profile.setdefault("password", "")
    user_profile.setdefault("history", [])
    user_profile.setdefault("notepad", "")
    user_profile.setdefault("has_liked", False)
    user_profile.setdefault("theme_color", "#1E90FF")
    user_profile.setdefault("bg_color", "#FFFFFF")
    user_profile.setdefault("clear_btn_color", "#5cb85c")
    user_profile.setdefault("staff_bar_color", "#FF4B4B")
    user_profile.setdefault("can_reset_passwords", False)
    user_profile.setdefault("created_at", time.time())
    user_profile.setdefault("is_temporary", False)
    user_profile["is_temporary"] = bool(user_profile.get("is_temporary", False))

    if user_profile["is_temporary"]:
        user_profile.setdefault("expire_at", time.time() + TEMP_ACCOUNT_LIFETIME)
    else:
        user_profile["expire_at"] = None

    user_profile.setdefault("sec_code", generate_account_secure_code(account_key))
    return user_profile


def ensure_user_profile(data, account_key):
    if not isinstance(data, dict):
        data = {}
    data.setdefault("user_data", {})
    if account_key not in data["user_data"] or not isinstance(data["user_data"][account_key], dict):
        data["user_data"][account_key] = {}
    data["user_data"][account_key] = normalize_user_profile(account_key, data["user_data"][account_key])
    return data


def save_global_data(data):
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp, DATA_FILE)
        return True
    except Exception:
        return False


def load_global_data():
    default = default_store()
    if not os.path.exists(DATA_FILE):
        return default

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return default

        for key, value in default.items():
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

        for key, profile in list(data["user_data"].items()):
            if isinstance(profile, dict):
                data["user_data"][key] = normalize_user_profile(key, profile)

        return data
    except Exception:
        return default


def persist_store(data=None):
    if data is None:
        data = st.session_state.global_store
    if not isinstance(data, dict):
        data = {}
    data.setdefault("user_data", {})
    for key, profile in list(data.get("user_data", {}).items()):
        if isinstance(profile, dict):
            data["user_data"][key] = normalize_user_profile(key, profile)
    save_global_data(data)
    st.session_state.global_store = data
    return data


def purge_expired_accounts(data):
    if not isinstance(data, dict):
        return default_store()
    now = time.time()
    changed = False
    expired = []

    for account_key, profile in list(data.get("user_data", {}).items()):
        if isinstance(profile, dict) and profile.get("is_temporary") is True:
            expire_at = profile.get("expire_at")
            if expire_at is not None and now > float(expire_at):
                expired.append(account_key)

    for key in expired:
        data["user_data"].pop(key, None)
        for role in ("admins", "moderators", "vips"):
            if role in data and key in data[role]:
                data[role] = [x for x in data[role] if x != key]
        changed = True

    if changed:
        save_global_data(data)
    return data


# --- Inicjalizacja sesji ---
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


st.set_page_config(page_title="Koder", page_icon="📟", layout="wide")

# --- UI ---
current_user = st.session_state.get("user_author_key", "")

if not current_user:
    st.title("📟 Koder")
    st.write("Zaloguj się lub utwórz konto.")

    tab_login, tab_register = st.tabs(["🔑 Zaloguj się", "📝 Rejestracja"])

    with tab_login:
        with st.form("login_form"):
            login_key = st.text_input("Klucz konta")
            login_password = st.text_input("Hasło", type="password")
            if st.form_submit_button("Zaloguj"):
                data = st.session_state.global_store
                profile = data.get("user_data", {}).get(login_key)
                if not profile:
                    st.error("Konto nie istnieje.")
                elif profile.get("password", "") != login_password:
                    st.error("Błędne hasło.")
                else:
                    st.session_state.user_author_key = login_key
                    st.query_params["ak"] = login_key
                    st.rerun()

    with tab_register:
        with st.form("register_form"):
            reg_key = st.text_input("Klucz konta")
            reg_nick = st.text_input("Nick")
            reg_pass = st.text_input("Hasło", type="password")
            if st.form_submit_button("Utwórz konto"):
                if not reg_key:
                    st.error("Klucz nie może być pusty.")
                elif reg_key in st.session_state.global_store.get("user_data", {}):
                    st.error("Klucz jest już zajęty.")
                else:
                    data = load_global_data()
                    data = ensure_user_profile(data, reg_key)
                    data["user_data"][reg_key].update({
                        "saved_nick": reg_nick or reg_key,
                        "password": reg_pass,
                        "theme_color": st.session_state.global_store.get("default_theme_color", "#1E90FF"),
                        "bg_color": st.session_state.global_store.get("default_bg_color", "#FFFFFF"),
                        "clear_btn_color": st.session_state.global_store.get("default_clear_btn_color", "#5cb85c"),
                        "is_temporary": False,
                        "expire_at": None,
                    })
                    persist_store(data)
                    st.session_state.user_author_key = reg_key
                    st.query_params["ak"] = reg_key
                    st.success("Konto utworzone.")
                    st.rerun()

    st.stop()

# --- Po zalogowaniu ---
user_data = st.session_state.global_store.get("user_data", {})
profile = normalize_user_profile(current_user, user_data.get(current_user, {}))
st.session_state.global_store["user_data"][current_user] = profile
persist_store(st.session_state.global_store)

st.title(f"Witaj, {profile.get('saved_nick', current_user)}")

if profile.get("is_temporary"):
    remaining = int(float(profile.get("expire_at", 0)) - time.time())
    st.caption(f"To konto testowe. Wygasa za: {max(0, remaining)} sekund.")
else:
    st.caption("To konto jest trwałe i nie będzie usuwane automatycznie.")

roles = []
if current_user in st.session_state.global_store.get("admins", []):
    roles.append("admin")
if current_user in st.session_state.global_store.get("moderators", []):
    roles.append("moderator")
if current_user in st.session_state.global_store.get("vips", []):
    roles.append("vip")

if not roles:
    roles.append("user")

st.write("Rangi:", ", ".join(roles))

if current_user == "admin" or current_user in st.session_state.global_store.get("admins", []):
    st.subheader("Zarządzanie rangami")
    with st.form("role_form"):
        target_key = st.selectbox("Użytkownik", options=sorted(user_data.keys()))
        new_role = st.selectbox("Nowa rola", ["user", "moderator", "vip", "admin"])
        if st.form_submit_button("Zapisz rangę"):
            if target_key == current_user and new_role != "admin":
                st.warning("Nie można zmienić własnej rangi na niższą niż admin.")
            else:
                set_role(target_key, new_role)
                st.success("Ranga zapisana.")
                st.rerun()

if st.button("Wyloguj"):
    st.session_state.pop("user_author_key", None)
    st.query_params.clear()
    st.rerun()

# --- Konto testowe demo ---
if st.button("Utwórz konto testowe (20 min)"):
    key = f"test_{int(time.time())}"
    data = load_global_data()
    data = ensure_user_profile(data, key)
    data["user_data"][key].update({
        "saved_nick": key,
        "password": "",
        "is_temporary": True,
        "expire_at": time.time() + TEMP_ACCOUNT_LIFETIME,
    })
    persist_store(data)
    st.success(f"Utworzono konto testowe: {key}")
    st.rerun()

st.write("---")
for key, profile in sorted(user_data.items()):
    status = "testowe" if profile.get("is_temporary") else "trwałe"
    st.write(f"- {key}: {status} | password={'tak' if profile.get('password') else 'nie'} | role={profile.get('role','user')}")


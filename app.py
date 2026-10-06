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
        "default_theme_color": "#1E90FF",
        "default_bg_color": "#FFFFFF",
        "default_clear_btn_color": "#5cb85c",
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return default_data
                for key, val in default_data.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception:
            return default_data
    return default_data


def save_global_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
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

    if is_temporary:
        expire_at = teraz_ts + CZAS_KONTA_TESTOWEGO  # Wygasa po 20 min
    else:
        expire_at = teraz_ts + BEZPIECZNY_CZAS_ZWYKLEGO  # Licznik na ~63 lata

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


# --- 1. INICJALIZACJA STANOWISKA SESJI ---
if "global_store" not in st.session_state:
    st.session_state.global_store = load_global_data()

# --- 2. AUTOMATYCZNE CZYSZCZENIE KONT ---
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
            for role in ["admins", "moderators", "vips"]:
                if role in current_data and k in current_data[role]:
                    current_data[role].remove(k)
                    db_changed = True

    if db_changed:
        save_global_data(current_data)
        st.session_state.global_store = current_data

# --- 3. PRZYPISANIE ZMIENNYCH Z AKTUALNEGO STANU ---
def_theme = st.session_state.global_store.get("default_theme_color", "#1E90FF")
def_bg = st.session_state.global_store.get("default_bg_color", "#FFFFFF")
def_clear = st.session_state.global_store.get("default_clear_btn_color", "#5cb85c")

params = st.query_params
url_key = params.get("ak", "").strip()

if "user_author_key" not in st.session_state:
    st.session_state.user_author_key = url_key if url_key else ""

if "emulated_from_admin2" in st.session_state and st.sidebar.button("⬅️ Powrót do panelu Admin2", type="primary"):
    del st.session_state["emulated_from_admin2"]
    if "emulated_role" in st.session_state:
        del st.session_state["emulated_role"]
    st.session_state.user_author_key = "admin2"
    st.query_params["ak"] = "admin2"
    st.query_params["auth"] = "true"
    st.rerun()

current_user = st.session_state.user_author_key

# ==============================================================================
# SPECIAL PANEL: KODY BEZPIECZEŃSTWA (kody / 1984)
# ==============================================================================
if current_user == "kody" or st.session_state.get("view_mode") == "kody_only":
    if "kody_authenticated" not in st.session_state:
        st.session_state.kody_authenticated = False

    if not st.session_state.kody_authenticated:
        st.title("🔑 Panel Weryfikacji Kodów Bezpieczeństwa")
        st.subheader("🔒 Weryfikacja tożsamości")

        with st.form("kody_login_form"):
            input_pass_kody = st.text_input("Podaj hasło do panelu kodów:", type="password", placeholder="Wpisz hasło...")
            submit_kody = st.form_submit_button("🔓 Zaloguj do panelu kodów")

            if submit_kody:
                if input_pass_kody.strip() == "1984":
                    st.session_state.kody_authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Niepoprawne hasło!")

        st.write("---")
        with st.form("kody_exit_form"):
            exit_key = st.text_input("Wróć do standardowego konta (wklej klucz):")
            submit_exit = st.form_submit_button("🚪 Opuść panel kodów")

            if submit_exit and exit_key.strip():
                ek = exit_key.strip()
                create_user_account(ek, is_temporary=False)
                st.session_state.user_author_key = ek
                st.query_params["ak"] = ek
                if "kody_authenticated" in st.session_state:
                    del st.session_state.kody_authenticated
                st.rerun()
        st.stop()

    st.title("🔑 Panel Weryfikacji Kodów Bezpieczeństwa")
    st.caption("Tryb podglądu zdefiniowany bezpośrednio w kodzie aplikacji.")

    if st.button("🚪 Powrót / Wyloguj z panelu kodów", type="primary", use_container_width=True):
        st.session_state.kody_authenticated = False
        st.session_state.user_author_key = ""
        st.query_params.clear()
        st.rerun()

    st.markdown("---")
    global_store = load_global_data()
    user_data = global_store.get("user_data", {})

    st.subheader("📋 Lista Kodów Bezpieczeństwa")
    search_user = st.text_input("🔍 Wyszukaj użytkownika (login):", placeholder="Wpisz login...").strip()

    rows = []
    for user_key, profile in user_data.items():
        if isinstance(profile, dict):
            if search_user and search_user.lower() not in user_key.lower():
                continue

            sec_code = (
                profile.get("sec_code")
                or profile.get("security_code")
                or profile.get("kod_bezpieczenstwa")
                or generate_account_secure_code(user_key)
            )
            nick = profile.get("saved_nick", user_key)
            is_temp = "TAK (Testowe)" if profile.get("is_temporary") else "NIE"

            rows.append({
                "Klucz / Login": user_key,
                "Nazwa / Nick": nick,
                "Kod Bezpieczeństwa": sec_code,
                "Konto Testowe": is_temp,
            })

    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("Brak użytkowników spełniających kryteria lub baza jest pusta.")
    st.stop()

# --- PANEL AWARYJNEGO KONTA WŁAŚCICIELA (admin2) ---
if current_user == "admin2":
    st.markdown("<h1 style='color: #FF0000; margin-bottom: 0;'>🚨 SYSTEM RATUNKOWY (admin2)</h1>", unsafe_allow_html=True)
    st.write("Uruchomiono niezależny panel awaryjnego resetu haseł, zarządzania kadrą oraz całkowitego czyszczenia kont.")
    st.write("---")

    if "admin2_authenticated" not in st.session_state:
        st.session_state.admin2_authenticated = params.get("auth", "") == "true"

    if not st.session_state.admin2_authenticated:
        st.subheader("🔒 Weryfikacja tożsamości systemu ratunkowego")
        with st.form("admin2_login_form"):
            input_pass_admin2 = st.text_input("Podaj pierwsze hasło ratunkowe:", type="password", placeholder="Wpisz pierwsze hasło...")
            input_pass2_admin2 = st.text_input("Podaj drugie hasło ratunkowe:", type="password", placeholder="Wpisz drugie hasło...")
            submit_login_admin2 = st.form_submit_button("🔓 Uzyskaj dostęp awaryjny")

            if submit_login_admin2:
                if input_pass_admin2 == "Przyrodnik1" and input_pass2_admin2 == "Ignacy":
                    st.session_state.admin2_authenticated = True
                    st.query_params["auth"] = "true"
                    components.html("""
                        <script>
                            localStorage.setItem("auth_admin2", "true");
                            window.parent.location.href = window.parent.location.pathname + "?ak=admin2&auth=true";
                        </script>
                    """, height=0, width=0)
                    st.rerun()
                else:
                    st.error("❌ Błędne hasła ratunkowe! Odmowa dostępu.")

        st.write("---")
        with st.form("admin2_exit_form_locked"):
            exit_key = st.text_input("Wróć do standardowego konta (wklej klucz):")
            if st.form_submit_button("Opuść system ratunkowy") and exit_key.strip():
                ek = exit_key.strip()
                st.session_state.user_author_key = ek
                st.query_params["ak"] = ek
                if "admin2_authenticated" in st.session_state:
                    del st.session_state.admin2_authenticated
                components.html(f"<script>localStorage.setItem('koder_author_key2', '{ek}'); window.parent.location.href = window.parent.location.pathname + '?ak={ek}';</script>", height=0, width=0)
                st.rerun()
        st.stop()

    st.success("⚙️ Autoryzacja poprawna. Masz pełną niezależną kontrolę nad strukturą danych systemu.")

    rc1, rc2 = st.columns([2, 1])
    with rc1:
        current_data = load_global_data()

        st.markdown("### Generator Kont Testowych (Ważne przez 20 minut)")
        tg_c1, tg_c2, tg_c3, tg_c4 = st.columns(4)
        if "last_created_test_key" not in st.session_state:
            st.session_state.last_created_test_key = None

        with tg_c1:
            if st.button("Stwórz: USER TEST", key="a2_gen_user_btn", use_container_width=True):
                test_key = f"user_test_{int(time.time())}"
                current_data["user_data"][test_key] = {
                    "password": "",
                    "saved_nick": "Zwykły User Test (20m)",
                    "is_temporary": True,
                    "expire_at": time.time() + 1200,
                    "history": [],
                    "notepad": "",
                }
                save_global_data(current_data)
                st.session_state.global_store = current_data
                st.session_state.last_created_test_key = test_key
                st.rerun()

        with tg_c2:
            if st.button("Stwórz: VIP TEST", key="a2_gen_vip_btn", use_container_width=True):
                test_key = f"vip_test_{int(time.time())}"
                current_data["user_data"][test_key] = {
                    "password": "",
                    "saved_nick": "VIP Testowy (20m)",
                    "is_temporary": True,
                    "expire_at": time.time() + 1200,
                    "history": [],
                    "notepad": "",
                }
                if "vips" not in current_data:
                    current_data["vips"] = []
                current_data["vips"].append(test_key)
                save_global_data(current_data)
                st.session_state.global_store = current_data
                st.session_state.last_created_test_key = test_key
                st.rerun()

        with tg_c3:
            if st.button("Stwórz: MOD TEST", key="a2_gen_mod_btn", use_container_width=True):
                test_key = f"mod_test_{int(time.time())}"
                current_data["user_data"][test_key] = {
                    "password": "",
                    "saved_nick": "Mod Testowy (20m)",
                    "is_temporary": True,
                    "expire_at": time.time() + 1200,
                    "history": [],
                    "notepad": "",
                }
                if "moderators" not in current_data:
                    current_data["moderators"] = []
                current_data["moderators"].append(test_key)
                save_global_data(current_data)
                st.session_state.global_store = current_data
                st.session_state.last_created_test_key = test_key
                st.rerun()

        with tg_c4:
            if st.button("Stwórz: ADMIN TEST", key="a2_gen_adm_btn", use_container_width=True):
                test_key = f"admin_test_{int(time.time())}"
                current_data["user_data"][test_key] = {
                    "password": "",
                    "saved_nick": "Admin Testowy (20m)",
                    "is_temporary": True,
                    "expire_at": time.time() + 1200,
                    "history": [],
                    "notepad": "",
                }
                if "admins" not in current_data:
                    current_data["admins"] = []
                current_data["admins"].append(test_key)
                save_global_data(current_data)
                st.session_state.global_store = current_data
                st.session_state.last_created_test_key = test_key
                st.rerun()

        active_temporary_accounts = [k for k, v in current_data.get("user_data", {}).items() if v.get("is_temporary")]

        if active_temporary_accounts:
            st.markdown("##### ⏱️ Szybkie logowanie na konta testowe (odliczanie na żywo):")

            @st.fragment(run_every=1.0)
            def render_countdown_buttons(accounts, data):
                to_log_cols = st.columns(min(len(accounts), 3))
                for t_idx, t_key in enumerate(accounts):
                    col_target = to_log_cols[t_idx % 3]
                    t_prof = data["user_data"][t_key]
                    rem_seconds = int(t_prof.get("expire_at", 0) - time.time())
                    time_label = f"{rem_seconds // 60}m {rem_seconds % 60}s" if rem_seconds > 0 else "Wygasło"

                    with col_target:
                        if st.button(f"👤 {t_key}\n⏳ {time_label}", key=f"quick_log_tmp_{t_key}_{t_idx}", use_container_width=True):
                            st.session_state["emulated_from_admin2"] = True
                            st.session_state.user_author_key = t_key
                            st.query_params["ak"] = t_key
                            st.query_params["auth"] = "true"
                            st.rerun()

            render_countdown_buttons(active_temporary_accounts, current_data)

        st.write("---")

        st.markdown("### 👑 Zarządzanie Rangami (Admin/Mod/VIP)")
        with st.form("admin2_grant_roles_form", clear_on_submit=True):
            target_key_a2 = st.text_input("Wpisz klucz konta (ID) użytkownika:").strip()
            chosen_role_a2 = st.selectbox("Wybierz docelową rangę:", ["Odbierz wszystkie rangi (Zwykły Użytkownik)", "VIP", "Moderator", "Administrator"])
            submit_role_a2 = st.form_submit_button("⚡ Zastosuj zmiany w rangach")

            if submit_role_a2 and target_key_a2:
                if target_key_a2 in current_data.get("user_data", {}):
                    for role_list in ["admins", "moderators", "vips"]:
                        if target_key_a2 in current_data.get(role_list, []):
                            current_data[role_list].remove(target_key_a2)

                    if chosen_role_a2 == "Administrator":
                        current_data.setdefault("admins", []).append(target_key_a2)
                    elif chosen_role_a2 == "Moderator":
                        current_data.setdefault("moderators", []).append(target_key_a2)
                    elif chosen_role_a2 == "VIP":
                        current_data.setdefault("vips", []).append(target_key_a2)

                    save_global_data(current_data)
                    st.session_state.global_store = current_data
                    st.success(f"✅ Ranga dla `{target_key_a2}` zaktualizowana do: **{chosen_role_a2}**")
                    st.rerun()
                else:
                    st.error("❌ Podane konto nie istnieje.")

        with st.expander("👥 Zwiń/Rozwiń pełną listę kadry i osób uprzywilejowanych", expanded=True):
            st.markdown("##### Aktualni Administratorzy, Moderatorzy i członkowie VIP:")
            all_staff_members = []
            for adm in current_data.get("admins", []):
                all_staff_members.append({"id": adm, "role": "Administrator", "color": "red"})
            for mod in current_data.get("moderators", []):
                all_staff_members.append({"id": mod, "role": "Moderator", "color": "orange"})
            for vp in current_data.get("vips", []):
                all_staff_members.append({"id": vp, "role": "VIP", "color": "purple"})

            if not all_staff_members:
                st.caption("Brak przypisanych rang specjalnych w systemie (wszyscy są zwykłymi użytkownikami).")
            else:
                for s_idx, member in enumerate(all_staff_members):
                    m_id, m_role, m_color = member["id"], member["role"], member["color"]
                    u_profile = current_data.get("user_data", {}).get(m_id, {})
                    m_nick = u_profile.get("saved_nick", m_id)

                    sc1, sc2 = st.columns([4.5, 1.5])
                    with sc1:
                        st.markdown(f"🆔 ID: `{m_id}` | Nazwa: **{m_nick}** — Ranga: :{m_color}[**{m_role}**]")
                    with sc2:
                        if st.button("🔴 Degraduj", key=f"deg_btn_{m_id}_{s_idx}", type="secondary", use_container_width=True):
                            for role_list in ["admins", "moderators", "vips"]:
                                if m_id in current_data.get(role_list, []):
                                    current_data[role_list].remove(m_id)
                            save_global_data(current_data)
                            st.session_state.global_store = current_data
                            st.error(f"Odebrano uprawnienia dla konta `{m_id}`!")
                            st.rerun()

        st.write("---")

        st.markdown("### 🔑 Awaryjne Resetowanie Haseł Użytkowników")
        resets_list_a2 = current_data.get("password_resets", [])
        if resets_list_a2:
            st.markdown("💬 *Oczekujące prośby o reset od użytkowników:*")
            for req_a2 in resets_list_a2:
                st.warning(f"Konto: `{req_a2.get('author_key')}` ({req_a2.get('sender_nick')}) zgłosiło kod: **{req_a2.get('text')}**")

        with st.form("admin2_direct_reset_password_form", clear_on_submit=True):
            input_reset_key_a2 = st.text_input("Wpisz klucz konta (ID) do skasowania hasła:")
            input_reset_code_a2 = st.text_input("Wpisz 6-cyfrowy Kod Bezpieczeństwa konta:")
            submit_reset_a2 = st.form_submit_button("💥 Całkowicie usuń hasło wybranego profilu")

            if submit_reset_a2:
                rk_a2, rc_a2 = input_reset_key_a2.strip(), input_reset_code_a2.strip()
                if rk_a2 in current_data.get("user_data", {}) and rc_a2 == generate_account_secure_code(rk_a2):
                    current_data["user_data"][rk_a2]["password"] = ""
                    current_data["password_resets"] = [m for m in current_data["password_resets"] if m.get("author_key") != rk_a2]
                    save_global_data(current_data)
                    st.session_state.global_store = current_data
                    st.success(f"✅ Hasło profilu `{rk_a2}` zostało wyzerowane pomyślnie!")
                    st.rerun()
                else:
                    st.error("❌ Błędny klucz konta lub nieprawidłowy przypisany Kod Bezpieczeństwa!")

        st.write("")
        st.markdown("##### 🔑 Sprawdzanie kodu bezpieczeństwa i statusu resetu konta:")
        chk_user_key = st.text_input("Wpisz klucz użytkownika (login) do sprawdzenia:", key="admin2_check_sec_user")

        if st.button("🔍 Sprawdź kod i zgłoszenia resetu", key="admin2_btn_check_sec", type="secondary"):
            if chk_user_key:
                all_users = current_data.get("user_data", {})
                if chk_user_key in all_users:
                    expected_sec_code = generate_account_secure_code(chk_user_key)
                    st.success(f"👤 Konto: **{chk_user_key}** | Prawidłowy kod bezpieczeństwa: ` {expected_sec_code} `")

                    user_requests = [req for req in current_data.get("password_resets", []) if req.get('author_key') == chk_user_key]
                    if user_requests:
                        st.info("📩 **Znaleziono aktywne zgłoszenie resetu hasła dla tego konta!**")
                        for req in user_requests:
                            user_submitted_code = str(req.get('text', '')).strip()
                            if user_submitted_code == expected_sec_code:
                                st.success(f"✅ Kod podany w zgłoszeniu przez użytkownika (`{user_submitted_code}`) jest **PRAWIDŁOWY**.")
                            else:
                                st.error(f"❌ Kod podany w zgłoszeniu przez użytkownika (`{user_submitted_code}`) jest **BŁĘDNY**! (Oszustwo / pomyłka)")
                    else:
                        st.caption("ℹ️ Ten użytkownik nie wysłał obecnie żadnej prośby o awaryjny reset hasła.")
                else:
                    st.error(f"Nie znaleziono w bazie użytkownika o loginie: {chk_user_key}")
            else:
                st.warning("Najpierw wpisz login konta!")

        st.write("---")

        st.markdown("### 🚨 Permanentne Wymazywanie Kont (Wipe)")
        keys_to_wipe = sorted([k for k in current_data.get("user_data", {}).keys() if k != "admin2"])

        if not keys_to_wipe:
            st.caption("Brak innych kont zarejestrowanych w bazie danych.")
        else:
            with st.expander("📂 Zwiń/Rozwiń pełną listę zarejestrowanych kont (Alfabetycznie)", expanded=False):
                for w_idx, w_key in enumerate(keys_to_wipe):
                    w_prof = current_data["user_data"][w_key]
                    w_nick = w_prof.get("saved_nick", "Brak")
                    time_info = ""
                    if w_prof.get("is_temporary"):
                        rem_seconds = int(w_prof.get("expire_at", 0) - time.time())
                        time_info = f" | ⏳ Ważne jeszcze: **{rem_seconds // 60}m {rem_seconds % 60}s**" if rem_seconds > 0 else " | ⏳ *Wygasło*"

                    wcol1, wcol2 = st.columns([4.0, 2.0])
                    with wcol1:
                        st.markdown(f"Konto ID: `{w_key}` | Nazwa profilu: **{w_nick}**{time_info}")
                    with wcol2:
                        if st.button("🗑️ Usuń konto", key=f"hard_wipe_btn_{w_key}_{w_idx}", type="primary", use_container_width=True):
                            if w_key in current_data["user_data"]:
                                del current_data["user_data"][w_key]
                            for role_list in ["admins", "moderators", "vips"]:
                                if w_key in current_data.get(role_list, []):
                                    current_data[role_list].remove(w_key)
                            save_global_data(current_data)
                            st.session_state.global_store = current_data
                            st.error(f"💥 Konto `{w_key}` zostało permanentnie wymazane z systemu!")
                            st.rerun()

    with rc2:
        st.markdown("### 🚪 Wyjście i Szybkie Przełączanie")
        switch_targets_list = ["admin"] + [a for a in current_data.get("admins", []) if a != "admin2"]
        chosen_switch_admin = st.selectbox("Wybierz konto docelowe:", switch_targets_list, key="admin2_quick_switch_select")
        if st.button(f"🔄 Zaloguj jako {chosen_switch_admin}", key="admin2_quick_switch_trigger", type="primary", use_container_width=True):
            st.session_state.user_author_key = chosen_switch_admin
            st.query_params["ak"] = chosen_switch_admin
            st.query_params["auth"] = "true"
            if "admin2_authenticated" in st.session_state:
                del st.session_state.admin2_authenticated
            components.html(f"""
                <script>
                    localStorage.removeItem("auth_admin2");
                    localStorage.setItem("koder_author_key2", "{chosen_switch_admin}");
                    localStorage.setItem("auth_{chosen_switch_admin}", "true");
                    window.parent.location.href = window.parent.location.pathname + "?ak={chosen_switch_admin}&auth=true";
                </script>
            """, height=0, width=0)
            st.rerun()
    st.stop()

# --- EKRAN LOGOWANIA I REJESTRACJI ---
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
                    st.session_state.global_store["user_data"][reg_key] = {
                        "history": [],
                        "notepad": "",
                        "has_liked": False,
                        "saved_nick": reg_nick.strip() if reg_nick.strip() else reg_key,
                        "password": reg_pass.strip(),
                        "theme_color": def_theme,
                        "bg_color": def_bg,
                        "clear_btn_color": def_clear,
                        "staff_bar_color": "#FF4B4B",
                        "can_reset_passwords": False,
                    }
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

    with tab_login:
        with st.form("login_form_global"):
            st.subheader("Zaloguj się do swojego profilu")
            log_key = st.text_input("Wpisz swój Klucz Konta:", placeholder="Twój unikalny login").strip()
            log_pass = st.text_input("Wpisz hasło :", type="password", placeholder="Hasło...")
            log_pass2 = st.text_input("Wpisz drugie hasło:", type="password", placeholder="Drugie hasło...") if (log_key == "admin2" and log_pass == "Przyrodnik1") else ""

            submit_log = st.form_submit_button("🔓 Zaloguj się")

            if submit_log:
                if not log_key:
                    st.error("❌ Musisz podać klucz konta.")
                elif log_key == "admin2":
                    if log_pass.strip() == "Przyrodnik1" and log_pass2.strip() == "Ignacy":
                        st.session_state.user_author_key = "admin2"
                        st.session_state.admin2_authenticated = True
                        st.query_params["ak"] = "admin2"
                        st.query_params["auth"] = "true"
                        components.html("""
                            <script>
                                localStorage.setItem("koder_author_key2", "admin2");
                                localStorage.setItem("auth_admin2", "true");
                                window.parent.location.href = window.parent.location.pathname + "?ak=admin2&auth=true";
                            </script>
                        """, height=0, width=0)
                        st.rerun()
                    else:
                        st.error("❌ Błędne hasła ratunkowe dla konta admin2!")
                elif log_key not in st.session_state.global_store["user_data"]:
                    st.error("❌ Takie konto nie istnieje. Załóż je w zakładce obok!")
                else:
                    user_db_profile = st.session_state.global_store["user_data"][log_key]
                    required_password = user_db_profile.get("password", "").strip()

                    if required_password and log_pass.strip() != required_password:
                        st.error("❌ Nieprawidłowe hasło dla tego konta!")
                    else:
                        st.session_state.user_author_key = log_key
                        st.query_params["ak"] = log_key
                        if required_password:
                            st.session_state.account_authenticated = True
                            components.html(f'<script>localStorage.setItem("auth_{log_key}", "true"); window.parent.location.href = window.parent.location.pathname + "?ak={log_key}&auth=true";</script>', height=0, width=0)
                        else:
                            st.session_state.account_authenticated = False
                            components.html(f"<script>localStorage.setItem('koder_author_key2', '{log_key}'); window.parent.location.href = window.parent.location.pathname + '?ak={log_key}';</script>", height=0, width=0)
                        st.success("🔓 Zalogowano pomyślnie!")
                        st.rerun()
    st.stop()

# --- LOGIKA RANGI DLA STANDARDOWYCH KONT ORAZ PANEL EMULACJI DLA GŁÓWNEGO ADMINA ---
is_real_root_admin = current_user == "admin"
is_real_promoted_admin = current_user in st.session_state.global_store.get("admins", [])
is_real_admin = is_real_root_admin or is_real_promoted_admin
is_real_moderator = current_user in st.session_state.global_store.get("moderators", [])

if is_real_admin:
    st.sidebar.markdown("### 👁️ Tryb Podglądu Rangi")
    st.sidebar.write("Jako Właściciel/Admin możesz zmienić punkt widzenia aplikacji bez utraty uprawnień.")

    if "emulated_role" not in st.session_state:
        st.session_state.emulated_role = "Właściciel/Admin (Domyślny)"

    preview_options = ["Właściciel/Admin (Domyślny)", "Moderator", "VIP", "Zwykły Użytkownik"]
    chosen_preview = st.sidebar.radio("Wyświetl stronę jako:", preview_options, index=preview_options.index(st.session_state.emulated_role))

    if chosen_preview != st.session_state.emulated_role:
        st.session_state.emulated_role = chosen_preview
        st.rerun()

    if st.session_state.emulated_role != "Właściciel/Admin (Domyślny)":
        st.sidebar.warning(f"⚠️ Aktywna emulacja rangi: **{st.session_state.emulated_role}**")

if is_real_admin and st.session_state.get("emulated_role") != "Właściciel/Admin (Domyślny)":
    current_emulation = st.session_state.emulated_role
    is_root_admin = is_real_root_admin if current_emulation == "Właściciel/Admin (Domyślny)" else False
    is_promoted_admin = is_real_promoted_admin if current_emulation == "Właściciel/Admin (Domyślny)" else False
    is_admin = False
    is_moderator = current_emulation == "Moderator"
    is_vip = current_emulation == "VIP"
    is_staff = current_emulation == "Moderator"
    has_kod3_access = current_emulation in ["Moderator", "VIP"]
else:
    is_root_admin = current_user == "admin"
    is_promoted_admin = current_user in st.session_state.global_store.get("admins", [])
    is_admin = is_root_admin or is_promoted_admin
    is_moderator = is_real_moderator
    is_vip = current_user in st.session_state.global_store.get("vips", [])
    is_staff = is_admin or is_moderator
    has_kod3_access = is_vip or is_staff

if current_user not in st.session_state.global_store["user_data"]:
    st.session_state.global_store["user_data"][current_user] = {
        "history": [],
        "notepad": "",
        "has_liked": False,
        "saved_nick": current_user,
        "password": st.session_state.get("auth_password", ""),
        "theme_color": def_theme,
        "bg_color": def_bg,
        "clear_btn_color": def_clear,
        "staff_bar_color": "#FF4B4B" if is_real_admin else ("#FFA500" if is_moderator else "#1E90FF"),
        "can_reset_passwords": False,
    }
    save_global_data(st.session_state.global_store)

user_profile = st.session_state.global_store["user_data"].get(current_user, {})

theme_color = user_profile.get("theme_color", "#1E90FF")
bg_color = user_profile.get("bg_color", "#FFFFFF")
clear_btn_color = user_profile.get("clear_btn_color", "#5cb85c")
staff_bar_color = user_profile.get("staff_bar_color", "#FF4B4B" if is_real_admin else ("#FFA500" if is_moderator else "#1E90FF"))


def get_contrast_text_color(hex_color):
    hex_color = hex_color.lstrip('#')
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#000000" if brightness > 135 else "#FFFFFF"
    except Exception:
        return "#FFFFFF"


text_color = get_contrast_text_color(theme_color)
clear_btn_text_color = get_contrast_text_color(clear_btn_color)
main_text_theme = get_contrast_text_color(bg_color)

# --- STYLOWANIE INTERFEJSU CSS ---
st.markdown(f"""
    <style>
        .stApp {{ background-color: {bg_color} !important; }}
        .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label {{ color: {main_text_theme} !important; }}
        
        @media (max-width: 768px) {{
            [data-testid="stHorizontalBlock"] {{
                flex-direction: column !important;
            }}
            [data-testid="stHorizontalBlock"] > div {{
                width: 100% !important;
                margin-bottom: 12px !important;
            }}
        }}

        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div {{ display: flex; gap: 10px

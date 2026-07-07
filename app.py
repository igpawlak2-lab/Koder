import re
import datetime
import os
import json
import uuid
import hashlib
import time  # POPRAWKA: Dodano brakujący import modułu time
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
                if "vips" not in data: data["vips"] = []
                if "staff_chat" not in data: data["staff_chat"] = [] 
                if "staff_dms" not in data: data["staff_dms"] = []
                if "support_chat" not in data: data["support_chat"] = [] 
                if "password_resets" not in data: data["password_resets"] = []
                if "announcement" not in data: data["announcement"] = "Brak aktualnych ogłoszeń."
                if "announcement_font" not in data: data["announcement_font"] = "sans-serif"
                if "announcement_size" not in data: data["announcement_size"] = 16
                if "announcement_bg_color" not in data: data["announcement_bg_color"] = "#e7f3fe"
                if "default_theme_color" not in data: data["default_theme_color"] = "#1E90FF"
                if "default_bg_color" not in data: data["default_bg_color"] = "#FFFFFF"
                if "default_clear_btn_color" not in data: data["default_clear_btn_color"] = "#5cb85c"
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

# --- AUTOMATYCZNE CZYSZCZENIE KONT TESTOWYCH PO 1 GODZINIE ---
now = time.time()
db_changed = False
current_data = load_global_data()

if "user_data" in current_data:
    expired_keys = [k for k, v in current_data["user_data"].items() if v.get("is_temporary") and now > v.get("expire_at", 0)]
    for k in expired_keys:
        del current_data["user_data"][k]
        if "admins" in current_data and k in current_data["admins"]: current_data["admins"].remove(k)
        if "moderators" in current_data and k in current_data["moderators"]: current_data["moderators"].remove(k)
        if "vips" in current_data and k in current_data["vips"]: current_data["vips"].remove(k)
        db_changed = True

if db_changed:
    save_global_data(current_data)
    st.session_state.global_store = current_data

# Inicjalizacja głównego magazynu w stanu sesji
if "global_store" not in st.session_state:
    st.session_state.global_store = load_global_data()

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

# Obsługa powrotu do konta admin2 z emulacji administratora
if "emulated_from_admin2" in st.session_state and st.sidebar.button("⬅️ Powrót do panelu Admin2", type="primary"):
    del st.session_state["emulated_from_admin2"]
    if "emulated_role" in st.session_state: del st.session_state["emulated_role"]
    st.session_state.user_author_key = "admin2"
    st.query_params["ak"] = "admin2"
    st.query_params["auth"] = "true"
    st.rerun()

current_user = st.session_state.user_author_key

# Funkcja generująca bezpieczny kod weryfikacyjny konta
def generate_account_secure_code(account_key):
    salt = "KoderSecureSystemSalt2026"
    hashed = hashlib.sha256((account_key + salt).encode('utf-8')).hexdigest()
    return str(int(hashed[:8], 16))[-6:].zfill(6)


# --- PANEL AWARYJNEGO KONTA WŁAŚCICIELA (admin2) ---  
if current_user == "admin2":  
    st.markdown("<h1 style='color: #FF0000; margin-bottom: 0;'>🚨 SYSTEM RATUNKOWY (admin2)</h1>", unsafe_allow_html=True)  
    st.write("Uruchomiono niezależny panel awaryjnego resetu haseł, zarządzania kadrą oraz całkowitego czyszczenia kont.")  
    st.write("---")  
      
    if "admin2_authenticated" not in st.session_state:  
        st.session_state.admin2_authenticated = (params.get("auth", "") == "true")  
          
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
                    components.html(f"""  
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
                if "admin2_authenticated" in st.session_state: del st.session_state.admin2_authenticated  
                components.html(f"<script>localStorage.setItem('koder_author_key2', '{ek}'); window.parent.location.href = window.parent.location.pathname + '?ak={ek}';</script>", height=0, width=0)  
                st.rerun()  
        st.stop()  
  
    st.success("⚙️ Autoryzacja poprawna. Masz pełną niezależną kontrolę nad strukturą danych systemu.")  
      
    rc1, rc2 = st.columns([2, 1])  
    with rc1:  
        current_data = load_global_data()  
          
        # --- GENERATOR KONT TESTOWYCH (Ważne przez 20 minut) ---  
        st.markdown("### 🧪 Generator Kont Testowych (Ważne przez 20 minut)")  
        tg_c1, tg_c2, tg_c3, tg_c4 = st.columns(4)  
        
        if "last_created_test_key" not in st.session_state:  
            st.session_state.last_created_test_key = None  
  
        with tg_c1:  
            if st.button("🧪 Stwórz: USER TEST", key="a2_gen_user_btn", use_container_width=True):  
                test_key = f"user_test_{int(time.time())}"  
                current_data["user_data"][test_key] = {"password": "test", "saved_nick": "Zwykły User Test (20m)", "is_temporary": True, "expire_at": time.time() + 1200, "history": [], "notepad": ""}  
                save_global_data(current_data); st.session_state.global_store = current_data  
                st.session_state.last_created_test_key = test_key  
                st.rerun()  
        with tg_c2:  
            if st.button("🧪 Stwórz: VIP TEST", key="a2_gen_vip_btn", use_container_width=True):  
                test_key = f"vip_test_{int(time.time())}"  
                current_data["user_data"][test_key] = {"password": "test", "saved_nick": "VIP Testowy (20m)", "is_temporary": True, "expire_at": time.time() + 1200, "history": [], "notepad": ""}  
                if "vips" not in current_data: current_data["vips"] = []  
                current_data["vips"].append(test_key)  
                save_global_data(current_data); st.session_state.global_store = current_data  
                st.session_state.last_created_test_key = test_key  
                st.rerun()  
        with tg_c3:  
            if st.button("🧪 Stwórz: MOD TEST", key="a2_gen_mod_btn", use_container_width=True):  
                test_key = f"mod_test_{int(time.time())}"  
                current_data["user_data"][test_key] = {"password": "test", "saved_nick": "Mod Testowy (20m)", "is_temporary": True, "expire_at": time.time() + 1200, "history": [], "notepad": ""}  
                if "moderators" not in current_data: current_data["moderators"] = []  
                current_data["moderators"].append(test_key)  
                save_global_data(current_data); st.session_state.global_store = current_data  
                st.session_state.last_created_test_key = test_key  
                st.rerun()  
        with tg_c4:  
            if st.button("🧪 Stwórz: ADMIN TEST", key="a2_gen_adm_btn", use_container_width=True):  
                test_key = f"admin_test_{int(time.time())}"  
                current_data["user_data"][test_key] = {"password": "test", "saved_nick": "Admin Testowy (20m)", "is_temporary": True, "expire_at": time.time() + 1200, "history": [], "notepad": ""}  
                if "admins" not in current_data: current_data["admins"] = []  
                current_data["admins"].append(test_key)  
                save_global_data(current_data); st.session_state.global_store = current_data  
                st.session_state.last_created_test_key = test_key  
                st.rerun()  
                  
        # Pole z kodem do skopiowania oraz przycisk błyskawicznego logowania  
        if st.session_state.last_created_test_key:  
            st.info(f"✨ Wygenerowano nowe konto czasowe!")  
            st.text_input("Skopiuj kod klucza konta:", value=st.session_state.last_created_test_key, readonly=True)  
            if st.button(f"🔗 Zaloguj automatycznie na konto: {st.session_state.last_created_test_key}", type="primary"):  
                target_acc = st.session_state.last_created_test_key  
                st.session_state["emulated_from_admin2"] = True  
                st.session_state.user_author_key = target_acc  
                st.query_params["ak"] = target_acc  
                st.query_params["auth"] = "true"  
                st.session_state.last_created_test_key = None  
                st.rerun()  
          
        # Szybkie automatyczne logowanie na istniejące, aktywne konta czasowe
        active_temporary_accounts = [k for k, v in current_data.get("user_data", {}).items() if v.get("is_temporary")]
        if active_temporary_accounts:
            st.markdown("##### ⏱️ Szybkie logowanie na konta testowe (z licznikiem czasu):")
            to_log_cols = st.columns(min(len(active_temporary_accounts), 3))
            for t_idx, t_key in enumerate(active_temporary_accounts):
                col_target = to_log_cols[t_idx % 3]
                
                # OBLICZANIE CZASU DLA LICZNIKA
                t_prof = current_data["user_data"][t_key]
                rem_seconds = int(t_prof.get("expire_at", 0) - time.time())
                if rem_seconds > 0:
                    time_label = f"{rem_seconds // 60}m {rem_seconds % 60}s"
                else:
                    time_label = "Wygasło"
                
                with col_target:
                    # Licznik został dodany bezpośrednio do tekstu na przycisku
                    if st.button(f"👤 {t_key}\n⏳ {time_label}", key=f"quick_log_tmp_{t_key}_{t_idx}", use_container_width=True):
                        st.session_state["emulated_from_admin2"] = True
                        st.session_state.user_author_key = t_key
                        st.query_params["ak"] = t_key
                        st.query_params["auth"] = "true"
                        st.rerun()
  
        st.write("---")  
  
        # --- ZARZĄDZANIE RANGAMI ---  
        st.markdown("### 👑 Zarządzanie Rangami z Poziomu Awaryjnego")  
        with st.form("admin2_grant_roles_form", clear_on_submit=True):  
            target_key_a2 = st.text_input("Wpisz klucz konta (ID) użytkownika do nadania/zmiany rangi:").strip()  
            chosen_role_a2 = st.selectbox("Wybierz rangę docelową:", ["Zwykły Użytkownik", "VIP", "Moderator", "Administrator"])  
            submit_role_a2 = st.form_submit_button("⚡ Zatwierdź rangę w systemie")  
              
            if submit_role_a2 and target_key_a2:  
                if target_key_a2 in current_data.get("user_data", {}):  
                    if target_key_a2 in current_data.get("admins", []): current_data["admins"].remove(target_key_a2)  
                    if target_key_a2 in current_data.get("moderators", []): current_data["moderators"].remove(target_key_a2)  
                    if target_key_a2 in current_data.get("vips", []): current_data["vips"].remove(target_key_a2)  
                      
                    if chosen_role_a2 == "Administrator":  
                        if "admins" not in current_data: current_data["admins"] = []  
                        current_data["admins"].append(target_key_a2)  
                    elif chosen_role_a2 == "Moderator":  
                        if "moderators" not in current_data: current_data["moderators"] = []  
                        current_data["moderators"].append(target_key_a2)  
                    elif chosen_role_a2 == "VIP":  
                        if "vips" not in current_data: current_data["vips"] = []  
                        current_data["vips"].append(target_key_a2)  
                          
                    save_global_data(current_data); st.session_state.global_store = current_data  
                    st.success(f"✅ Zaktualizowano rangę dla konta `{target_key_a2}` na status: **{chosen_role_a2}**")  
                    st.rerun()  
                else:  
                    st.error("❌ Podane konto nie istnieje w bazie danych profilu.")  
  
        st.write("---")  
  
        # --- NIEZALEŻNY PANEL RESETU HASEŁ DLA ADMIN2 ---  
        st.markdown("### 🔑 Awaryjne Resetowanie Haseł Użytkowników")  
        resets_list_a2 = current_data.get("password_resets", [])  
        if resets_list_a2:  
            st.markdown("💬 *Oczekujące prośby o reset od użytkowników:*")  
            for r_idx_a2, req_a2 in enumerate(resets_list_a2):  
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
                    save_global_data(current_data); st.session_state.global_store = current_data  
                    st.success(f"✅ Hasło profilu `{rk_a2}` zostało wyzerowane pomyślnie!")  
                    st.rerun()  
                else:  
                    st.error("❌ Błędny klucz konta lub nieprawidłowy przypisany Kod Bezpieczeństwa!")  
  
        st.write("---")  
          
                # --- ROZWIJANA LISTA USUWANIA KONT WIPE (ALFABETYCZNIE) ---  
        st.markdown("### 🚨 Permanentne Wymazywanie Kont (Wipe)")  
        all_registered_keys = list(current_data.get("user_data", {}).keys())  
        keys_to_wipe = [k for k in all_registered_keys if k != "admin2"]  
        keys_to_wipe.sort()  
          
        if not keys_to_wipe:  
            st.caption("Brak innych kont zarejestrowanych w bazie danych.")  
        else:  
            with st.expander("📂 Zwiń/Rozwiń pełną listę zarejestrowanych kont (Alfabetycznie)", expanded=False):  
                for w_idx, w_key in enumerate(keys_to_wipe):  
                    w_prof = current_data["user_data"][w_key]  
                    w_nick = w_prof.get("saved_nick", "Brak")  
                      
                    # Dynamiczne obliczanie czasu dla kont czasowych na liście  
                    time_info = ""  
                    if w_prof.get("is_temporary"):  
                        rem_seconds = int(w_prof.get("expire_at", 0) - time.time())  
                        if rem_seconds > 0:  
                            time_info = f" | ⏳ Ważne jeszcze: **{rem_seconds // 60}m {rem_seconds % 60}s**"  
                        else:  
                            time_info = " | ⏳ *Wygasło*"  
                      
                    wcol1, wcol2 = st.columns([4.0, 2.0])  
                    with wcol1:  
                        st.markdown(f"Konto ID: `{w_key}` | Nazwa profilu: **{w_nick}**{time_info}")  
                    with wcol2:  
                        if st.button("🗑️ Usuń konto", key=f"hard_wipe_btn_{w_key}_{w_idx}", type="primary", use_container_width=True):  
                            if w_key in current_data["user_data"]: del current_data["user_data"][w_key]  
                            if w_key in current_data.get("admins", []): current_data["admins"].remove(w_key)  
                            if w_key in current_data.get("moderators", []): current_data["moderators"].remove(w_key)  
                            if w_key in current_data.get("vips", []): current_data["vips"].remove(w_key)  
                            save_global_data(current_data); st.session_state.global_store = current_data  
                            st.error(f"💥 Konto `{w_key}` zostało permanentnie wymazane z systemu!")  
                            st.rerun()  
    with rc2:  
        st.markdown("### 🚪 Wyjście i Szybkie Przełączanie")  
        all_admins_registered = current_data.get("admins", [])  
        switch_targets_list = ["admin"] + [a for a in all_admins_registered if a != "admin2"]  
        chosen_switch_admin = st.selectbox("Wybierz konto docelowe:", switch_targets_list, key="admin2_quick_switch_select")  
        if st.button(f"🔄 Zaloguj jako {chosen_switch_admin}", key="admin2_quick_switch_trigger", type="primary", use_container_width=True):  
            st.session_state.user_author_key = chosen_switch_admin  
            st.query_params["ak"] = chosen_switch_admin  
            st.query_params["auth"] = "true"  
            if "admin2_authenticated" in st.session_state: del st.session_state.admin2_authenticated  
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
                    st.session_state.global_store["user_data"][reg_key] = {
                        "history": [], "notepad": "", "has_liked": False, 
                        "saved_nick": reg_nick.strip() if reg_nick.strip() else reg_key, 
                        "password": reg_pass.strip(),  
                        "theme_color": def_theme, "bg_color": def_bg, "clear_btn_color": def_clear,
                        "staff_bar_color": "#FF4B4B",
                        "can_reset_passwords": False
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
            
            if log_key == "admin2" and log_pass == "Przyrodnik1":
                log_pass2 = st.text_input("Wpisz drugie hasło:", type="password", placeholder="Drugie hasło...")
            else:
                log_pass2 = ""
                
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
is_real_root_admin = (current_user == "admin")  
is_real_promoted_admin = (current_user in st.session_state.global_store.get("admins", [])) 
is_real_admin = is_real_root_admin or is_real_promoted_admin
is_real_moderator = (current_user in st.session_state.global_store.get("moderators", []))

# PASEK BOCZNY (SIDEBAR) DLA WŁAŚCICIELA - WYBÓR WIDOKU (EMULACJA)
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

# Kalkulacja uprawnień końcowych na podstawie wybranego trybu podglądu
if is_real_admin and st.session_state.get("emulated_role") != "Właściciel/Admin (Domyślny)":
    current_emulation = st.session_state.emulated_role
    is_root_admin = is_real_root_admin if current_emulation == "Właściciel/Admin (Domyślny)" else False
    is_promoted_admin = is_real_promoted_admin if current_emulation == "Właściciel/Admin (Domyślny)" else False
    is_admin = False
    is_moderator = (current_emulation == "Moderator")
    is_vip = (current_emulation == "VIP")
    is_staff = (current_emulation == "Moderator")
    has_kod3_access = (current_emulation in ["Moderator", "VIP"])
else:
    # Standardowe przypisanie ról dla pozostałych użytkowników
    is_root_admin = (current_user == "admin")  
    is_promoted_admin = (current_user in st.session_state.global_store.get("admins", [])) 
    is_admin = is_root_admin or is_promoted_admin
    is_moderator = is_real_moderator
    is_vip = (current_user in st.session_state.global_store.get("vips", []))
    is_staff = is_admin or is_moderator  
    has_kod3_access = is_vip or is_staff

# Zabezpieczenie integralności profilu - POBIERA ISTNIEJĄCE HASŁO ZAMIAST JE ZEROWAĆ
if current_user not in st.session_state.global_store["user_data"]:
    st.session_state.global_store["user_data"][current_user] = {
        "history": [], "notepad": "", "has_liked": False, "saved_nick": current_user, 
        "password": st.session_state.get("auth_password", ""),  
        "theme_color": def_theme, "bg_color": def_bg, "clear_btn_color": def_clear,
        "staff_bar_color": "#FF4B4B" if is_real_admin else ("#FFA500" if is_moderator else "#1E90FF"),
        "can_reset_passwords": False
    }
    save_global_data(st.session_state.global_store)

user_profile = st.session_state.global_store["user_data"].get(current_user, {})

theme_color = user_profile.get("theme_color", "#1E90FF")
bg_color = user_profile.get("bg_color", "#FFFFFF")
clear_btn_color = user_profile.get("clear_btn_color", "#5cb85c")
staff_bar_color = user_profile.get("staff_bar_color", "#FF4B4B" if is_real_admin else ("#FFA500" if is_moderator else "#1E90FF"))

can_user_reset_passwords = is_real_root_admin or user_profile.get("can_reset_passwords", False)

def get_contrast_text_color(hex_color):
    hex_color = hex_color.lstrip('#')
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#000000" if brightness > 135 else "#FFFFFF"
    except: return "#FFFFFF"

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

        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div {{ display: flex; gap: 10px; margin-top: 5px; width: 100%; }}
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label {{
            background-color: {"#262730" if main_text_theme == "#FFFFFF" else "#F0F2F6"} !important; 
            border: 2px solid {"#434654" if main_text_theme == "#FFFFFF" else "#E0E2E6"} !important; 
            padding: 12px 10px !important; border-radius: 10px; cursor: pointer; transition: all 0.2s ease-in-out;
            display: flex; align-items: center; justify-content: center; flex: 1;
            min-width: 140px; font-size: 16px !important; font-weight: bold !important; white-space: nowrap !important;
            color: {main_text_theme} !important;
        }}
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label div[data-testid="stMarkdownContainer"]::before {{ display: none !important; }}
        div[data-testid="stRadio"] input[type="radio"] {{ display: none; }}
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label:has(input:checked) {{
            background-color: {theme_color} !important; color: {text_color} !important; border-color: {theme_color} !important; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
        }}
        div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label:has(input:checked) div[data-testid="stMarkdownContainer"] {{ color: {text_color} !important; }}
        div.stButton > button {{
            background-color: {clear_btn_color} !important; color: {clear_btn_text_color} !important;
            border: 2px solid {clear_btn_color} !important; border-radius: 8px !important; font-weight: bold !important;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.1) !important; transition: all 0.2s ease-in-out !important;
        }}
        .stApp div.stButton > button p, .stApp div.stButton > button div, .stApp div.stButton > button span {{ color: {clear_btn_text_color} !important; }}
        div.stButton > button:hover {{ background-color: {clear_btn_color} !important; opacity: 0.85 !important; border-color: {clear_btn_color} !important; transform: scale(1.01); }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{ border-color: {theme_color} !important; border-radius: 12px; background-color: {"#1E1E1E" if main_text_theme == "#FFFFFF" else "#F9FAFB"}; }}
        
        .chat-box-container {{
            border: 1px solid #ccc;
            border-radius: 8px;
            background-color: #fcfcfc;
            margin-top: 10px;
        }}
    </style>
""", unsafe_allow_html=True)

# --- OBSŁUGA ZABEZPIECZENIA HASŁEM GŁÓWNYM ---
url_auth_state = params.get("auth", "")
if "account_authenticated" not in st.session_state:
    st.session_state.account_authenticated = (url_auth_state == "true")

account_has_password = user_profile.get("password", "").strip() != ""

if account_has_password and not st.session_state.account_authenticated:
    st.title("🔒 Konto zabezpieczone hasłem")
    st.write("Ten klucz konta ma przypisane hasło. Wprowadź je, aby uzyskać dostęp.")
    
    components.html(f"""
        <script>
            var localAuthState = localStorage.getItem("auth_{current_user}");
            var currentUrl = new URL(window.parent.location.href);
            if (localAuthState === "true" && currentUrl.searchParams.get("auth") !== "true") {{
                currentUrl.searchParams.set("auth", "true");
                window.parent.location.href = currentUrl.href;
            }}
        </script>
    """, height=0, width=0)
    
    with st.form("login_password_form"):
        input_pass = st.text_input("Podaj hasło do profilu:", type="password", placeholder="Wpisz hasło...")
        submit_login = st.form_submit_button("🔒 Odblokuj dostęp")
        
        if submit_login:
            if input_pass.strip() == user_profile.get("password"):
                st.session_state.account_authenticated = True
                st.query_params["auth"] = "true"
                components.html(f"""
                    <script>
                        localStorage.setItem("auth_{current_user}", "true");
                        window.parent.location.href = window.parent.location.pathname + "?ak={current_user}&auth=true";
                    </script>
                """, height=0, width=0)
                st.rerun()
            else:
                st.error("❌ Nieprawidłowe hasło konto!")
    
    st.write("---")
    st.markdown("### 💡 Zapomniałeś hasła?")
    st.write("Aby zapobiec niechcianym zmianom, musisz samodzielnie podać prawidłowy Kod Bezpieczeństwa przypisany do Twojego konta.")
    
    with st.form("emergency_reset_request_form"):
        user_entered_code = st.text_input("Wpisz swój 6-cyfrowy Kod Bezpieczeństwa:", type="default", placeholder="np. 123456", max_chars=6)
        submit_request = st.form_submit_button("📩 Wyślij prośbę o reset hasła do Właściciela")
        
        if submit_request:
            clean_code = user_entered_code.strip()
            expected_code = generate_account_secure_code(current_user)
            
            if not clean_code:
                st.error("❌ Musisz podać swój kod bezpieczeństwa, aby wysłać prośbę!")
            elif clean_code != expected_code:
                st.error("❌ Podany Kod Bezpieczeństwa jest nieprawidłowy! Zgłoszenie nie zostało wysłane.")
            else:
                time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                locked_user_nick = user_profile.get("saved_nick", "").strip()
                display_name_on_request = locked_user_nick if locked_user_nick else f"Konto_{current_user[:6]}"
                
                emergency_message = {
                    "sender_nick": display_name_on_request, "time": time_stamp,
                    "text": f"Zapomniałem hasła, proszę o reset (podaje ten 6 cyfrowy kod: **{clean_code}**)",
                    "author_key": current_user
                }
                current_data = load_global_data()
                if "password_resets" not in current_data: current_data["password_resets"] = []
                already_sent = any(m.get("author_key") == current_user for m in current_data["password_resets"])
                
                if already_sent:
                    st.warning("⚠️ Prośba o reset oczekuje już w panelu Właściciela. Czekaj cierpliwie.")
                else:
                    current_data["password_resets"].append(emergency_message)
                    save_global_data(current_data)
                    st.session_state.global_store = current_data
                    st.success("✅ Prośba została pomyślnie dostarczona do tajnego panelu Właściciela!")
    
    st.write("---")
    with st.expander("🔄 Chcesz zalogować się na inne konto?"):
        if st.button("🚪 Przejdź do ekranu wyboru konta"):
            st.session_state.user_author_key = ""
            st.query_params.clear()
            components.html("<script>localStorage.removeItem('koder_author_key2'); window.parent.location.href = window.parent.location.pathname;</script>", height=0, width=0)
            st.rerun()
    st.stop()

# --- MAPA UKŁADU OKRESOWEGO I FUNKCJE ENKODERA ---
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

# --- SYSTEMY KODOWANIA V1 ORAZ V2 ---
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
        else: val, idx = int(converted), ""
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
        return f"{g}{to_subscript(sub)}{to_superscript(o)}"
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
    g_part, o_part, sub_part = "", "", ""
    for char in s:
        if char in REV_SUP: o_part += REV_SUP[char]
        elif char in REV_SUB: sub_part += REV_SUB[char]
        else: g_part += char
    if not g_part or not o_part: return "?"
    try:
        g, o, pos = int(g_part), int(o_part), sub_part
        for i, (vg, vo, vs) in DATA_MAP.items():
            if vg == g and vo == o: return vs[1].upper() if pos == "2" and len(vs) > 1 else vs[0].upper()
    except ValueError: pass
    return "?"

# --- UNIKALNY ALGORYTM: KOD 3 ---
def enc_v3(l):
    for i, (g, o, s) in DATA_MAP.items():
        if s == l: return f"{o}.{g}.0"
    for i, (g, o, s) in DATA_MAP.items():
        if s[0] == l and len(s) > 1: return f"{o}.{g}.1"
        if len(s) > 1 and s[1] == l.lower(): return f"{o}.{g}.2"
    return "?"

def format_v3_unicode(code_str):
    if "." in code_str:
        parts = code_str.split(".")
        o_val, g_val, pos = parts[0], parts[1], parts[2]
        unicode_g = to_subscript(g_val)
        unicode_pos = to_superscript(pos) if pos in ["1", "2"] else ""
        return f"{o_val}{unicode_g}{unicode_pos}"
    return code_str

def dec_v3(s):
    s = s.strip()
    if not s: return "?"
    try:
        o_part, g_str, pos_str = "", "", ""
        in_sub, in_sup = False, False
        for char in s:
            if char in REV_SUB: 
                g_str += REV_SUB[char]
                in_sub = True
            elif char in REV_SUP: 
                pos_str += REV_SUP[char]
                in_sup = True
            else:
                if not in_sub and not in_sup:
                    o_part += char
        o = int(o_part)
        g = int(g_str)
        pos = pos_str if pos_str in ["1", "2"] else "0"
        
        for i, (vg, vo, vs) in DATA_MAP.items():
            if vo == o and vg == g:
                return vs[1].upper() if pos == "2" and len(vs) > 1 else vs[0].upper()
    except: pass
    return "?"


# --- DYNAMICZNY NAGŁÓWEK Z RANGAMI ORAZ WIDOKIEM EMULACJI ---
if is_real_root_admin:
    st.markdown("<h1 style='margin-bottom: 0;'>📟 KODER <span style='color: #FF4B4B; font-size: 1.2rem; vertical-align: middle; background-color: rgba(255,75,75,0.1); padding: 4px 8px; border-radius: 6px; margin-left: 10px; font-weight: bold;'>Właściciel</span></h1>", unsafe_allow_html=True)
elif is_promoted_admin:
    st.markdown("<h1 style='margin-bottom: 0;'>📟 KODER <span style='color: #FF4B4B; font-size: 1.2rem; vertical-align: middle; background-color: rgba(255,75,75,0.1); padding: 4px 8px; border-radius: 6px; margin-left: 10px; font-weight: bold;'>Admin</span></h1>", unsafe_allow_html=True)
elif is_moderator:
    st.markdown("<h1 style='margin-bottom: 0;'>📟 KODER <span style='color: #FFA500; font-size: 1.2rem; vertical-align: middle; background-color: rgba(255,165,0,0.1); padding: 4px 8px; border-radius: 6px; margin-left: 10px; font-weight: bold;'>Moderator</span></h1>", unsafe_allow_html=True)
elif is_vip:
    st.markdown("<h1 style='margin-bottom: 0;'>📟 KODER <span style='color: #BA55D3; font-size: 1.2rem; vertical-align: middle; background-color: rgba(186,85,211,0.1); padding: 4px 8px; border-radius: 6px; margin-left: 10px; font-weight: bold;'>VIP 🌟</span></h1>", unsafe_allow_html=True)
else:
    st.title("📟 KODER")

st.write("Uniwersalny system kodowania i dekodowania tekstu.")

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
        available_codes = ["Kod 1", "Kod 2"]
        if has_kod3_access:
            available_codes.append("Kod 3")
            
        st.radio("Wybierz system kodu:", available_codes, horizontal=True, key="proto_selection")
        st.radio("Wybierz operację:", ["Koduj", "Odkoduj"], horizontal=True, key="mode_selection")
        
        proto = st.session_state.proto_selection
        mode = st.session_state.mode_selection
        
        st.write(" ")
        txt = st.text_input("Wprowadź dane i zatwierdź Enterem:", placeholder="Wpisz dane tutaj...", key="main_encoder_input_field")
        
        if txt:
            if "Kod 3" in proto and not has_kod3_access:
                st.error("❌ Brak uprawnień! Kod 3 jest dostępny wyłącznie dla użytkowników z rangą VIP lub wyższą.")
            else:
                res_display = ""
                if mode == "Koduj":
                    words = clean_txt(txt).split(' ')
                    if "Kod 1" in proto:
                        raw_words = [[enc_v1(l) for l in w] for w in words]
                        res_display = "   ".join([" ".join([format_v1_unicode(l) for l in w]) for w in raw_words])
                    elif "Kod 2" in proto:
                        raw_words = [[enc_v2(l) for l in w] for w in words]
                        res_display = "   ".join([" ".join([format_v2_unicode(l) for l in w]) for w in raw_words])
                    elif "Kod 3" in proto:
                        raw_words = [[enc_v3(l) for l in w] for w in words]
                        res_display = "   ".join([" ".join([format_v3_unicode(l) for l in w]) for w in raw_words])
                else:
                    decoded_words = []
                    for w in txt.split("   "):
                        word_chars = []
                        for s in w.strip().split(" "):
                            if s: 
                                if "Kod 1" in proto: word_chars.append(dec_v1(s))
                                elif "Kod 2" in proto: word_chars.append(dec_v2(s))
                                elif "Kod 3" in proto: word_chars.append(dec_v3(s))
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

    # --- PANEL KOMUNIKACJI STAFFU ---
    if is_staff:
        with tab_chat:
            with st.expander("💬 Otwórz Chat Staffu / Awaryjny", expanded=False):
                st.radio("Wybierz rodzaj czatu:", ["👥 Grupa Ogólna Staffu", "💬 Wiadomości Prywatne (DM)"], horizontal=True, key="staff_chat_type")
                chat_type = st.session_state.staff_chat_type
                
                role_label = "Admin" if (is_admin or is_real_admin) else "Moderator"
                staff_nick = user_saved_nick if user_saved_nick else f"User_{current_user[:6]}"
                
                if chat_type == "👥 Grupa Ogólna Staffu":
                    st.markdown(f"<h3>🕵️‍♂️ Prywatny kanał komunikacji</h3>", unsafe_allow_html=True)
                    with st.form("staff_chat_group_form", clear_on_submit=True):
                        chat_msg = st.text_input(f"Wiadomość jako **{staff_nick} ({role_label})**:", placeholder="Wpisz tajną wiadomość do ekipy...")
                        btn_col1, btn_col2 = st.columns([3.5, 2.5])
                        with btn_col1: send_chat = st.form_submit_button("🚀 Wyślij do Staffu")
                        with btn_col2: refresh_group = st.form_submit_button("🔄 Odśwież wiadomości")
                        
                        if send_chat and chat_msg.strip():
                            time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                            formatted_msg = {
                                "sender_nick": staff_nick, "sender_role": role_label, "time": time_stamp,
                                "text": chat_msg.strip(), "bar_color": staff_bar_color, "author_key": current_user  
                            }
                            current_data = load_global_data()
                            if "staff_chat" not in current_data: current_data["staff_chat"] = []
                            current_data["staff_chat"].append(formatted_msg)
                            save_global_data(current_data)
                            st.session_state.global_store = current_data
                            st.rerun()
                            
                        if refresh_group:
                            st.session_state.global_store = load_global_data()
                            st.rerun()

                    if st.button("🗑️ Wyczyść cały Chat Staffu", key="global_clear_staff_chat_btn"):
                        current_data = load_global_data()
                        current_data["staff_chat"] = []
                        save_global_data(current_data)
                        st.session_state.global_store = current_data
                        st.rerun()

                    staff_messages = st.session_state.global_store.get("staff_chat", [])
                    st.write(" ")
                    with st.container(height=450):
                        if not staff_messages:
                            st.caption("Brak wiadomości.")
                        else:
                            for idx_reversed, msg in enumerate(reversed(staff_messages)):
                                original_idx = len(staff_messages) - 1 - idx_reversed
                                fallback_color = "#FF4B4B" if msg.get("sender_role") == "Admin" else "#FFA500"
                                current_bar_color = msg.get("bar_color", fallback_color)
                                is_my_own_message = (msg.get("author_key") == current_user)
                                
                                ch_col1, ch_col2 = st.columns([4.5, 1.5])
                                with ch_col1:
                                    st.markdown(f"""
                                        <div style="background-color: rgba(255,255,255,0.02); padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid {current_bar_color};">
                                            <span style="font-weight: bold; color: {main_text_theme};">[{msg.get('sender_role')}] {msg.get('sender_nick')}</span> 
                                            <span style="font-size: 0.8rem; opacity: 0.5; float: right;">{msg.get('time')}</span>
                                            <p style="margin: 4px 0 0 0; font-size: 1.05rem; color: {main_text_theme};">{msg.get('text')}</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                                with ch_col2:
                                    if is_my_own_message:
                                        if st.button("❌ Usuń", key=f"del_gmsg_{original_idx}", type="primary", use_container_width=True):
                                            current_data = load_global_data()
                                            if original_idx < len(current_data["staff_chat"]):
                                                current_data["staff_chat"].pop(original_idx)
                                                save_global_data(current_data)
                                                st.session_state.global_store = current_data
                                                st.rerun()
                                    else:
                                        st.button("🔒 Zablokowane", key=f"lock_gmsg_{original_idx}", disabled=True, use_container_width=True)

                else:
                    st.subheader("💬 Prywatne Wiadomości 1 na 1")
                    all_users = st.session_state.global_store.get("user_data", {})
                    mod_list = st.session_state.global_store.get("moderators", [])
                    admin_list = st.session_state.global_store.get("admins", [])
                    
                    staff_targets = {}
                    for u_key, u_val in all_users.items():
                        is_target_staff = (u_key == "admin") or (u_key in admin_list) or (u_key in mod_list)
                        if is_target_staff and u_key != current_user:
                            saved_name = u_val.get("saved_nick", "").strip()
                            if saved_name:
                                t_role = "Właściciel" if u_key == "admin" else ("Admin" if u_key in admin_list else "Moderator")
                                staff_targets[f"{saved_name} ({t_role})"] = u_key
                    
                    if not staff_targets:
                        st.warning("⚠️ Nie znaleziono innych członków ekipy posiadających ustawiony podpis (nick).")
                    else:
                        target_label = st.selectbox("Wybierz odbiorcę prywatnej wiadomości:", list(staff_targets.keys()))
                        target_user_key = staff_targets[target_label]
                        
                        with st.form("staff_dm_form", clear_on_submit=True):
                            dm_msg = st.text_input(f"Prywatna wiadomość do **{target_label.split(' ')[0]}**:", placeholder="Wpisz treść...")
                            dm_btn_col1, dm_btn_col2 = st.columns([3.5, 2.5])
                            with dm_btn_col1: send_dm = st.form_submit_button("🔒 Wyślij bezpieczną wiadomość")
                            with dm_btn_col2: refresh_dms = st.form_submit_button("🔄 Odśwież wiadomości")
                            
                            if send_dm and dm_msg.strip():
                                time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                                formatted_dm = {
                                    "sender_key": current_user, "sender_nick": staff_nick, "sender_role": role_label,
                                    "receiver_key": target_user_key, "time": time_stamp, "text": dm_msg.strip(), "bar_color": staff_bar_color
                                }
                                current_data = load_global_data()
                                if "staff_dms" not in current_data: current_data["staff_dms"] = []
                                current_data["staff_dms"].append(formatted_dm)
                                save_global_data(current_data)
                                st.session_state.global_store = current_data
                                st.rerun()
                                
                            if refresh_dms:
                                st.session_state.global_store = load_global_data()
                                st.rerun()
                        
                        all_dms = st.session_state.global_store.get("staff_dms", [])
                        visible_dms = []
                        for o_idx, dm in enumerate(all_dms):
                            if (dm.get("sender_key") == current_user and dm.get("receiver_key") == target_user_key) or \
                               (dm.get("sender_key") == target_user_key and dm.get("receiver_key") == current_user):
                                visible_dms.append((o_idx, dm))
                                
                        st.write(" ")
                        with st.container(height=260):
                            if not visible_dms:
                                st.caption(f"Brak historii z {target_label.split(' ')[0]}.")
                            else:
                                for original_dm_idx, dm in reversed(visible_dms):
                                    is_my_own_dm = (dm.get("sender_key") == current_user)
                                    fallback_color = "#FF4B4B" if dm.get("sender_role") == "Admin" else "#FFA500"
                                    current_bar_color = dm.get("bar_color", fallback_color)
                                    
                                    dm_col1, dm_col2 = st.columns([4.5, 1.5])
                                    with dm_col1:
                                        st.markdown(f"""
                                            <div style="background-color: rgba(30,144,255,0.03); padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid {current_bar_color};">
                                                <span style="color: {current_bar_color}; font-weight: bold;">🔑 {dm.get('sender_nick')}</span> 
                                                <span style="font-size: 0.75rem; opacity: 0.5; margin-left: 5px;">➔ do: {target_label.split(' ')[0]}</span>
                                                <span style="font-size: 0.8rem; opacity: 0.6; float: right;">{dm.get('time')}</span>
                                                <p style="margin: 4px 0 0 0; font-size: 1rem; font-style: italic;">{dm.get('text')}</p>
                                            </div>
                                        """, unsafe_allow_html=True)
                                    with dm_col2:
                                        if is_my_own_dm:
                                            if st.button("❌ Usuń", key=f"del_dm_{original_dm_idx}", type="primary", use_container_width=True):
                                                current_data = load_global_data()
                                                if original_dm_idx < len(current_data["staff_dms"]):
                                                    current_data["staff_dms"].pop(original_dm_idx)
                                                    save_global_data(current_data)
                                                    st.session_state.global_store = current_data
                                                    st.rerun()
                                                    
    # --- TABLICA OGŁOSZEŃ ---
    st.write("---")
    st.subheader("📢 Tablica Ogłoszeń")
    current_announcement = st.session_state.global_store.get("announcement", "Brak aktualnych ogłoszeń.")
    ann_font = st.session_state.global_store.get("announcement_font", "sans-serif")
    ann_size = st.session_state.global_store.get("announcement_size", 16)
    ann_bg = st.session_state.global_store.get("announcement_bg_color", "#e7f3fe")
    
    ann_text_color = "#0c5460" if get_contrast_text_color(ann_bg) == "#000000" else "#FFFFFF"
    ann_border_color = "#2196F3" if ann_text_color == "#0c5460" else ann_bg
    
    st.markdown(f"""
        <div style="background-color: {ann_bg}; border-left: 6px solid {ann_border_color}; padding: 15px; border-radius: 6px; margin-bottom: 15px; font-family: {ann_font}, Arial, sans-serif; font-size: {ann_size}px; color: {ann_text_color}; line-height: 1.5;">
            {current_announcement}
        </div>
    """, unsafe_allow_html=True)
    
    if is_staff:
        st.markdown("#### ⚙️ Konfiguracja Tablicy Ogłoszeń (Widoczne tylko dla Kadry)")
        new_announcement_text = st.text_area("Zmień treść ogłoszenia globalnego:", value=current_announcement)
        f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 1.0])
        with f_col1:
            font_options = {"Bezszeryfowa (Modern)": "sans-serif", "Szeryfowa (Classic)": "serif", "Monospace (Kodowa)": "monospace"}
            current_font_index = list(font_options.values()).index(ann_font) if ann_font in font_options.values() else 0
            chosen_font_label = st.selectbox("Wybierz krój czcionki:", list(font_options.keys()), index=current_font_index)
            selected_font_value = font_options[chosen_font_label]
        with f_col2: selected_size_value = st.slider("Wielkość tekstu (px):", min_value=12, max_value=36, value=int(ann_size), step=1)
        with f_col3: selected_ann_bg = st.color_picker("Tło tablicy:", value=ann_bg, key="admin_ann_bg_picker")
            
        if st.button("💾 Zapisz ogłoszenie i wygląd", key="save_announcement_btn"):
            current_data = load_global_data()
            current_data["announcement"] = new_announcement_text.strip()
            current_data["announcement_font"] = selected_font_value
            current_data["announcement_size"] = selected_size_value
            current_data["announcement_bg_color"] = selected_ann_bg
            save_global_data(current_data)
            st.session_state.global_store = current_data
            st.success("Ogłoszenie zaktualizowane!")
            st.rerun()

with c2:
    st.subheader("Historia operacji")
    if st.button("🗑️ Wyczyść historię operacji", type="primary"):
        st.session_state.global_store["user_data"][current_user]["history"] = []
        save_global_data(st.session_state.global_store)
        st.rerun()
    
    with st.container(height=240):
        if not user_history: st.caption("Brak operacji.")
        else:
            for item in user_history: st.code(item, language="text")

    st.write(" ")
    st.subheader("📝 Twój Prywatny Notatnik")
    def save_notepad_instantly():
        if "local_notepad_field" in st.session_state:
            val = st.session_state.local_notepad_field
            st.session_state.global_store["user_data"][current_user]["notepad"] = val
            save_global_data(st.session_state.global_store)

    note_input = st.text_area("Zapisz swoje uwagi:", value=user_notepad_content, placeholder="Wpisz notatki, kody lub sekwencje...", height=180, key="local_notepad_field", on_change=save_notepad_instantly)

    # --- CZAT POMOCNICZY (SUPPORT) ---
    st.write("---")
    if is_staff:
        with st.expander("📞 Otwórz Czat Pomocniczy (Support)", expanded=False):
            st.write("Wybierz kod konta użytkownika, aby odpowiedzieć:")
            support_users = []
            all_users_data = st.session_state.global_store.get("user_data", {})
            admins_list = st.session_state.global_store.get("admins", [])
            mods_list = st.session_state.global_store.get("moderators", [])
            
            for u_key in all_users_data.keys():
                if u_key != "admin" and u_key not in admins_list and u_key not in mods_list:
                    support_users.append(u_key)
                    
            if not support_users:
                st.caption("Brak zarejestrowanych użytkowników w systemie.")
            else:
                chosen_support_user = st.selectbox("Wybierz użytkownika z listy:", support_users, key="support_user_select")
                
                with st.form("support_response_form", clear_on_submit=True):
                    st.write(f"Odpowiedź do użytkownika **[{chosen_support_user}]**:")
                    reply_txt = st.text_area("Wpisz treść pomocy...", placeholder="Jak mogę pomóc temu użytkownikowi?", key="support_reply_area")
                    send_reply_btn = st.form_submit_button("Wyślij odpowiedź wsparcia")
                    
                    if send_reply_btn and reply_txt.strip():
                        time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                        new_reply = {
                            "sender_key": current_user,
                            "sender_nick": user_saved_nick if user_saved_nick else current_user,
                            "sender_role": "Właściciel (admin)" if (is_admin or is_real_admin) else "Moderator",
                            "receiver_key": chosen_support_user,
                            "time": time_stamp,
                            "text": reply_txt.strip()
                        }
                        current_data = load_global_data()
                        if "support_chat" not in current_data: current_data["support_chat"] = []
                        current_data["support_chat"].append(new_reply)
                        save_global_data(current_data)
                        st.session_state.global_store = current_data
                        st.rerun()

                st.markdown("### Pełna historia wszystkich zgłoszeń systemowych:")
                all_support_messages = st.session_state.global_store.get("support_chat", [])
                
                with st.container(height=400):
                    if not all_support_messages:
                        st.caption("Brak zarejestrowanej historii zgłoszeń.")
                    else:
                        for msg in reversed(all_support_messages):
                            msg_sender = msg.get("sender_key")
                            if msg_sender == "admin" or msg_sender in admins_list or msg_sender in mods_list:
                                st.markdown(f"⏱️ `{msg.get('time')}` | **{msg.get('sender_role', 'Staff')} ({msg_sender})** ➡️ do `{msg.get('receiver_key')}` : {msg.get('text')}")
                            else:
                                st.markdown(f"⏱️ `{msg.get('time')}` | **Użytkownik ({msg_sender})**: {msg.get('text')}")
    else:
        st.subheader("💬 Centrum Pomocy Technicznej")
        chat_expanded = st.toggle("💬 Otwórz czat z konsultantem", value=False, key="user_chat_toggle_state")
        
        if chat_expanded:
            st.markdown('<div class="chat-box-container">', unsafe_allow_html=True)
            with st.form("user_support_send_form", clear_on_submit=True):
                user_msg_input = st.text_input("Napisz do administracji (Zatwierdź Enterem):", placeholder="Wpisz treść pytania lub problemu tutaj...")
                if st.form_submit_button("🚀 Wyślij wiadomość"):
                    if user_msg_input.strip():
                        clean_user_msg = user_msg_input.strip().replace('j', 'i').replace('J', 'I')
                        time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                        
                        new_user_msg_obj = {
                            "sender_key": current_user, "sender_nick": user_saved_nick if user_saved_nick else current_user,
                            "sender_role": "Użytkownik", "receiver_key": "ALL_STAFF", "text": clean_user_msg, "time": time_stamp
                        }
                        
                        current_data = load_global_data()
                        if "support_chat" not in current_data: current_data["support_chat"] = []
                        current_data["support_chat"].append(new_user_msg_obj)
                        save_global_data(current_data)
                        st.session_state.global_store = current_data
                        st.success("Wiadomość wysłana!")
                        st.rerun()
            
            st.write("📋 **Historia Twojej rozmowy:**")
            global_support_chat = st.session_state.global_store.get("support_chat", [])
            user_visible_messages = [m for m in global_support_chat if m.get("sender_key") == current_user or m.get("receiver_key") == current_user]
            
            with st.container(height=280):
                if not user_visible_messages:
                    st.caption("Brak wiadomości in historii. Napisz wyżej, aby rozpocząć konwersację.")
                else:
                    for msg in reversed(user_visible_messages):
                        if msg.get("sender_role") == "Użytkownik":
                            st.markdown(f"""
                                <div style='background-color: rgba(30,144,255,0.08); padding:8px; border-radius:6px; margin-bottom:5px; text-align:right;'>
                                    <span style='font-size:0.75rem; opacity:0.6;'>{msg.get('time')}</span> | <b>Ty</b><br>{msg.get('text')}
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                                <div style='background-color: rgba(0,200,80,0.08); padding:8px; border-radius:6px; margin-bottom:5px;'>
                                    <b>{msg.get('sender_role')} ({msg.get('sender_nick')})</b> | <span style='font-size:0.75rem; opacity:0.6;'>{msg.get('time')}</span><br>{msg.get('text')}
                                </div>
                            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.caption("Czat jest obecnie zamknięty. Kliknij przełącznik powyżej, aby skontaktować się z administratorem.")

# --- GLOBALNE POLUBIENIA ---
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
with col_like2: st.write(f"Ta strona została polubiona już **{st.session_state.global_store.get('likes', 0)}** razy!")

st.write(" ")

# --- PANEL PERSONALIZACJI WYGLĄDU I ZABEZPIECZEŃ ---
with st.expander("🎨 Personalizacja Wyglądu i Zarządzanie Kontem"):
    st.subheader("🔐 Bezpieczeństwo konta")
    saved_password = user_profile.get("password", "").strip()
    my_secure_code = generate_account_secure_code(current_user)
    st.markdown(f"ℹ️ Twój osobisty **Kod Bezpieczeństwa Konta:** ` {my_secure_code} `")
    
    if st.button("🚪 Wyloguj się całkowicie z aplikacji", type="primary", key="logout_action_button_trigger"):
        st.session_state.user_author_key = ""
        st.session_state.account_authenticated = False
        if "emulated_role" in st.session_state: del st.session_state["emulated_role"]
        st.query_params.clear()
        components.html(f"""
            <script>
                localStorage.removeItem("auth_{current_user}");
                localStorage.removeItem("koder_author_key2");
                window.parent.location.href = window.parent.location.pathname;
            </script>
        """, height=0, width=0)
        st.rerun()
            
    if not saved_password:
        st.info("💡 To konto nie posiada obecnie hasła (dostęp samym kluczem).")
        with st.form("set_password_form"):
            new_pass = st.text_input("Ustaw hasło dla profilu:", type="password", placeholder="Wpisz silne hasło...")
            submit_pass = st.form_submit_button("🔒 Aktywuj hasło")
            if submit_pass and new_pass.strip():
                st.session_state.global_store["user_data"][current_user]["password"] = new_pass.strip()
                save_global_data(st.session_state.global_store)
                st.session_state.account_authenticated = True
                components.html(f'<script>localStorage.setItem("auth_{current_user}", "true");</script>', height=0, width=0)
                st.success("Hasło zostało pomyślnie ustawione!")
                st.rerun()
    else:
        st.success("🔒 Twoje konto jest chronione hasłem.")
        if st.button("❌ Usuń hasło (logowanie samym kluczem)", type="primary", key="delete_password_completely"):
            st.session_state.global_store["user_data"][current_user]["password"] = ""
            save_global_data(st.session_state.global_store)
            st.session_state.account_authenticated = False
            components.html(f'<script>localStorage.removeItem("auth_{current_user}");</script>', height=0, width=0)
            st.rerun()
            
    st.write("---")
    st.subheader("Twoje własne ustawienia kolorów")
    
    if is_staff: 
        cc_col1, cc_col2, cc_col3, cc_col4 = st.columns(4)
    else: 
        cc_col1, cc_col2, cc_col3 = st.columns(3); cc_col4 = None
        
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
    if cc_col4:
        with cc_col4:
            chosen_bar_color = st.color_picker("Twój pasek na czacie:", value=staff_bar_color, key="user_staff_bar_picker")
            if chosen_bar_color != staff_bar_color:
                st.session_state.global_store["user_data"][current_user]["staff_bar_color"] = chosen_bar_color
                save_global_data(st.session_state.global_store)
                st.rerun()

    # --- PANEL UPRAWNIEŃ (ZARZĄDZANIE SYSTEMEM PRZEZ KADRĘ) ---
    current_role = st.session_state.get("emulated_role", "")

    if is_admin or is_moderator:
        st.write("---")
        st.subheader("👑 Panel Zarządzania Systemem (Widoczne tylko dla Kadry)")
        
        # Ograniczenie zakładek dla promowanych adminów z nadania oraz moderatorów
        if is_admin and current_role == "Właściciel/Admin (Domyślny)": 
            if can_user_reset_passwords:
                adm_tabs = st.tabs(["👥 Moderatorzy", "🛡️ Administratorzy", "🌟 Ranga VIP", "🔑 Resetowanie Haseł"])
            else:
                adm_tabs = st.tabs(["👥 Moderatorzy", "🛡️ Administratorzy", "🌟 Ranga VIP"])
        else: 
            adm_tabs = st.tabs(["🌟 Zarządzanie VIP"])
            
        # --- BLOK DLA PEŁNEGO / WYŻSZEGO STAFFU (Właściciel / Admin w trybie domyślnym) ---
        if is_admin and current_role == "Właściciel/Admin (Domyślny)":
            
            # --- ZAKŁADKA 1: MODERATORZY ---
            with adm_tabs[0]:
                current_mods = st.session_state.global_store.get("moderators", [])
                
                with st.form("add_moderator_form", clear_on_submit=True):
                    mod_key_input = st.text_input("Wklej klucz konta, które chcesz awansować na Moderatora:")
                    submit_mod = st.form_submit_button("➕ Nadaj uprawnienia moderatora")
                    if submit_mod and mod_key_input.strip():
                        target_key = mod_key_input.strip()
                        target_user_profile = st.session_state.global_store.get("user_data", {}).get(target_key, {})
                        target_password = target_user_profile.get("password", "").strip()
                        
                        if target_key == "admin" or target_key in st.session_state.global_store.get("admins", []): st.error("❌ Wyższa ranga.")
                        elif target_key in current_mods: st.warning("⚠️ Już jest mod.")
                        elif not target_password: st.error("❌ Błąd bezpieczeństwa: Użytkownik musi najpierw ustawić hasło na swoim koncie, aby otrzymać rangę Moderatora!")
                        else:
                            current_data = load_global_data()
                            if "moderators" not in current_data: current_data["moderators"] = []
                            current_data["moderators"].append(target_key)
                            if "vips" in current_data and target_key in current_data["vips"]: current_data["vips"].remove(target_key)
                            save_global_data(current_data)
                            st.session_state.global_store = current_data
                            st.success(f"✅ Nadano rangę Moderatora dla `{target_key}`")
                            st.rerun()
                            
                if current_mods:
                    for m_idx, m_key in enumerate(current_mods):
                        m_col1, m_col2 = st.columns([4.0, 2.0])
                        with m_col1:
                            u_nick = st.session_state.global_store["user_data"].get(m_key, {}).get("saved_nick", "")
                            is_temp = st.session_state.global_store["user_data"].get(m_key, {}).get("is_temporary", False)
                            badge_temp = " ⏳ [KONTO TESTOWE]" if is_temp else ""
                            st.markdown(f"🔑 `{m_key}`" + (f" (Podpis: **{u_nick}**)" if u_nick else "") + badge_temp)
                        with m_col2:
                            if st.button("❌ Odbierz rangę MOD", key=f"remove_mod_{m_idx}", type="primary", use_container_width=True):
                                current_data = load_global_data()
                                if m_key in current_data.get("moderators", []): current_data["moderators"].remove(m_key)
                                save_global_data(current_data)
                                st.session_state.global_store = current_data
                                st.rerun()

            # --- ZAKŁADKA 2: ADMINISTRATORZY ---
            with adm_tabs[1]:
                current_admins = st.session_state.global_store.get("admins", [])

                # Blok przydzielania uprawnień (Tylko dla głównego konta "admin")
                if is_real_root_admin and current_admins:
                    st.markdown("#### 🔑 Przydziel uprawnienia do resetowania haseł")
                    wybrany_admin = st.selectbox("Wybierz administratora z nadania:", current_admins, key="root_select_admin_for_perms")
                    
                    if wybrany_admin:
                        admin_prof_data = st.session_state.global_store["user_data"].get(wybrany_admin, {})
                        current_reset_perm = admin_prof_data.get("can_reset_passwords", False)
                        checkbox_reset_perm = st.checkbox("Zezwól temu administratorowi na resetowanie haseł", value=current_reset_perm, key="root_checkbox_reset_perm")
                        
                        if st.button(f"Zapisz uprawnienia dla {wybrany_admin}", key="save_admin_perms_btn"):
                            current_data = load_global_data()
                            if wybrany_admin in current_data["user_data"]:
                                current_data["user_data"][wybrany_admin]["can_reset_passwords"] = checkbox_reset_perm
                                save_global_data(current_data)
                                st.session_state.global_store = current_data
                                st.success(f"✅ Zaktualizowano uprawnienia dla administratora: **{wybrany_admin}**!")
                                st.rerun()
                    st.write("---")
                
                # Formularz nadawania rangi ADMIN (Ukryty dla adminów z nadania)
                if is_real_root_admin:
                    with st.form("add_admin_form", clear_on_submit=True):
                        adm_key_input = st.text_input("Wklej klucz konta, które chcesz awansować na Administratora:")
                        submit_adm = st.form_submit_button("👑 Nadaj uprawnienia administratora")
                        if submit_adm and adm_key_input.strip():
                            target_key = adm_key_input.strip()
                            target_user_profile = st.session_state.global_store.get("user_data", {}).get(target_key, {})
                            target_password = target_user_profile.get("password", "").strip()
                            
                            if target_key != "admin" and target_key not in current_admins:
                                if not target_password:
                                    st.error("❌ Błąd bezpieczeństwa: Użytkownik musi najpierw ustawić hasło na swoim koncie, aby otrzymać rangę Administratora!")
                                else:
                                    current_data = load_global_data()
                                    if "admins" not in current_data: current_data["admins"] = []
                                    current_data["admins"].append(target_key)
                                    if "moderators" in current_data and target_key in current_data["moderators"]: current_data["moderators"].remove(target_key)
                                    if "vips" in current_data and target_key in current_data["vips"]: current_data["vips"].remove(target_key)
                                    save_global_data(current_data)
                                    st.session_state.global_store = current_data
                                    st.success(f"🛡️ Nadano rangę Administratora dla `{target_key}`")
                                    st.rerun()
                else:
                    st.info("ℹ️ Jako administrator z nadania nie posiadasz uprawnień do tworzenia oraz mianowania nowych administratorów.")
                            
                if current_admins:
                    st.markdown("#### Zarejestrowani Administratorzy:")
                    for a_idx, a_key in enumerate(current_admins):
                        a_col1, a_col2 = st.columns([4.0, 2.0])
                        with a_col1:
                            u_nick = st.session_state.global_store["user_data"].get(a_key, {}).get("saved_nick", "")
                            is_temp = st.session_state.global_store["user_data"].get(a_key, {}).get("is_temporary", False)
                            badge_temp = " ⏳ [TEST]" if is_temp else ""
                            has_reset_badge = " [🔑 Ma dostęp do resetu]" if st.session_state.global_store["user_data"].get(a_key, {}).get("can_reset_passwords", False) else ""
                            st.markdown(f"🛡️ `{a_key}`" + (f" (Podpis: **{u_nick}**)" if u_nick else "") + f"<span style='color: #5cb85c; font-weight: bold;'>{has_reset_badge}</span>" + badge_temp, unsafe_allow_html=True)
                        with a_col2:
                            if is_real_root_admin:
                                if st.button("❌ Odbierz rangę ADMIN", key=f"remove_adm_{a_idx}", type="primary", use_container_width=True):
                                    current_data = load_global_data()
                                    if a_key in current_data.get("admins", []): current_data["admins"].remove(a_key)
                                    if a_key in current_data["user_data"]: current_data["user_data"][a_key]["can_reset_passwords"] = False
                                    save_global_data(current_data)
                                    st.session_state.global_store = current_data
                                    st.rerun()
                            else:
                                st.button("🔒 Zablokowane", key=f"disabled_strip_adm_{a_idx}", disabled=True, use_container_width=True)

            # --- ZAKŁADKA 4: RESETOWANIE HASEŁ (Dynamicznie ukrywana) ---
            if can_user_reset_passwords:
                with adm_tabs[3]:
                    st.markdown("### 🔒 Skrzynka próśb o reset haseł")
                    resets_list = st.session_state.global_store.get("password_resets", [])
                    with st.container(height=220):
                        if not resets_list: st.caption("Brak nowych próśb.")
                        else:
                            for r_reversed_idx, req in enumerate(reversed(resets_list)):
                                orig_req_idx = len(resets_list) - 1 - r_reversed_idx
                                r_col1, r_col2 = st.columns([4.2, 1.8])
                                with r_col1:
                                    st.markdown(f"""
                                        <div style="background-color: rgba(255,0,0,0.06); padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #FF0000;">
                                            <span style="color: #FF0000; font-weight: bold;">👤 Kto: {req.get('sender_nick')}</span>
                                            <span style="font-size: 0.75rem; opacity: 0.5; margin-left: 10px;">Klucz: `{req.get('author_key')}`</span>
                                            <p style="margin: 4px 0 0 0; font-size: 0.95rem;">{req.get('text')}</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                                with r_col2:
                                    if st.button("🗑️ Odrzuć / Usuń", key=f"del_req_{orig_req_idx}", type="primary", use_container_width=True):
                                        current_data = load_global_data()
                                        if orig_req_idx < len(current_data["password_resets"]):
                                            current_data["password_resets"].pop(orig_req_idx)
                                            save_global_data(current_data)
                                            st.session_state.global_store = current_data
                                            st.rerun()

                    st.write("---")
                    with st.form("reset_user_password_form", clear_on_submit=True):
                        reset_key = st.text_input("1. Klucz konta użytkownika (ID):")
                        reset_code = st.text_input("2. Przepisany 6-cyfrowy Kod Bezpieczeństwa:")
                        submit_reset = st.form_submit_button("💥 Całkowicie usuń hasło profilu")
                        if submit_reset:
                            rk, rc = reset_key.strip(), reset_code.strip()
                            if rk in st.session_state.global_store.get("user_data", {}) and rc == generate_account_secure_code(rk):
                                current_data = load_global_data()
                                current_data["user_data"][rk]["password"] = ""
                                current_data["password_resets"] = [m for m in current_data["password_resets"] if m.get("author_key") != rk]
                                save_global_data(current_data)
                                st.session_state.global_store = current_data
                                st.success("Hasło skasowane!")
                                st.rerun()

        # --- SEKCJA: ZARZĄDZANIE VIP (Widoczne dla całej kadry) ---
        vip_tab_target = adm_tabs[2] if (is_admin and current_role == "Właściciel/Admin (Domyślny)") else adm_tabs[0]
        
        with vip_tab_target:
            current_vips = st.session_state.global_store.get("vips", [])
            
            with st.form("add_vip_real_fixed_form", clear_on_submit=True):
                st.markdown("#### 🌟 Nadaj rangę VIP (Uprawnienie Kadry)")
                vip_key_input = st.text_input("Wklej klucz konta, które chcesz awansować na VIP-a:")
                submit_vip = st.form_submit_button("🌟 Zatwierdź status VIP")
                
                if submit_vip and vip_key_input.strip():
                    target_key = vip_key_input.strip()
                    target_user_profile = st.session_state.global_store.get("user_data", {}).get(target_key, {})
                    target_password = target_user_profile.get("password", "").strip()
                    
                    if target_key == "admin" or target_key in st.session_state.global_store.get("admins", []) or target_key in st.session_state.global_store.get("moderators", []):
                        st.error("❌ Ta osoba posiada już rangę w strukturze kadry (posiada już wbudowany dostęp do Kodu 3).")
                    elif target_key in current_vips:
                        st.warning("⚠️ Ten użytkownik ma już status VIP.")
                    elif not target_password:
                        st.error("❌ Błąd bezpieczeństwa: Użytkownik musi posiadać ustawione hasło na profilu przed nadaniem rangi VIP!")
                    else:
                        current_data = load_global_data()
                        if "vips" not in current_data: current_data["vips"] = []
                        current_data["vips"].append(target_key)
                        save_global_data(current_data)
                        st.session_state.global_store = current_data
                        st.success(f"✅ Sukces! Nadano rangę VIP dla `{target_key}`. Użytkownik uzyskał dostęp do Kodu 3.")
                        st.rerun()
                        
            if current_vips:
                st.markdown("---")
                st.markdown("#### Zarejestrowani członkowie VIP:")
                for v_idx, v_key in enumerate(current_vips):
                    v_col1, v_col2 = st.columns([4.0, 2.0])
                    with v_col1:
                        v_nick = st.session_state.global_store["user_data"].get(v_key, {}).get("saved_nick", "")
                        is_temp = st.session_state.global_store["user_data"].get(v_key, {}).get("is_temporary", False)
                        badge_temp = " ⏳ [TEST]" if is_temp else ""
                        st.markdown(f"🌟 `{v_key}`" + (f" (Podpis: **{v_nick}**)" if v_nick else "") + badge_temp)
                    with v_col2:
                        if st.button("❌ Odbierz rangę VIP", key=f"remove_vip_act_{v_idx}", type="primary", use_container_width=True):
                            current_data = load_global_data()
                            if v_key in current_data.get("vips", []): current_data["vips"].remove(v_key)
                            save_global_data(current_data)
                            st.session_state.global_store = current_data
                            st.rerun()

        # --- SEKCJA: MODYFIKACJA KOLORÓW (Widoczna dla całej kadry: Admin i Mod) ---
        st.write("---")
        st.markdown("#### 🎨 Modyfikacja Domyślnych Barw Aplikacji (Dla nowych użytkowników)")
        adm_cc1, adm_cc2, adm_cc3 = st.columns(3)
        with adm_cc1: new_def_theme = st.color_picker("Domyślny przycisk wyboru:", value=def_theme, key="staff_def_theme")
        with adm_cc2: new_def_bg = st.color_picker("Domyślne tło aplikacji:", value=def_bg, key="staff_def_bg")
        with adm_cc3: new_def_clear = st.color_picker("Domyślne przyciski akcji:", value=def_clear, key="staff_def_clear")
        
        if (new_def_theme != def_theme) or (new_def_bg != def_bg) or (new_def_clear != def_clear):
            current_data = load_global_data()
            current_data["default_theme_color"], current_data["default_bg_color"], current_data["default_clear_btn_color"] = new_def_theme, new_def_bg, new_def_clear
            save_global_data(current_data)
            st.session_state.global_store = current_data
            st.rerun()

    st.write("---")
    st.write("**Twój unikalny klucz konta:**")
    st.code(st.session_state.user_author_key, language="text")
    
    new_nick = st.text_input("Zmień swój stały podpis (nick):", value=user_saved_nick)
    if new_nick != user_saved_nick:
        st.session_state.global_store["user_data"][current_user]["saved_nick"] = new_nick.strip()
        save_global_data(st.session_state.global_store)
        st.rerun()

# --- FORMULARZ DODAWANIA KOMENTARZY ---
with st.form("comment_form", clear_on_submit=True):
    default_author = user_saved_nick if user_saved_nick else ""
    nick = st.text_input("Twój podpis/nick:", value=default_author, placeholder="Anonim")
    komentarz_tekst = st.text_area("Napisz komentarz o stronie:")
    wyslij = st.form_submit_button("Dodaj komentarz")
    
    if wyslij and komentarz_tekst.strip():
        podpis = nick.strip() if nick.strip() else "Anonim"
        ranga_label = " Właściciel" if current_user == "admin" else (" Admin" if current_user in st.session_state.global_store.get("admins", []) else (" Moderator" if current_user in st.session_state.global_store.get("moderators", []) else (" VIP 🌟" if current_user in st.session_state.global_store.get("vips", []) else "")))
        nowy_komentarz_tekst = f"**{podpis}{ranga_label}** | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}:\n{komentarz_tekst.strip()}"
        nowy_komentarz_obj = {"text": nowy_komentarz_tekst, "author_key": current_user}
        current_data = load_global_data()
        current_data["comments"].insert(0, nowy_komentarz_obj)
        save_global_data(current_data)
        st.session_state.global_store = current_data
        st.rerun()

# --- WYŚWIETLANIE KOMENTARZY (POPRAWKA: Usunięto przycisk masowego usuwania) ---
comments_list = st.session_state.global_store.get("comments", [])
if comments_list:
    for idx, com in enumerate(comments_list):
        if isinstance(com, dict) and "text" in com:
            cc1, cc2 = st.columns([4.8, 1.2])
            with cc1: st.info(com["text"])
            with cc2:
                if is_staff or is_real_admin:
                    if st.button("🗑️ Usuń (STAFF)", key=f"del_com_{idx}", type="primary", use_container_width=True):
                        current_data = load_global_data()
                        current_data["comments"].pop(idx)
                        save_global_data(current_data)
                        st.session_state.global_store = current_data
                        st.rerun()
                elif com.get("author_key") == current_user and current_user not in ["", "anonymous", "legacy"]:
                    if st.button("❌ Usuń", key=f"del_com_{idx}", type="primary", use_container_width=True):
                        current_data = load_global_data()
                        current_data["comments"].pop(idx)
                        save_global_data(current_data)
                        st.session_state.global_store = current_data
                        st.rerun()

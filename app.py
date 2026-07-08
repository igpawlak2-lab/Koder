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
        "announcement": "Brak aktualnych ogzeń.",  
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
                    
               
        # Szybkie automatyczne logowanie na istniejące, aktywne konta czasowe  
        active_temporary_accounts = [k for k, v in current_data.get("user_data", {}).items() if v.get("is_temporary")]  
          
        if active_temporary_accounts:  
            st.markdown("##### ⏱️ Szybkie logowanie na konta testowe (odliczanie na żywo):")  
              
            # Tworzymy izolowany fragment, który odświeża tylko przyciski czasowe  
            @st.fragment(run_every=1.0)  
            def render_countdown_buttons(accounts, data):  
                to_log_cols = st.columns(min(len(accounts), 3))  
                for t_idx, t_key in enumerate(accounts):  
                    col_target = to_log_cols[t_idx % 3]  
                      
                    # OBLICZANIE CZASU  
                    t_prof = data["user_data"][t_key]  
                    rem_seconds = int(t_prof.get("expire_at", 0) - time.time())  
                      
                    if rem_seconds > 0:  
                        time_label = f"{rem_seconds // 60}m {rem_seconds % 60}s"  
                    else:  
                        time_label = "Wygasło"  
                      
                    with col_target:  
                        if st.button(f"👤 {t_key}\n⏳ {time_label}", key=f"quick_log_tmp_{t_key}_{t_idx}", use_container_width=True):  
                            st.session_state["emulated_from_admin2"] = True  
                            st.session_state.user_author_key = t_key  
                            st.query_params["ak"] = t_key  
                            st.query_params["auth"] = "true"  
                            st.rerun()  
  
            # Wywołanie fragmentu  
            render_countdown_buttons(active_temporary_accounts, current_data)  
    
        st.write("---")    
    
        # --- ZARZĄDZANIE RANGAMI ---    
        st.markdown("### 👑 Zarządzanie Rangami (Admin/Mod/VIP)")    
        with st.form("admin2_grant_roles_form", clear_on_submit=True):    
            target_key_a2 = st.text_input("Wpisz klucz konta (ID) użytkownika:").strip()    
            chosen_role_a2 = st.selectbox("Wybierz docelową rangę:",   
                                         ["Odbierz wszystkie rangi (Zwykły Użytkownik)", "VIP", "Moderator", "Administrator"])    
            submit_role_a2 = st.form_submit_button("⚡ Zastosuj zmiany w rangach")    
                
            if submit_role_a2 and target_key_a2:    
                if target_key_a2 in current_data.get("user_data", {}):    
                    # Czyszczenie ze wszystkich list ról (zawsze wykonujemy jako reset)  
                    if target_key_a2 in current_data.get("admins", []): current_data["admins"].remove(target_key_a2)    
                    if target_key_a2 in current_data.get("moderators", []): current_data["moderators"].remove(target_key_a2)    
                    if target_key_a2 in current_data.get("vips", []): current_data["vips"].remove(target_key_a2)    
                        
                    # Nadawanie nowej rangi  
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
                    st.success(f"✅ Ranga dla `{target_key_a2}` zaktualizowana do: **{chosen_role_a2}**")    
                    st.rerun()  
                else:    
                    st.error("❌ Podane konto nie istnieje.")    
  
        # --- ROZWIJANA LISTA CAŁEJ KADRY SYSTEMU ---  
        with st.expander("👥 Zwiń/Rozwiń pełną listę kadry i osób uprzywilejowanych", expanded=True):  
            st.markdown("##### Aktualni Administratorzy, Moderatorzy i członkowie VIP:")  
              
            list_of_admins = current_data.get("admins", [])  
            list_of_mods = current_data.get("moderators", [])  
            list_of_vips = current_data.get("vips", [])  
              
            all_staff_members = []  
            for adm in list_of_admins: all_staff_members.append({"id": adm, "role": "Administrator", "color": "red"})  
            for mod in list_of_mods: all_staff_members.append({"id": mod, "role": "Moderator", "color": "orange"})  
            for vp in list_of_vips: all_staff_members.append({"id": vp, "role": "VIP", "color": "purple"})  
              
            if not all_staff_members:  
                st.caption("Brak przypisanych rang specjalnych w systemie (wszyscy są zwykłymi użytkownikami).")  
            else:  
                for s_idx, member in enumerate(all_staff_members):  
                    m_id = member["id"]  
                    m_role = member["role"]  
                    m_color = member["color"]  
                      
                    u_profile = current_data.get("user_data", {}).get(m_id, {})  
                    m_nick = u_profile.get("saved_nick", m_id)  
                      
                    sc1, sc2 = st.columns([4.5, 1.5])  
                    with sc1:  
                        st.markdown(f"🆔 ID: `{m_id}` | Nazwa: **{m_nick}** — Ranga: :{m_color}[**{m_role}**]")  
                    with sc2:  
                        if st.button("🔴 Degraduj", key=f"deg_btn_{m_id}_{s_idx}", type="secondary", use_container_width=True):  
                            if m_id in current_data.get("admins", []): current_data["admins"].remove(m_id)  
                            if m_id in current_data.get("moderators", []): current_data["moderators"].remove(m_id)  
                            if m_id in current_data.get("vips", []): current_data["vips"].remove(m_id)  
                              
                            save_global_data(current_data); st.session_state.global_store = current_data  
                            st.error(f"Odebrano uprawnienia dla konta `{m_id}`!")  
                            st.rerun()  
  
        st.write("---")    
    
        # --- NIEZALEŻNY PANEL RESETU HASEŁ (DLA KAŻDEJ RANGI) ---    
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
  
        # --- PRZYWRÓCONE: SPRAWDZANIE KODU BEZPIECZEŃSTWA I STATUSU RESETU ---  
        st.write("")  
        st.markdown("##### 🔑 Sprawdzanie kodu bezpieczeństwa i statusu resetu konta:")  
          
        chk_user_key = st.text_input("Wpisz klucz użytkownika (login) do sprawdzenia:", key="admin2_check_sec_user")  
          
        if st.button("🔍 Sprawdź kod i zgłoszenia resetu", key="admin2_btn_check_sec", type="secondary"):  
            if chk_user_key:  
                all_users = current_data.get("user_data", {})  
                if chk_user_key in all_users:  
                    u_prof = all_users[chk_user_key]  
                      
                    expected_sec_code = generate_account_secure_code(chk_user_key)  
                    st.success(f"👤 Konto: **{chk_user_key}** | Prawidłowy kod bezpieczeństwa: ` {expected_sec_code} `")  
                      
                    resets_list_a2 = current_data.get("password_resets", [])  
                    user_requests = [req for req in resets_list_a2 if req.get('author_key') == chk_user_key]  
                      
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
        st.write("---")    
    
        # --- NIEZALEŻNY PANEL RESETU HASEŁ ---    
        st.write("---")    
    
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
    except:  
        return "#FFFFFF"  
  
text_color = get_contrast_text_color(theme_color)  
clear_btn_text_color = get_contrast_text_color(clear_btn_color)  
main_text_theme = get_contrast_text_color(bg_color)  
  
# --- STYLOWANIE INTERFEJSU CSS ---  
st.markdown(f"""  
 <style>  
 .stApp {{  
 background-color: {bg_color} !important;  
 }}  
 .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label {{  
 color: {main_text_theme} !important;  
 }}  
 @media (max-width: 768px) {{  
 [data-testid="stHorizontalBlock"] {{  
 flex-direction: column !important;  
 }}  
 [data-testid="stHorizontalBlock"] > div {{  
 width: 100% !important;  
 margin-bottom: 12px !important;  
 }}  
 }}  
 div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div {{  
 display: flex;  
 gap: 10px;  
 margin-top: 5px;  
 width: 100%;  
 }}  
 div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label {{  
 background-color: {"#262730" if main_text_theme == "#FFFFFF" else "#F0F2F6"} !important;  
 border: 2px solid {"#434654" if main_text_theme == "#FFFFFF" else "#E0E2E6"} !important;  
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
 color: {main_text_theme} !important;  
 }}  
 div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label div[data-testid="stMarkdownContainer"]::before {{  
 display: none !important;  
 }}  
 div[data-testid="stRadio"] input[type="radio"] {{  
 display: none;  
 }}  
 div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label:has(input:checked) {{  
 background-color: {theme_color} !important;  
 color: {text_color} !important;  
 border-color: {theme_color} !important;  
 box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);  
 }}  
 div[data-testid="stRadio"] [data-testid="stWidgetLabel"] + div label:has(input:checked) div[data-testid="stMarkdownContainer"] {{  
 color: {text_color} !important;  
 }}  
 div.stButton > button {{  
 background-color: {clear_btn_color} !important;  
 color: {clear_btn_text_color} !important;  
 border: 2px solid {clear_btn_color} !important;  
 border-radius: 8px !important;  
 font-weight: bold !important;  
 box-shadow: 0px 2px 5px rgba(0,0,0,0.1) !important;  
 transition: all 0.2s ease-in-out !important;  
 }}  
 .stApp div.stButton > button p, .stApp div.stButton > button div, .stApp div.stButton > button span {{  
 color: {clear_btn_text_color} !important;  
 }}  
 div.stButton > button:hover {{  
 background-color: {clear_btn_color} !important;  
 opacity: 0.85 !important;  
 border-color: {clear_btn_color} !important;  
 transform: scale(1.01);  
 }}  
 div[data-testid="stVerticalBlockBorderWrapper"] {{  
 border-color: {theme_color} !important;  
 border-radius: 12px;  
 background-color: {"#1E1E1E" if main_text_theme == "#FFFFFF" else "#F9FAFB"};  
 }}  
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
    st.stop()


# ==============================================================================
# --- IZOLOWANY FRAGMENT MONITORUJĄCY NOWE WPISY (DLA WSZYSTKICH CZATÓW) ---
# ==============================================================================
@st.fragment(run_every=2.0)
def system_powiadomien_globalnych():
    """Funkcja działająca asynchronicznie w tle, sprawdzająca nowości"""
    dane = load_global_data()
    
    czaty = {
        "Czat Staff": "staff_chat",
        "Wsparcie": "support_chat",
        "Komentarze": "comments"
    }
    
    aktualna_liczba = 0
    ostatnia_tresc = ""
    ostatni_autor = ""
    zrodlo_powiadomienia = "System"
    
    for nazwa_wyswietlana, klucz_bazy in czaty.items():
        lista_msg = dane.get(klucz_bazy, [])
        aktualna_liczba += len(lista_msg)
        
        # Pobieranie danych najnowszej wiadomości (indeks 0 z insert(0))
        if lista_msg and not ostatnia_tresc:
            ostatnia = lista_msg[0]
            if isinstance(ostatnia, dict):
                ostatnia_tresc = ostatnia.get("text", ostatnia.get("tresc", "Wysłał nową wiadomość"))
                ostatni_autor = ostatnia.get("sender_nick", ostatnia.get("author", "Użytkownik"))
                zrodlo_powiadomienia = nazwa_wyswietlana

    # Inicjalizacja liczników sesji
    if "globalny_licznik_powiadomien" not in st.session_state:
        st.session_state.globalny_licznik_powiadomien = aktualna_liczba
        # Skrypt żądający uprawnień desktopowych raz przy wejściu na stronę
        components.html("""
            <script>
            if ("Notification" in window && Notification.permission !== "granted" && Notification.permission !== "denied") {
                Notification.requestPermission();
            }
            </script>
        """, height=0, width=0)
    else:
        # Sprawdzamy czy przyby

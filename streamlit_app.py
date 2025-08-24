import streamlit as st
import sqlite3
from contextlib import closing
from datetime import datetime
import pandas as pd
import yaml
import base64

DB_PATH = "ism_partners.db"
USERS_PATH = "users.yaml"

# Expected columns for partners import / form
EXPECTED = ["company_name","address","number","postal_code","city","phone",
            "employees_count","website","responsible","role","email","activity","sector_class","tags"]

HEADER_MAP = {
    "company_name": ["nom","nom de l’entreprise","nom de l'entreprise","entreprise","company"],
    "address": ["adresse","rue"],
    "number": ["numéro","numero","n°","num"],
    "postal_code": ["code postal","cp"],
    "city": ["localité","ville","commune","localite"],
    "phone": ["téléphone","telephone","tel"],
    "employees_count": ["personnes employées (nombre)","effectif","nb employés","nb employes","employés","employes"],
    "website": ["site internet","site web","site","url"],
    "responsible": ["responsable","nom du contact","contact"],
    "role": ["fonction","titre","poste"],
    "email": ["e-mail","email","mail","e-mail 1","email 1","mail 1"],
    "activity": ["activité","activite"],
    "sector_class": ["classification sectorielle","secteur","categorie","catégorie"],
    "tags": ["tags","mots-clés","mots cles"]
}

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def ensure_schema():
    """Create tables if needed and run additive migrations (no data loss)."""
    schema = '''
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        address TEXT,
        number TEXT,
        postal_code TEXT,
        city TEXT,
        phone TEXT,
        employees_count INTEGER,
        website TEXT,
        responsible TEXT,
        role TEXT,
        email TEXT,
        activity TEXT,
        sector_class TEXT,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partner_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        function TEXT,
        email TEXT,
        phone TEXT,
        mobile TEXT,
        is_jury INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (partner_id) REFERENCES partners(id) ON DELETE CASCADE
    );
    '''
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.executescript(schema)
        # Add missing columns to partners if table exists with older schema
        cur.execute("PRAGMA table_info(partners)")
        existing = {row[1] for row in cur.fetchall()}
        wanted = {
            "company_name":"TEXT","address":"TEXT","number":"TEXT","postal_code":"TEXT",
            "city":"TEXT","phone":"TEXT","employees_count":"INTEGER","website":"TEXT",
            "responsible":"TEXT","role":"TEXT","email":"TEXT","activity":"TEXT",
            "sector_class":"TEXT","tags":"TEXT","created_at":"TIMESTAMP"
        }
        for col, ctype in wanted.items():
            if col not in existing:
                cur.execute(f"ALTER TABLE partners ADD COLUMN {col} {ctype}")
        # Create contacts table if missing
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contacts'")
        if cur.fetchone() is None:
            cur.execute('''
                CREATE TABLE contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER NOT NULL,
                    full_name TEXT NOT NULL,
                    function TEXT,
                    email TEXT,
                    phone TEXT,
                    mobile TEXT,
                    is_jury INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (partner_id) REFERENCES partners(id) ON DELETE CASCADE
                )
            ''')
        conn.commit()

@st.cache_data(show_spinner=False)
def run_query(query, params=()):
    with closing(get_conn()) as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df

def exec_sql(query, params=()):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return cur.lastrowid

def upsert_partner(values, partner_id=None):
    fields = EXPECTED
    if partner_id:
        setters = ", ".join([f"{f}=?" for f in fields])
        params = [values.get(f) for f in fields] + [partner_id]
        exec_sql(f"UPDATE partners SET {setters} WHERE id=?", params)
        return partner_id
    else:
        cols = ", ".join(fields)
        placeholders = ", ".join(["?"]*len(fields))
        params = [values.get(f) for f in fields]
        return exec_sql(f"INSERT INTO partners ({cols}) VALUES ({placeholders})", params)

def delete_partner(pid):
    exec_sql("DELETE FROM partners WHERE id=?", (pid,))

# Contacts CRUD
def list_contacts(partner_id:int):
    return run_query("SELECT * FROM contacts WHERE partner_id=? ORDER BY full_name", (partner_id,))

def upsert_contact(values, contact_id=None):
    fields = ["partner_id","full_name","function","email","phone","mobile","is_jury","notes"]
    if contact_id:
        setters = ", ".join([f"{f}=?" for f in fields[1:]])  # exclude partner_id
        params = [values.get(f) for f in fields[1:]] + [contact_id]
        exec_sql(f"UPDATE contacts SET {setters} WHERE id=?", params)
        return contact_id
    else:
        cols = ", ".join(fields)
        placeholders = ", ".join(["?"]*len(fields))
        params = [values.get(f) for f in fields]
        return exec_sql(f"INSERT INTO contacts ({cols}) VALUES ({placeholders})", params)

def delete_contact(cid):
    exec_sql("DELETE FROM contacts WHERE id=?", (cid,))

def load_users():
    try:
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

def authenticate(email, password, users):
    if not email or not password:
        return False
    user = users.get(email.strip().lower())
    return user and user.get("password") == password

def login(users):
    st.sidebar.header("Connexion enseignant")
    email = st.sidebar.text_input("Adresse e-mail", key="login_email")
    pwd = st.sidebar.text_input("Mot de passe", type="password", key="login_pwd")
    if st.sidebar.button("Se connecter"):
        if authenticate(email, pwd, users):
            st.session_state["user_email"] = email.strip().lower()
            st.success("Connexion réussie.")
        else:
            st.error("Identifiants invalides.")
    if "user_email" in st.session_state:
        st.sidebar.success(f"Connecté: {st.session_state['user_email']}")
        if st.sidebar.button("Se déconnecter"):
            st.session_state.pop("user_email")
            st.rerun()

def download_db_button():
    """Show a backup download link in the sidebar when logged in."""
    try:
        with open(DB_PATH, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:file/sqlite;base64,{b64}" download="ism_partners_backup.db">📥 Télécharger la base SQLite</a>'
        st.sidebar.markdown("### Sauvegarde")
        st.sidebar.markdown(href, unsafe_allow_html=True)
    except FileNotFoundError:
        st.sidebar.error("Base de données introuvable.")

# ---------- UI HELPERS (navigation) ----------
def set_view(view:str, partner_id:int|None=None):
    st.session_state["view"] = view
    if partner_id is not None:
        st.session_state["selected_partner_id"] = int(partner_id)

def get_view():
    return st.session_state.get("view","list")

def get_selected_partner():
    pid = st.session_state.get("selected_partner_id")
    if pid is None:
        return None
    df = run_query("SELECT * FROM partners WHERE id=?", (pid,))
    if df.empty:
        return None
    return df.iloc[0].to_dict()

# ---------- FORMS ----------
def partner_form(existing=None):
    st.markdown("### Fiche partenaire")
    with st.form("partner_form", clear_on_submit=False):
        company_name = st.text_input("Nom de l’entreprise *", value=(existing or {}).get("company_name",""))
        c1, c2, c3 = st.columns(3)
        with c1:
            address = st.text_input("Adresse", value=(existing or {}).get("address",""))
            postal_code = st.text_input("Code postal", value=(existing or {}).get("postal_code",""))
            phone = st.text_input("Téléphone", value=(existing or {}).get("phone",""))
            website = st.text_input("Site internet", value=(existing or {}).get("website",""))
        with c2:
            number = st.text_input("Numéro", value=(existing or {}).get("number",""))
            city = st.text_input("Localité", value=(existing or {}).get("city",""))
            employees_count = st.number_input("Personnes employées (nombre)", min_value=0, value=int((existing or {}).get("employees_count") or 0))
            activity = st.text_input("Activité", value=(existing or {}).get("activity",""))
        with c3:
            responsible = st.text_input("Responsable", value=(existing or {}).get("responsible",""))
            role = st.text_input("Fonction", value=(existing or {}).get("role",""))
            email = st.text_input("E-mail", value=(existing or {}).get("email",""))
            sector_class = st.text_input("Classification sectorielle", value=(existing or {}).get("sector_class",""))
        tags = st.text_input("Tags (séparés par des virgules)", value=(existing or {}).get("tags",""))

        submitted = st.form_submit_button("Enregistrer")
        if submitted:
            if not company_name.strip():
                st.error("Le nom de l’entreprise est obligatoire.")
            else:
                payload = {
                    "company_name": company_name.strip(),
                    "address": address.strip(),
                    "number": number.strip(),
                    "postal_code": postal_code.strip(),
                    "city": city.strip(),
                    "phone": phone.strip(),
                    "employees_count": int(employees_count),
                    "website": website.strip(),
                    "responsible": responsible.strip(),
                    "role": role.strip(),
                    "email": email.strip(),
                    "activity": activity.strip(),
                    "sector_class": sector_class.strip(),
                    "tags": tags.strip()
                }
                pid = (existing or {}).get("id")
                pid = upsert_partner(payload, partner_id=pid)
                st.success("Partenaire enregistré.")
                set_view("detail", pid)
                st.rerun()

def contacts_block(partner_id:int):
    st.markdown("### Contacts du partenaire")
    dfc = list_contacts(partner_id)
    if dfc.empty:
        st.info("Aucun contact pour l’instant.")
    else:
        st.dataframe(dfc[["id","full_name","function","email","phone","mobile","is_jury","notes"]], use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### Ajouter / modifier un contact")
    with st.form("contact_form", clear_on_submit=False):
        mode = st.radio("Mode", ["Ajouter", "Modifier"], horizontal=True, key="contact_mode")
        if mode == "Modifier" and not dfc.empty:
            contact_options = {f"{r['full_name']} (#{r['id']})": int(r['id']) for _, r in dfc.iterrows()}
            selected_label = st.selectbox("Sélectionnez un contact", list(contact_options.keys()))
            selected_id = contact_options[selected_label]
            current = dfc[dfc["id"]==selected_id].iloc[0].to_dict()
        else:
            current = {}

        col1, col2, col3 = st.columns(3)
        with col1:
            full_name = st.text_input("Nom complet *", value=current.get("full_name",""))
            function = st.text_input("Fonction", value=current.get("function",""))
            email = st.text_input("E-mail", value=current.get("email",""))
        with col2:
            phone = st.text_input("Téléphone", value=current.get("phone",""))
            mobile = st.text_input("Mobile", value=current.get("mobile",""))
            is_jury = st.checkbox("Jury à inviter ?", value=bool(current.get("is_jury", 0)))
        with col3:
            notes = st.text_area("Notes", value=current.get("notes",""), height=100)

        submitted = st.form_submit_button("Enregistrer le contact")
        if submitted:
            if not full_name.strip():
                st.error("Le nom du contact est obligatoire.")
            else:
                payload = {
                    "partner_id": partner_id,
                    "full_name": full_name.strip(),
                    "function": function.strip(),
                    "email": email.strip(),
                    "phone": phone.strip(),
                    "mobile": mobile.strip(),
                    "is_jury": 1 if is_jury else 0,
                    "notes": notes.strip()
                }
                if mode == "Modifier" and current.get("id"):
                    upsert_contact(payload, contact_id=int(current["id"]))
                    st.success("Contact mis à jour.")
                else:
                    upsert_contact(payload, contact_id=None)
                    st.success("Contact ajouté.")
                st.rerun()

    if not dfc.empty:
        st.markdown("#### Supprimer un contact")
        cids = dfc["id"].astype(str).tolist()
        to_del = st.selectbox("Sélectionner l’ID du contact", [""] + cids, key="del_contact_select")
        if to_del:
            if st.button("Supprimer ce contact", type="secondary"):
                delete_contact(int(to_del))
                st.warning("Contact supprimé.")
                st.rerun()

# ---------- VUES ----------
def list_view():
    st.subheader("Partenaires")
    top = st.container()
    with top:
        c1, c2 = st.columns([3,1])
        with c1:
            search = st.text_input("🔎 Rechercher (nom, activité, ville, responsable, tags…)", key="search_term")
        with c2:
            if st.button("➕ Nouveau partenaire", use_container_width=True):
                set_view("create")
                st.rerun()

    # Instant filtering
    q = (st.session_state.get("search_term") or "").strip().lower()
    df = run_query("SELECT * FROM partners ORDER BY company_name")
    if q:
        def row_match(row):
            hay = " ".join([str(row.get(col,"") or "") for col in ["company_name","activity","city","responsible","sector_class","tags"]]).lower()
            return q in hay
        df = df[df.apply(row_match, axis=1)]

    if df.empty:
        st.info("Aucun partenaire. Ajoutez le premier via **Nouveau partenaire**.")
        return

    # Grid of cards
    n_cols = 3
    rows = [df.iloc[i:i+n_cols] for i in range(0, len(df), n_cols)]
    for chunk in rows:
        cols = st.columns(n_cols)
        for col, (_, r) in zip(cols, chunk.iterrows()):
            with col:
                st.markdown(
                    f"""
                    <div style="border:1px solid #ddd;border-radius:12px;padding:12px; margin-bottom:12px;">
                        <div style="font-weight:700;font-size:1.05rem;">{r['company_name']}</div>
                        <div style="opacity:0.8;">{(r.get('city') or '')}</div>
                        <div style="opacity:0.8;">{(r.get('activity') or '')}</div>
                        <div style="margin-top:8px; font-size:0.9rem; opacity:0.8;">{(r.get('sector_class') or '')}</div>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Ouvrir la fiche", key=f"open_{int(r['id'])}"):
                    set_view("detail", int(r["id"]))
                    st.rerun()

def detail_view():
    data = get_selected_partner()
    if not data:
        st.warning("Aucun partenaire sélectionné.")
        if st.button("⬅️ Retour à la liste"):
            set_view("list")
            st.rerun()
        return

    top = st.container()
    with top:
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("⬅️ Retour à la liste", use_container_width=True):
                set_view("list")
                st.rerun()
        with c2:
            if st.button("➕ Nouveau partenaire", use_container_width=True):
                set_view("create")
                st.rerun()
        with c3:
            if st.button("🗑️ Supprimer ce partenaire", type="secondary", use_container_width=True):
                delete_partner(int(data["id"]))
                st.warning("Partenaire supprimé.")
                set_view("list")
                st.rerun()

    partner_form(existing=data)
    st.divider()
    contacts_block(partner_id=int(data["id"]))

def create_view():
    top = st.container()
    with top:
        if st.button("⬅️ Retour à la liste"):
            set_view("list")
            st.rerun()
    partner_form(existing=None)

# ---------- IMPORT ----------
def auto_map_headers(df):
    mapping = {}
    lower_cols = {c.lower().strip(): c for c in df.columns}
    for target, aliases in HEADER_MAP.items():
        for key, orig in lower_cols.items():
            if key == target:
                mapping[target] = orig
                break
        if target not in mapping:
            for alias in aliases:
                for key, orig in lower_cols.items():
                    if key == alias:
                        mapping[target] = orig
                        break
                if target in mapping:
                    break
    return mapping

def import_block():
    st.subheader("Import en lot (.csv, .xls, .xlsx) — Partenaires")
    uploaded = st.file_uploader("Importer un fichier de partenaires", type=["csv","xls","xlsx"])
    if not uploaded:
        st.info("Utilisez le modèle: partners_template.csv")
        return

    try:
        if uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            xls = pd.ExcelFile(uploaded)
            sheet = st.selectbox("Feuille à importer", xls.sheet_names)
            df = xls.parse(sheet)
    except Exception as e:
        st.error(f"Erreur de lecture du fichier: {e}")
        return

    st.write("Aperçu :")
    st.dataframe(df.head(), use_container_width=True)

    st.markdown("### Mapping des colonnes")
    auto = auto_map_headers(df)
    cols_map = {}
    for target in EXPECTED:
        default = auto.get(target, None)
        idx = 1 + list(df.columns).index(default) if (default in df.columns) else 0
        cols_map[target] = st.selectbox(f"{target}", ["---"] + list(df.columns), index=idx, key=f"map_{target}")

    if st.button("Importer"):
        if cols_map["company_name"] == "---":
            st.error("La colonne 'company_name' est obligatoire.")
            return
        inserted = 0
        for _, r in df.iterrows():
            payload = {}
            for t in EXPECTED:
                src = cols_map[t]
                val = "" if src == "---" else r.get(src, "")
                if pd.isna(val):
                    val = ""
                payload[t] = str(val)
            # employees_count to int
            try:
                payload["employees_count"] = int(float(payload["employees_count"])) if payload["employees_count"] else 0
            except:
                payload["employees_count"] = 0
            upsert_partner(payload, None)
            inserted += 1
        st.success(f"Import terminé: {inserted} partenaires insérés.")
        st.rerun()

# ---------- MAIN ----------
def main():
    st.set_page_config(page_title="ISM Partenaires", page_icon="🤝", layout="wide")
    ensure_schema()
    users = load_users()

    st.title("CRM Partenaires – ISM Fontaine L’Evêque")
    st.caption("Accès réservé aux enseignants.")

    # Connexion
    login(users)

    # Sidebar backup button (visible only when logged in)
    if "user_email" in st.session_state:
        download_db_button()

    if "user_email" not in st.session_state:
        st.info("Veuillez vous connecter pour accéder à la base de données.")
        st.stop()

    # Tabs: Partenaires (list/cards + detail) | Import
    tab1, tab2 = st.tabs(["Partenaires", "Import"])
    with tab1:
        view = get_view()
        if view == "list":
            list_view()
        elif view == "detail":
            detail_view()
        elif view == "create":
            create_view()
        else:
            set_view("list")
            list_view()
    with tab2:
        import_block()

if __name__ == "__main__":
    main()

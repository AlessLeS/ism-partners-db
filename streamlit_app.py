
import streamlit as st
import sqlite3
from contextlib import closing
from datetime import datetime
import pandas as pd
import yaml

DB_PATH = "ism_partners.db"
USERS_PATH = "users.yaml"

EXPECTED = ["company_name","address","number","postal_code","city","phone",
            "employees_count","website","responsible","role","email","activity","sector_class"]

HEADER_MAP = {
    "company_name": ["nom","nom de l’entreprise","nom de l'entreprise","entreprise","company"],
    "address": ["adresse","rue"],
    "number": ["numéro","numero","n°","num"],
    "postal_code": ["code postal","cp"],
    "city": ["localité","ville","commune","localite"],
    "phone": ["téléphone","telephone","tel"],
    "employees_count": ["personnes employées (nombre)","effectif","nb employés","nb employés (nombre)","employés"],
    "website": ["site internet","site web","site","url"],
    "responsible": ["responsable","nom du contact","contact"],
    "role": ["fonction","titre"],
    "email": ["e-mail","email","mail","e-mail 1","email 1","mail 1"],
    "activity": ["activité","activite"],
    "sector_class": ["classification sectorielle","secteur","categorie"]
}

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def ensure_schema():
    schema = """
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.executescript(schema)
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

def partner_form(existing=None):
    st.subheader("Fiche partenaire")
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
                    "sector_class": sector_class.strip()
                }
                pid = (existing or {}).get("id")
                upsert_partner(payload, partner_id=pid)
                st.success("Partenaire enregistré.")
                st.rerun()

def partners_table():
    st.subheader("Liste des partenaires")
    with st.expander("Filtres", expanded=True):
        q = st.text_input("Recherche (nom, activité, ville, responsable...)")
        city = st.text_input("Localité")
        sector = st.text_input("Classification sectorielle")

    query = "SELECT * FROM partners WHERE 1=1"
    params = []
    if q:
        query += " AND (company_name LIKE ? OR activity LIKE ? OR responsible LIKE ? OR comments LIKE ? OR city LIKE ?)"
        like = f"%{q}%"
        params += [like, like, like, like, like]
    if city:
        query += " AND city LIKE ?"
        params.append(f"%{city}%")
    if sector:
        query += " AND sector_class LIKE ?"
        params.append(f"%{sector}%")

    df = run_query(query, params)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty:
        csv_buffer = df.to_csv(index=False).encode("utf-8")
        st.download_button("Télécharger (CSV)", data=csv_buffer, file_name=f"partenaires_{datetime.now().date()}.csv", mime="text/csv")

        st.markdown("---")
        st.write("**Éditer / supprimer**")
        ids = df["id"].tolist()
        selected_id = st.selectbox("Sélectionner un partenaire par ID", [""] + [str(i) for i in ids])
        if selected_id:
            pid = int(selected_id)
            row = df[df["id"] == pid].iloc[0].to_dict()
            partner_form(existing=row)
            if st.button("Supprimer ce partenaire", type="secondary"):
                delete_partner(pid)
                st.warning("Partenaire supprimé.")
                st.rerun()

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
    st.subheader("Import en lot (.csv, .xls, .xlsx)")
    uploaded = st.file_uploader("Importer un fichier", type=["csv","xls","xlsx"])
    if not uploaded:
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
        idx = 1 + list(df.columns).index(default) if default in df.columns else 0
        cols_map[target] = st.selectbox(f"{target}", ["---"] + list(df.columns), index=idx)

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
        st.success(f"Import terminé: {inserted} lignes insérées.")
        st.rerun()

def main():
    st.set_page_config(page_title="ISM Partenaires", page_icon="🤝", layout="wide")
    ensure_schema()
    users = load_users()

    st.title("Base de données des partenaires – ISM Fontaine L’Evêque")
    st.caption("Accès réservé aux enseignants.")

    # Auth (peut être désactivé pour tests)
    st.sidebar.header("Connexion")
    login(users)
    if "user_email" not in st.session_state:
        st.info("Veuillez vous connecter pour accéder à la base de données.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Ajouter / Modifier", "Lister / Exporter", "Import"])
    with tab1:
        partner_form()
    with tab2:
        partners_table()
    with tab3:
        import_block()

if __name__ == "__main__":
    main()

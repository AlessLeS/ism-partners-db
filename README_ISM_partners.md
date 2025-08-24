# ISM Fontaine L’Evêque – CRM Partenaires

*Application Streamlit pour la gestion centralisée des partenaires et de leurs contacts.*

---

## 🎯 Objectif
- Gérer **les partenaires** et **plusieurs contacts par partenaire** (petit CRM).
- Interface unique **Partenaires** pour lister, rechercher, ouvrir une fiche, créer et modifier.
- Onglet **Import** pour charger des partenaires en lot (CSV/Excel).

---

## 📋 Modèle de données (v4)
### Table `partners`
- company_name, address, number, postal_code, city, phone, employees_count, website,
- responsible, role, email, activity, sector_class, **tags**, created_at

### Table `contacts` (1‑N avec `partners`)
- partner_id (FK), **full_name**, function, email, phone, mobile, **is_jury**, notes, created_at

---

## 🚀 Fonctionnalités clés
- **Partenaires (onglet unique)** : vue liste filtrable + ouverture d’une fiche détaillée
- **Création/édition** du partenaire dans la fiche
- **Contacts liés** : liste, ajout, modification, suppression
- **Export CSV** de la liste filtrée
- **Import** partenaires (.csv/.xls/.xlsx) avec mapping automatique des colonnes
- **Sauvegarde** : téléchargement de la base SQLite depuis la sidebar (enseignants connectés)

---

## 🛠 Installation
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

> Identifiants de démo à adapter dans `users.yaml`.

---

## 📦 Fichiers utiles
- `streamlit_app.py` – application principale (nouvelle UI « Partenaires »)
- `schema.sql` – schéma de BD (inclut `contacts`)
- `partners_template.csv` – modèle d’import partenaires
- `contacts_template.csv` – **nouveau** modèle d’import des contacts (optionnel, via script personnalisé)
- `requirements.txt`, `users.yaml`

---

## 🔐 Sécurité
- Connexion **enseignants uniquement** via `users.yaml`
- Téléchargement de sauvegarde SQLite via la sidebar

---

## 🗺 Roadmap légère
- Import des **contacts** depuis l’onglet Import (actuellement: partenaires uniquement)
- Statistiques simples (nb partenaires par secteur, etc.)

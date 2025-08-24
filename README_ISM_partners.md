# ISM Fontaine L’Evêque – CRM Partenaires (vue cartes + recherche instantanée)

Cette version apporte une **vue “cartes”** dès l’arrivée sur l’onglet *Partenaires*, avec une **barre de recherche instantanée** et une **navigation claire** vers la fiche complète.

## ✅ Ce qui change dans l’UI
- **Accueil “Partenaires” = liste de cartes** (3 colonnes) pour **tous** les partenaires.
- **Recherche en direct** (nom, activité, ville, responsable, tags…) qui réduit la liste **au fil de la frappe**.
- **Clique sur “Ouvrir la fiche”** sur une carte → **fiche complète** (édition) + **bloc Contacts** (ajout/modif/suppression).
- **Bouton “➕ Nouveau partenaire”** → page dédiée d’encodage. Une fois enregistré, redirection vers la fiche.

## 🧭 Navigation interne
- Vue **list** (par défaut) → Vue **detail** (après clic) → Vue **create** (nouveau partenaire).
- Boutons Retour/Nouveau/Supprimer depuis la fiche.

## 🧱 Données
- Table `partners` (tags ajoutés) et table `contacts` (1‑N) avec suppression en cascade.

## 🚀 Démarrage
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

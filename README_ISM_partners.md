# ISM Fontaine L’Evêque – Base de données Partenaires

![Bannière du projet](docs/banner.png)  
*Application Streamlit pour la gestion centralisée des partenaires externes de l'ISM Fontaine L’Evêque.*

---

## 🎯 Objectif du projet
- Centraliser toutes les informations sur les **partenaires externes** de l’école.
- Offrir aux enseignants une interface simple pour **ajouter**, **modifier**, **rechercher** et **exporter** des partenaires.
- Faciliter l’**importation des fichiers Excel ou CSV existants** via un mapping automatique des colonnes.
- Fournir aux élèves des listes filtrées **imprimées** par les enseignants.

---

## 📋 Champs de la base de données (V3)
| Champ                        | Description |
|------------------------------|-------------|
| **Nom de l’entreprise**      | Raison sociale du partenaire |
| **Adresse**                  | Rue/Voie |
| **Numéro**                   | Numéro dans l’adresse |
| **Code postal**               | Code postal de la localité |
| **Localité**                 | Ville ou commune |
| **Téléphone**                 | Numéro principal |
| **Personnes employées**       | Nombre d’employés |
| **Site internet**             | URL |
| **Responsable**               | Nom du responsable |
| **Fonction**                  | Poste/Fonction du responsable |
| **E-mail**                    | Contact e-mail principal |
| **Activité**                  | Domaine d’activité |
| **Classification sectorielle**| Secteur d’activité |

---

## 🚀 Fonctionnalités

### Interface d’accueil
![Capture accueil](docs/screenshot_home.png)

- **Connexion enseignants** via `users.yaml`
- Accès restreint (pas d’accès élèves)

### Formulaire partenaire
![Capture formulaire](docs/screenshot_form.png)

- Formulaire simple et clair pour saisir les champs obligatoires
- Modification facile des partenaires existants

### Recherche et export
![Capture recherche](docs/screenshot_search.png)

- Filtrage par nom, ville, secteur, responsable…
- Export CSV des résultats filtrés

### Import intelligent
![Capture import](docs/screenshot_import.png)

- Support des formats `.csv`, `.xls`, `.xlsx`
- Sélection de la feuille Excel
- Mapping automatique des colonnes avec possibilité d’ajustement

---

## 🛠 Installation locale

1. **Cloner le dépôt** :
```bash
git clone https://github.com/<TON_USER>/ism-partners-db.git
cd ism-partners-db
```

2. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

3. **Lancer l’application** :
```bash
streamlit run streamlit_app.py
```

4. **Connexion** :
- Identifiant : `enseignant1@ismfontaine.be`
- Mot de passe : `demo1234`  
(*À modifier dans `users.yaml`*)

---

## 🌐 Déploiement sur Streamlit Cloud

1. Créez un compte sur [Streamlit Cloud](https://streamlit.io/cloud).
2. Liez votre dépôt GitHub.
3. Paramètres :
   - **Main file path** : `streamlit_app.py`
   - **Branch** : `main`
4. **Deploy** et récupérer le lien public.
5. Modifier `users.yaml` avant diffusion.

---

## 📂 Structure du projet
```
ism-partners-db/
├── streamlit_app.py         # Application Streamlit
├── schema.sql               # Schéma de la base SQLite
├── partners_template.csv    # Modèle d’import
├── requirements.txt         # Dépendances Python
├── users.yaml               # Comptes enseignants
└── README.md                # Documentation
```

---

## 🔒 Sécurité
- Authentification **enseignants uniquement**.
- Les élèves n’ont pas accès à l’interface, uniquement aux exports imprimés.
- Gestion des comptes via `users.yaml`.

---

## 📌 Évolutions possibles
- Ajout d’un champ **Commentaires**
- Gestion des **sections** associées aux partenaires
- **SSO Microsoft 365** pour connexion automatique
- Dashboard statistique

---

## 📜 Licence
Projet interne ISM Fontaine L’Evêque – **usage réservé**.

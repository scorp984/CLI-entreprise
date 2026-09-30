# Documentation API — Gestion des Employés

Projet **CLI-entreprise** — API REST développée avec Flask (Python) et MySQL.

## Informations générales

| | |
|---|---|
| **Base URL** | `http://127.0.0.1:5000` |
| **Format** | JSON |
| **Authentification** | Session Flask par cookie; les opérations d'administration sont réservées au PDG |

Toutes les requêtes et réponses utilisent le format JSON. Le header `Content-Type: application/json` doit être envoyé pour les requêtes `POST` et `PUT`.

---

## Table des routes

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/auth/login` | Ouvre une session |
| `POST` | `/auth/logout` | Ferme la session |
| `GET` | `/auth/me` | Retourne le compte connecté |
| `GET` | `/auth/comptes` | Liste les comptes (PDG) |
| `POST` | `/auth/comptes` | Crée un compte et sa fiche employé (PDG) |
| `PUT` | `/auth/comptes/<id>` | Modifie un compte (PDG) |
| `DELETE` | `/auth/comptes/<id>` | Supprime un compte (PDG) |
| `GET` | `/developpeur/fiche` | Charge la fiche du développeur connecté |
| `POST` | `/developpeur/fiche` | Crée sa fiche technique |
| `PUT` | `/developpeur/fiche` | Modifie sa fiche technique |
| `GET` | `/developpeur/projets/<projet_id>/fichiers` | Liste les fichiers et leur historique pour un projet |
| `POST` | `/developpeur/projets/<projet_id>/fichiers` | Ajoute un fichier à une étape du projet |
| `GET` | `/developpeur/fichiers/<id>` | Télécharge un fichier actif du projet |
| `DELETE` | `/developpeur/fichiers/<id>` | Supprime logiquement un fichier déposé par le développeur connecté |
| `GET` | `/manager/projets` | Liste les projets, éventuellement filtrés par développeur |
| `POST` | `/manager/projets` | Attribue un projet à un ou plusieurs développeurs |
| `GET` | `/manager/projets/<projet_id>/fichiers` | Liste les fichiers déposés pour un projet |
| `GET` | `/manager/fichiers/<id>` | Télécharge un fichier actif d'un projet |
| `GET` | `/manager/developpeurs/<id>/fiche` | Retourne les projets et tâches d'un développeur |
| `GET` | `/manager/qui-fait-quoi` | Recherche une tâche affectée |
| `GET` | `/employes` | Récupère la liste de tous les employés |
| `POST` | `/employes` | Ajoute un nouvel employé |
| `PUT` | `/employes/<id>` | Met à jour un employé existant |
| `DELETE` | `/employes/<id>` | Supprime un employé |

Les routes protégées exigent le cookie de session reçu à la connexion. Un visiteur reçoit `401`; un compte connecté sans rôle PDG reçoit `403` pour les opérations d'administration.

## Gestion des comptes

`GET /auth/comptes` renvoie `id`, `identifiant`, `role`, `actif` et `date_creation`. Les mots de passe hashes ne sont jamais retournés.

`POST /auth/comptes` exige une session PDG et crée un compte ainsi qu'une fiche employé liée au compte. Les rôles proposés à la création sont `manager`, `comptable` et `developpeur`; le rôle PDG reste créé par le script serveur.

La liaison et la table de fiche sont ajoutées par `database/migration_fiche_technique_developpeur.sql`. Sur une base qui ne l'a pas encore reçue, exécuter une seule fois depuis PowerShell à la racine du dépôt :

```powershell
Get-Content -Raw ".\logiciel\database\migration_fiche_technique_developpeur.sql" |
  & "C:\UwAmp\bin\database\mysql-5.6.20\bin\mysql.exe" -u patron -p cli_entreprise
```

Pour les comptes développeur déjà présents lors de la migration, associer chaque compte à la bonne fiche employé après avoir vérifié les deux listes :

```sql
SELECT id, identifiant FROM comptes WHERE role = 'developpeur' AND employe_id IS NULL;
SELECT id, nom, prenom, date_embauche FROM employes WHERE poste = 'developpeur';
UPDATE comptes SET employe_id = 7 WHERE id = 9;
```

Remplacer `7` par l'identifiant employé et `9` par l'identifiant du compte qui correspondent à la même personne. Les comptes créés ensuite par `POST /auth/comptes` sont liés automatiquement.

`PUT /auth/comptes/<id>` accepte un ou plusieurs champs parmi `identifiant`, `role`, `mot_de_passe` et `actif`. Le mot de passe est rehaché; omettre `mot_de_passe` le laisse inchangé. `actif` doit être un booléen. Le dernier compte PDG actif ne peut pas être désactivé, rétrogradé ou supprimé, et un utilisateur ne peut pas supprimer son propre compte.

`DELETE /auth/comptes/<id>` supprime le compte uniquement. La fiche employé est conservée et son lien au compte est supprimé.

## Fiche technique développeur

Appliquer une fois la migration `database/migration_fiche_technique_developpeur.sql` à la base. Les comptes développeur créés avant cette migration doivent être associés manuellement à leur fiche employé, après vérification des identifiants :

```sql
SELECT id, identifiant FROM comptes WHERE role = 'developpeur' AND employe_id IS NULL;
SELECT id, nom, prenom, date_embauche FROM employes WHERE poste = 'developpeur';
UPDATE comptes SET employe_id = 7 WHERE id = 9;
```

Remplacer `7` et `9` par les identifiants correspondant à la bonne personne. Les nouveaux comptes créés par l'API sont liés automatiquement.

La page du développeur charge `GET /developpeur/fiche`. Si aucune fiche n'existe, le formulaire permet de la créer avec `POST`; ensuite, les changements utilisent `PUT`. L'API n'accepte que le développeur connecté et déduit son employé depuis la session.

Exemple de corps JSON pour `POST` ou `PUT` :

```json
{
  "competences": "Python, SQL",
  "disponibilite": "Temps plein",
  "experience_avant_embauche": 2
}
```

`experience_avant_embauche` est le nombre d'années déclaré avant l'embauche. L'expérience totale affichée est ce nombre additionné aux années complètes écoulées depuis `employes.date_embauche`; elle augmente à chaque anniversaire d'embauche.

## Routes manager

Ces routes exigent une session de rôle `manager` ou `pdg`.

Pour permettre les projets partagés, appliquer une seule fois `database/migration_equipe_projet.sql` :

```powershell
Get-Content -Raw ".\logiciel\database\migration_equipe_projet.sql" |
  & "C:\UwAmp\bin\database\mysql-5.6.20\bin\mysql.exe" -u patron -p cli_entreprise
```

Pour assigner des tâches différentes aux membres, appliquer aussi une seule fois la migration suivante depuis la racine du dépôt :

```powershell
Get-Content -Raw ".\logiciel\database\migration_taches_developpeur.sql" |
  & "C:\UwAmp\bin\database\mysql-5.6.20\bin\mysql.exe" -u patron -p cli_entreprise
```

La migration reprend les projets existants et leurs développeurs actuels. `POST /manager/projets` accepte `employe_ids` (un ou plusieurs identifiants), un nom de projet, une date ISO et une liste de tâches. Le projet, ses membres et ses tâches sont enregistrés dans une même transaction :

```json
{
  "employe_ids": [7, 8],
  "nom": "Refonte API",
  "taches": [
    {"employe_id": 7, "description": "Développement frontend"},
    {"employe_id": 8, "description": "Développement backend"}
  ],
  "date_debut": "2026-09-26"
}
```

L'ancien champ `employe_id` reste accepté pour attribuer un projet à un seul développeur. Chaque membre voit ses tâches assignées sur sa fiche. Les anciennes tâches sans assignation sont considérées comme communes. Dans « Qui fait quoi ? », le manager peut consulter la fiche, tous les projets de la personne, la composition des équipes et les tâches assignées à chaque développeur.

`GET /manager/projets` renvoie tous les projets avec leur développeur et leurs tâches. Le paramètre facultatif `employe_id` permet de filtrer les projets.

`GET /manager/developpeurs/<id>/fiche` retourne la fiche d'un développeur, avec ses projets et les tâches associées.

La réponse inclut également `fiche_technique` quand le développeur a renseigné ses compétences, sa disponibilité et son expérience.

## Fiche développeur

`GET /developpeur/fiche` retourne la fiche du développeur connecté et indique `fiche_complete: false` s'il doit encore la remplir. `POST /developpeur/fiche` crée sa fiche; `PUT /developpeur/fiche` la modifie. Ces routes utilisent le compte de la session et refusent les autres rôles.

Le champ `experience_avant_embauche` correspond à l'expérience déclarée avant son arrivée. L'API calcule l'expérience totale en lui ajoutant les années complètes depuis la date `employes.date_embauche`; un an supplémentaire n'est compté qu'à chaque anniversaire d'embauche.

## Fichiers de projet

Appliquer une fois `database/migration_fichiers_projets.sql` à la base depuis la racine du dépôt :

```powershell
Get-Content -Raw ".\logiciel\database\migration_fichiers_projets.sql" |
  & "C:\UwAmp\bin\database\mysql-5.6.20\bin\mysql.exe" -u patron -p cli_entreprise
```

Les fichiers sont stockés sous `logiciel/storage/fichiers_projets`, hors du dossier public du frontend. Le chemin peut être remplacé avec la variable d'environnement `PROJECT_FILES_DIRECTORY`.

Les routes de fichiers sont réservées au développeur connecté et vérifient son appartenance au projet via `projet_developpeurs`. Pour déposer un ou plusieurs fichiers de la même étape, envoyer une requête `multipart/form-data` à `POST /developpeur/projets/<projet_id>/fichiers` avec un champ `fichier` répété et un champ `etape` (`diagramme`, `dossier` ou `compte-rendu`). La requête entière, fichiers cumulés, est limitée à 25 Mo; les extensions acceptées dépendent de l'étape.

`GET /developpeur/projets/<projet_id>/fichiers` retourne les métadonnées, y compris les fichiers supprimés afin de conserver l'historique. `DELETE /developpeur/fichiers/<id>` marque le fichier comme supprimé sans effacer son contenu stocké; il n'est alors plus téléchargeable. Seul le développeur qui l'a déposé peut le supprimer.

Le manager et le PDG peuvent consulter `GET /manager/projets/<projet_id>/fichiers` pour voir les documents, leur étape, leur auteur et leur statut. Le téléchargement se fait avec `GET /manager/fichiers/<id>`. Les fichiers supprimés restent visibles dans l'historique mais ne sont pas téléchargeables.

`GET /manager/qui-fait-quoi?employe_id=7&projet=Refonte%20API&tache=Développement` recherche une tâche exacte et retourne le développeur, le projet et la tâche correspondants.

Les projets peuvent être partagés entre plusieurs développeurs grâce à `projet_developpeurs`. Les tâches peuvent être rattachées à un développeur via `taches.employe_id`; appliquer les migrations d'équipe et de tâches décrites plus haut avant d'utiliser ces fonctionnalités.

---

## GET /employes

Récupère la liste complète des employés enregistrés en base de données.

### Requête

```http
GET /employes HTTP/1.1
Host: 127.0.0.1:5000
```

### Réponse — succès (200)

```json
[
  {
    "id": 1,
    "nom": "Dupont",
    "prenom": "Marie",
    "poste": "Développeuse",
    "date_embauche": "2023-05-12",
    "salaire": 2800
  },
  {
    "id": 2,
    "nom": "Martin",
    "prenom": "Léo",
    "poste": "Comptable",
    "date_embauche": "2021-09-01",
    "salaire": 2500
  }
]
```

### Réponse — erreur (400)

```json
{
  "error": "Erreur de connexion à la base de données"
}
```

---

## POST /employes

Ajoute un nouvel employé à la base de données.

### Champs requis

| Champ | Type | Description |
|---|---|---|
| `nom` | string | Nom de famille |
| `prenom` | string | Prénom |
| `poste` | string | Intitulé du poste |
| `date_embauche` | string (`YYYY-MM-DD`) | Date d'embauche |
| `salaire` | number | Salaire mensuel |

Tous les champs sont **obligatoires**. Si un champ est manquant ou vide, la requête est rejetée.

### Requête

```http
POST /employes HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json

{
  "nom": "Dupont",
  "prenom": "Marie",
  "poste": "Développeuse",
  "date_embauche": "2023-05-12",
  "salaire": 2800
}
```

### Réponse — succès (201)

```json
{
  "message": "Employé ajouté avec succès"
}
```

### Réponse — erreur (400)

Corps manquant ou non conforme :

```json
{
  "error": "Le corps JSON est obligatoire"
}
```

Champ(s) manquant(s) :

```json
{
  "error": "Tous les champs sont obligatoires"
}
```

Connexion base de données échouée :

```json
{
  "error": "Erreur de connexion à la base de données"
}
```

---

## PUT /employes/{id}

Met à jour les informations d'un employé existant. Tous les champs doivent être renvoyés (mise à jour complète, pas partielle).

### Paramètre d'URL

| Paramètre | Type | Description |
|---|---|---|
| `id` | integer | Identifiant de l'employé à modifier |

### Champs requis

Identiques à `POST /employes` : `nom`, `prenom`, `poste`, `date_embauche`, `salaire`.

### Requête

```http
PUT /employes/1 HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json

{
  "nom": "Dupont",
  "prenom": "Marie",
  "poste": "Lead Développeuse",
  "date_embauche": "2023-05-12",
  "salaire": 3200
}
```

### Réponse — succès (200)

```json
{
  "message": "Employé mis à jour avec succès"
}
```

### Réponse — erreur (404)

L'`id` fourni ne correspond à aucun employé :

```json
{
  "error": "Employé introuvable"
}
```

### Réponse — erreur (400)

```json
{
  "error": "Le corps JSON est obligatoire"
}
```

```json
{
  "error": "Tous les champs sont obligatoires"
}
```

---

## DELETE /employes/{id}

Supprime un employé de la base de données.

### Paramètre d'URL

| Paramètre | Type | Description |
|---|---|---|
| `id` | integer | Identifiant de l'employé à supprimer |

### Requête

```http
DELETE /employes/1 HTTP/1.1
Host: 127.0.0.1:5000
```

### Réponse — succès (200)

```json
{
  "message": "Employé supprimé avec succès"
}
```

### Réponse — erreur (404)

```json
{
  "error": "Employé introuvable"
}
```

---

## Codes de statut HTTP utilisés

| Code | Signification | Utilisé quand |
|---|---|---|
| `200` | OK | Lecture, mise à jour ou suppression réussie |
| `201` | Created | Création réussie |
| `400` | Bad Request | JSON manquant/invalide, champ requis manquant, erreur de connexion DB |
| `404` | Not Found | L'employé demandé n'existe pas |

> **Note technique** : les erreurs de connexion à la base de données renvoient actuellement un code `400`. D'un point de vue strict, ce type d'erreur est plutôt côté serveur et devrait renvoyer un `500 Internal Server Error`. Point d'amélioration possible.

---

## Sécurité

- Toutes les requêtes SQL utilisent des **requêtes paramétrées** (`%s` + tuple de valeurs) plutôt que de la concaténation de chaînes, ce qui protège contre les **injections SQL**.
- Aucune authentification n'est actuellement en place : n'importe qui ayant accès au serveur peut lire, créer, modifier ou supprimer des employés. À ajouter avant tout déploiement public (ex. clé API, JWT, ou authentification basique).
- L'option `debug=True` du serveur Flask ne doit **jamais** être activée en production : elle expose des informations sensibles en cas d'erreur.

---

## Exemples avec `curl`

```bash
# Lister tous les employés
curl http://127.0.0.1:5000/employes

# Ajouter un employé
curl -X POST http://127.0.0.1:5000/employes \
  -H "Content-Type: application/json" \
  -d '{"nom":"Dupont","prenom":"Marie","poste":"Développeuse","date_embauche":"2023-05-12","salaire":2800}'

# Mettre à jour un employé (id = 1)
curl -X PUT http://127.0.0.1:5000/employes/1 \
  -H "Content-Type: application/json" \
  -d '{"nom":"Dupont","prenom":"Marie","poste":"Lead Développeuse","date_embauche":"2023-05-12","salaire":3200}'

# Supprimer un employé (id = 1)
curl -X DELETE http://127.0.0.1:5000/employes/1
```
